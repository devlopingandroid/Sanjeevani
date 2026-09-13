"""Tests for Phase 7 — Multimodal Wellness Context.

Tests cover:
- Rule 1: Critical chat / crisis indicator overrides sensor data -> critical_concern
- Rule 2: High sensor stress + normal/no chat -> capped at elevated_concern (cannot escalate to high_concern from sensor alone)
- Rule 3: Agreement & Max evaluation (High sensor + High chat -> high_concern)
- Sensor only evaluation (capped at elevated_concern)
- Chat only evaluation (high_concern)
- Missing sensor data handling (returns NO_DATA safely without fake values)
- Missing chat assessment handling (returns NO_DATA safely)
- Crisis indicator override (crisis_indicator=True -> critical_concern)
- No fake data policy verification
- API route authentication & response format
"""
import pytest
from datetime import datetime, timezone
from app.core.security import create_access_token
from app.models.user import User
from app.models.device import Device, DeviceStatus
from app.models.stress_prediction import StressPrediction
from app.models.conversation import Conversation
from app.models.emotional_assessment import EmotionalAssessment
from app.models.risk_event import RiskEvent
from app.services.wellness_context_service import WellnessContextService


def create_wellness_test_user(db_session, email="wellness_user@example.com", name="Wellness User"):
    user = User(
        email=email,
        hashed_password="hashed_secret_password",
        full_name=name,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def test_rule_1_conflicting_critical_chat_normal_sensor(db_session):
    """Rule 1: Critical chat or crisis indicator overrides sensor reading -> critical_concern."""
    # Chat says CRITICAL, Sensor says LOW / NORMAL
    wellness = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="CRITICAL",
        crisis_indicator=False,
        physiological_stress_level="LOW",
        physiological_stress_score=15.0,
    )
    assert wellness[0] == "critical_concern"
    assert wellness[1] == "CRISIS_LANGUAGE_OVERRIDE"

    # Crisis indicator True, Sensor says LOW / NORMAL
    wellness_crisis = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="NORMAL",
        crisis_indicator=True,
        physiological_stress_level="LOW",
        physiological_stress_score=10.0,
    )
    assert wellness_crisis[0] == "critical_concern"
    assert wellness_crisis[1] == "CRISIS_LANGUAGE_OVERRIDE"


def test_rule_2_conflicting_high_sensor_normal_chat_capped(db_session):
    """Rule 2: High sensor stress + normal chat -> capped at elevated_concern."""
    wellness = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="NORMAL",
        crisis_indicator=False,
        physiological_stress_level="HIGH",
        physiological_stress_score=85.0,
    )
    assert wellness[0] == "elevated_concern"
    assert wellness[1] == "SENSOR_HIGH_CAPPED_AT_ELEVATED"


def test_rule_3_both_signals_agree(db_session):
    """Rule 3: Both signals high -> high_concern."""
    wellness = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="HIGH",
        crisis_indicator=False,
        physiological_stress_level="HIGH",
        physiological_stress_score=80.0,
    )
    assert wellness[0] == "high_concern"
    assert wellness[1] == "BOTH_SIGNALS_AGREE"


def test_sensor_only(db_session):
    """Sensor only (high stress) -> capped at elevated_concern without chat corroboration."""
    wellness = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="NO_DATA",
        crisis_indicator=False,
        physiological_stress_level="HIGH",
        physiological_stress_score=90.0,
    )
    assert wellness[0] == "elevated_concern"
    assert wellness[1] == "SENSOR_HIGH_CAPPED_AT_ELEVATED"


def test_chat_only(db_session):
    """Chat only (high risk) -> high_concern."""
    wellness = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="HIGH",
        crisis_indicator=False,
        physiological_stress_level=None,
        physiological_stress_score=None,
    )
    assert wellness[0] == "high_concern"
    assert wellness[1] == "BOTH_SIGNALS_AGREE"


def test_missing_sensor_data(db_session):
    """Missing sensor data returns normal_wellness when chat is normal."""
    wellness = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="NORMAL",
        crisis_indicator=False,
        physiological_stress_level=None,
        physiological_stress_score=None,
    )
    assert wellness[0] == "normal_wellness"
    assert wellness[1] == "ROUTINE_MONITORING"


def test_missing_chat_assessment(db_session):
    """Missing chat assessment returns normal_wellness when sensor is low."""
    wellness = WellnessContextService.resolve_multimodal_priority(
        conversational_risk="NO_DATA",
        crisis_indicator=False,
        physiological_stress_level="LOW",
        physiological_stress_score=20.0,
    )
    assert wellness[0] == "normal_wellness"
    assert wellness[1] == "ROUTINE_MONITORING"


def test_no_fake_data_policy(db_session):
    """Service gracefully handles unmonitored users without fabricating fake readings."""
    user, _ = create_wellness_test_user(db_session, "nofake@example.com")
    
    context = WellnessContextService.evaluate_context(db_session, user)
    assert context.user_id == user.id
    assert context.physiological_stress_level is None
    assert context.physiological_stress_score is None
    assert context.conversational_risk_level is None
    assert context.crisis_indicator is False
    assert context.wellness_concern_level == "normal_wellness"


def test_api_wellness_context_endpoint_integration(client, db_session):
    """API endpoint returns valid MultimodalWellnessResponse for authenticated user."""
    user, headers = create_wellness_test_user(db_session, "apiwellness@example.com")

    # Add Device and StressPrediction
    device = Device(device_id="DEV_WELLNESS_001", name="Sanjeevni Band", user_id=user.id, status=DeviceStatus.CONNECTED)
    db_session.add(device)
    db_session.commit()

    prediction = StressPrediction(
        device_id="DEV_WELLNESS_001",
        timestamp=datetime.now(timezone.utc),
        stress_level="HIGH",
        stress_score=88.5,
        confidence=0.9,
    )
    db_session.add(prediction)

    # Add Conversation and RiskEvent (NORMAL)
    conv = Conversation(user_id=user.id, title="Wellness Chat")
    db_session.add(conv)
    db_session.commit()

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="NORMAL",
        reason_category="routine_wellness_monitoring",
    )
    db_session.add(risk_event)
    db_session.commit()

    # Call API
    response = client.get("/api/v1/wellness-context", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["device_id"] == "DEV_WELLNESS_001"
    assert data["physiological_stress_level"] == "HIGH"
    assert data["conversational_risk_level"] == "NORMAL"
    # Rule 2: High sensor + normal chat -> capped at elevated_concern
    assert data["wellness_concern_level"] == "elevated_concern"
    assert data["rule_applied"] == "SENSOR_HIGH_CAPPED_AT_ELEVATED"


def test_api_unauthorized_access(client):
    """Unauthenticated GET requests must be rejected with 401."""
    response = client.get("/api/v1/wellness-context")
    assert response.status_code == 401
