"""Sensor data quality and integrity checking for SANJEEVNI.

Validates single samples and 30-second physiological windows before ML feature extraction.
Enforces the NO-MOCK-DATA policy: returns explicit error and insufficient states
if real sensors are disconnected, saturated, or lead-off.
"""
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from app.schemas.common import DataStatus


class DataQualityChecker:
    """Evaluates whether incoming sensor readings represent valid human physiology."""

    # Lead-off detection thresholds for MAX30102
    MIN_PPG_AMPLITUDE = 1000  # Raw ADC below 1000 indicates finger not placed on optical sensor

    # GSR saturation bounds (3.3V ADC reference)
    MIN_GSR_VOLTAGE = 0.05
    MAX_GSR_VOLTAGE = 3.25

    # Physiological temperature bounds (MAX30205)
    MIN_TEMP_F = 68.0    # 20.0 °C
    MAX_TEMP_F = 113.0   # 45.0 °C

    # Minimum window constraints for 30s window @ ~25 Hz
    MIN_SAMPLE_COUNT = 500          # At least ~20 seconds worth of samples
    MIN_WINDOW_DURATION_SEC = 25.0  # Time span between first and last sample
    MAX_TIMESTAMP_GAP_SEC = 8.0     # Reject windows with large disconnection gaps

    @classmethod
    def check_sample(cls, sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Checks a single incoming sensor packet."""
        issues = []

        ir = sample.get("ir") or sample.get("IR", 0)
        red = sample.get("red") or sample.get("RED", 0)
        gsr_v = sample.get("gsr_voltage") or sample.get("GSR_Voltage", 0.0)
        temp_f = sample.get("temperature") or sample.get("temp_f") or sample.get("Temp_F", 0.0)

        # PPG contact check
        if ir < cls.MIN_PPG_AMPLITUDE or red < cls.MIN_PPG_AMPLITUDE:
            issues.append("SENSOR_LEAD_OFF: PPG optical readings indicate no skin contact")

        # GSR saturation check
        if gsr_v < cls.MIN_GSR_VOLTAGE or gsr_v > cls.MAX_GSR_VOLTAGE:
            issues.append("GSR_SATURATION: GSR voltage near rail limits")

        # Temperature check
        if temp_f < cls.MIN_TEMP_F or temp_f > cls.MAX_TEMP_F:
            issues.append("TEMPERATURE_ERROR: Unphysiological temperature reading")

        is_valid = len(issues) == 0
        return is_valid, issues

    @classmethod
    def evaluate_30s_window(cls, samples: List[Dict[str, Any]]) -> Tuple[bool, str, str]:
        """Evaluates whether a 30-second window is ready and of sufficient quality for ML inference.

        Returns:
            Tuple[is_valid: bool, status: str, reason: str]
            Status can be: "VALID", "INSUFFICIENT_DATA", or "SENSOR_ERROR"
        """
        if not samples or len(samples) < cls.MIN_SAMPLE_COUNT:
            count = len(samples) if samples else 0
            return (
                False,
                DataStatus.INSUFFICIENT_DATA,
                f"Insufficient buffer samples ({count}/{cls.MIN_SAMPLE_COUNT} required for 30s window).",
            )

        # Parse timestamps to verify real duration and continuity
        timestamps: List[datetime] = []
        for s in samples:
            ts = s.get("sensor_timestamp") or s.get("timestamp")
            if isinstance(ts, datetime):
                timestamps.append(ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc))
            elif isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    timestamps.append(dt)
                except Exception:
                    pass

        if len(timestamps) >= 2:
            timestamps.sort()
            duration = (timestamps[-1] - timestamps[0]).total_seconds()
            if duration < cls.MIN_WINDOW_DURATION_SEC:
                return (
                    False,
                    DataStatus.INSUFFICIENT_DATA,
                    f"Sensor window span ({duration:.1f}s) is shorter than required {cls.MIN_WINDOW_DURATION_SEC}s.",
                )

            # Check for excessive gaps (connection drops)
            gaps = [
                (timestamps[i + 1] - timestamps[i]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]
            if gaps and max(gaps) > cls.MAX_TIMESTAMP_GAP_SEC:
                return (
                    False,
                    DataStatus.INSUFFICIENT_DATA,
                    f"Discontinuous telemetry: gap of {max(gaps):.1f}s detected in 30s window.",
                )

        # Signal Quality: Lead-off check across window
        ir_vals = np.array([float(s.get("ir") or s.get("IR", 0)) for s in samples])
        red_vals = np.array([float(s.get("red") or s.get("RED", 0)) for s in samples])
        lead_off_ratio = np.mean((ir_vals < cls.MIN_PPG_AMPLITUDE) | (red_vals < cls.MIN_PPG_AMPLITUDE))
        if lead_off_ratio > 0.30:
            return (
                False,
                DataStatus.SENSOR_ERROR,
                f"Optical sensor lead-off: {lead_off_ratio * 100:.1f}% of PPG samples indicate poor skin contact.",
            )

        # Signal Quality: GSR saturation check
        gsr_vals = np.array([float(s.get("gsr_voltage") or s.get("GSR_Voltage", 0.0)) for s in samples])
        sat_ratio = np.mean((gsr_vals < cls.MIN_GSR_VOLTAGE) | (gsr_vals > cls.MAX_GSR_VOLTAGE))
        if sat_ratio > 0.50:
            return (
                False,
                DataStatus.SENSOR_ERROR,
                f"GSR rail saturation: {sat_ratio * 100:.1f}% of EDA samples are near rail limits.",
            )

        # Signal Quality: Temperature check
        temp_vals = np.array([float(s.get("temperature") or s.get("temp_f") or s.get("Temp_F", 0.0)) for s in samples])
        mean_temp = float(np.mean(temp_vals))
        if mean_temp < cls.MIN_TEMP_F or mean_temp > cls.MAX_TEMP_F:
            return (
                False,
                DataStatus.SENSOR_ERROR,
                f"Unphysiological mean temperature ({mean_temp:.1f}°F) in 30s window.",
            )

        return True, DataStatus.REAL_DATA, "Window validated and ready for ML inference."
