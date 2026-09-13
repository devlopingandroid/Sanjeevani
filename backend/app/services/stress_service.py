"""Stress inference coordination service for SANJEEVNI.

Coordinates:
30-second rolling buffer -> Data quality gating -> 26-feature extraction ->
ML Model inference (predict_proba) -> Supabase PostgreSQL persistence -> Structured API response.

Follows the strict NO-MOCK-DATA policy:
Never generates synthetic or random fallback predictions.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.stress_prediction import StressPrediction
from app.schemas.stress import StressPredictionResponse
from app.schemas.common import DataStatus
from app.processing.buffer import buffer_manager
from app.processing.data_quality import DataQualityChecker
from app.processing.feature_extractor import extract_26_features
from app.ml.predictor import StressPredictor
from app.ml.model_loader import model_loader
from app.ml.metadata import NUM_EXPECTED_FEATURES
from app.core.logging import logger


class StressService:
    """Coordinates real-time physiological signal processing and ML inference."""

    @staticmethod
    def get_latest_prediction(db: Session, device_id: str) -> StressPredictionResponse:
        """Returns the most recent real prediction stored in the database for a device."""
        latest = (
            db.query(StressPrediction)
            .filter(StressPrediction.device_id == device_id)
            .order_by(desc(StressPrediction.timestamp))
            .first()
        )

        if not latest:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=DataStatus.NO_DATA,
                stress_level=None,
                stress_score=None,
                raw_probability=None,
                confidence=None,
                predicted_at=None,
                model_status="READY" if model_loader.is_available else "MODEL_UNAVAILABLE",
                message="No historical stress predictions found for this device.",
                features_used_count=0,
                features_snapshot=None,
            )

        raw_prob = round(latest.stress_score / 100.0, 4) if latest.stress_score is not None else None
        return StressPredictionResponse(
            device_id=device_id,
            data_status=DataStatus.REAL_DATA,
            stress_level=latest.stress_level,
            stress_score=latest.stress_score,
            raw_probability=raw_prob,
            confidence=latest.confidence,
            predicted_at=latest.timestamp,
            model_status="READY" if model_loader.is_available else "MODEL_UNAVAILABLE",
            message="Retrieved latest verified stress prediction from database.",
            features_used_count=NUM_EXPECTED_FEATURES,
            features_snapshot=latest.features_snapshot,
        )

    @staticmethod
    def run_prediction(db: Session, device_id: str) -> StressPredictionResponse:
        """Evaluates the 30s buffer, extracts 26 features, executes inference, and persists results."""
        # 1. Check ML Model availability
        if not model_loader.is_available:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=DataStatus.MODEL_UNAVAILABLE,
                stress_level=None,
                stress_score=None,
                raw_probability=None,
                confidence=None,
                predicted_at=None,
                model_status="MODEL_UNAVAILABLE",
                message=model_loader.status_message,
                features_used_count=0,
                features_snapshot=None,
            )

        # 2. Retrieve samples from device's isolated 30s buffer
        samples = buffer_manager.get_device_samples(device_id)

        # 3. Data Quality & Window Completeness Gating
        is_valid_win, win_status, win_reason = DataQualityChecker.evaluate_30s_window(samples)
        if not is_valid_win:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=DataStatus(win_status),
                stress_level=None,
                stress_score=None,
                raw_probability=None,
                confidence=None,
                predicted_at=None,
                model_status="READY",
                message=win_reason,
                features_used_count=0,
                features_snapshot=None,
            )

        # 4. Extract exactly 26 features
        features, features_dict = extract_26_features(samples)
        if features is None or len(features) != NUM_EXPECTED_FEATURES:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=DataStatus.INSUFFICIENT_DATA,
                stress_level=None,
                stress_score=None,
                raw_probability=None,
                confidence=None,
                predicted_at=None,
                model_status="READY",
                message="Feature extraction could not compute 26 valid features from the current window.",
                features_used_count=0,
                features_snapshot=None,
            )

        # 5. Perform real ML inference using predict_proba()
        inference = StressPredictor.predict(features, features_dict)
        if inference["status"] != DataStatus.REAL_DATA:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=DataStatus(inference["status"]),
                stress_level=None,
                stress_score=None,
                raw_probability=None,
                confidence=None,
                predicted_at=None,
                model_status="READY",
                message=inference["message"],
                features_used_count=NUM_EXPECTED_FEATURES,
                features_snapshot=features_dict,
            )

        # 6. Persist real inference to database
        now = datetime.now(timezone.utc)
        db_prediction = StressPrediction(
            device_id=device_id,
            timestamp=now,
            stress_level=inference["stress_level"],
            stress_score=inference["stress_score"],
            confidence=inference["confidence"],
            features_snapshot=features_dict,
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        return StressPredictionResponse(
            device_id=device_id,
            data_status=DataStatus.REAL_DATA,
            stress_level=inference["stress_level"],
            stress_score=inference["stress_score"],
            raw_probability=inference["raw_probability"],
            confidence=inference["confidence"],
            predicted_at=now,
            model_status="READY",
            message=inference["message"],
            features_used_count=NUM_EXPECTED_FEATURES,
            features_snapshot=features_dict,
        )
