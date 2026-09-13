"""Deterministic feature extraction pipeline for SANJEEVNI Stress ML Model.

Extracts exactly 26 physiological features from the 30-second sensor window
in the exact mathematical representation and order expected by Sanjeevni_Best_Stress_Model.pkl:

1. eda_mean      - Mean skin conductance (μS)
2. eda_std       - Standard deviation of skin conductance (μS)
3. eda_min       - Minimum skin conductance (μS)
4. eda_max       - Maximum skin conductance (μS)
5. eda_range     - Peak-to-peak amplitude range (eda_max - eda_min)
6. eda_slope     - Linear trend slope d(EDA)/dt (μS/s)
7. scr_count     - Count of phasic Skin Conductance Responses (peaks)
8. scr_mean      - Mean amplitude of detected phasic SCR peaks (μS)
9. bvp_mean      - Mean of zero-centered bandpass-filtered BVP
10. bvp_std      - Standard deviation of BVP amplitude
11. bvp_min      - Minimum BVP amplitude
12. bvp_max      - Maximum BVP amplitude
13. bvp_range    - BVP amplitude range (bvp_max - bvp_min)
14. bvp_hr       - Heart rate derived from BVP systolic peaks (BPM)
15. hr_mean      - Mean heart rate across the 30-second window (BPM)
16. hr_std       - Standard deviation of heart rate (BPM)
17. hr_min       - Minimum instantaneous heart rate (BPM)
18. hr_max       - Maximum instantaneous heart rate (BPM)
19. acc_mean     - Mean 3D acceleration magnitude (scaled 1g = 64.0)
20. acc_std      - Standard deviation of 3D acceleration magnitude
21. acc_min      - Minimum 3D acceleration magnitude
22. acc_max      - Maximum 3D acceleration magnitude
23. acc_range    - Acceleration magnitude range (acc_max - acc_min)
24. acc_rms      - Root Mean Square of 3D acceleration magnitude
25. temp_mean    - Mean peripheral skin temperature (°Celsius)
26. temp_std     - Standard deviation of skin temperature (°Celsius)

Pure numpy implementation ensuring deterministic execution, zero OpenBLAS/C-extension
deadlocks on Windows, and sub-millisecond execution.
"""
import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from app.ml.metadata import FEATURE_NAMES_26, NUM_EXPECTED_FEATURES
from app.processing.signal_processing import bandpass_filter, find_peaks


def calc_linear_slope_per_sec(arr: np.ndarray, fs: float = 25.0) -> float:
    """Calculates linear slope d(signal)/dt in units per second."""
    n = len(arr)
    if n < 2:
        return 0.0
    t = np.arange(n) / fs  # time in seconds
    denom = np.var(t) * n
    if denom == 0:
        return 0.0
    cov = np.sum((t - np.mean(t)) * (arr - np.mean(arr)))
    return float(cov / denom)


def extract_scr_peaks(eda: np.ndarray, fs: float = 25.0) -> Tuple[float, float]:
    """Detects phasic Skin Conductance Responses (SCR).

    Extracts phasic component via moving baseline subtraction,
    then detects peaks with amplitude >= 0.02 μS and minimum spacing >= 1.0s.

    Returns:
        Tuple[scr_count: float, scr_mean: float]
    """
    n = len(eda)
    if n < int(fs * 4.0):  # Require at least 4 seconds
        return 0.0, 0.0

    # Moving average filter for tonic baseline (window length = 4 seconds)
    win_len = max(3, int(fs * 4.0))
    tonic = np.convolve(eda, np.ones(win_len) / win_len, mode="same")
    phasic = eda - tonic

    # Find peaks with minimum distance of 1.0s (fs samples) and prominence >= 0.02 μS
    min_dist = max(1, int(fs * 1.0))
    peaks = find_peaks(phasic, min_distance=min_dist, prominence=0.02)

    scr_count = float(len(peaks))
    if len(peaks) > 0:
        scr_mean = float(np.mean(phasic[peaks]))
    else:
        scr_mean = 0.0

    return scr_count, scr_mean


