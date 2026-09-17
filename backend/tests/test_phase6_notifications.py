"""Tests for Phase 6 — Trusted Contact Notification Service.

Tests cover:
- Eligible CRITICAL event notification dispatch (status = 'sent', trusted_contact_notified = True)
- Eligible HIGH event notification dispatch (with high_and_critical preference)
- Consent restriction (consent_given = False -> skipped_no_consent)
- Disabled contact restriction (enabled = False -> skipped_disabled)
- Notification level mismatch (critical_only contact receiving HIGH event -> skipped_preference_mismatch)
- Elevated and Normal risk events NEVER trigger notifications under any setting (skipped_low_risk)
- Idempotency enforcement (duplicate risk event notification attempt skipped)
- Provider failure handling (captures error_category and records status = 'failed')
- Provider timeout handling (captures NETWORK_TIMEOUT and records status = 'failed')
- Privacy safeguard (verifies message body contains NO conversation text or vitals)
- Cross-user isolation (User A's event does not notify User B's contact)
- Zero external HTTP calls during automated testing (mocked provider calls)
"""
import pytest
from unittest.mock import MagicMock, patch
from app.core.security import create_access_token
from app.models.user import User
from app.models.conversation import Conversation
from app.models.trusted_contact import TrustedContact
from app.models.risk_event import RiskEvent
from app.models.notification_event import NotificationEvent
from app.services.notification_service import NotificationService
from app.services.notification_provider import (
    BaseNotificationProvider,
    NotificationDeliveryError,
    ConsoleNotificationProvider,
    TwilioNotificationProvider,
)
from app.services.risk_engine import RiskEngineService


def create_test_user_with_contact(
    db_session,
    email="notif_user@example.com",
    name="Notification User",
    phone="+919876543210",
    consent_given=True,
    enabled=True,
    notification_level="high_and_critical",
):
    user = User(
        email=email,
        hashed_password="hashed_secret_password",
        full_name=name,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    contact = TrustedContact(
        user_id=user.id,
        name="Emergency Contact",
        phone_number=phone,
        relationship="Parent",
        consent_given=consent_given,
        enabled=enabled,
        notification_level=notification_level,
    )
    db_session.add(contact)

    conv = Conversation(user_id=user.id, title="Test Conversation")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(contact)
    db_session.refresh(conv)

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, contact, conv, headers


def test_eligible_critical_event_notification_sent(db_session):
    """Eligible CRITICAL risk event dispatches alert successfully."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "critical_user@example.com", notification_level="critical_only"
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="CRITICAL",
        reason_category="acute_crisis_indicator_detected",
        action_taken="crisis_resources_provided",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    # Dispatch using Mock Provider
    mock_provider = MagicMock(spec=BaseNotificationProvider)
    mock_provider.send_notification.return_value = {
        "delivered": True,
        "provider_message_id": "msg-12345",
        "details": {},
    }

    notif_event = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )

    assert notif_event.status == "sent"
    assert notif_event.risk_level == "CRITICAL"
    assert notif_event.recipient_phone == "+919876543210"
    assert risk_event.trusted_contact_notified is True
    assert risk_event.notification_status == "sent"
    mock_provider.send_notification.assert_called_once()


def test_eligible_high_event_notification_sent(db_session):
    """Eligible HIGH risk event dispatches alert when user preference allows high_and_critical."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "high_user@example.com", notification_level="high_and_critical"
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="HIGH",
        reason_category="severe_distress_signal_detected",
        action_taken="supportive_guidance_provided",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    mock_provider.send_notification.return_value = {
        "delivered": True,
        "provider_message_id": "msg-67890",
        "details": {},
    }

    notif_event = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )

    assert notif_event.status == "sent"
    assert notif_event.risk_level == "HIGH"
    assert risk_event.trusted_contact_notified is True
    assert risk_event.notification_status == "sent"


