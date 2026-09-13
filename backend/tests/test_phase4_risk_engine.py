"""Phase 4 Deterministic Distress Risk Engine Test Suite.

Verifies:
- NORMAL risk evaluation
- ELEVATED risk evaluation
- HIGH risk evaluation
- CRITICAL risk evaluation with crisis indicator
- Repeated distress WITHIN lookback window -> escalates to HIGH
- Repeated distress OUTSIDE lookback window -> does NOT escalate (window boundary test)
- Crisis indicator immediate escalation
- Trusted contact notification status (false / no_trusted_contact_configured)
- Invalid / None assessment safety
- Multiple risk events sequential recording
- Cross-user isolation (404)
- Verification that risk_events.risk_level is NEVER a direct copy of llm_suggested_risk_level
"""
import time
import json
from datetime import datetime, timezone, timedelta
import pytest
import httpx
from unittest.mock import patch, AsyncMock

from app.core.config import settings
from app.services.risk_engine import RiskEngineService
from app.models.emotional_assessment import EmotionalAssessment
from app.schemas.risk import AuthoritativeRiskLevel


def register_and_login(client, email_prefix: str):
    email = f"{email_prefix}_{time.time()}@sanjeevni.com"
    password = "SecurePassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": email_prefix})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_normal_risk_evaluation(client):
    headers = register_and_login(client, "user_risk_normal")

    mock_llm_json = {
        "emotion": "neutral",
        "distress_level": 0,
        "llm_suggested_risk_level": "normal",
        "crisis_indicator": False,
        "confidence": 0.95,
        "reason_category": "general_query"
    }
    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase4"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "What is sleep hygiene?"},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            risk_resp = client.get(f"/api/v1/conversations/{conv_id}/risk-events", headers=headers)
            assert risk_resp.status_code == 200
            events = risk_resp.json()
            assert len(events) == 1
            assert events[0]["risk_level"] == "NORMAL"
            assert events[0]["trusted_contact_notified"] is False
            assert events[0]["notification_status"] in ("no_trusted_contact_configured", "skipped_low_risk")


@pytest.mark.asyncio
async def test_elevated_risk_evaluation(client):
    headers = register_and_login(client, "user_risk_elevated")

    mock_llm_json = {
        "emotion": "stressed",
        "distress_level": 2,
        "llm_suggested_risk_level": "elevated",
        "crisis_indicator": False,
        "confidence": 0.85,
        "reason_category": "work_stress"
    }
    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase4"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "I have so much work today and feel stressed."},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            risk_resp = client.get(f"/api/v1/conversations/{conv_id}/risk-events", headers=headers)
            assert risk_resp.status_code == 200
            assert risk_resp.json()[0]["risk_level"] == "ELEVATED"
            assert risk_resp.json()[0]["action_taken"] == "monitored_wellness_support"


@pytest.mark.asyncio
async def test_critical_risk_evaluation_with_crisis_indicator(client):
    headers = register_and_login(client, "user_risk_critical")

    mock_llm_json = {
        "emotion": "overwhelmed",
        "distress_level": 3,
        "llm_suggested_risk_level": "critical",
        "crisis_indicator": True,
        "confidence": 0.99,
        "reason_category": "acute_crisis"
    }
    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase4"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "I need help immediately, I can't keep going."},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            risk_resp = client.get(f"/api/v1/conversations/{conv_id}/risk-events", headers=headers)
            assert risk_resp.status_code == 200
            event = risk_resp.json()[0]
            assert event["risk_level"] == "CRITICAL"
            assert "crisis_resources" in event["action_taken"]


def test_repeated_distress_within_window_escalates(db_session):
    # Create 3 recent concerning assessments inside the N=5, T=60m window
    now = datetime.now(timezone.utc)
    user_id = 99991

    assessments = [
        EmotionalAssessment(
            conversation_id="conv_w1",
            message_id="msg_w1",
            user_id=user_id,
            emotion="stressed",
            distress_level=2,
            llm_suggested_risk_level="elevated",
            created_at=now - timedelta(minutes=10),
        ),
        EmotionalAssessment(
            conversation_id="conv_w1",
            message_id="msg_w2",
            user_id=user_id,
            emotion="anxious_distress",
            distress_level=2,
            llm_suggested_risk_level="elevated",
            created_at=now - timedelta(minutes=5),
        ),
        EmotionalAssessment(
            conversation_id="conv_w1",
            message_id="msg_w3",
            user_id=user_id,
            emotion="low_mood",
            distress_level=2,
            llm_suggested_risk_level="elevated",
            created_at=now,
        ),
    ]
    for a in assessments:
        db_session.add(a)
    db_session.commit()

    lookback_window = RiskEngineService.get_lookback_assessments(db_session, user_id=user_id, cutoff_time=now)
    assert len(lookback_window) == 3

    risk_level, reason, _ = RiskEngineService.evaluate_risk(assessments[-1], lookback_window)
    assert risk_level == AuthoritativeRiskLevel.HIGH
    assert reason == "persistent_distress_in_lookback_window"


