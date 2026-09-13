"""Tests for Phase 8 — Emotional Wellness UI & Data Retention API.

Tests cover:
- DELETE /api/v1/users/me/emotional-data successfully purges emotional assessments, risk events, and notification audit records for the user.
- Preserves user's conversations and raw chat_messages intact.
- Enforces strict JWT authentication (401 on missing auth).
- Ensures user A cannot delete user B's emotional data.
"""
import pytest
from app.core.security import create_access_token
from app.models.user import User
from app.models.conversation import Conversation, ChatMessage
from app.models.emotional_assessment import EmotionalAssessment
from app.models.risk_event import RiskEvent
from app.models.notification_event import NotificationEvent


def create_deletion_test_user(db_session, email="delete_user@example.com"):
    user = User(
        email=email,
        hashed_password="hashed_secret_password",
        full_name="Deletion User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    conv = Conversation(user_id=user.id, title="User Conversation")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    chat_msg = ChatMessage(
        conversation_id=conv.id,
        user_id=user.id,
        role="user",
        message="Hello Sanjeevni",
    )
    db_session.add(chat_msg)
    db_session.commit()
    db_session.refresh(chat_msg)

    assessment = EmotionalAssessment(
        user_id=user.id,
        conversation_id=conv.id,
        message_id=chat_msg.id,
        emotion="neutral",
        distress_level=0,
        llm_suggested_risk_level="normal",
        crisis_indicator=False,
        confidence=0.9,
    )
    db_session.add(assessment)
    db_session.commit()

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        assessment_id=assessment.id,
        risk_level="NORMAL",
        reason_category="routine_wellness_monitoring",
    )
    db_session.add(risk_event)
    db_session.commit()

    notif = NotificationEvent(
        risk_event_id=risk_event.id,
        user_id=user.id,
        provider="console",
        status="skipped_low_risk",
        risk_level="NORMAL",
    )
    db_session.add(notif)
    db_session.commit()

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, conv, headers


def test_delete_emotional_data_success(client, db_session):
    """Deleting emotional data purges assessments & risk events but retains conversation text."""
    user, conv, headers = create_deletion_test_user(db_session, "del_success@example.com")

    # Verify data exists
    assert db_session.query(EmotionalAssessment).filter_by(user_id=user.id).count() == 1
    assert db_session.query(RiskEvent).filter_by(user_id=user.id).count() == 1
    assert db_session.query(NotificationEvent).filter_by(user_id=user.id).count() == 1

    # Call DELETE /api/v1/users/me/emotional-data
    response = client.delete("/api/v1/users/me/emotional-data", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_assessments_count"] == 1
    assert data["deleted_risk_events_count"] == 1
    assert data["deleted_notification_events_count"] == 1

    # Verify assessments, risk events, and notification audit logs are deleted
    assert db_session.query(EmotionalAssessment).filter_by(user_id=user.id).count() == 0
    assert db_session.query(RiskEvent).filter_by(user_id=user.id).count() == 0
    assert db_session.query(NotificationEvent).filter_by(user_id=user.id).count() == 0

    # Verify conversation and raw chat_message remain intact
    assert db_session.query(Conversation).filter_by(id=conv.id).count() == 1
    assert db_session.query(ChatMessage).filter_by(conversation_id=conv.id).count() == 1


def test_delete_emotional_data_unauthorized(client):
    """Unauthenticated requests must yield 401."""
    response = client.delete("/api/v1/users/me/emotional-data")
    assert response.status_code == 401


def test_delete_emotional_data_user_isolation(client, db_session):
    """User A deleting their emotional data does NOT delete User B's data."""
    user_a, conv_a, headers_a = create_deletion_test_user(db_session, "usera_del@example.com")
    user_b, conv_b, headers_b = create_deletion_test_user(db_session, "userb_del@example.com")

    # User A deletes
    res_a = client.delete("/api/v1/users/me/emotional-data", headers=headers_a)
    assert res_a.status_code == 200

    # User A's data deleted
    assert db_session.query(EmotionalAssessment).filter_by(user_id=user_a.id).count() == 0

    # User B's data remains untouched
    assert db_session.query(EmotionalAssessment).filter_by(user_id=user_b.id).count() == 1
    assert db_session.query(RiskEvent).filter_by(user_id=user_b.id).count() == 1
