"""Health check endpoints for container orchestrators and liveness probes."""
from datetime import datetime, timezone
from fastapi import APIRouter, status, Response
from app.db.database import check_db_connection
from app.ml.model_loader import model_loader

router = APIRouter(tags=["Health"])


@router.get(
    "/health/live",
    summary="Liveness Probe",
    description="Confirms that the FastAPI process is alive and accepting connections.",
    status_code=status.HTTP_200_OK,
)
def liveness_check():
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "sanjeevni-backend",
    }


@router.get(
    "/health/ready",
    summary="Readiness Probe",
    description="Checks downstream dependencies including database connection and ML model availability.",
)
def readiness_check(response: Response):
    db_ok = check_db_connection()
    model_ok = model_loader.is_available

    is_ready = db_ok  # DB is strictly mandatory for ready status

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "database": "connected" if db_ok else "unreachable",
            "ml_model": "loaded" if model_ok else "unavailable",
        },
        "model_status_detail": model_loader.status_message,
    }
