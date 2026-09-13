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
        """Returns the authoritative dashboard summary.

        If no device or no sensor data exists, returns explicit NO_DATA / DEVICE_DISCONNECTED
        with vitals=None. NO FAKE VALUES ARE EVER USED.
        """
        # If device_id not specified, find the most recently active device
        device: Optional[Device] = None
        if device_id:
            device = DeviceService.get_by_device_id(db, device_id)
        else:
            device = db.query(Device).order_by(desc(Device.last_seen)).first()

        if not device:
            return DashboardSummaryResponse(
                device_id=None,
                device_status=DeviceStatus.NO_DATA,
                data_status=DataStatus.NO_DATA,
                last_seen=None,
                vitals=None,
                stress=None,
                message="No wearable device registered. Waiting for device connection...",
            )

        # Refresh device state based on current server time
        device = DeviceService.refresh_status(db, device)

        if device.status == DeviceStatus.DISCONNECTED:
            return DashboardSummaryResponse(
                device_id=device.device_id,
                device_status=device.status,
                data_status=DataStatus.DEVICE_DISCONNECTED,
                last_seen=device.last_seen,
                vitals=None,
                stress=None,
                message="Device disconnected. Waiting for wearable to reconnect...",
            )

        # Fetch latest real processed metrics
        latest_metrics = (
            db.query(ProcessedMetrics)
            .filter(ProcessedMetrics.device_id == device.device_id)
            .order_by(desc(ProcessedMetrics.timestamp))
            .first()
        )

        vitals_snapshot: Optional[VitalsSnapshot] = None
        if latest_metrics:
            vitals_snapshot = VitalsSnapshot(
                heart_rate_bpm=latest_metrics.heart_rate_bpm,
                hrv_rmssd_ms=latest_metrics.hrv_rmssd_ms,
                temperature_f=latest_metrics.temperature_f,
                skin_conductance_us=latest_metrics.skin_conductance_us,
                motion_magnitude=latest_metrics.motion_magnitude,
                last_updated=latest_metrics.timestamp,
            )

        # Fetch latest real stress prediction
        latest_stress = (
            db.query(StressPrediction)
            .filter(StressPrediction.device_id == device.device_id)
            .order_by(desc(StressPrediction.timestamp))
            .first()
        )

        stress_snapshot: Optional[StressSnapshot] = None
        if latest_stress:
            stress_snapshot = StressSnapshot(
                stress_level=latest_stress.stress_level,
                stress_score=latest_stress.stress_score,
                confidence=latest_stress.confidence,
                predicted_at=latest_stress.timestamp,
            )

        # Determine overall data status
        if vitals_snapshot is None and stress_snapshot is None:
            data_status = DataStatus.INSUFFICIENT_DATA
            message = "Wearable connected. Collecting sensor buffer..."
        else:
            data_status = DataStatus.REAL_DATA
            message = "Streaming live wearable telemetry."

        return DashboardSummaryResponse(
            device_id=device.device_id,
            device_status=device.status,
            data_status=data_status,
            last_seen=device.last_seen,
            vitals=vitals_snapshot,
            stress=stress_snapshot,
            message=message,
        )
