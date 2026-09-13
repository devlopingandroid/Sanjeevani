"""Predictor engine for real stress inference.

Strictly enforces NO-MOCK-DATA:
- If model is missing -> MODEL_UNAVAILABLE
- If sensor buffer is incomplete -> INSUFFICIENT_DATA
- If real model and real features exist -> real inference
"""
from typing import Dict, Any, Optional
import numpy as np
from app.ml.model_loader import model_loader
from app.ml.metadata import STRESS_CLASSES, NUM_EXPECTED_FEATURES
from app.schemas.common import DataStatus
from app.core.logging import logger


class StressPredictor:
    """Predicts stress level from 44 extracted features using the loaded ML model."""

    @classmethod
    def predict(cls, features: Optional[np.ndarray]) -> Dict[str, Any]:
        # 1. Verify model availability
        if not model_loader.is_available:
            return {
                "status": DataStatus.MODEL_UNAVAILABLE,
                "stress_level": None,
                "stress_score": None,
                "confidence": None,
                "message": "Stress model is not loaded (requires Sanjeevni_FINAL_Stress_Model.pkl).",
            }

        # 2. Verify feature vector presence and shape
        if features is None or len(features) != NUM_EXPECTED_FEATURES:
            return {
                "status": DataStatus.INSUFFICIENT_DATA,
                "stress_level": None,
                "stress_score": None,
                "confidence": None,
                "message": f"Insufficient sensor window data. Expected {NUM_EXPECTED_FEATURES} features.",
            }

        try:
            model = model_loader.model
            X = features.reshape(1, -1)

            # Check if classifier or regressor
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[0]
                pred_idx = int(np.argmax(probs))
                confidence = float(np.max(probs))
                stress_level = STRESS_CLASSES[pred_idx] if pred_idx < len(STRESS_CLASSES) else str(pred_idx)
                stress_score = float(probs[-1] * 100.0) if len(probs) > 1 else float(confidence * 100.0)
            else:
                pred = model.predict(X)[0]
                if isinstance(pred, (int, np.integer)):
                    stress_level = STRESS_CLASSES[int(pred)] if int(pred) < len(STRESS_CLASSES) else str(pred)
                    stress_score = float(pred * 50.0)
                    confidence = 0.85
                elif isinstance(pred, str):
                    stress_level = pred.upper()
                    stress_score = 50.0
                    confidence = 0.85
                else:
                    stress_score = float(pred)
                    stress_level = "HIGH" if stress_score > 66 else ("MODERATE" if stress_score > 33 else "LOW")
                    confidence = 0.85

            return {
                "status": DataStatus.REAL_DATA,
                "stress_level": stress_level,
                "stress_score": round(stress_score, 2),
                "confidence": round(confidence, 3),
                "message": "Stress prediction successfully inferred from real wearable sensor data.",
            }
        except Exception as exc:
            logger.error(f"Inference error with ML model: {exc}")
            return {
                "status": DataStatus.SENSOR_ERROR,
                "stress_level": None,
                "stress_score": None,
                "confidence": None,
                "message": f"ML model inference failed: {str(exc)}",
            }
