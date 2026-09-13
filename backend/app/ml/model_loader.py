"""Model loader for the SANJEEVNI Stress ML Model.

Follows the NO-MOCK-DATA policy: If the real model file is absent,
reports MODEL_UNAVAILABLE instead of silently providing dummy predictions.
"""
import os
import joblib
from typing import Any, Optional, List
from app.core.config import settings
from app.core.logging import logger
from app.ml.metadata import FEATURE_NAMES_26, NUM_EXPECTED_FEATURES


class ModelLoader:
    """Manages loading and status verification of the stress prediction model."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self._model: Optional[Any] = None
        self._feature_names: List[str] = FEATURE_NAMES_26
        self._is_loaded: bool = False
        self._load_error: Optional[str] = None

    def load(self) -> bool:
        """Attempts to load the model from disk once and cache it safely."""
        # Check primary configured path, and fallback to absolute path if running from subfolder
        resolved_path = self.model_path
        if not os.path.exists(resolved_path):
            alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.model_path)
            if os.path.exists(alt_path):
                resolved_path = alt_path
            else:
                self._is_loaded = False
                self._load_error = f"Model file not found at '{self.model_path}'"
                logger.warning(
                    f"ML model not found at {self.model_path}. "
                    f"Prediction endpoints will return MODEL_UNAVAILABLE."
                )
                return False

        try:
            raw_obj = joblib.load(resolved_path)
            # Unwrap dictionary container if present
            if isinstance(raw_obj, dict) and "model" in raw_obj:
                self._model = raw_obj["model"]
            else:
                self._model = raw_obj

            # Cache feature names if present on model
            if hasattr(self._model, "feature_names_in_"):
                self._feature_names = list(self._model.feature_names_in_)
            else:
                self._feature_names = FEATURE_NAMES_26

            # Verify feature count matches expected 26
            n_features = getattr(self._model, "n_features_in_", len(self._feature_names))
            if n_features != NUM_EXPECTED_FEATURES:
                logger.warning(
                    f"Model n_features_in_ ({n_features}) differs from expected {NUM_EXPECTED_FEATURES}"
                )

            self._is_loaded = True
            self._load_error = None
            logger.info(
                f"Successfully loaded {self._model.__class__.__name__} from {resolved_path} "
                f"with {n_features} features"
            )
            return True
        except Exception as exc:
            self._is_loaded = False
            self._load_error = f"Failed to load model: {str(exc)}"
            logger.error(f"Error loading model from {resolved_path}: {exc}")
            return False

    @property
    def is_available(self) -> bool:
        return self._is_loaded and self._model is not None

    @property
    def model(self) -> Optional[Any]:
        return self._model

    @property
    def feature_names(self) -> List[str]:
        return self._feature_names

    @property
    def status_message(self) -> str:
        if self.is_available:
            return "ML model loaded and ready for real inference"
        return self._load_error or "ML model file not found on disk"


# Singleton instance
model_loader = ModelLoader()
