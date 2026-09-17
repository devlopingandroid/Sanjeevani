"""Async Bounded Ingestion Queue and Background Database Worker for SANJEEVNI.

Batches incoming high-frequency ESP32 sensor samples into single PostgreSQL transactions,
preventing Supabase connection pool exhaustion while preserving sensor acquisition fidelity (~25 Hz).
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.sensor import SensorData
from app.schemas.sensor import CanonicalSensorPacket
from app.services.device_service import DeviceService
from app.core.logging import logger

QUEUE_MAX_SIZE = 10000
BATCH_COLLECT_TIMEOUT_SEC = 0.2  # 200 ms maximum wait before flushing
BATCH_MAX_ITEMS = 100             # Bulk insert size limit


class SensorQueueWriter:
    def __init__(self, maxsize: int = QUEUE_MAX_SIZE):
        self._maxsize = maxsize
        self._queue: Optional[asyncio.Queue[CanonicalSensorPacket]] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._logger_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._last_heartbeat_time: Dict[str, float] = {}

        # Metrics counters for observability
        self.received_samples = 0
        self.queued_samples = 0
        self.db_inserted = 0
        self.db_failed = 0
        self.db_batches = 0
        self.queue_overflows = 0

    def initialize(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if self._queue is None or (loop and self._queue._loop is not loop):
            self._queue = asyncio.Queue(maxsize=self._maxsize)

    @property
    def queue(self) -> asyncio.Queue[CanonicalSensorPacket]:
        if self._queue is None:
            self.initialize()
        return self._queue

    def enqueue(self, packet: CanonicalSensorPacket) -> bool:
        """Enqueues a validated sensor packet. Returns False if queue is full."""
        self.received_samples += 1
        try:
            self.queue.put_nowait(packet)
            self.queued_samples = self.queue.qsize()
            return True
        except asyncio.QueueFull:
            self.queue_overflows += 1
            logger.warning(
                f"Ingestion queue full ({self._maxsize} items). Dropped packet from {packet.device_id}."
            )
            return False

    def enqueue_batch(self, packets: List[CanonicalSensorPacket]) -> int:
        """Enqueues a list of packets. Returns count of successfully enqueued packets."""
        accepted = 0
        for p in packets:
            if self.enqueue(p):
                accepted += 1
        return accepted

    async def start(self):
        """Starts background database writer and logging tasks."""
        self.initialize()
        self._is_running = True
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._db_writer_loop())
        if self._logger_task is None or self._logger_task.done():
            self._logger_task = asyncio.create_task(self._metrics_logger_loop())
        logger.info(f"SensorQueueWriter background worker started (max_queue={self._maxsize}).")

    async def stop(self):
        """Stops background tasks and performs final flush."""
        self._is_running = False
        if self._logger_task and not self._logger_task.done():
            self._logger_task.cancel()
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        await self.flush_queue()
        logger.info("SensorQueueWriter background worker stopped cleanly.")

    async def flush_queue(self):
        """Flushes all queued items to DB synchronously."""
        if self._queue is None or self._queue.empty():
            return

        batch: List[CanonicalSensorPacket] = []
        while not self._queue.empty():
            try:
                batch.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        if batch:
            self._write_batch_to_db(batch)

    def _write_batch_to_db(self, batch: List[CanonicalSensorPacket]):
        """Executes one single PostgreSQL transaction for the entire batch of samples."""
        if not batch:
            return

        # Sort batch deterministically by sequence_number and timestamp before inserting
        batch.sort(
            key=lambda p: (
                p.sequence_number if p.sequence_number is not None else float("inf"),
                p.sensor_timestamp or datetime.min,
            )
        )

        db: Session = SessionLocal()
        try:
            now_utc = datetime.now(timezone.utc)
            db_records = [
                SensorData(
                    device_id=p.device_id,
                    sensor_timestamp=p.sensor_timestamp,
                    received_at=p.received_at or now_utc,
                    sequence_number=p.sequence_number,
                    transport=p.transport.value if hasattr(p.transport, "value") else str(p.transport),
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
                for p in batch
            ]
            db.add_all(db_records)

            # Throttled heartbeat update (at most once every 30 seconds per device)
            now_mono = time.monotonic()
            devices_seen = set(p.device_id for p in batch if p.device_id)
            for dev_id in devices_seen:
                if now_mono - self._last_heartbeat_time.get(dev_id, 0.0) > 30.0:
                    try:
                        DeviceService.update_heartbeat(db, dev_id, transport="HTTP", is_valid=True)
                        self._last_heartbeat_time[dev_id] = now_mono
                    except Exception as hb_exc:
                        logger.warning(f"Failed updating device heartbeat for {dev_id}: {hb_exc}")

            db.commit()
            self.db_inserted += len(batch)
            self.db_batches += 1
        except Exception as exc:
            db.rollback()
            retryable = [p for p in batch if getattr(p, "_retries", 0) < 3]
            for p in retryable:
                setattr(p, "_retries", getattr(p, "_retries", 0) + 1)
                try:
                    self.queue.put_nowait(p)
                except Exception:
                    pass

            unrecoverable_count = len(batch) - len(retryable)
            self.db_failed += unrecoverable_count
            logger.error(f"Failed to persist sensor batch of {len(batch)} records to DB (requeued {len(retryable)}): {exc}")
        finally:
            db.close()
            self.queued_samples = self.queue.qsize() if self._queue else 0

    async def _db_writer_loop(self):
        """Continuously pulls samples from queue and performs bulk DB inserts."""
        while self._is_running:
            try:
                batch: List[CanonicalSensorPacket] = []
                start_time = asyncio.get_event_loop().time()

                while len(batch) < BATCH_MAX_ITEMS:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    remaining_timeout = max(0.01, BATCH_COLLECT_TIMEOUT_SEC - elapsed)
                    if remaining_timeout <= 0.01 and len(batch) > 0:
                        break

                    try:
                        packet = await asyncio.wait_for(self.queue.get(), timeout=remaining_timeout)
                        batch.append(packet)
                    except (asyncio.TimeoutError, TimeoutError):
                        break

                if batch:
                    # Run bulk insert in background thread pool to avoid blocking asyncio event loop
                    await asyncio.to_thread(self._write_batch_to_db, batch)
                else:
                    await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Unexpected error in db_writer_loop: {exc}")
                await asyncio.sleep(0.5)

    async def _metrics_logger_loop(self):
        """Periodic logger for operational metrics every 5 seconds."""
        while self._is_running:
            try:
                await asyncio.sleep(5.0)
                logger.info(
                    f"SENSOR INGEST STATUS | received_samples={self.received_samples} | "
                    f"queued_samples={self.queue.qsize()} | db_inserted={self.db_inserted} | "
                    f"db_failed={self.db_failed} | db_batches={self.db_batches}"
                )
            except asyncio.CancelledError:
                break
            except Exception:
                pass


sensor_queue_writer = SensorQueueWriter()

