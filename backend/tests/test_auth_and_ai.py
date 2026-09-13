"""Tests for Authentication and xAI Grok Backend Integration."""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_register_and_login_flow():
    email = f"test_user_{pytest.importorskip('time').time()}@sanjeevni.com"
    password = "SecurePassword123!"

    # 1. Register
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test Runner"},
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == email
    assert user_data["full_name"] == "Test Runner"
    assert "password" not in user_data
    assert "hashed_password" not in user_data

    # 2. Login with valid credentials
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 3. Access protected /users/me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    # 4. Refresh token
    refresh_resp = client.post("/api/v1/auth/refresh", headers=headers)
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    # 5. Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True


def test_auth_invalid_credentials():
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@sanjeevni.com", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert "error_code" in resp.json()


def test_protected_route_without_token():
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_ai_chat_requires_auth():
    resp = client.post(
        "/api/v1/ai/chat",
        json={"message": "I am feeling stressed"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ai_chat_xai_unavailable_honest_error():
    # Login as a valid user
    email = f"ai_test_{pytest.importorskip('time').time()}@sanjeevni.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "full_name": "AI Tester"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # When XAI_API_KEY is None or empty, returns 503 honest error
    with patch.object(settings, "XAI_API_KEY", None):
        resp = client.post(
            "/api/v1/ai/chat",
            json={"message": "How do I lower stress?"},
            headers=headers,
        )
        assert resp.status_code == 503
        data = resp.json()
        assert "temporarily unavailable" in data["message"].lower()
