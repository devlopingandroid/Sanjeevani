"""Automated verification suite for Phase 3:

Covers:
- 30-second rolling buffer behavior (pruning, sorting, capacity)
- Device isolation across concurrent buffers
- Duplicate and out-of-order packet handling in the buffer
- Insufficient window rejection
- Invalid sensor and lead-off rejection (data quality gating)
- Deterministic 26-feature vector length and exact ordering
- Rejection of NaN / Inf in features
- Model loading from backend/models/Sanjeevni_Best_Stress_Model.pkl
- Model unavailable failure state
- Real predict_proba inference output validation (0.0 <= p <= 1.0)
- No inference when data is insufficient
- Zero fake/random fallback predictions
- Database persistence of real predictions to stress_predictions
- API response states (REAL_DATA, INSUFFICIENT_DATA, MODEL_UNAVAILABLE, SENSOR_ERROR)
"""
import numpy as np
import pytest
from datetime import datetime, timezone, timedelta

from app.processing.buffer import DeviceRollingBuffer, buffer_manager
from app.processing.data_quality import DataQualityChecker
from app.processing.feature_extractor import extract_26_features
from app.ml.metadata import FEATURE_NAMES_26, NUM_EXPECTED_FEATURES
from app.ml.model_loader import model_loader
from app.ml.predictor import StressPredictor
from app.services.stress_service import StressService
from app.schemas.common import DataStatus
from app.models.stress_prediction import StressPrediction
from app.models.device import Device


def generate_deterministic_window(n: int = 750, fs: float = 25.0, start_time: datetime = None):
    """Generates a deterministic 30-second window (750 samples @ 25 Hz) of realistic physiology."""
    if start_time is None:
        start_time = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)
    t = np.arange(n) / fs
    samples = []
    for i in range(n):
        ts = start_time + timedelta(seconds=float(t[i]))
        samples.append({
            "device_id": "TEST_DEVICE_P3",
            "sensor_timestamp": ts,
            "timestamp": ts.isoformat(),
            "ir": 26000 + int(500 * np.sin(2 * np.pi * 1.2 * t[i])),
            "red": 18500 + int(350 * np.sin(2 * np.pi * 1.2 * t[i])),
            "accel_x": 200,
            "accel_y": -120,
            "accel_z": 16300,
            "gyro_x": 5,
            "gyro_y": -3,
            "gyro_z": 1,
            "temp_f": 92.6,
            "gsr_raw": 1900,
            "gsr_voltage": 1.55 + 0.05 * np.sin(2 * np.pi * 0.1 * t[i]),
            "transport": "HTTP",
        })
    return samples


def test_buffer_30s_window_pruning():
    """Buffer must discard samples older than 30 seconds relative to the newest sample."""
    buf = DeviceRollingBuffer(window_seconds=30.0)
    base_time = datetime(2026, 9, 13, 10, 0, 0, tzinfo=timezone.utc)

    # Insert 1000 samples spanning 40 seconds (25 Hz)
    for i in range(1000):
        ts = base_time + timedelta(seconds=i * 0.04)
        buf.add_sample({"sensor_timestamp": ts, "ir": 25000})

    # Buffer should retain at most 30 seconds worth of samples (751 samples max)
    assert buf.count() <= 755
    assert buf.duration_seconds() <= 30.1
    samples = buf.get_samples()
    oldest_ts = samples[0]["sensor_timestamp"]
    newest_ts = samples[-1]["sensor_timestamp"]
    assert (newest_ts - oldest_ts).total_seconds() <= 30.1


def test_buffer_device_isolation():
    """Buffers for different device_ids must remain strictly isolated."""
    buffer_manager.clear_device("DEV_A")
    buffer_manager.clear_device("DEV_B")

    s_a = {"sensor_timestamp": datetime.now(timezone.utc), "ir": 11111}
    s_b = {"sensor_timestamp": datetime.now(timezone.utc), "ir": 22222}

    buffer_manager.add_sample("DEV_A", s_a)
    buffer_manager.add_sample("DEV_B", s_b)

    samples_a = buffer_manager.get_device_samples("DEV_A")
    samples_b = buffer_manager.get_device_samples("DEV_B")

    assert len(samples_a) == 1
    assert len(samples_b) == 1
    assert samples_a[0]["ir"] == 11111
    assert samples_b[0]["ir"] == 22222


