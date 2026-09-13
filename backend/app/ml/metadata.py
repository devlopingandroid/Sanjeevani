"""Metadata and feature schemas for the SANJEEVNI Stress ML Model.

The verified Sanjeevni_Best_Stress_Model.pkl was trained on exactly 26 features
derived from 30-second physiological windows (EDA, BVP, HR, Accelerometer, Temperature).
"""

# The authoritative 26 features in the exact order expected by the trained model
FEATURE_NAMES_26 = [
    # 1-8: Electrodermal Activity (EDA) / Galvanic Skin Response (GSR)
    "eda_mean",      # Mean skin conductance (μS)
    "eda_std",       # Standard deviation of skin conductance (μS)
    "eda_min",       # Minimum skin conductance (μS)
    "eda_max",       # Maximum skin conductance (μS)
    "eda_range",     # Peak-to-peak amplitude range (eda_max - eda_min) (μS)
    "eda_slope",     # Linear trend slope d(EDA)/dt over time (μS/s)
    "scr_count",     # Count of phasic Skin Conductance Responses (peaks)
    "scr_mean",      # Mean amplitude of detected phasic SCR peaks (μS)

    # 9-14: Blood Volume Pulse (BVP) from Optical Photoplethysmography (PPG)
    "bvp_mean",      # Mean of zero-centered bandpass-filtered BVP
    "bvp_std",       # Standard deviation of BVP amplitude
    "bvp_min",       # Minimum BVP amplitude
    "bvp_max",       # Maximum BVP amplitude
    "bvp_range",     # BVP amplitude range (bvp_max - bvp_min)
    "bvp_hr",        # Heart rate derived from BVP systolic peaks (BPM)

    # 15-18: Heart Rate (HR)
    "hr_mean",       # Mean heart rate across the 30-second window (BPM)
    "hr_std",        # Standard deviation of heart rate (BPM)
    "hr_min",        # Minimum instantaneous heart rate (BPM)
    "hr_max",        # Maximum instantaneous heart rate (BPM)

    # 19-24: Tri-Axial Accelerometer (ACC)
    "acc_mean",      # Mean 3D acceleration magnitude (scaled 1g = 64.0)
    "acc_std",       # Standard deviation of 3D acceleration magnitude
    "acc_min",       # Minimum 3D acceleration magnitude
    "acc_max",       # Maximum 3D acceleration magnitude
    "acc_range",     # Acceleration magnitude range (acc_max - acc_min)
    "acc_rms",       # Root Mean Square of 3D acceleration magnitude

    # 25-26: Skin Temperature (TEMP)
    "temp_mean",     # Mean peripheral skin temperature (°Celsius)
    "temp_std",      # Standard deviation of skin temperature (°Celsius)
]

# Backward-compatibility alias
FEATURE_NAMES = FEATURE_NAMES_26
NUM_EXPECTED_FEATURES = 26

# Binary classification targets: 0 = Baseline / Non-Stress, 1 = Stress
STRESS_CLASSES = ["BASELINE", "STRESS"]
