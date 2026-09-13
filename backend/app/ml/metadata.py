"""Metadata and feature schemas for the SANJEEVNI Stress ML Model."""

# Canonical list of 44 features extracted across the 30-second rolling sensor window
FEATURE_NAMES = [
    # 1-9: PPG Optical & Morphological
    "ppg_ir_mean",
    "ppg_ir_std",
    "ppg_ir_skew",
    "ppg_ir_kurtosis",
    "ppg_red_mean",
    "ppg_red_std",
    "ppg_red_skew",
    "ppg_red_kurtosis",
    "ppg_ac_dc_ratio",
    # 10-18: Heart Rate & Heart Rate Variability (HRV)
    "hr_mean",
    "hr_std",
    "ibi_mean",
    "ibi_std",
    "hrv_rmssd",
    "hrv_sdnn",
    "hrv_pnn50",
    "hrv_pnn20",
    "hrv_lf_hf_ratio",
    # 19-27: Galvanic Skin Response (Electrodermal Activity)
    "gsr_raw_mean",
    "gsr_raw_std",
    "gsr_voltage_mean",
    "gsr_voltage_std",
    "gsr_voltage_min",
    "gsr_voltage_max",
    "gsr_tonic_mean",
    "gsr_phasic_mean",
    "gsr_scr_peaks_count",
    # 28-32: Skin Temperature Dynamics
    "temp_mean",
    "temp_std",
    "temp_min",
    "temp_max",
    "temp_slope",
    # 33-38: Tri-axial Accelerometer & Motion
    "acc_magnitude_mean",
    "acc_magnitude_std",
    "acc_magnitude_max",
    "acc_x_std",
    "acc_y_std",
    "acc_z_std",
    # 39-44: Tri-axial Gyroscope & Angular Velocity
    "gyro_magnitude_mean",
    "gyro_magnitude_std",
    "gyro_x_std",
    "gyro_y_std",
    "gyro_z_std",
    "motion_entropy",
]

NUM_EXPECTED_FEATURES = 44
STRESS_CLASSES = ["LOW", "MODERATE", "HIGH"]
