"""Thread-safe rolling 30-second sensor buffer for SANJEEVNI.

Strictly isolates buffers per device_id, enforces timestamp chronological ordering,
prunes expired samples based on real sensor timestamps, eliminates duplicate packets,
and handles out-of-order telemetry without creating synthetic fill-ins.
"""
from bisect import bisect_left
from threading import Lock
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.logging import logger
from app.schemas.sensor import parse_flexible_timestamp


def get_sample_datetime(sample: Dict[str, Any]) -> datetime:
    """Extracts a timezone-aware UTC datetime from a sample dict."""
    raw = sample.get("sensor_timestamp") or sample.get("timestamp") or sample.get("received_at")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if raw is not None:
        try:
            return parse_flexible_timestamp(raw)
        except Exception:
            pass
    return datetime.now(timezone.utc)


class DeviceRollingBuffer:
    """Stores the latest 30 seconds of real physiological sensor samples for a single device."""

    def __init__(self, window_seconds: float = 30.0, max_capacity: int = 1200):
        self.window_seconds = window_seconds
        self.max_capacity = max_capacity
        self._samples: List[Dict[str, Any]] = []
        self._timestamps: List[datetime] = []
        self._lock = Lock()

    def add_sample(self, sample: Dict[str, Any]) -> bool:
        """Adds a real sensor sample to the buffer in chronological order.

        Prunes samples older than window_seconds from the newest sample.
        Detects and discards duplicates.
        Returns True if added, False if duplicate.
        """
        with self._lock:
            ts = get_sample_datetime(sample)

            # Check for duplicate timestamp
            idx = bisect_left(self._timestamps, ts)
            if idx < len(self._timestamps) and self._timestamps[idx] == ts:
                # Duplicate timestamp detected; do not add duplicate sample
                return False

            # Insert in chronological order
            self._timestamps.insert(idx, ts)
            self._samples.insert(idx, sample)

            # Prune samples older than window_seconds relative to the latest sample
            if self._timestamps:
                cutoff = self._timestamps[-1] - timedelta(seconds=self.window_seconds)
                prune_idx = bisect_left(self._timestamps, cutoff)
                if prune_idx > 0:
                    del self._timestamps[:prune_idx]
                    del self._samples[:prune_idx]

            # Enforce hard upper bound on memory
            if len(self._samples) > self.max_capacity:
                excess = len(self._samples) - self.max_capacity
                del self._timestamps[:excess]
                del self._samples[:excess]

            return True

    def add_batch(self, samples: List[Dict[str, Any]]) -> int:
        """Adds a list of samples. Returns number of accepted new samples."""
        added = 0
        for s in samples:
            if self.add_sample(s):
                added += 1
        return added

    def get_samples(self) -> List[Dict[str, Any]]:
        """Returns a snapshot copy of all valid samples currently inside the 30s window."""
        with self._lock:
            return list(self._samples)

    def count(self) -> int:
        with self._lock:
            return len(self._samples)

    def duration_seconds(self) -> float:
        """Returns the actual elapsed time span in seconds across the current buffer."""
        with self._lock:
            if len(self._timestamps) < 2:
                return 0.0
            return (self._timestamps[-1] - self._timestamps[0]).total_seconds()

    def is_ready(self, min_samples: int = 500, min_duration_sec: float = 25.0) -> bool:
        """Checks if the buffer has enough real data spanning the 30-second window."""
        with self._lock:
            if len(self._samples) < min_samples:
                return False
            if len(self._timestamps) >= 2:
                span = (self._timestamps[-1] - self._timestamps[0]).total_seconds()
                return span >= min_duration_sec
            return False

    def clear(self) -> None:
        """Resets the buffer."""
        with self._lock:
            self._samples.clear()
            self._timestamps.clear()

    def get_latest_sample(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self._samples:
                return self._samples[-1]
            return None


class SensorBufferManager:
    """Manages strictly isolated rolling buffers across all registered devices."""

    def __init__(self):
        self._device_buffers: Dict[str, DeviceRollingBuffer] = {}
        self._manager_lock = Lock()

    def get_buffer(self, device_id: str) -> DeviceRollingBuffer:
        with self._manager_lock:
            if device_id not in self._device_buffers:
                self._device_buffers[device_id] = DeviceRollingBuffer(
                    window_seconds=float(settings.BUFFER_WINDOW_SECONDS),
                )
            return self._device_buffers[device_id]

    def add_sample(self, device_id: str, sample: Dict[str, Any]) -> bool:
        buf = self.get_buffer(device_id)
        return buf.add_sample(sample)

    def add_batch(self, device_id: str, samples: List[Dict[str, Any]]) -> int:
        buf = self.get_buffer(device_id)
        return buf.add_batch(samples)

    def is_device_ready(self, device_id: str) -> bool:
        with self._manager_lock:
            if device_id not in self._device_buffers:
                return False
            return self._device_buffers[device_id].is_ready()

    def get_device_samples(self, device_id: str) -> List[Dict[str, Any]]:
        with self._manager_lock:
            if device_id not in self._device_buffers:
                return []
            return self._device_buffers[device_id].get_samples()

    def clear_device(self, device_id: str) -> None:
        with self._manager_lock:
            if device_id in self._device_buffers:
                self._device_buffers[device_id].clear()


# Global singleton instance
buffer_manager = SensorBufferManager()