def test_critical_only_preference_blocks_high_event(db_session):
    """HIGH risk event is skipped if contact preference is critical_only."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "crit_only_user@example.com", notification_level="critical_only"
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="HIGH",
        reason_category="severe_distress_signal_detected",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    mock_provider = MagicMock(spec=BaseNotificationProvider)

    notif_event = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )

    assert notif_event.status == "skipped_preference_mismatch"
    assert notif_event.error_category == "PREFERENCE_MISMATCH"
    assert risk_event.trusted_contact_notified is False
    assert risk_event.notification_status == "skipped_preference_mismatch"
    mock_provider.send_notification.assert_not_called()


def test_elevated_and_normal_risk_never_trigger_notification(db_session):
    """ELEVATED and NORMAL risk levels are NEVER notification-eligible under any setting."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "low_risk_user@example.com", consent_given=True, enabled=True, notification_level="high_and_critical"
    )

    # Test ELEVATED
    risk_elevated = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="ELEVATED",
        reason_category="moderate_distress_signal_detected",
    )
    db_session.add(risk_elevated)
    db_session.commit()
    db_session.refresh(risk_elevated)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    notif_elevated = NotificationService.evaluate_and_dispatch(
        db_session, risk_elevated, provider_override=mock_provider
    )

    assert notif_elevated.status == "skipped_low_risk"
    assert risk_elevated.trusted_contact_notified is False
    assert risk_elevated.notification_status == "skipped_low_risk"

    # Test NORMAL
    risk_normal = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="NORMAL",
        reason_category="routine_wellness_monitoring",
    )
    db_session.add(risk_normal)
    db_session.commit()
    db_session.refresh(risk_normal)

    notif_normal = NotificationService.evaluate_and_dispatch(
        db_session, risk_normal, provider_override=mock_provider
    )

    assert notif_normal.status == "skipped_low_risk"
    assert risk_normal.trusted_contact_notified is False
    assert risk_normal.notification_status == "skipped_low_risk"

    mock_provider.send_notification.assert_not_called()


def test_no_consent_blocks_notification(db_session):
    """Notification is skipped if contact exists but consent_given is False."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "noconsent_notif@example.com", consent_given=False
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="CRITICAL",
        reason_category="acute_crisis_indicator_detected",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    notif_event = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )

    assert notif_event.status == "skipped_no_consent"
    assert notif_event.error_category == "NO_EXPLICIT_CONSENT"
    assert risk_event.trusted_contact_notified is False
    assert risk_event.notification_status == "skipped_no_consent"
    mock_provider.send_notification.assert_not_called()


def test_disabled_contact_blocks_notification(db_session):
    """Notification is skipped if contact enabled toggle is False."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "disabled_notif@example.com", enabled=False
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="CRITICAL",
        reason_category="acute_crisis_indicator_detected",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    notif_event = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )

    assert notif_event.status == "skipped_disabled"
    assert notif_event.error_category == "CONTACT_DISABLED"
    assert risk_event.trusted_contact_notified is False
    assert risk_event.notification_status == "skipped_disabled"
    mock_provider.send_notification.assert_not_called()


def test_idempotency_prevents_duplicate_notification(db_session):
    """Idempotency check prevents duplicate notifications for the same risk_event_id."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "idempotent_user@example.com"
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="CRITICAL",
        reason_category="acute_crisis_indicator_detected",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    mock_provider.send_notification.return_value = {
        "delivered": True,
        "provider_message_id": "msg-first",
    }

    # First attempt -> Sent
    first_notif = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )
    assert first_notif.status == "sent"
    assert mock_provider.send_notification.call_count == 1

    # Second attempt -> Idempotent skip
    second_notif = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )
    assert second_notif.id == first_notif.id
    assert mock_provider.send_notification.call_count == 1  # Not called again


def test_provider_failure_handled_gracefully(db_session):
    """Provider error raises NotificationDeliveryError and records status = failed."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "fail_user@example.com"
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="CRITICAL",
        reason_category="acute_crisis_indicator_detected",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    mock_provider.send_notification.side_effect = NotificationDeliveryError(
        "Twilio authentication failed", category="PROVIDER_AUTHENTICATION_ERROR", status_code=401
    )

    notif_event = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )

    assert notif_event.status == "failed"
    assert notif_event.error_category == "PROVIDER_AUTHENTICATION_ERROR"
    assert risk_event.trusted_contact_notified is False
    assert risk_event.notification_status == "failed"


def test_provider_timeout_handled_gracefully(db_session):
    """Provider network timeout records NETWORK_TIMEOUT error category."""
    user, contact, conv, _ = create_test_user_with_contact(
        db_session, "timeout_user@example.com"
    )

    risk_event = RiskEvent(
        user_id=user.id,
        conversation_id=conv.id,
        risk_level="CRITICAL",
        reason_category="acute_crisis_indicator_detected",
    )
    db_session.add(risk_event)
    db_session.commit()
    db_session.refresh(risk_event)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    mock_provider.send_notification.side_effect = NotificationDeliveryError(
        "Network request timed out after 10s", category="NETWORK_TIMEOUT"
    )

    notif_event = NotificationService.evaluate_and_dispatch(
        db_session, risk_event, provider_override=mock_provider
    )

    assert notif_event.status == "failed"
    assert notif_event.error_category == "NETWORK_TIMEOUT"
    assert risk_event.trusted_contact_notified is False


