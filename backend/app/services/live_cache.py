"""Live process-level sensor cache for real-time telemetry display.

Completely decouples real-time UI/API rendering from database health.
"""
from collections import deque
from threading import Lock
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.schemas.sensor import CanonicalSensorPacket

LIVE_CACHE_MAX_SAMPLES = 500
DISCONNECT_TIMEOUT_SECONDS = 15.0


class LiveSensorCache:
    def __init__(self, maxsize: int = LIVE_CACHE_MAX_SAMPLES):
        self.maxsize = maxsize
        self._latest_by_device: Dict[str, Dict[str, Any]] = {}
        self._recent_samples: Dict[str, deque] = {}
        self._lock = Lock()

    def update(self, packet: CanonicalSensorPacket) -> Dict[str, Any]:
        """Updates live cache immediately when a valid packet arrives."""
        sample_dict = packet.model_dump()
        device_id = packet.device_id

        # Normalize timestamps for JSON serialization
        if isinstance(sample_dict.get("sensor_timestamp"), datetime):
            sample_dict["sensor_timestamp"] = sample_dict["sensor_timestamp"].isoformat()
        if isinstance(sample_dict.get("received_at"), datetime):
            sample_dict["received_at"] = sample_dict["received_at"].isoformat()
        else:
            sample_dict["received_at"] = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._latest_by_device[device_id] = sample_dict
            if device_id not in self._recent_samples:
                self._recent_samples[device_id] = deque(maxlen=self.maxsize)
            self._recent_samples[device_id].append(sample_dict)

        return sample_dict

    def update_batch(self, packets: List[CanonicalSensorPacket]) -> List[Dict[str, Any]]:
        results = []
        for p in packets:
            results.append(self.update(p))
        return results

    def get_latest(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns latest sample and connectivity status for a device."""
        with self._lock:
            target_device = device_id
            if not target_device and self._latest_by_device:
                target_device = max(
                    self._latest_by_device.keys(),
                    key=lambda k: self._latest_by_device[k].get("received_at", ""),
                )

            if not target_device or target_device not in self._latest_by_device:
                return {
                    "device_id": device_id,
                    "connected": False,
                    "source": "live_cache",
                    "sample": None,
                }

            sample = self._latest_by_device[target_device]
            recv_raw = sample.get("received_at")
            connected = False
            if recv_raw:
                try:
                    recv_dt = datetime.fromisoformat(str(recv_raw).replace("Z", "+00:00"))
                    now_utc = datetime.now(timezone.utc)
                    connected = (now_utc - recv_dt).total_seconds() < DISCONNECT_TIMEOUT_SECONDS
                except Exception:
                    connected = True

            return {
                "device_id": target_device,
                "connected": connected,
                "source": "live_cache",
                "sample": sample,
                "last_received_at": recv_raw,
                "sequence_number": sample.get("sequence_number"),
            }

    def get_recent(self, device_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns the last N samples for charting/history."""
        with self._lock:
            if device_id not in self._recent_samples:
                return []
            samples = list(self._recent_samples[device_id])
            limit = min(max(1, limit), self.maxsize)
            return samples[-limit:]


live_sensor_cache = LiveSensorCache()
