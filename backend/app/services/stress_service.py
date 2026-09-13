"""Stress inference coordination service."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.stress_prediction import StressPrediction
from app.schemas.stress import StressPredictionResponse
from app.schemas.common import DataStatus
from app.processing.buffer import buffer_manager
from app.processing.feature_extractor import extract_44_features
from app.ml.predictor import StressPredictor
from app.ml.model_loader import model_loader
from app.core.logging import logger


class StressService:

    @staticmethod
    def get_latest_prediction(db: Session, device_id: str) -> StressPredictionResponse:
        """Returns the most recent real prediction stored in the database."""
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
                confidence=None,
                predicted_at=None,
                model_status="READY" if model_loader.is_available else "MODEL_UNAVAILABLE",
                message="No historical stress predictions found for this device.",
                features_used_count=0,
            )

        return StressPredictionResponse(
            device_id=device_id,
            data_status=DataStatus.REAL_DATA,
            stress_level=latest.stress_level,
            stress_score=latest.stress_score,
            confidence=latest.confidence,
            predicted_at=latest.timestamp,
            model_status="READY" if model_loader.is_available else "MODEL_UNAVAILABLE",
            message="Retrieved latest verified stress prediction.",
            features_used_count=44,
        )

    @staticmethod
    def run_prediction(db: Session, device_id: str) -> StressPredictionResponse:
        """Executes real feature extraction and stress inference on the current buffer."""
        # 1. Check ML Model availability
        if not model_loader.is_available:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=DataStatus.MODEL_UNAVAILABLE,
                stress_level=None,
                stress_score=None,
                confidence=None,
                predicted_at=None,
                model_status="MODEL_UNAVAILABLE",
                message=model_loader.status_message,
                features_used_count=0,
            )

        # 2. Extract features from rolling 30s buffer
        samples = buffer_manager.get_device_samples(device_id)
        features = extract_44_features(samples)

        if features is None:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=DataStatus.INSUFFICIENT_DATA,
                stress_level=None,
                stress_score=None,
                confidence=None,
                predicted_at=None,
                model_status="READY",
                message=f"Insufficient buffer data ({len(samples)} samples). A 30s window (~750 samples) is required.",
                features_used_count=0,
            )

        # 3. Perform real inference
        inference_result = StressPredictor.predict(features)

        if inference_result["status"] != DataStatus.REAL_DATA:
            return StressPredictionResponse(
                device_id=device_id,
                data_status=inference_result["status"],
                stress_level=None,
                stress_score=None,
                confidence=None,
                predicted_at=None,
                model_status="READY",
                message=inference_result["message"],
                features_used_count=len(features),
            )

        now = datetime.now(timezone.utc)
        # 4. Save prediction record to database
        db_prediction = StressPrediction(
            device_id=device_id,
            timestamp=now,
            stress_level=inference_result["stress_level"],
            stress_score=inference_result["stress_score"],
            confidence=inference_result["confidence"],
            features_snapshot={"feature_count": len(features)},
        )
        db.add(db_prediction)
        db.commit()

        return StressPredictionResponse(
            device_id=device_id,
            data_status=DataStatus.REAL_DATA,
            stress_level=inference_result["stress_level"],
            stress_score=inference_result["stress_score"],
            confidence=inference_result["confidence"],
            predicted_at=now,
            model_status="READY",
            message=inference_result["message"],
            features_used_count=len(features),
        )