def test_privacy_safeguard_message_format():
    """Verify message contains ONLY minimal necessary text, no chat transcript or vitals."""
    msg_critical = NotificationService.format_notification_message("Rahul Sharma", "CRITICAL")
    assert "Rahul Sharma" in msg_critical
    assert "Sanjeevni Emergency Alert" in msg_critical
    assert "does not diagnose mental health conditions" in msg_critical
    # Strict checks for data leakage
    assert "heart_rate" not in msg_critical
    assert "transcript" not in msg_critical
    assert "bearer" not in msg_critical
    assert "http" not in msg_critical

    msg_high = NotificationService.format_notification_message("Priya", "HIGH")
    assert "Priya" in msg_high
    assert "high distress" in msg_high
    assert "make sure they are safe" in msg_high


def test_cross_user_isolation(db_session):
    """User A's risk event evaluates strictly User A's trusted contact."""
    user_a, contact_a, conv_a, _ = create_test_user_with_contact(
        db_session, "usera_notif@example.com", name="User A", phone="+11111111111"
    )
    user_b, contact_b, conv_b, _ = create_test_user_with_contact(
        db_session, "userb_notif@example.com", name="User B", phone="+22222222222"
    )

    risk_event_a = RiskEvent(
        user_id=user_a.id,
        conversation_id=conv_a.id,
        risk_level="CRITICAL",
        reason_category="acute_crisis_indicator_detected",
    )
    db_session.add(risk_event_a)
    db_session.commit()
    db_session.refresh(risk_event_a)

    mock_provider = MagicMock(spec=BaseNotificationProvider)
    mock_provider.send_notification.return_value = {"delivered": True, "provider_message_id": "msg-a"}

    notif_event_a = NotificationService.evaluate_and_dispatch(
        db_session, risk_event_a, provider_override=mock_provider
    )

    assert notif_event_a.user_id == user_a.id
    assert notif_event_a.recipient_phone == "+11111111111"
    assert notif_event_a.recipient_phone != contact_b.phone_number


def test_twilio_provider_missing_credentials(monkeypatch):
    """TwilioNotificationProvider raises PROVIDER_UNCONFIGURED when credentials are missing."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", None)
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", None)
    monkeypatch.setattr(settings, "TWILIO_FROM_PHONE", None)
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", None)

    with pytest.raises(NotificationDeliveryError) as exc_info:
        TwilioNotificationProvider(mode="sms")

    assert exc_info.value.category == "PROVIDER_UNCONFIGURED"


def test_twilio_provider_success_sdk(monkeypatch):
    """TwilioNotificationProvider dispatches successfully via Twilio Python SDK."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "ACtest123456789")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "authtoken123456")
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "+15005550006")

    mock_msg = MagicMock()
    mock_msg.sid = "SM1234567890abcdef"
    mock_msg.status = "queued"
    mock_msg.price = "0.0075"
    mock_msg.date_created = "2026-09-14 02:30:00"

    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.return_value = mock_msg

    with patch("twilio.rest.Client", return_value=mock_client_instance):
        provider = TwilioNotificationProvider(mode="sms")
        result = provider.send_notification("+919876543210", "Sanjeevni Alert: Test message")

    assert result["delivered"] is True
    assert result["provider_message_id"] == "SM1234567890abcdef"
    mock_client_instance.messages.create.assert_called_once_with(
        body="Sanjeevni Alert: Test message",
        from_="+15005550006",
        to="+919876543210",
    )


def test_twilio_provider_failure_redacts_auth_token(monkeypatch):
    """TwilioNotificationProvider redacts TWILIO_AUTH_TOKEN from error messages."""
    from app.core.config import settings
    secret_token = "SUPER_SECRET_TWILIO_AUTH_TOKEN_999"
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "ACtest123456789")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", secret_token)
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "+15005550006")

    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.side_effect = Exception(
        f"Twilio API request failed with auth token {secret_token}"
    )

    with patch("twilio.rest.Client", return_value=mock_client_instance):
        provider = TwilioNotificationProvider(mode="sms")
        with pytest.raises(NotificationDeliveryError) as exc_info:
            provider.send_notification("+919876543210", "Test message")

    err_msg = str(exc_info.value)
    assert secret_token not in err_msg
    assert "[REDACTED]" in err_msg


def test_twilio_provider_timeout_category(monkeypatch):
    """TwilioNotificationProvider returns NETWORK_TIMEOUT on request timeout."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "ACtest123456789")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "authtoken123456")
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "+15005550006")

    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.side_effect = TimeoutError("Twilio request timeout")

    with patch("twilio.rest.Client", return_value=mock_client_instance):
        provider = TwilioNotificationProvider(mode="sms")
        with pytest.raises(NotificationDeliveryError) as exc_info:
            provider.send_notification("+919876543210", "Test message")

    assert exc_info.value.category == "NETWORK_TIMEOUT"

