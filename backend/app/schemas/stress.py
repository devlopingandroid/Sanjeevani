"""Stress prediction schemas adhering to the NO-MOCK-DATA policy."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import DataStatus


class StressInferenceRequest(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")


class StressPredictionResponse(BaseModel):
    """Stress prediction output.

    If model is missing, returns data_status = MODEL_UNAVAILABLE.
    If samples are < 30s buffer, returns data_status = INSUFFICIENT_DATA.
    If sensor quality is poor (lead-off/saturation), returns data_status = SENSOR_ERROR.
    """
    device_id: str
    data_status: DataStatus
    stress_level: Optional[str] = None  # "BASELINE" or "STRESS"
    stress_score: Optional[float] = None  # Continuous score (0.0 - 100.0)
    raw_probability: Optional[float] = None  # Raw model probability [0.0 - 1.0]
    confidence: Optional[float] = None
    predicted_at: Optional[datetime] = None
    model_status: str
    message: str
    features_used_count: int = 0
    features_snapshot: Optional[Dict[str, float]] = None


class ModelTestRequest(BaseModel):
    """Development/testing schema containing exactly 26 physiological features."""
    eda_mean: float = Field(..., description="Mean skin conductance (μS)")
    eda_std: float = Field(..., description="Standard deviation of skin conductance (μS)")
    eda_min: float = Field(..., description="Minimum skin conductance (μS)")
    eda_max: float = Field(..., description="Maximum skin conductance (μS)")
    eda_range: float = Field(..., description="Peak-to-peak amplitude range (μS)")
    eda_slope: float = Field(..., description="Linear trend slope d(EDA)/dt (μS/s)")
    scr_count: float = Field(..., description="Count of phasic Skin Conductance Responses")
    scr_mean: float = Field(..., description="Mean amplitude of detected phasic SCR peaks (μS)")
    bvp_mean: float = Field(..., description="Mean of zero-centered bandpass-filtered BVP")
    bvp_std: float = Field(..., description="Standard deviation of BVP amplitude")
    bvp_min: float = Field(..., description="Minimum BVP amplitude")
    bvp_max: float = Field(..., description="Maximum BVP amplitude")
    bvp_range: float = Field(..., description="BVP amplitude range")
    bvp_hr: float = Field(..., description="Heart rate derived from BVP systolic peaks (BPM)")
    hr_mean: float = Field(..., description="Mean heart rate across 30s window (BPM)")
    hr_std: float = Field(..., description="Standard deviation of heart rate (BPM)")
    hr_min: float = Field(..., description="Minimum instantaneous heart rate (BPM)")
    hr_max: float = Field(..., description="Maximum instantaneous heart rate (BPM)")
    acc_mean: float = Field(..., description="Mean 3D acceleration magnitude")
    acc_std: float = Field(..., description="Standard deviation of 3D acceleration magnitude")
    acc_min: float = Field(..., description="Minimum 3D acceleration magnitude")
    acc_max: float = Field(..., description="Maximum 3D acceleration magnitude")
    acc_range: float = Field(..., description="Acceleration magnitude range")
    acc_rms: float = Field(..., description="Root Mean Square of 3D acceleration magnitude")
    temp_mean: float = Field(..., description="Mean peripheral skin temperature (°C)")
    temp_std: float = Field(..., description="Standard deviation of skin temperature (°C)")


class ModelTestResponse(BaseModel):
    """Response schema returned by the manual model testing endpoint."""
    status: str = "MODEL_TEST_SUCCESS"
    prediction: int  # 0 (BASELINE) or 1 (STRESS)
    stress_level: str  # "BASELINE" or "STRESS"
    stress_probability: float  # [0.0 - 1.0]
    confidence: float
    model_name: str = "Sanjeevni_Best_Stress_Model.pkl"
    feature_count: int = 26
    threshold: float = 0.5
    message: str = "Manual model test completed successfully."