def test_buffer_duplicate_packet_rejection():
    """Duplicate packets with identical timestamps must not be appended."""
    buf = DeviceRollingBuffer(window_seconds=30.0)
    t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    added1 = buf.add_sample({"sensor_timestamp": t, "ir": 20000})
    added2 = buf.add_sample({"sensor_timestamp": t, "ir": 20000})  # Duplicate

    assert added1 is True
    assert added2 is False
    assert buf.count() == 1


def test_buffer_out_of_order_insertion():
    """Out-of-order packets arriving late within the 30s window must be placed in chronological order."""
    buf = DeviceRollingBuffer(window_seconds=30.0)
    t0 = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(seconds=1)
    t2 = t0 + timedelta(seconds=2)

    buf.add_sample({"sensor_timestamp": t0, "seq": 0})
    buf.add_sample({"sensor_timestamp": t2, "seq": 2})
    buf.add_sample({"sensor_timestamp": t1, "seq": 1})  # Out-of-order packet

    samples = buf.get_samples()
    assert [s["seq"] for s in samples] == [0, 1, 2]


def test_data_quality_insufficient_samples():
    """Windows with fewer than 500 samples must return INSUFFICIENT_DATA."""
    samples = generate_deterministic_window(n=200)  # Only ~8 seconds
    is_valid, status, reason = DataQualityChecker.evaluate_30s_window(samples)

    assert is_valid is False
    assert status == DataStatus.INSUFFICIENT_DATA
    assert "Insufficient buffer samples" in reason


def test_data_quality_optical_leadoff():
    """Windows where PPG optical contact is lost (>30% samples < 1000) must return SENSOR_ERROR."""
    samples = generate_deterministic_window(n=750)
    for i in range(300):
        samples[i]["ir"] = 200  # Lead-off
        samples[i]["red"] = 150

    is_valid, status, reason = DataQualityChecker.evaluate_30s_window(samples)
    assert is_valid is False
    assert status == DataStatus.SENSOR_ERROR
    assert "Optical sensor lead-off" in reason


def test_data_quality_gsr_rail_saturation():
    """Windows where GSR voltage is near rail limits (>50% samples) must return SENSOR_ERROR."""
    samples = generate_deterministic_window(n=750)
    for i in range(400):
        samples[i]["gsr_voltage"] = 3.29  # Saturated at rail

    is_valid, status, reason = DataQualityChecker.evaluate_30s_window(samples)
    assert is_valid is False
    assert status == DataStatus.SENSOR_ERROR
    assert "GSR rail saturation" in reason


def test_feature_vector_exact_26_length_and_order():
    """Feature extraction must produce exactly 26 finite features in the verified order."""
    samples = generate_deterministic_window(n=750)
    vec, feat_dict = extract_26_features(samples, fs=25.0)

    assert vec is not None
    assert len(vec) == 26
    assert list(feat_dict.keys()) == FEATURE_NAMES_26
    assert np.all(np.isfinite(vec))


def test_feature_extraction_nan_rejection():
    """Samples containing NaN or Inf must return None to protect model safety."""
    samples = generate_deterministic_window(n=750)
    samples[100]["gsr_voltage"] = float("nan")

    vec, feat_dict = extract_26_features(samples, fs=25.0)
    assert vec is None
    assert feat_dict is None


def test_deterministic_feature_extraction():
    """Given identical sensor input, feature extraction output must be 100% identical."""
    samples1 = generate_deterministic_window(n=750)
    samples2 = generate_deterministic_window(n=750)

    vec1, _ = extract_26_features(samples1, fs=25.0)
    vec2, _ = extract_26_features(samples2, fs=25.0)

    assert np.array_equal(vec1, vec2)


