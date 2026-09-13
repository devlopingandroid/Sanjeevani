"""Tests for Authentication, User Profile, Avatar, and xAI Grok Backend Integration."""
import io
import time
import pytest
from unittest.mock import patch
from app.core.config import settings


def test_register_and_login_flow(client):
    email = f"test_user_{time.time()}@sanjeevni.com"
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
    assert user_data.get("profile_image_url") is None
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
    me_data = me_resp.json()
    assert me_data["email"] == email
    assert me_data["full_name"] == "Test Runner"
    assert "password" not in me_data
    assert "hashed_password" not in me_data
    assert "access_token" not in me_data

    # 4. Refresh token
    refresh_resp = client.post("/api/v1/auth/refresh", headers=headers)
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    # 5. Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True


def test_auth_invalid_credentials(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@sanjeevni.com", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert "error_code" in resp.json()


def test_protected_route_without_token(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_update_profile_and_avatar(client):
    email = f"profile_user_{time.time()}@sanjeevni.com"
    password = "SecurePassword123!"

    # 1. Register with initial name
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Yash"},
    )
    assert reg.status_code == 201
    assert reg.json()["full_name"] == "Yash"

    # 2. Login
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. GET /users/me returns real name and nullable profile_image_url
    me_resp = client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Yash"
    assert me_resp.json()["profile_image_url"] is None

    # 4. PATCH /users/me updates full_name
    patch_resp = client.patch(
        "/api/v1/users/me",
        json={"full_name": "Yash Goel"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["full_name"] == "Yash Goel"

    # 5. Unauthorized PATCH /users/me is rejected
    unauth_patch = client.patch("/api/v1/users/me", json={"full_name": "Hacker"})
    assert unauth_patch.status_code == 401

    # 6. Upload avatar (valid PNG)
    fake_png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("avatar.png", io.BytesIO(fake_png_data), "image/png")}
    avatar_resp = client.post("/api/v1/users/me/avatar", files=files, headers=headers)
    assert avatar_resp.status_code == 200
    avatar_data = avatar_resp.json()
    assert avatar_data["profile_image_url"] is not None
    assert "/uploads/avatars/avatar_" in avatar_data["profile_image_url"]
    assert avatar_data["full_name"] == "Yash Goel"

    # 7. Avatar upload with invalid file type rejected
    bad_files = {"file": ("malicious.exe", io.BytesIO(b"malware"), "application/octet-stream")}
    bad_resp = client.post("/api/v1/users/me/avatar", files=bad_files, headers=headers)
    assert bad_resp.status_code == 400

    # 8. Avatar upload without token rejected
    unauth_avatar = client.post("/api/v1/users/me/avatar", files=files)
    assert unauth_avatar.status_code == 401

    # 9. Verify GET /users/me returns persisted profile_image_url
    refreshed_me = client.get("/api/v1/users/me", headers=headers)
    assert refreshed_me.status_code == 200
    assert refreshed_me.json()["profile_image_url"] == avatar_data["profile_image_url"]
    assert refreshed_me.json()["full_name"] == "Yash Goel"


def test_ai_chat_requires_auth(client):
    resp = client.post(
        "/api/v1/ai/chat",
        json={"message": "I am feeling stressed"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ai_chat_xai_unavailable_honest_error(client):
    # Login as a valid user
    email = f"ai_test_{time.time()}@sanjeevni.com"
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
