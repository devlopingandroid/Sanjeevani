"""Stress prediction endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.stress import StressPredictionResponse, StressInferenceRequest
from app.services.stress_service import StressService

router = APIRouter(prefix="/stress", tags=["Stress"])


@router.get(
    "/latest/{device_id}",
    response_model=StressPredictionResponse,
    summary="Get Latest Stress Prediction",
    description="Retrieves the most recent verified stress prediction for the specified wearable.",
)
def get_latest_stress(
    device_id: str,
    db: Session = Depends(get_db),
):
    return StressService.get_latest_prediction(db, device_id)


@router.post(
    "/predict",
    response_model=StressPredictionResponse,
    summary="Trigger Stress Inference",
    description=(
        "Extracts 44 features from the rolling 30s sensor buffer and evaluates stress "
        "using the real ML model. Returns MODEL_UNAVAILABLE if model file is missing, "
        "or INSUFFICIENT_DATA if buffer has less than 30s of samples."
    ),
)
def trigger_stress_prediction(
    request: StressInferenceRequest,
    db: Session = Depends(get_db),
):
    return StressService.run_prediction(db, request.device_id)
