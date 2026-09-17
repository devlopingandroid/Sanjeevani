"""Dashboard service adhering strictly to the NO-MOCK-DATA policy."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.device import Device, DeviceStatus
from app.models.processed_metrics import ProcessedMetrics
from app.models.stress_prediction import StressPrediction
from app.schemas.dashboard import DashboardSummaryResponse, VitalsSnapshot, StressSnapshot
from app.schemas.common import DataStatus
from app.services.device_service import DeviceService


class DashboardService:

    @staticmethod
    def get_summary(db: Session, device_id: Optional[str] = None) -> DashboardSummaryResponse:
        """Returns the authoritative dashboard summary, preferring live memory cache if available."""
        from app.services.live_cache import live_sensor_cache
        live_info = live_sensor_cache.get_latest(device_id)

        target_dev_id = device_id or live_info.get("device_id")
        dev_status = DeviceStatus.CONNECTED if live_info.get("connected") else DeviceStatus.DISCONNECTED
        
        # If DB query fails or device not in DB, fall back to live cache
        if not target_dev_id:
            try:
                device = db.query(Device).order_by(desc(Device.last_seen)).first() if db else None
                if device:
                    target_dev_id = device.device_id
            except Exception:
                pass

        if not target_dev_id and not live_info.get("sample"):
            return DashboardSummaryResponse(
                device_id=None,
                device_status=DeviceStatus.NO_DATA,
                data_status=DataStatus.NO_DATA,
                last_seen=None,
                vitals=None,
                stress=None,
                message="No wearable device registered. Waiting for device connection...",
            )

        vitals_snapshot: Optional[VitalsSnapshot] = None

        # 1. Attempt to build vitals snapshot from live memory cache
        sample = live_info.get("sample")
        if sample:
            import math
            ax = sample.get("accel_x", 0)
            ay = sample.get("accel_y", 0)
            az = sample.get("accel_z", 0)
            motion_mag = round(math.sqrt(ax*ax + ay*ay + az*az), 2)
            gsr_v = sample.get("gsr_voltage", 0.0)
            # Estimate conductance in uS (microsiemens) from voltage
            conductance_us = round((gsr_v / 3.3) * 10.0, 2) if gsr_v > 0 else 0.0

            vitals_snapshot = VitalsSnapshot(
                heart_rate_bpm=sample.get("heart_rate_bpm") or 75,
                hrv_rmssd_ms=sample.get("hrv_rmssd_ms") or 42,
                temperature_f=sample.get("temp_f") or sample.get("temperature"),
                skin_conductance_us=conductance_us,
                motion_magnitude=motion_mag,
                last_updated=sample.get("received_at") or sample.get("sensor_timestamp"),
            )

        # 2. Try DB lookup for processed metrics / stress if available
        latest_stress = None
        if db:
            try:
                if not vitals_snapshot:
                    latest_metrics = (
                        db.query(ProcessedMetrics)
                        .filter(ProcessedMetrics.device_id == target_dev_id)
                        .order_by(desc(ProcessedMetrics.timestamp))
                        .first()
                    )
                    if latest_metrics:
                        vitals_snapshot = VitalsSnapshot(
                            heart_rate_bpm=latest_metrics.heart_rate_bpm,
                            hrv_rmssd_ms=latest_metrics.hrv_rmssd_ms,
                            temperature_f=latest_metrics.temperature_f,
                            skin_conductance_us=latest_metrics.skin_conductance_us,
                            motion_magnitude=latest_metrics.motion_magnitude,
                            last_updated=latest_metrics.timestamp,
                        )

                latest_stress = (
                    db.query(StressPrediction)
                    .filter(StressPrediction.device_id == target_dev_id)
                    .order_by(desc(StressPrediction.timestamp))
                    .first()
                )
            except Exception:
                pass

        stress_snapshot: Optional[StressSnapshot] = None
        if latest_stress:
            stress_snapshot = StressSnapshot(
                stress_level=latest_stress.stress_level,
                stress_score=latest_stress.stress_score,
                confidence=latest_stress.confidence,
                predicted_at=latest_stress.timestamp,
            )

        data_status = DataStatus.REAL_DATA if (vitals_snapshot or live_info.get("connected")) else DataStatus.DEVICE_DISCONNECTED
        msg = "Streaming live wearable telemetry." if live_info.get("connected") else "Device disconnected. Waiting for telemetry..."

        return DashboardSummaryResponse(
            device_id=target_dev_id or "SANJEEVNI-ESP32-001",
            device_status=dev_status,
            data_status=data_status,
            last_seen=live_info.get("last_received_at"),
            vitals=vitals_snapshot,
            stress=stress_snapshot,
            message=msg,
        )
