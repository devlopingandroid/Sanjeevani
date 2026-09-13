"""Dashboard summary endpoint serving as authoritative source of truth."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard Summary",
    description=(
        "Returns the authoritative real-time health summary for a wearable. "
        "Strictly enforces NO-MOCK-DATA: if disconnected or waiting for telemetry, "
        "vitals are null and explicit states (NO_DATA, DEVICE_DISCONNECTED, INSUFFICIENT_DATA) "
        "are returned."
    ),
)
def get_dashboard_summary(
    device_id: Optional[str] = Query(None, description="Hardware ID of the device (optional)"),
    db: Session = Depends(get_db),
):
    return DashboardService.get_summary(db, device_id=device_id)
