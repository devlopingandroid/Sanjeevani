"""Tests for Phase 5 — Trusted Contact and Consent System.

Tests cover:
- Create trusted contact with explicit consent
- Fetch trusted contact (GET /api/v1/trusted-contact)
- Update trusted contact (PATCH /api/v1/trusted-contact)
- Delete trusted contact (DELETE /api/v1/trusted-contact)
- Disable trusted contact (PATCH with enabled=False)
- Mandatory consent enforcement (reject consent_given=False)
- Invalid phone format rejection
- Notification preference validation (high_and_critical, critical_only allowed)
- Strict rejection of "elevated" or "normal" as notification_level
- Unauthorized access (401)
- Cross-user isolation (user A cannot access user B's contact)
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.user import User


def create_test_user(db_session, email="contact_user@example.com", name="Test Contact User"):
    user = User(
        email=email,
        hashed_password="hashed_secret_password",
        full_name=name,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def test_get_trusted_contact_not_found(client, db_session):
    """By default, no trusted contact exists (404)."""
    user, headers = create_test_user(db_session, "user1@example.com")
    response = client.get("/api/v1/trusted-contact", headers=headers)
    assert response.status_code == 404
    assert "No trusted contact configured" in response.json()["detail"]


def test_create_trusted_contact_success(client, db_session):
    """Create a trusted contact with valid parameters and explicit consent."""
    user, headers = create_test_user(db_session, "user2@example.com")
    payload = {
        "name": "Dr. Ramesh Sharma",
        "phone_number": "+919876543210",
        "relationship": "Physician",
        "enabled": True,
        "consent_given": True,
        "notification_level": "high_and_critical"
    }
    response = client.post("/api/v1/trusted-contact", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dr. Ramesh Sharma"
    assert data["phone_number"] == "+919876543210"
    assert data["relationship"] == "Physician"
    assert data["enabled"] is True
    assert data["consent_given"] is True
    assert data["notification_level"] == "high_and_critical"
    assert data["user_id"] == user.id


def test_create_trusted_contact_consent_required(client, db_session):
    """Attempting to create contact without explicit consent MUST be rejected with 422."""
    user, headers = create_test_user(db_session, "noconsent@example.com")
    payload = {
        "name": "Jane Doe",
        "phone_number": "+1234567890",
        "consent_given": False,
        "notification_level": "critical_only"
    }
    response = client.post("/api/v1/trusted-contact", json=payload, headers=headers)
    assert response.status_code == 422


def test_create_trusted_contact_invalid_phone(client, db_session):
    """Attempting to create contact with invalid phone format MUST be rejected with 422."""
    user, headers = create_test_user(db_session, "badphone@example.com")
    payload = {
        "name": "Jane Doe",
        "phone_number": "123",  # Too short
        "consent_given": True,
        "notification_level": "critical_only"
    }
    response = client.post("/api/v1/trusted-contact", json=payload, headers=headers)
    assert response.status_code == 422

    payload["phone_number"] = "invalid_phone_string_abc!"
    response = client.post("/api/v1/trusted-contact", json=payload, headers=headers)
    assert response.status_code == 422


def test_reject_elevated_and_normal_notification_level(client, db_session):
    """Notification level MUST reject 'elevated' and 'normal' values."""
    user, headers = create_test_user(db_session, "badlevel@example.com")
    
    # Try 'elevated'
    payload = {
        "name": "Jane Doe",
        "phone_number": "+12345678901",
        "consent_given": True,
        "notification_level": "elevated"
    }
    response = client.post("/api/v1/trusted-contact", json=payload, headers=headers)
    assert response.status_code == 422

    # Try 'normal'
    payload["notification_level"] = "normal"
    response = client.post("/api/v1/trusted-contact", json=payload, headers=headers)
    assert response.status_code == 422


def test_update_and_disable_trusted_contact(client, db_session):
    """Update contact attributes and disable/enable contact."""
    user, headers = create_test_user(db_session, "updateuser@example.com")
    
    # Create first
    client.post("/api/v1/trusted-contact", json={
        "name": "Original Name",
        "phone_number": "+919999999999",
        "consent_given": True,
        "notification_level": "high_and_critical"
    }, headers=headers)

    # Patch update
    update_payload = {
        "name": "Updated Name",
        "notification_level": "critical_only",
        "enabled": False
    }
    response = client.patch("/api/v1/trusted-contact", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["notification_level"] == "critical_only"
    assert data["enabled"] is False


def test_delete_trusted_contact(client, db_session):
    """Delete an existing trusted contact."""
    user, headers = create_test_user(db_session, "deluser@example.com")
    
    # Create
    client.post("/api/v1/trusted-contact", json={
        "name": "Contact to Delete",
        "phone_number": "+918888888888",
        "consent_given": True,
    }, headers=headers)

    # Delete
    response = client.delete("/api/v1/trusted-contact", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify GET now returns 404
    get_res = client.get("/api/v1/trusted-contact", headers=headers)
    assert get_res.status_code == 404


def test_unauthorized_access(client):
    """Unauthenticated requests must be rejected with 401."""
    assert client.get("/api/v1/trusted-contact").status_code == 401
    assert client.post("/api/v1/trusted-contact", json={}).status_code == 401
    assert client.patch("/api/v1/trusted-contact", json={}).status_code == 401
    assert client.delete("/api/v1/trusted-contact").status_code == 401


def test_cross_user_isolation(client, db_session):
    """User A's trusted contact is completely isolated from User B."""
    user_a, headers_a = create_test_user(db_session, "usera@example.com")
    user_b, headers_b = create_test_user(db_session, "userb@example.com")

    # User A creates a contact
    client.post("/api/v1/trusted-contact", json={
        "name": "User A Contact",
        "phone_number": "+11111111111",
        "consent_given": True,
        "notification_level": "high_and_critical"
    }, headers=headers_a)

    # User B checks GET -> 404 Not Found
    res_b = client.get("/api/v1/trusted-contact", headers=headers_b)
    assert res_b.status_code == 404

    # User B patches -> 404 Not Found
    patch_b = client.patch("/api/v1/trusted-contact", json={"name": "Hacked Name"}, headers=headers_b)
    assert patch_b.status_code == 404

    # User B deletes -> 404 Not Found
    del_b = client.delete("/api/v1/trusted-contact", headers=headers_b)
    assert del_b.status_code == 404

    # User A's contact remains unchanged
    res_a = client.get("/api/v1/trusted-contact", headers=headers_a)
    assert res_a.status_code == 200
    assert res_a.json()["name"] == "User A Contact"
