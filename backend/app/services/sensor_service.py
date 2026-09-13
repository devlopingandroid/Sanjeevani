"""Sensor ingestion and validation service.

Serves as the single authoritative ingestion layer for all transports:
USB Serial, HTTP, and Wi-Fi.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import deque
from threading import Lock
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.sensor import SensorData, SensorBatch
from app.models.processed_metrics import ProcessedMetrics
from app.schemas.sensor import (
    CanonicalSensorPacket,
    SensorIngestResponse,
    SensorQuality,
    SensorTransport,
)
from app.services.device_service import DeviceService
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

        # 1. Update device heartbeat and metrics
        device = DeviceService.update_heartbeat(
            db, packet.device_id, transport=transport_str, is_valid=True
        )

        # 2. Duplicate Detection
        # If sequence number present, check by (device_id, sequence_number)
        is_duplicate = False
        if packet.sequence_number is not None:
            existing = (
                db.query(SensorData)
                .filter(
                    and_(
                        SensorData.device_id == packet.device_id,
                        SensorData.sequence_number == packet.sequence_number,
                    )
                )
                .first()
            )
            if existing:
                is_duplicate = True
        else:
            # Check by (device_id, sensor_timestamp)
            existing = (
                db.query(SensorData)
                .filter(
                    and_(
                        SensorData.device_id == packet.device_id,
                        SensorData.sensor_timestamp == packet.sensor_timestamp,
                    )
                )
                .first()
            )
            if existing:
                is_duplicate = True

        if is_duplicate:
            logger.debug(f"Duplicate packet detected for {packet.device_id} at {packet.sensor_timestamp}")
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

        # 3. Track metrics (ordering & sampling rate)
        metrics = metrics_tracker.record_packet(
            packet.device_id, packet.sensor_timestamp, now_utc
        )

        # 4. Add to rolling buffer
        sample_dict = packet.model_dump()
        buffer_manager.add_sample(packet.device_id, sample_dict)

        # 5. Persist raw record to Supabase PostgreSQL / SQLite
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
            message="Packet successfully validated and persisted",
        )

    # Alias for backward compatibility
    ingest_single_packet = ingest_canonical_packet

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
