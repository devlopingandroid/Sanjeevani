"""High-performance signal processing module for physiological sensor streams.

Pure-numpy implementation to ensure deterministic execution, zero OpenBLAS/C-extension
deadlocks on Windows, and sub-millisecond real-time responsiveness.
"""
import numpy as np
from typing import List, Dict, Any, Optional


def bandpass_filter(
    data: np.ndarray,
    lowcut_hz: float = 0.7,
    highcut_hz: float = 3.5,
    fs: float = 25.0,
) -> np.ndarray:
    """Zero-phase bandpass filter isolating cardiac pulse frequencies (0.7 - 3.5 Hz).

    Implemented via difference of cascaded moving averages (boxcar bandpass).
    """
    if len(data) < 5:
        return data

    # Window lengths corresponding to high and low cutoff periods
    fast_win = max(1, int(fs / highcut_hz))
    slow_win = max(fast_win + 1, int(fs / lowcut_hz))

    # Remove DC baseline offset first to prevent edge convolution spikes
    ac_data = data - np.mean(data)

    # Fast moving average (removes high-frequency sensor noise)
    fast_ma = np.convolve(ac_data, np.ones(fast_win) / fast_win, mode="same")
    # Slow moving average (estimates low-frequency baseline drift)
    slow_ma = np.convolve(ac_data, np.ones(slow_win) / slow_win, mode="same")

    # Bandpass output = fast_ma - slow_ma
    return fast_ma - slow_ma


def find_peaks(
    signal_data: np.ndarray,
    min_distance: int = 10,
    prominence: Optional[float] = None,
) -> np.ndarray:
    """Finds local maxima separated by at least min_distance with optional prominence."""
    peaks = []
    n = len(signal_data)
    if n < 3:
        return np.array([], dtype=int)

    std_val = float(np.std(signal_data))
    threshold = prominence if prominence is not None else std_val * 0.4

    for i in range(1, n - 1):
        if signal_data[i] > signal_data[i - 1] and signal_data[i] > signal_data[i + 1]:
            if signal_data[i] >= threshold:
                if not peaks or (i - peaks[-1]) >= min_distance:
                    peaks.append(i)
                elif signal_data[i] > signal_data[peaks[-1]]:
                    peaks[-1] = i

    return np.array(peaks, dtype=int)


def compute_vitals_from_buffer(
    samples: List[Dict[str, Any]], fs: float = 25.0
) -> Dict[str, Optional[float]]:
    """Calculates real vitals from rolling buffer samples.

    Returns dict with keys: heart_rate_bpm, hrv_rmssd_ms, temperature_f,
    skin_conductance_us, motion_magnitude.
    Strictly returns None if signals are insufficient or below quality criteria.
    """
    vitals: Dict[str, Optional[float]] = {
        "heart_rate_bpm": None,
        "hrv_rmssd_ms": None,
        "temperature_f": None,
        "skin_conductance_us": None,
        "motion_magnitude": None,
    }

    if not samples or len(samples) < 50:  # Require at least 2 seconds (50 samples @ 25Hz)
        return vitals

    # Extract arrays
    ir_vals = np.array([s.get("ir") or s.get("IR", 0) for s in samples], dtype=float)
    temp_vals = np.array([s.get("temp_f") or s.get("Temp_F", 0.0) for s in samples], dtype=float)
    gsr_v_vals = np.array([s.get("gsr_voltage") or s.get("GSR_Voltage", 0.0) for s in samples], dtype=float)
    ax_vals = np.array([s.get("accel_x") or s.get("Accel_X", 0) for s in samples], dtype=float)
    ay_vals = np.array([s.get("accel_y") or s.get("Accel_Y", 0) for s in samples], dtype=float)
    az_vals = np.array([s.get("accel_z") or s.get("Accel_Z", 0) for s in samples], dtype=float)

    # 1. Temperature mean
    valid_temp = temp_vals[(temp_vals >= 70.0) & (temp_vals <= 115.0)]
    if len(valid_temp) > 0:
        vitals["temperature_f"] = round(float(np.mean(valid_temp)), 2)

    # 2. Motion magnitude
    acc_magnitude = np.sqrt(ax_vals**2 + ay_vals**2 + az_vals**2)
    vitals["motion_magnitude"] = round(float(np.mean(acc_magnitude)), 2)

    # 3. GSR Conductance (in microsiemens)
    valid_gsr = gsr_v_vals[(gsr_v_vals > 0.05) & (gsr_v_vals < 3.25)]
    if len(valid_gsr) > 0:
        vitals["skin_conductance_us"] = round(float(np.mean(valid_gsr)), 3)

    # 4. PPG Heart Rate & HRV
    # Check minimum optical amplitude for finger contact
    if np.mean(ir_vals) > 5000 and len(ir_vals) >= 125:  # At least 5s of clean PPG
        try:
            filtered_ir = bandpass_filter(ir_vals, lowcut_hz=0.7, highcut_hz=3.5, fs=fs)
            min_dist = int(0.4 * fs)  # Max 150 BPM
            peaks = find_peaks(filtered_ir, min_distance=min_dist)

            if len(peaks) >= 3:
                ibis = np.diff(peaks) / fs * 1000.0  # ms
                valid_ibis = ibis[(ibis >= 300) & (ibis <= 1500)]  # 40 - 200 bpm

                if len(valid_ibis) >= 2:
                    mean_ibi = float(np.mean(valid_ibis))
                    vitals["heart_rate_bpm"] = round(60000.0 / mean_ibi, 1)

                    successive_diffs = np.diff(valid_ibis)
                    if len(successive_diffs) > 0:
                        rmssd = np.sqrt(np.mean(successive_diffs**2))
                        vitals["hrv_rmssd_ms"] = round(float(rmssd), 2)
        except Exception:
            pass

    return vitals
