import math
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.stress import (
    StressPredictionResponse,
    StressInferenceRequest,
    ModelTestRequest,
    ModelTestResponse,
)
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.stress_service import StressService
from app.ml.model_loader import model_loader
from app.ml.predictor import StressPredictor
from app.ml.metadata import FEATURE_NAMES_26
from app.schemas.common import DataStatus
from app.core.exceptions import SanjeevniException, ErrorCode
from app.core.logging import logger

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
        "Extracts 26 features from the rolling 30s sensor buffer and evaluates Estimated Stress "
        "using predict_proba() on the real ML model. Returns MODEL_UNAVAILABLE if model file is missing, "
        "SENSOR_ERROR if optical/GSR signals fail quality checks, or INSUFFICIENT_DATA if buffer has less than 30s of samples."
    ),
)
def trigger_stress_prediction(
    request: StressInferenceRequest,
    db: Session = Depends(get_db),
):
    return StressService.run_prediction(db, request.device_id)


@router.post(
    "/model-test",
    response_model=ModelTestResponse,
    summary="Manual Model Compatibility Test",
    description=(
        "DEVELOPMENT/TESTING ONLY endpoint to evaluate manually entered 26 feature values "
        "directly against the real .pkl ML model. Does NOT modify production sensor history or DB."
    ),
)
def run_manual_model_test(
    request: ModelTestRequest,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"[MODEL_COMPATIBILITY_TEST_ONLY] Manual model test initiated by user_id={current_user.id}")

    # 1. Verify model availability
    if not model_loader.is_available:
        raise SanjeevniException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=ErrorCode.MODEL_UNAVAILABLE,
            message="Stress prediction ML model is not available.",
        )

    # 2. Build feature vector & dictionary in exact 26 feature order
    features_dict: dict[str, float] = {}
    feature_values: list[float] = []

    for name in FEATURE_NAMES_26:
        val = getattr(request, name)
        if math.isnan(val) or math.isinf(val):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Feature '{name}' must be a finite number (NaN/Inf rejected).",
            )
        features_dict[name] = float(val)
        feature_values.append(float(val))

    feature_vector = np.array(feature_values, dtype=float)

    # 3. Perform real ML inference using existing StressPredictor & joblib .pkl model
    inference = StressPredictor.predict(feature_vector, features_dict)

    if inference["status"] != DataStatus.REAL_DATA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=inference.get("message", "Model test inference failed."),
        )

    p_stress = float(inference["raw_probability"])
    stress_level = str(inference["stress_level"])
    prediction = 1 if stress_level == "STRESS" else 0

    return ModelTestResponse(
        status="MODEL_TEST_SUCCESS",
        prediction=prediction,
        stress_level=stress_level,
        stress_probability=round(p_stress, 4),
        confidence=round(float(inference["confidence"]), 3),
        model_name="Sanjeevni_Best_Stress_Model.pkl",
        feature_count=26,
        threshold=0.5,
        message="Manual model test completed successfully.",
    )