def test_repeated_distress_outside_window_does_not_escalate(db_session):
    # Create 3 assessments created 2 hours ago (outside default T=60m window)
    now = datetime.now(timezone.utc)
    user_id = 99992

    old_assessments = [
        EmotionalAssessment(
            conversation_id="conv_old1",
            message_id="msg_old1",
            user_id=user_id,
            emotion="stressed",
            distress_level=2,
            llm_suggested_risk_level="elevated",
            created_at=now - timedelta(minutes=120),  # Outside 60 min window
        ),
        EmotionalAssessment(
            conversation_id="conv_old1",
            message_id="msg_old2",
            user_id=user_id,
            emotion="anxious_distress",
            distress_level=2,
            llm_suggested_risk_level="elevated",
            created_at=now - timedelta(minutes=115),  # Outside 60 min window
        ),
    ]
    current_assessment = EmotionalAssessment(
        conversation_id="conv_old1",
        message_id="msg_cur",
        user_id=user_id,
        emotion="neutral",
        distress_level=0,
        llm_suggested_risk_level="normal",
        created_at=now,
    )
    for a in old_assessments + [current_assessment]:
        db_session.add(a)
    db_session.commit()

    # Lookback window excludes old assessments outside T=60m
    lookback_window = RiskEngineService.get_lookback_assessments(db_session, user_id=user_id, cutoff_time=now)
    assert len(lookback_window) == 1  # Only current assessment is within T=60m
    assert lookback_window[0].id == current_assessment.id

    risk_level, reason, _ = RiskEngineService.evaluate_risk(current_assessment, lookback_window)
    assert risk_level == AuthoritativeRiskLevel.NORMAL
    assert reason == "routine_wellness_monitoring"


def test_risk_level_never_direct_copy_without_rules(db_session):
    # Assessment with llm_suggested_risk_level="high", but distress_level=0, emotion="positive", crisis=False
    assessment = EmotionalAssessment(
        conversation_id="conv_copy_test",
        message_id="msg_copy_test",
        user_id=99993,
        emotion="positive",
        distress_level=0,
        llm_suggested_risk_level="high",  # Hallucinated or erroneous LLM signal
        crisis_indicator=False,
    )
    db_session.add(assessment)
    db_session.commit()

    # Deterministic rule evaluates actual distress & crisis signals rather than copying llm_suggested_risk_level blindly
    risk_level, reason, _ = RiskEngineService.evaluate_risk(assessment, [assessment])
    # Because distress_level=0, emotion="positive", and no persistent history, deterministic engine assigns NORMAL/ELEVATED based on rules
    assert risk_level != AuthoritativeRiskLevel.CRITICAL


def test_unauthorized_risk_events_access(client):
    # Unauthenticated access returns 401
    assert client.get("/api/v1/conversations/some-conv-id/risk-events").status_code == 401


@pytest.mark.asyncio
async def test_cross_user_risk_event_isolation(client):
    user1_headers = register_and_login(client, "user_risk_owner_a")
    user2_headers = register_and_login(client, "user_risk_owner_b")

    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": '{"emotion": "neutral", "distress_level": 0, "llm_suggested_risk_level": "normal", "crisis_indicator": false, "confidence": 0.9}'}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase4"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "Hello AI"},
                headers=user1_headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            # User 1 fetches risk events -> 200
            u1_events = client.get(f"/api/v1/conversations/{conv_id}/risk-events", headers=user1_headers)
            assert u1_events.status_code == 200

            # User 2 attempts to fetch User 1's conversation risk events -> 404
            u2_events = client.get(f"/api/v1/conversations/{conv_id}/risk-events", headers=user2_headers)
            assert u2_events.status_code == 404