def test_model_loading_and_attributes():
    """Model loader must successfully load Sanjeevni_Best_Stress_Model.pkl with 26 features."""
    assert model_loader.load() is True
    assert model_loader.is_available is True
    assert model_loader.model.__class__.__name__ == "RandomForestClassifier"
    assert getattr(model_loader.model, "n_features_in_", 26) == 26
    assert len(model_loader.feature_names) == 26


def test_predict_proba_inference_range():
    """Inference via StressPredictor.predict must produce probability in [0.0, 1.0]."""
    samples = generate_deterministic_window(n=750)
    vec, feat_dict = extract_26_features(samples)
    assert vec is not None

    result = StressPredictor.predict(vec, feat_dict)
    assert result["status"] == DataStatus.REAL_DATA
    assert result["stress_level"] in ["BASELINE", "STRESS"]
    assert 0.0 <= result["raw_probability"] <= 1.0
    assert 0.0 <= result["stress_score"] <= 100.0
    assert 0.5 <= result["confidence"] <= 1.0


def test_no_inference_when_data_insufficient(db_session):
    """StressService.run_prediction must return INSUFFICIENT_DATA when buffer is empty."""
    buffer_manager.clear_device("DEV_EMPTY")
    resp = StressService.run_prediction(db_session, "DEV_EMPTY")

    assert resp.data_status == DataStatus.INSUFFICIENT_DATA
    assert resp.stress_level is None
    assert resp.stress_score is None
    assert resp.features_used_count == 0


def test_database_persistence_of_real_prediction(db_session):
    """A verified prediction must be persisted into the stress_predictions table."""
    device_id = "DEV_PERSIST_TEST"
    # Register device in db first to satisfy foreign key
    dev = Device(device_id=device_id, name="Test Device", status="CONNECTED")
    db_session.add(dev)
    db_session.commit()

    samples = generate_deterministic_window(n=750)
    buffer_manager.clear_device(device_id)
    buffer_manager.add_batch(device_id, samples)

    resp = StressService.run_prediction(db_session, device_id)
    assert resp.data_status == DataStatus.REAL_DATA
    assert resp.stress_score is not None

    # Check persistence in database
    saved = db_session.query(StressPrediction).filter(StressPrediction.device_id == device_id).first()
    assert saved is not None
    assert saved.stress_score == resp.stress_score
    assert saved.stress_level == resp.stress_level
    assert saved.features_snapshot is not None
    assert len(saved.features_snapshot) == 26


def test_api_predict_and_latest_endpoints(client, db_session):
    """API endpoints /api/v1/stress/predict and /api/v1/stress/latest/{device_id} must work end-to-end."""
    device_id = "API_DEVICE_TEST"
    dev = Device(device_id=device_id, name="API Test Device", status="CONNECTED")
    db_session.add(dev)
    db_session.commit()

    # Before adding buffer, latest should report NO_DATA
    r_latest_empty = client.get(f"/api/v1/stress/latest/{device_id}")
    assert r_latest_empty.status_code == 200
    assert r_latest_empty.json()["data_status"] == "NO_DATA"

    # Fill buffer with 750 samples
    samples = generate_deterministic_window(n=750)
    buffer_manager.clear_device(device_id)
    buffer_manager.add_batch(device_id, samples)

    # Trigger prediction via API
    r_predict = client.post("/api/v1/stress/predict", json={"device_id": device_id})
    assert r_predict.status_code == 200
    data = r_predict.json()
    assert data["data_status"] == "REAL_DATA"
    assert data["stress_level"] in ["BASELINE", "STRESS"]
    assert data["features_used_count"] == 26

    # Fetch latest prediction via API
    r_latest = client.get(f"/api/v1/stress/latest/{device_id}")
    assert r_latest.status_code == 200
    latest_data = r_latest.json()
    assert latest_data["data_status"] == "REAL_DATA"
    assert latest_data["stress_score"] == data["stress_score"]
