"""Backend unit tests for manual model test endpoint POST /api/v1/stress/model-test."""
import time
import pytest
from unittest.mock import patch
from app.models.stress_prediction import StressPrediction
from app.ml.model_loader import model_loader
from app.ml.metadata import FEATURE_NAMES_26


def get_valid_26_payload():
    """Generates a valid 26-feature payload with realistic physiological values."""
    return {
        "eda_mean": 0.52,
        "eda_std": 0.13,
        "eda_min": 0.20,
        "eda_max": 0.85,
        "eda_range": 0.65,
        "eda_slope": 0.002,
        "scr_count": 3.0,
        "scr_mean": 0.25,
        "bvp_mean": 0.05,
        "bvp_std": 12.4,
        "bvp_min": -45.0,
        "bvp_max": 48.0,
        "bvp_range": 93.0,
        "bvp_hr": 74.0,
        "hr_mean": 75.2,
        "hr_std": 4.1,
        "hr_min": 68.0,
        "hr_max": 86.0,
        "acc_mean": 64.2,
        "acc_std": 1.5,
        "acc_min": 62.0,
        "acc_max": 68.0,
        "acc_range": 6.0,
        "acc_rms": 64.2,
        "temp_mean": 33.5,
        "temp_std": 0.2,
    }


def test_unauthenticated_model_test_rejected(client):
    payload = get_valid_26_payload()
    resp = client.post("/api/v1/stress/model-test", json=payload)
    assert resp.status_code == 401


def test_valid_26_feature_model_test_success(client, db_session):
    # Register & Login
    email = f"model_tester_{time.time()}@sanjeevni.com"
    password = "SecurePassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Model Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    count_before = db_session.query(StressPrediction).count()

    payload = get_valid_26_payload()
    resp = client.post("/api/v1/stress/model-test", json=payload, headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] == "MODEL_TEST_SUCCESS"
    assert data["prediction"] in (0, 1)
    assert data["stress_level"] in ("BASELINE", "STRESS")
    assert 0.0 <= data["stress_probability"] <= 1.0
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["feature_count"] == 26
    assert data["model_name"] == "Sanjeevni_Best_Stress_Model.pkl"
    assert data["threshold"] == 0.5

    # Production persistence isolation assertion: DB count must NOT change
    count_after = db_session.query(StressPrediction).count()
    assert count_after == count_before


def test_missing_feature_rejected(client):
    email = f"tester_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = get_valid_26_payload()
    del payload["temp_std"]  # Delete 1 required feature

    resp = client.post("/api/v1/stress/model-test", json=payload, headers=headers)
    assert resp.status_code == 422


def test_invalid_numeric_value_rejected(client):
    email = f"tester_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = get_valid_26_payload()
    payload["eda_mean"] = "not-a-number"

    resp = client.post("/api/v1/stress/model-test", json=payload, headers=headers)
    assert resp.status_code == 422


def test_nan_and_infinity_rejected(client):
    email = f"tester_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # NaN test (string "NaN")
    nan_payload = get_valid_26_payload()
    nan_payload["hr_mean"] = "NaN"
    resp_nan = client.post("/api/v1/stress/model-test", json=nan_payload, headers=headers)
    assert resp_nan.status_code in (400, 422)

    # Infinity test (string "Infinity")
    inf_payload = get_valid_26_payload()
    inf_payload["hr_mean"] = "Infinity"
    resp_inf = client.post("/api/v1/stress/model-test", json=inf_payload, headers=headers)
    assert resp_inf.status_code in (400, 422)


def test_model_unavailable_returns_honest_error(client):
    email = f"tester_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = get_valid_26_payload()

    with patch.object(model_loader, "_is_loaded", False):
        resp = client.post("/api/v1/stress/model-test", json=payload, headers=headers)
        assert resp.status_code == 503
        data = resp.json()
        assert data["error_code"] == "MODEL_UNAVAILABLE"
        assert "not available" in data["message"].lower()
