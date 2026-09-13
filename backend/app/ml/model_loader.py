"""Model loader for the SANJEEVNI Stress ML Model.

Follows the NO-MOCK-DATA policy: If the real model file is absent,
reports MODEL_UNAVAILABLE instead of silently providing dummy predictions.
"""
import os
import joblib
from typing import Any, Optional
from app.core.config import settings
from app.core.logging import logger


class ModelLoader:
    """Manages loading and status verification of the stress prediction model."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self._model: Optional[Any] = None
        self._is_loaded: bool = False
        self._load_error: Optional[str] = None

    def load(self) -> bool:
        """Attempts to load the model from disk."""
        if not os.path.exists(self.model_path):
            self._is_loaded = False
            self._load_error = f"Model file not found at '{self.model_path}'"
            logger.warning(
                f"ML model not found at {self.model_path}. "
                f"Prediction endpoints will return MODEL_UNAVAILABLE."
            )
            return False

        try:
            self._model = joblib.load(self.model_path)
            self._is_loaded = True
            self._load_error = None
            logger.info(f"Successfully loaded stress ML model from {self.model_path}")
            return True
        except Exception as exc:
            self._is_loaded = False
            self._load_error = f"Failed to load model: {str(exc)}"
            logger.error(f"Error loading model from {self.model_path}: {exc}")
            return False

    @property
    def is_available(self) -> bool:
        return self._is_loaded and self._model is not None

    @property
    def model(self) -> Optional[Any]:
        return self._model

    @property
    def status_message(self) -> str:
        if self.is_available:
            return "ML model loaded and ready for real inference"
        return self._load_error or "ML model file not found on disk"


model_loader = ModelLoader()
