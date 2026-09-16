"""Sensor ingestion and validation service.

Serves as the single authoritative ingestion layer for all transports:
USB Serial, HTTP, and Wi-Fi.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from collections import deque
from threading import Lock
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.sensor import SensorData, SensorBatch
from app.models.processed_metrics import ProcessedMetrics
from app.schemas.sensor import (
    CanonicalSensorPacket,
    SensorBatchPayload,
    SensorIngestResponse,
    SensorQuality,
    SensorTransport,
)
from app.services.device_service import DeviceService
from app.services.live_cache import live_sensor_cache
from app.services.sensor_queue_writer import sensor_queue_writer
from app.processing.buffer import buffer_manager
from app.processing.signal_processing import compute_vitals_from_buffer
from app.core.exceptions import InvalidSensorPacketException
from app.core.logging import logger


class IngestionMetricsTracker:
    """Thread-safe tracker for sampling rate and packet statistics per device."""

    def __init__(self, history_len: int = 50):
        self.history_len = history_len
        self._timestamps: Dict[str, deque] = {}
        self._last_sensor_ts: Dict[str, datetime] = {}
        self._lock = Lock()

    def record_packet(self, device_id: str, sensor_ts: datetime, received_at: datetime) -> Dict[str, Any]:
        with self._lock:
            if device_id not in self._timestamps:
                self._timestamps[device_id] = deque(maxlen=self.history_len)

            q = self._timestamps[device_id]
            q.append(received_at)

            # Check out-of-order
            last_ts = self._last_sensor_ts.get(device_id)
            is_out_of_order = False
            if last_ts is not None and sensor_ts < last_ts:
                is_out_of_order = True
            else:
                self._last_sensor_ts[device_id] = sensor_ts

            # Calculate rolling sampling rate
            sampling_rate_hz = None
            if len(q) >= 10:
                duration_sec = (q[-1] - q[0]).total_seconds()
                if duration_sec > 0:
                    sampling_rate_hz = round((len(q) - 1) / duration_sec, 2)

            return {
                "is_out_of_order": is_out_of_order,
                "sampling_rate_hz": sampling_rate_hz,
            }


metrics_tracker = IngestionMetricsTracker()


class SensorService:

    @staticmethod
    def ingest_canonical_packet(
        db: Session, packet: CanonicalSensorPacket
    ) -> SensorIngestResponse:
        """Canonical ingestion method used by USB Serial, HTTP, and Wi-Fi transports."""
        now_utc = packet.received_at or datetime.now(timezone.utc)
        transport_str = packet.transport.value if hasattr(packet.transport, "value") else str(packet.transport)

        # Check duplicate if DB session is present
        is_duplicate = False
        if db is not None:
            try:
                if packet.sequence_number is not None:
                    existing = db.query(SensorData).filter(
                        and_(
                            SensorData.device_id == packet.device_id,
                            SensorData.sequence_number == packet.sequence_number,
                        )
                    ).first()
                    if existing:
                        is_duplicate = True
            except Exception:
                pass

        if is_duplicate:
            return SensorIngestResponse(
                accepted=False,
                device_id=packet.device_id,
                received_at=now_utc,
                sensor_timestamp=packet.sensor_timestamp,
                quality=packet.quality or SensorQuality.GOOD,
                is_duplicate=True,
                is_out_of_order=False,
                packets_received=1,
                packets_ingested=0,
                message="Duplicate packet detected; discarded to maintain database integrity",
            )

        # 1. Update live sensor cache immediately
        live_sample = live_sensor_cache.update(packet)

        # 2. Track metrics (ordering & sampling rate)
        metrics = metrics_tracker.record_packet(
            packet.device_id, packet.sensor_timestamp, now_utc
        )

        # 3. Add to rolling buffer in RAM for signal processing
        sample_dict = packet.model_dump()
        buffer_manager.add_sample(packet.device_id, sample_dict)

        # 4. Enqueue for asynchronous background database persistence
        sensor_queue_writer.enqueue(packet)

        # 5. If db session provided (e.g., in unit tests), attempt non-blocking sync write
        if db is not None:
            try:
                DeviceService.update_heartbeat(
                    db, packet.device_id, transport=transport_str, is_valid=True
                )
                db_record = SensorData(
                    device_id=packet.device_id,
                    sensor_timestamp=packet.sensor_timestamp,
                    received_at=now_utc,
                    sequence_number=packet.sequence_number,
                    transport=transport_str,
                    quality=packet.quality.value if hasattr(packet.quality, "value") else str(packet.quality),
                    ir=packet.ir,
                    red=packet.red,
                    accel_x=packet.accel_x,
                    accel_y=packet.accel_y,
                    accel_z=packet.accel_z,
                    gyro_x=packet.gyro_x,
                    gyro_y=packet.gyro_y,
                    gyro_z=packet.gyro_z,
                    temp_f=packet.temperature,
                    gsr_raw=packet.gsr_raw,
                    gsr_voltage=packet.gsr_voltage,
                )
                db.add(db_record)
                db.commit()
            except Exception as exc:
                if db:
                    db.rollback()
                logger.warning(f"Background DB write deferred for {packet.device_id}: {exc}")

        return SensorIngestResponse(
            accepted=True,
            device_id=packet.device_id,
            received_at=now_utc,
            sensor_timestamp=packet.sensor_timestamp,
            quality=packet.quality or SensorQuality.GOOD,
            is_duplicate=False,
            is_out_of_order=metrics["is_out_of_order"],
            packets_received=1,
            packets_ingested=1,
            sampling_rate_hz=metrics["sampling_rate_hz"],
            message="Packet successfully validated and updated in live memory cache",
        )

    # Alias for backward compatibility
    ingest_single_packet = ingest_canonical_packet

    @staticmethod
    def ingest_payload(
        payload: Union[SensorBatchPayload, CanonicalSensorPacket],
        db: Optional[Session] = None,
    ) -> SensorIngestResponse:
        """Ingests batched or single sensor packet payload."""
        packets: List[CanonicalSensorPacket] = []

        if isinstance(payload, SensorBatchPayload):
            raw_packets = payload.readings or payload.packets
            if not raw_packets:
                raise InvalidSensorPacketException("Batch payload must contain at least 1 reading in 'readings' or 'packets'")

            batch_device_id = payload.device_id
            batch_transport = payload.transport

            for p in raw_packets:
                if (not p.device_id or p.device_id == "SANJEEVNI-ESP32-001") and batch_device_id:
                    p.device_id = batch_device_id
                if batch_transport:
                    p.transport = batch_transport if isinstance(batch_transport, SensorTransport) else SensorTransport(batch_transport)
                packets.append(p)
        elif isinstance(payload, CanonicalSensorPacket):
            packets = [payload]
        else:
            raise InvalidSensorPacketException("Unrecognized payload format")

        if not packets:
            raise InvalidSensorPacketException("No valid sensor readings found in payload")

        device_id = packets[0].device_id or "SANJEEVNI-ESP32-001"
        now_utc = datetime.now(timezone.utc)

        # Check duplicate if DB session is supplied
        is_duplicate = False
        if db is not None and len(packets) == 1 and packets[0].sequence_number is not None:
            try:
                existing = db.query(SensorData).filter(
                    and_(
                        SensorData.device_id == packets[0].device_id,
                        SensorData.sequence_number == packets[0].sequence_number,
                    )
                ).first()
                if existing:
                    is_duplicate = True
            except Exception:
                pass

        if is_duplicate:
            return SensorIngestResponse(
                status="duplicate",
                accepted=False,
                success=False,
                device_id=packets[0].device_id,
                received_at=now_utc,
                sensor_timestamp=packets[0].sensor_timestamp,
                quality=packets[0].quality or SensorQuality.GOOD,
                is_duplicate=True,
                is_out_of_order=False,
                packets_received=1,
                packets_ingested=0,
                message="Duplicate packet detected; discarded to maintain database integrity",
            )

        # 1. Update live sensor cache immediately with all readings in batch
        live_sensor_cache.update_batch(packets)

        # 2. Add sample dicts to rolling signal processing buffer manager
        sample_dicts = [p.model_dump() for p in packets]
        buffer_manager.add_batch(device_id, sample_dicts)

        # 3. Track metrics & identify latest sequence number
        latest_seq = None
        is_out_of_order = False
        for p in packets:
            metrics = metrics_tracker.record_packet(
                p.device_id, p.sensor_timestamp, p.received_at or now_utc
            )
            if metrics.get("is_out_of_order"):
                is_out_of_order = True
            if p.sequence_number is not None:
                if latest_seq is None or p.sequence_number > latest_seq:
                    latest_seq = p.sequence_number

        # 4. Enqueue all packets into background database queue
        sensor_queue_writer.enqueue_batch(packets)

        # 5. If db session provided (e.g. unit tests), execute synchronous write
        if db is not None:
            try:
                for p in packets:
                    transport_str = p.transport.value if hasattr(p.transport, "value") else str(p.transport)
                    DeviceService.update_heartbeat(db, p.device_id, transport=transport_str, is_valid=True)
                    db_record = SensorData(
                        device_id=p.device_id,
                        sensor_timestamp=p.sensor_timestamp,
                        received_at=p.received_at or now_utc,
                        sequence_number=p.sequence_number,
                        transport=transport_str,
                        quality=p.quality.value if hasattr(p.quality, "value") else str(p.quality),
                        ir=p.ir,
                        red=p.red,
                        accel_x=int(round(p.accel_x)),
                        accel_y=int(round(p.accel_y)),
                        accel_z=int(round(p.accel_z)),
                        gyro_x=int(round(p.gyro_x)),
                        gyro_y=int(round(p.gyro_y)),
                        gyro_z=int(round(p.gyro_z)),
                        temp_f=p.temperature,
                        gsr_raw=p.gsr_raw,
                        gsr_voltage=p.gsr_voltage,
                    )
                    db.add(db_record)
                db.commit()
            except Exception as exc:
                if db:
                    db.rollback()
                logger.warning(f"Sync DB write in ingest_payload deferred: {exc}")

        first_seq = packets[0].sequence_number
        last_seq = packets[-1].sequence_number
        logger.info(
            f"SENSOR BATCH | device={device_id} | received={len(packets)} | first_seq={first_seq} | last_seq={last_seq}"
        )

        return SensorIngestResponse(
            status="success",
            accepted=True,
            success=True,
            device_id=device_id,
            received=len(packets),
            latest_sequence_number=latest_seq if latest_seq is not None else last_seq,
            received_at=now_utc,
            sensor_timestamp=packets[-1].sensor_timestamp,
            quality=packets[-1].quality or SensorQuality.GOOD,
            is_duplicate=False,
            is_out_of_order=is_out_of_order,
            packets_received=len(packets),
            packets_ingested=len(packets),
            message=f"Successfully ingested batch of {len(packets)} sensor readings",
        )

    @staticmethod
    def ingest_batch(
        db: Session, device_id: str, packets: List[CanonicalSensorPacket]
    ) -> SensorIngestResponse:
        """Validates and persists a batch of real sensor packets."""
        if not packets:
            raise InvalidSensorPacketException("Batch cannot be empty")

        DeviceService.update_heartbeat(db, device_id, transport="HTTP", is_valid=True)

        sample_dicts = [p.model_dump() for p in packets]
        buffer_manager.add_batch(device_id, sample_dicts)

        now_utc = datetime.now(timezone.utc)
        db_records = [
            SensorData(
                device_id=device_id,
                sensor_timestamp=p.sensor_timestamp,
                received_at=now_utc,
                sequence_number=p.sequence_number,
                transport=p.transport.value if hasattr(p.transport, "value") else str(p.transport),
                quality=p.quality.value if hasattr(p.quality, "value") else str(p.quality),
                ir=p.ir,
                red=p.red,
                accel_x=p.accel_x,
                accel_y=p.accel_y,
                accel_z=p.accel_z,
                gyro_x=p.gyro_x,
                gyro_y=p.gyro_y,
                gyro_z=p.gyro_z,
                temp_f=p.temperature,
                gsr_raw=p.gsr_raw,
                gsr_voltage=p.gsr_voltage,
            )
            for p in packets
        ]
        db.add_all(db_records)
        db.flush()

        batch_record = SensorBatch(
            batch_id=str(uuid.uuid4()),
            device_id=device_id,
            sample_count=len(packets),
            start_timestamp=packets[0].sensor_timestamp,
            end_timestamp=packets[-1].sensor_timestamp,
            transport="HTTP",
        )
        db.add(batch_record)
        db.commit()

        return SensorIngestResponse(
            accepted=True,
            device_id=device_id,
            received_at=now_utc,
            sensor_timestamp=packets[-1].sensor_timestamp,
            quality=packets[-1].quality or SensorQuality.GOOD,
            packets_received=len(packets),
            packets_ingested=len(packets),
            message=f"Successfully ingested batch of {len(packets)} sensor packets",
        )
