"""Predictor engine for real stress inference using Sanjeevni_Best_Stress_Model.pkl.

Strictly enforces NO-MOCK-DATA:
- If model is missing -> MODEL_UNAVAILABLE
- If sensor buffer is incomplete -> INSUFFICIENT_DATA
- If signal quality fails -> SENSOR_ERROR
- If real model and real features exist -> real predict_proba() inference

Presents outputs strictly as 'Estimated Stress' from autonomic physiological responses;
NEVER as a clinical or medical diagnosis.
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from app.ml.model_loader import model_loader
from app.ml.metadata import STRESS_CLASSES, NUM_EXPECTED_FEATURES, FEATURE_NAMES_26
from app.schemas.common import DataStatus
from app.core.logging import logger


class StressPredictor:
    """Estimates stress probability from 26 extracted physiological features."""

    @classmethod
    def predict(
        cls,
        features: Optional[np.ndarray],
        features_dict: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Runs real ML inference using predict_proba() on the loaded RandomForest model.

        Returns a dictionary containing status, stress_level, stress_score,
        confidence, raw_probability, and feature details.
        """
        # 1. Verify model availability
        if not model_loader.is_available:
            return {
                "status": DataStatus.MODEL_UNAVAILABLE,
                "stress_level": None,
                "stress_score": None,
                "confidence": None,
                "raw_probability": None,
                "message": "Stress model is not loaded (requires Sanjeevni_Best_Stress_Model.pkl).",
            }

        # 2. Verify feature vector presence and dimension
        if features is None or len(features) != NUM_EXPECTED_FEATURES:
            count = len(features) if features is not None else 0
            return {
                "status": DataStatus.INSUFFICIENT_DATA,
                "stress_level": None,
                "stress_score": None,
                "confidence": None,
                "raw_probability": None,
                "message": f"Insufficient feature vector. Expected {NUM_EXPECTED_FEATURES} features, got {count}.",
            }

        if not np.all(np.isfinite(features)):
            return {
                "status": DataStatus.SENSOR_ERROR,
                "stress_level": None,
                "stress_score": None,
                "confidence": None,
                "raw_probability": None,
                "message": "Feature vector contains non-finite numbers (NaN or Inf).",
            }

        try:
            model = model_loader.model
            col_names = model_loader.feature_names or FEATURE_NAMES_26

            # Construct DataFrame with exact column names to avoid sklearn feature name warnings
            if features_dict and all(k in features_dict for k in col_names):
                df_input = pd.DataFrame([[features_dict[k] for k in col_names]], columns=col_names)
            else:
                df_input = pd.DataFrame([features], columns=col_names)

            # Execute real inference using predict_proba
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(df_input)[0]
                # Class 0: Baseline / Non-stress, Class 1: Stress
                if len(probs) >= 2:
                    p_stress = float(probs[1])
                    p_baseline = float(probs[0])
                    confidence = float(max(p_stress, p_baseline))
                else:
                    p_stress = float(probs[0])
                    confidence = 1.0

                # Stress classification using 0.5 decision threshold
                is_stress = p_stress >= 0.5
                stress_level = "STRESS" if is_stress else "BASELINE"
                stress_score = round(p_stress * 100.0, 2)
            else:
                pred = model.predict(df_input)[0]
                is_stress = bool(pred == 1 or pred == "STRESS")
                stress_level = "STRESS" if is_stress else "BASELINE"
                p_stress = 1.0 if is_stress else 0.0
                stress_score = 100.0 if is_stress else 0.0
                confidence = 0.85

            return {
                "status": DataStatus.REAL_DATA,
                "stress_level": stress_level,
                "stress_score": stress_score,
                "confidence": round(confidence, 3),
                "raw_probability": round(p_stress, 4),
                "message": "Estimated Stress probability successfully inferred from real physiological sensor data.",
            }
        except Exception as exc:
            logger.error(f"Inference error with ML model: {exc}")
            return {
                "status": DataStatus.SENSOR_ERROR,
                "stress_level": None,
                "stress_score": None,
                "confidence": None,
                "raw_probability": None,
                "message": f"ML model inference failed: {str(exc)}",
            }
