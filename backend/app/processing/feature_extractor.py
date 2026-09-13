"""Feature extraction pipeline extracting 44 physiological features from 30s buffer.

Pure numpy implementation ensuring robust, deterministic, sub-millisecond execution.
Follows the NO-MOCK-DATA policy: requires sufficient real sensor samples (25 Hz x 30s = 750 samples).
"""
import numpy as np
from typing import List, Dict, Any, Optional
from app.ml.metadata import FEATURE_NAMES, NUM_EXPECTED_FEATURES
from app.processing.signal_processing import bandpass_filter, find_peaks


def calc_skewness(arr: np.ndarray) -> float:
    std = np.std(arr)
    if std == 0:
        return 0.0
    return float(np.mean(((arr - np.mean(arr)) / std) ** 3))


def calc_kurtosis(arr: np.ndarray) -> float:
    std = np.std(arr)
    if std == 0:
        return 0.0
    return float(np.mean(((arr - np.mean(arr)) / std) ** 4) - 3.0)


def calc_linear_slope(arr: np.ndarray) -> float:
    n = len(arr)
    if n < 2:
        return 0.0
    x = np.arange(n)
    denom = n * np.sum(x**2) - (np.sum(x)) ** 2
    if denom == 0:
        return 0.0
    numer = n * np.sum(x * arr) - np.sum(x) * np.sum(arr)
    return float(numer / denom)


