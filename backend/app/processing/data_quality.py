"""Sensor data quality and integrity checking."""
from typing import Dict, Any, List, Tuple


class DataQualityChecker:
    """Evaluates whether incoming sensor readings represent valid human physiology."""

    # Lead-off detection thresholds for MAX30102
    MIN_PPG_AMPLITUDE = 1000  # Raw ADC below this implies sensor not in skin contact

    # GSR saturation bounds
    MIN_GSR_VOLTAGE = 0.05
    MAX_GSR_VOLTAGE = 3.25

    @classmethod
    def check_sample(cls, sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
        issues = []

        ir = sample.get("ir") or sample.get("IR", 0)
        red = sample.get("red") or sample.get("RED", 0)
        gsr_v = sample.get("gsr_voltage") or sample.get("GSR_Voltage", 0.0)

        # PPG contact check
        if ir < cls.MIN_PPG_AMPLITUDE or red < cls.MIN_PPG_AMPLITUDE:
            issues.append("SENSOR_LEAD_OFF: PPG optical readings indicate no skin contact")

        # GSR saturation check
        if gsr_v < cls.MIN_GSR_VOLTAGE or gsr_v > cls.MAX_GSR_VOLTAGE:
            issues.append("GSR_SATURATION: GSR voltage near rail limits")

        is_valid = len(issues) == 0
        return is_valid, issues