def extract_26_features(
    samples: List[Dict[str, Any]], fs: float = 25.0
) -> Tuple[Optional[np.ndarray], Optional[Dict[str, float]]]:
    """Extracts the authoritative 26 physiological features from a 30s window.

    Returns:
        Tuple[features_array (1D numpy array length 26), features_dict]
        or (None, None) if samples are insufficient or contain invalid numbers.
    """
    if not samples or len(samples) < 100:
        return None, None

    try:
        # Extract raw arrays
        ir = np.array([float(s.get("ir") or s.get("IR", 0)) for s in samples])
        red = np.array([float(s.get("red") or s.get("RED", 0)) for s in samples])
        ax = np.array([float(s.get("accel_x") or s.get("Accel_X", 0)) for s in samples])
        ay = np.array([float(s.get("accel_y") or s.get("Accel_Y", 0)) for s in samples])
        az = np.array([float(s.get("accel_z") or s.get("Accel_Z", 0)) for s in samples])
        temp_f = np.array([float(s.get("temperature") or s.get("temp_f") or s.get("Temp_F", 0.0)) for s in samples])
        gsr_v = np.array([float(s.get("gsr_voltage") or s.get("GSR_Voltage", 0.0)) for s in samples])

        # Validate non-finite numbers
        for arr in [ir, red, ax, ay, az, temp_f, gsr_v]:
            if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                return None, None

        feats: Dict[str, float] = {}

        # ==========================================================
        # 1-8: Electrodermal Activity (EDA / GSR)
        # ==========================================================
        # Calibrate GSR voltage to skin conductance in microSiemens (μS)
        # Scale: ~1.5V corresponds to ~2.25 μS; clipped to physiological human bounds (0.01 - 50.0 μS)
        eda = np.clip(gsr_v * 1.5, 0.01, 50.0)

        feats["eda_mean"] = float(np.mean(eda))
        feats["eda_std"] = float(np.std(eda))
        feats["eda_min"] = float(np.min(eda))
        feats["eda_max"] = float(np.max(eda))
        feats["eda_range"] = float(np.ptp(eda))
        feats["eda_slope"] = calc_linear_slope_per_sec(eda, fs=fs)

        scr_count, scr_mean = extract_scr_peaks(eda, fs=fs)
        feats["scr_count"] = scr_count
        feats["scr_mean"] = scr_mean

        # ==========================================================
        # 9-14: Blood Volume Pulse (BVP) from Photoplethysmography
        # ==========================================================
        # Bandpass filter IR signal between 0.5 Hz and 4.0 Hz (cardiac band)
        bvp = bandpass_filter(ir, lowcut_hz=0.5, highcut_hz=4.0, fs=fs)

        feats["bvp_mean"] = float(np.mean(bvp))
        feats["bvp_std"] = float(np.std(bvp))
        feats["bvp_min"] = float(np.min(bvp))
        feats["bvp_max"] = float(np.max(bvp))
        feats["bvp_range"] = float(np.ptp(bvp))

        # Peak detection on optical BVP systolic pulses
        # Refractory period: minimum 0.35s distance (up to 171 BPM)
        min_dist = max(1, int(0.35 * fs))
        peaks = find_peaks(bvp, min_distance=min_dist)

        duration_sec = max(1.0, len(samples) / fs)
        if len(peaks) < 2:
            # Cannot determine pulse rate without systolic peaks; reject instead of faking data
            return None, None
        feats["bvp_hr"] = float((len(peaks) / duration_sec) * 60.0)

        # ==========================================================
        # 15-18: Heart Rate (HR)
        # ==========================================================
        ibis_sec = np.diff(peaks) / fs
        # Physiological filtering: 0.3s (200 BPM) to 1.5s (40 BPM)
        valid_ibis = ibis_sec[(ibis_sec >= 0.30) & (ibis_sec <= 1.50)]
        if len(valid_ibis) < 2:
            # Cannot establish valid physiological heart rate; reject instead of faking data
            return None, None

        hr_series = 60.0 / valid_ibis
        feats["hr_mean"] = float(np.mean(hr_series))
        feats["hr_std"] = float(np.std(hr_series))
        feats["hr_min"] = float(np.min(hr_series))
        feats["hr_max"] = float(np.max(hr_series))

        # ==========================================================
        # 19-24: Accelerometer (ACC)
        # ==========================================================
        # MPU6050: default sensitivity +-2g (1g = 16384 LSB).
        # Model was trained with Empatica E4 1/64g scaling (1g = 64.0 units).
        # Conversion: raw / 16384 * 64.0 = raw / 256.0
        acc_x_scaled = ax / 256.0
        acc_y_scaled = ay / 256.0
        acc_z_scaled = az / 256.0
        acc_mag = np.sqrt(acc_x_scaled**2 + acc_y_scaled**2 + acc_z_scaled**2)

        feats["acc_mean"] = float(np.mean(acc_mag))
        feats["acc_std"] = float(np.std(acc_mag))
        feats["acc_min"] = float(np.min(acc_mag))
        feats["acc_max"] = float(np.max(acc_mag))
        feats["acc_range"] = float(np.ptp(acc_mag))
        feats["acc_rms"] = float(np.sqrt(np.mean(acc_mag**2)))

        # ==========================================================
        # 25-26: Skin Temperature (TEMP)
        # ==========================================================
        # Convert MAX30205 Fahrenheit to Celsius: (°F - 32) * 5 / 9
        temp_c = (temp_f - 32.0) * (5.0 / 9.0)

        feats["temp_mean"] = float(np.mean(temp_c))
        feats["temp_std"] = float(np.std(temp_c))

        # ==========================================================
        # Assemble exact 26-feature vector in strict order
        # ==========================================================
        feature_vector = np.array([feats[name] for name in FEATURE_NAMES_26], dtype=np.float64)

        # Final verification: exactly 26 items and all finite
        if len(feature_vector) != NUM_EXPECTED_FEATURES:
            return None, None
        if not np.all(np.isfinite(feature_vector)):
            return None, None

        return feature_vector, feats

    except Exception:
        return None, None


# Backward compatibility alias
def extract_44_features(samples: List[Dict[str, Any]], fs: float = 25.0) -> Optional[np.ndarray]:
    """Compatibility wrapper redirecting legacy callers to extract_26_features."""
    arr, _ = extract_26_features(samples, fs)
    return arr
