"""Thread-safe rolling 30-second sensor buffer for SANJEEVNI.

At 25 Hz (40ms interval from ESP32), a 30-second sliding window contains 750 samples.
"""
from collections import deque
from threading import Lock
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.logging import logger


class DeviceRollingBuffer:
    """Stores the latest N seconds of real sensor samples for a single device."""

    def __init__(self, window_seconds: int = 30, sampling_rate_hz: int = 25):
        self.window_seconds = window_seconds
        self.sampling_rate_hz = sampling_rate_hz
        self.capacity = window_seconds * sampling_rate_hz  # 30 * 25 = 750 samples
        self._buffer: deque = deque(maxlen=self.capacity)
        self._lock = Lock()

    def add_sample(self, sample: Dict[str, Any]) -> None:
        """Appends a new real sensor reading to the buffer."""
        with self._lock:
            self._buffer.append(sample)

    def add_batch(self, samples: List[Dict[str, Any]]) -> None:
        """Appends a batch of real sensor readings."""
        with self._lock:
            for s in samples:
                self._buffer.append(s)

    def get_samples(self) -> List[Dict[str, Any]]:
        """Returns a snapshot copy of all samples currently in the buffer."""
        with self._lock:
            return list(self._buffer)

    def count(self) -> int:
        with self._lock:
            return len(self._buffer)

    def is_ready(self, minimum_threshold: float = 0.8) -> bool:
        """Checks if the buffer has enough real data to extract meaningful features.

        By default requires at least 80% (600 samples) of the full 30s window.
        """
        required_samples = int(self.capacity * minimum_threshold)
        with self._lock:
            return len(self._buffer) >= required_samples

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

    def get_latest_sample(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self._buffer:
                return self._buffer[-1]
            return None


class SensorBufferManager:
    """Manages buffers across all registered devices."""

    def __init__(self):
        self._device_buffers: Dict[str, DeviceRollingBuffer] = {}
        self._manager_lock = Lock()

    def get_buffer(self, device_id: str) -> DeviceRollingBuffer:
        with self._manager_lock:
            if device_id not in self._device_buffers:
                self._device_buffers[device_id] = DeviceRollingBuffer(
                    window_seconds=settings.BUFFER_WINDOW_SECONDS,
                    sampling_rate_hz=settings.EXPECTED_SAMPLING_RATE_HZ,
                )
            return self._device_buffers[device_id]

    def add_sample(self, device_id: str, sample: Dict[str, Any]) -> None:
        buf = self.get_buffer(device_id)
        buf.add_sample(sample)

    def add_batch(self, device_id: str, samples: List[Dict[str, Any]]) -> None:
        buf = self.get_buffer(device_id)
        buf.add_batch(samples)

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


# Global singleton instance
buffer_manager = SensorBufferManager()
