# SANJEEVNI Phase 3 — Signal Processing, Feature Extraction & ML Inference Specification

## 1. Overview
Phase 3 implements the real-time physiological signal processing and machine learning inference pipeline for SANJEEVNI. It processes raw sensor telemetry from an ESP32 wearable across a 30-second rolling window, extracts 26 scientifically validated features in strict order, and executes real probability estimation via `predict_proba()` on `Sanjeevni_Best_Stress_Model.pkl`.

> [!IMPORTANT]
> **Clinical Disclaimer**: The outputs of this system represent **"Estimated Stress"** calculated from autonomic nervous system peripheral responses (vasoconstriction, galvanic skin conductance, heart rate variability, motion, and peripheral temperature). It is **NOT** a medical diagnosis, clinical tool, or diagnostic measurement of stress disorders or generalized anxiety.

---

## 2. Sensor-to-Model Signal Mapping Matrix

| Hardware Sensor | Hardware Measurement | Sampling Rate | Conversion & Units | Model Concept | Expected Range |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GSR (GPIO 34)** | Analog Voltage ($0 - 3.3\text{V}$) | 25 Hz | $G = \text{clip}(V \times 1.5, 0.01, 50.0)$ | Skin Conductance ($\mu\text{S}$) | $0.04 - 40.0\,\mu\text{S}$ |
| **MAX30102 (IR)** | Infrared Photoplethysmography | 25 Hz | Bandpass filtered $0.5 - 4.0\,\text{Hz}$ | Blood Volume Pulse (BVP) | Zero-centered AC ($\pm 500$) |
| **MAX30102 (IR)** | Systolic Peak-to-Peak Intervals | 25 Hz | $HR = 60 / \Delta t$ ($300 - 1500\,\text{ms}$) | Heart Rate (HR) | $40 - 200\,\text{BPM}$ |
| **MPU6050** | 3-axis Accelerometer | 25 Hz | $a = \frac{\text{raw}}{256.0}$ ($1g = 64.0\,\text{units}$) | 3D Acceleration Magnitude | $\sim 64.0$ at rest ($1g$) |
| **MAX30205** | Skin Temperature (°F) | 25 Hz | $T_C = (T_F - 32.0) \times \frac{5}{9}$ | Peripheral Skin Temp (°C) | $20.0 - 42.0^\circ\text{C}$ |

---

## 3. The 30-Second Rolling Window
- **Nominal Sample Rate**: ~25 Hz (~40 ms interval).
- **Nominal Sample Count**: 750 samples in a 30-second sliding window.
- **Window Gating Criteria**:
  - Requires at least 500 valid samples.
  - Requires at least 25.0 seconds between the oldest and newest sample timestamps.
  - Disallows telemetry gaps exceeding 8.0 seconds (indicating packet loss or disconnect).
  - Chronological bisect insertion ensures out-of-order packets are placed in sequence.
  - Duplicate packets with identical timestamps are automatically rejected.

---

## 4. Authoritative 26-Feature Vector Specification

The model `Sanjeevni_Best_Stress_Model.pkl` is a `RandomForestClassifier` consisting of 500 decision trees. It strictly expects the following 26 features in exact index order:

| Index | Feature Name | Mathematical Definition | Physiological Unit |
| :--- | :--- | :--- | :--- |
| **1** | `eda_mean` | $\mu(EDA) = \frac{1}{N}\sum EDA_i$ | $\mu\text{S}$ (MicroSiemens) |
| **2** | `eda_std` | $\sigma(EDA) = \sqrt{\frac{1}{N}\sum (EDA_i - \mu)^2}$ | $\mu\text{S}$ |
| **3** | `eda_min` | $\min(EDA)$ | $\mu\text{S}$ |
| **4** | `eda_max` | $\max(EDA)$ | $\mu\text{S}$ |
| **5** | `eda_range` | $\max(EDA) - \min(EDA)$ | $\mu\text{S}$ |
| **6** | `eda_slope` | $\frac{d(EDA)}{dt} = \frac{\text{Cov}(t, EDA)}{\text{Var}(t)}$ | $\mu\text{S}/\text{sec}$ |
| **7** | `scr_count` | Count of phasic peaks where $h \ge 0.02\,\mu\text{S}, \Delta t \ge 1.0\,\text{s}$ | Count ($0 - 20$) |
| **8** | `scr_mean` | $\frac{1}{M}\sum \text{amplitude}(SCR\_peaks)$ | $\mu\text{S}$ |
| **9** | `bvp_mean` | Mean of bandpass-filtered BVP ($0.5 - 4.0\,\text{Hz}$) | Arbitrary optical units ($\approx 0$) |
| **10** | `bvp_std` | Standard deviation of bandpass-filtered BVP | Arbitrary optical units |
| **11** | `bvp_min` | Minimum of filtered BVP | Arbitrary optical units |
| **12** | `bvp_max` | Maximum of filtered BVP | Arbitrary optical units |
| **13** | `bvp_range` | Peak-to-peak optical BVP range | Arbitrary optical units |
| **14** | `bvp_hr` | Optical heart rate: $\frac{\text{peaks count}}{\text{duration in sec}} \times 60$ | BPM |
| **15** | `hr_mean` | Mean instantaneous heart rate from valid IBIs | BPM |
| **16** | `hr_std` | Standard deviation of instantaneous heart rate | BPM |
| **17** | `hr_min` | Minimum instantaneous heart rate | BPM |
| **18** | `hr_max` | Maximum instantaneous heart rate | BPM |
| **19** | `acc_mean` | Mean 3D acceleration magnitude ($1g = 64.0$) | Scaled units ($64.0 = 1.0g$) |
| **20** | `acc_std` | Standard deviation of 3D acceleration magnitude | Scaled units |
| **21** | `acc_min` | Minimum 3D acceleration magnitude | Scaled units |
| **22** | `acc_max` | Maximum 3D acceleration magnitude | Scaled units |
| **23** | `acc_range` | Acceleration range ($\max - \min$) | Scaled units |
| **24** | `acc_rms` | Root Mean Square: $\sqrt{\frac{1}{N}\sum a_i^2}$ | Scaled units |
| **25** | `temp_mean` | Mean skin temperature converted to Celsius | °Celsius |
| **26** | `temp_std` | Standard deviation of skin temperature | °Celsius |

---

## 5. Inference & Decision Rules
- **Method**: `model.predict_proba(df)` where `df` has columns matching `FEATURE_NAMES_26`.
- **Classes**: `[0, 1]` (0 = Baseline / Non-Stress, 1 = Stress).
- **Classification Threshold**: `0.50`.
- **Continuous Score**: $P(\text{Stress}) \times 100.0$.
- **Confidence**: $\max(P_0, P_1)$.

---

## 6. Safety & Failure States
In accordance with the **NO DATA = NO VALUE** policy:
- `MODEL_UNAVAILABLE`: Returned if model file is absent or fails to load.
- `INSUFFICIENT_DATA`: Returned if buffer contains $< 500$ samples, span $< 25.0\,\text{s}$, or large telemetry gap.
- `SENSOR_ERROR`: Returned if optical lead-off is detected ($> 30\%$ samples with $IR < 1000$), GSR is saturated ($> 50\%$ samples near rails), or temperatures are unphysiological.
- Under NO circumstance does the backend fabricate fallback predictions or random probabilities.
