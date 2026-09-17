"""Exhibition Demo Mode Helper for SANJEEVNI Backend.

Provides bounded synthetic GSR generation (strictly 2000 - 2500) and demo stress calculations
ONLY when DEMO_MODE=true is explicitly configured in environment variables.

DEFAULT: DEMO_MODE=false (Production real-data pipeline).
"""
import math
from typing import Tuple, Dict, Any, List

MIN_DEMO_GSR_RAW = 2000
MAX_DEMO_GSR_RAW = 2500


def calculate_demo_gsr(seq_or_index: int = 0) -> Tuple[int, float]:
    """Generates a smooth, bounded synthetic GSR reading (2000 - 2500) and corresponding voltage.
    
    Formula:
    voltage = round((gsr_raw / 4095.0) * 3.3, 3)
    """
    # Smooth bounded oscillation between 2000 and 2500
    wave = 0.5 * (1.0 + math.sin((seq_or_index or 0) * 0.1))
    raw_val = int(round(MIN_DEMO_GSR_RAW + wave * (MAX_DEMO_GSR_RAW - MIN_DEMO_GSR_RAW)))
    raw_val = max(MIN_DEMO_GSR_RAW, min(MAX_DEMO_GSR_RAW, raw_val))
    
    voltage = round((raw_val / 4095.0) * 3.3, 3)
    return raw_val, voltage


def inject_demo_gsr_if_needed(sample: Dict[str, Any], index: int = 0) -> Tuple[Dict[str, Any], bool]:
    """Injects synthetic GSR if sample has missing/unwired GSR and DEMO_MODE=true."""
    from app.core.config import settings

    if not getattr(settings, "DEMO_MODE", False):
        return sample, False

    current_gsr_raw = sample.get("gsr_raw") or sample.get("GSR_Raw") or 0
    current_gsr_v = sample.get("gsr_voltage") or sample.get("GSR_Voltage") or 0.0

    # Inject demo GSR only if physical reading is absent or near zero (< 50 ADC / < 0.05V)
    if current_gsr_raw < 50 or current_gsr_v < 0.05:
        seq = sample.get("sequence_number") or index
        raw_val, voltage = calculate_demo_gsr(seq)
        sample["gsr_raw"] = raw_val
        sample["GSR_Raw"] = raw_val
        sample["gsr_voltage"] = voltage
        sample["GSR_Voltage"] = voltage
        sample["is_demo"] = True
        return sample, True

    return sample, False


def calculate_demo_stress_percentage(samples: List[Dict[str, Any]]) -> float:
    """Calculates deterministic demo stress percentage (0.0 - 100.0%) from demo GSR signal range."""
    if not samples:
        return 45.0

    gsr_vals = []
    for s in samples:
        raw = s.get("gsr_raw") or s.get("GSR_Raw") or 2250
        gsr_vals.append(raw)

    avg_gsr = sum(gsr_vals) / float(len(gsr_vals))
    # Map 2000 -> 15.0%, 2500 -> 85.0%
    ratio = (avg_gsr - MIN_DEMO_GSR_RAW) / float(MAX_DEMO_GSR_RAW - MIN_DEMO_GSR_RAW)
    pct = 15.0 + ratio * 70.0
    return round(max(0.0, min(100.0, pct)), 1)