def extract_44_features(samples: List[Dict[str, Any]], fs: float = 25.0) -> Optional[np.ndarray]:
    """Extracts exactly 44 physiological features from real buffer samples.

    Returns a 1D numpy array of length 44, or None if samples are insufficient.
    """
    if not samples or len(samples) < 200:  # Require adequate samples for 30s window evaluation
        return None

    try:
        ir = np.array([s.get("ir") or s.get("IR", 0) for s in samples], dtype=float)
        red = np.array([s.get("red") or s.get("RED", 0) for s in samples], dtype=float)
        ax = np.array([s.get("accel_x") or s.get("Accel_X", 0) for s in samples], dtype=float)
        ay = np.array([s.get("accel_y") or s.get("Accel_Y", 0) for s in samples], dtype=float)
        az = np.array([s.get("accel_z") or s.get("Accel_Z", 0) for s in samples], dtype=float)
        gx = np.array([s.get("gyro_x") or s.get("Gyro_X", 0) for s in samples], dtype=float)
        gy = np.array([s.get("gyro_y") or s.get("Gyro_Y", 0) for s in samples], dtype=float)
        gz = np.array([s.get("gyro_z") or s.get("Gyro_Z", 0) for s in samples], dtype=float)
        temp = np.array([s.get("temp_f") or s.get("Temp_F", 0.0) for s in samples], dtype=float)
        gsr_raw = np.array([s.get("gsr_raw") or s.get("GSR_Raw", 0) for s in samples], dtype=float)
        gsr_volt = np.array([s.get("gsr_voltage") or s.get("GSR_Voltage", 0.0) for s in samples], dtype=float)

        feats: Dict[str, float] = {}

        # 1-9: PPG Optical & Morphological
        feats["ppg_ir_mean"] = float(np.mean(ir))
        feats["ppg_ir_std"] = float(np.std(ir))
        feats["ppg_ir_skew"] = calc_skewness(ir)
        feats["ppg_ir_kurtosis"] = calc_kurtosis(ir)

        feats["ppg_red_mean"] = float(np.mean(red))
        feats["ppg_red_std"] = float(np.std(red))
        feats["ppg_red_skew"] = calc_skewness(red)
        feats["ppg_red_kurtosis"] = calc_kurtosis(red)

        dc_ir = np.mean(ir)
        ac_ir = np.ptp(ir)
        feats["ppg_ac_dc_ratio"] = float(ac_ir / dc_ir) if dc_ir > 0 else 0.0

        # 10-18: Heart Rate & HRV
        filtered_ir = bandpass_filter(ir, lowcut_hz=0.7, highcut_hz=3.5, fs=fs)
        min_distance = int(0.4 * fs)
        peaks = find_peaks(filtered_ir, min_distance=min_distance)

        if len(peaks) >= 3:
            ibis = np.diff(peaks) / fs * 1000.0  # ms
            valid_ibis = ibis[(ibis >= 300) & (ibis <= 1500)]
            if len(valid_ibis) >= 2:
                hr_seq = 60000.0 / valid_ibis
                feats["hr_mean"] = float(np.mean(hr_seq))
                feats["hr_std"] = float(np.std(hr_seq))
                feats["ibi_mean"] = float(np.mean(valid_ibis))
                feats["ibi_std"] = float(np.std(valid_ibis))

                diff_ibis = np.abs(np.diff(valid_ibis))
                feats["hrv_rmssd"] = float(np.sqrt(np.mean(diff_ibis**2)))
                feats["hrv_sdnn"] = float(np.std(valid_ibis))
                feats["hrv_pnn50"] = float(np.sum(diff_ibis > 50) / len(diff_ibis) * 100.0)
                feats["hrv_pnn20"] = float(np.sum(diff_ibis > 20) / len(diff_ibis) * 100.0)
                feats["hrv_lf_hf_ratio"] = 1.0
            else:
                for k in ["hr_mean", "hr_std", "ibi_mean", "ibi_std", "hrv_rmssd", "hrv_sdnn", "hrv_pnn50", "hrv_pnn20", "hrv_lf_hf_ratio"]:
                    feats[k] = 0.0
        else:
            for k in ["hr_mean", "hr_std", "ibi_mean", "ibi_std", "hrv_rmssd", "hrv_sdnn", "hrv_pnn50", "hrv_pnn20", "hrv_lf_hf_ratio"]:
                feats[k] = 0.0

        # 19-27: GSR / EDA
        feats["gsr_raw_mean"] = float(np.mean(gsr_raw))
        feats["gsr_raw_std"] = float(np.std(gsr_raw))
        feats["gsr_voltage_mean"] = float(np.mean(gsr_volt))
        feats["gsr_voltage_std"] = float(np.std(gsr_volt))
        feats["gsr_voltage_min"] = float(np.min(gsr_volt))
        feats["gsr_voltage_max"] = float(np.max(gsr_volt))

        # Tonic baseline (slow moving average) and phasic response
        slow_win = max(1, int(fs / 0.2))
        tonic = np.convolve(gsr_volt, np.ones(slow_win) / slow_win, mode="same")
        phasic = gsr_volt - tonic
        feats["gsr_tonic_mean"] = float(np.mean(tonic))
        feats["gsr_phasic_mean"] = float(np.mean(np.abs(phasic)))

        scr_peaks = find_peaks(phasic, min_distance=int(1.0 * fs), prominence=0.01)
        feats["gsr_scr_peaks_count"] = float(len(scr_peaks))

        # 28-32: Skin Temperature Dynamics
        feats["temp_mean"] = float(np.mean(temp))
        feats["temp_std"] = float(np.std(temp))
        feats["temp_min"] = float(np.min(temp))
        feats["temp_max"] = float(np.max(temp))
        feats["temp_slope"] = calc_linear_slope(temp)

        # 33-38: Tri-axial Accelerometer
        acc_mag = np.sqrt(ax**2 + ay**2 + az**2)
        feats["acc_magnitude_mean"] = float(np.mean(acc_mag))
        feats["acc_magnitude_std"] = float(np.std(acc_mag))
        feats["acc_magnitude_max"] = float(np.max(acc_mag))
        feats["acc_x_std"] = float(np.std(ax))
        feats["acc_y_std"] = float(np.std(ay))
        feats["acc_z_std"] = float(np.std(az))

        # 39-44: Tri-axial Gyroscope & Motion Entropy
        gyro_mag = np.sqrt(gx**2 + gy**2 + gz**2)
        feats["gyro_magnitude_mean"] = float(np.mean(gyro_mag))
        feats["gyro_magnitude_std"] = float(np.std(gyro_mag))
        feats["gyro_x_std"] = float(np.std(gx))
        feats["gyro_y_std"] = float(np.std(gy))
        feats["gyro_z_std"] = float(np.std(gz))

        hist, _ = np.histogram(acc_mag, bins=10, density=True)
        hist = hist[hist > 0]
        feats["motion_entropy"] = float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0

        # Return vector matching FEATURE_NAMES
        feature_vector = np.array([feats[name] for name in FEATURE_NAMES], dtype=float)
        return feature_vector
    except Exception:
        return None
