"""Notification Engine Service (Phase 6).

Evaluates eligibility rules, formats privacy-safe messages, dispatches notifications,
enforces idempotency, and records full audit logs in notification_events.

STRICT NOTIFICATION RULES:
1. AUTHORITATIVE RISK LEVEL: risk_events.risk_level MUST be "HIGH" or "CRITICAL".
   "NORMAL" and "ELEVATED" risk levels are NEVER notification-eligible under any configuration.
2. CONSENT REQUIRED: trusted_contacts.consent_given MUST be True.
3. ENABLED REQUIRED: trusted_contacts.enabled MUST be True.
4. PREFERENCE ALIGNMENT:
   - "high_and_critical" accepts HIGH and CRITICAL.
   - "critical_only" accepts CRITICAL only.
5. IDEMPOTENCY: Exactly one notification attempt per risk event ID.
6. PRIVACY GUARANTEE: Never include chat transcripts, conversation history, sensor data, or diagnostic claims.
"""
from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.user import User
from app.models.risk_event import RiskEvent
from app.models.trusted_contact import TrustedContact
from app.models.notification_event import NotificationEvent
from app.services.notification_provider import (
    get_notification_provider,
    NotificationDeliveryError,
    BaseNotificationProvider,
)


class NotificationService:
    @classmethod
    def format_notification_message(cls, user_name: Optional[str], risk_level: str) -> str:
        """Formats minimum necessary privacy-safe alert message."""
        display_name = user_name if user_name else "your contact"
        level_upper = str(risk_level).upper()

        if level_upper == "CRITICAL":
            return (
                f"Sanjeevni Emergency Alert: Sanjeevni detected critical distress risk in recent interactions. "
                f"Please check in with {display_name} immediately or reach out to local emergency services if needed. "
                f"(Sanjeevni does not diagnose mental health conditions)."
            )
        else:
            # HIGH
            return (
                f"Sanjeevni Alert: Sanjeevni detected high distress in {display_name}'s recent interaction. "
                f"Please check in with them and make sure they are safe."
            )

    @classmethod
    def evaluate_and_dispatch(
        cls,
        db: Session,
        risk_event: RiskEvent,
        provider_override: Optional[BaseNotificationProvider] = None,
    ) -> NotificationEvent:
        """Evaluates eligibility, enforces idempotency, dispatches alert, and updates database audit logs."""
        user_id = risk_event.user_id
        risk_level = str(risk_event.risk_level).upper()

        # 1. Idempotency Check — Check if a NotificationEvent already exists for this risk_event_id
        existing_event = (
            db.query(NotificationEvent)
            .filter(NotificationEvent.risk_event_id == risk_event.id)
            .first()
        )
        if existing_event:
            logger.info(f"[NOTIFICATION] Idempotency triggered: risk_event {risk_event.id} already processed.")
            return existing_event

        # 2. Rule: NORMAL and ELEVATED are NEVER notification-eligible
        if risk_level not in ("HIGH", "CRITICAL"):
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=None,
                recipient_phone=None,
                provider="none",
                status="skipped_low_risk",
                notification_level=None,
                risk_level=risk_level,
                attempt_count=0,
                attempted_at=datetime.now(timezone.utc),
                error_category="EXCLUSION_POLICY",
                error_message=f"Risk level '{risk_level}' is not notification-eligible. Only HIGH and CRITICAL can trigger alerts.",
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = False
            risk_event.notification_status = "skipped_low_risk"
            db.commit()
            db.refresh(notification_event)
            return notification_event

        # 3. Fetch User's TrustedContact
        trusted_contact = (
            db.query(TrustedContact)
            .filter(TrustedContact.user_id == user_id)
            .first()
        )

        # 4. Rule: Trusted Contact Must Exist
        if not trusted_contact:
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=None,
                recipient_phone=None,
                provider="none",
                status="skipped_no_contact",
                notification_level=None,
                risk_level=risk_level,
                attempt_count=0,
                attempted_at=datetime.now(timezone.utc),
                error_category="NO_TRUSTED_CONTACT",
                error_message="No trusted contact configured for this user.",
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = False
            risk_event.notification_status = "skipped_no_contact"
            db.commit()
            db.refresh(notification_event)
            return notification_event

        # 5. Rule: Explicit Consent Required
        if not trusted_contact.consent_given:
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=trusted_contact.id,
                recipient_phone=trusted_contact.phone_number,
                provider="none",
                status="skipped_no_consent",
                notification_level=trusted_contact.notification_level,
                risk_level=risk_level,
                attempt_count=0,
                attempted_at=datetime.now(timezone.utc),
                error_category="NO_EXPLICIT_CONSENT",
                error_message="User has not given explicit consent for trusted contact notifications.",
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = False
            risk_event.notification_status = "skipped_no_consent"
            db.commit()
            db.refresh(notification_event)
            return notification_event

        # 6. Rule: Enabled Contact Required
        if not trusted_contact.enabled:
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=trusted_contact.id,
                recipient_phone=trusted_contact.phone_number,
                provider="none",
                status="skipped_disabled",
                notification_level=trusted_contact.notification_level,
                risk_level=risk_level,
                attempt_count=0,
                attempted_at=datetime.now(timezone.utc),
                error_category="CONTACT_DISABLED",
                error_message="Trusted contact notification toggle is currently disabled by user.",
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = False
            risk_event.notification_status = "skipped_disabled"
            db.commit()
            db.refresh(notification_event)
            return notification_event

        # 7. Rule: Preference Alignment
        # high_and_critical -> HIGH or CRITICAL
        # critical_only -> CRITICAL only
        contact_pref = str(trusted_contact.notification_level).lower()
        if contact_pref == "critical_only" and risk_level == "HIGH":
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=trusted_contact.id,
                recipient_phone=trusted_contact.phone_number,
                provider="none",
                status="skipped_preference_mismatch",
                notification_level=trusted_contact.notification_level,
                risk_level=risk_level,
                attempt_count=0,
                attempted_at=datetime.now(timezone.utc),
                error_category="PREFERENCE_MISMATCH",
                error_message="Contact configured for critical_only alerts; current event risk is HIGH.",
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = False
            risk_event.notification_status = "skipped_preference_mismatch"
            db.commit()
            db.refresh(notification_event)
            return notification_event

        # 8. All Eligibility Checks Passed — Dispatch Notification
        user = db.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user else None
        message_body = cls.format_notification_message(user_name, risk_level)

        provider = provider_override or get_notification_provider()
        provider_name = provider.__class__.__name__.replace("NotificationProvider", "").lower()

        try:
            result = provider.send_notification(
                recipient_phone=trusted_contact.phone_number,
                message_body=message_body,
                metadata={
                    "risk_event_id": risk_event.id,
                    "risk_level": risk_level,
                    "notification_level": trusted_contact.notification_level,
                },
            )
            
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=trusted_contact.id,
                recipient_phone=trusted_contact.phone_number,
                provider=provider_name,
                status="sent",
                notification_level=trusted_contact.notification_level,
                risk_level=risk_level,
                attempt_count=1,
                attempted_at=datetime.now(timezone.utc),
                delivered_at=datetime.now(timezone.utc),
                error_category=None,
                error_message=None,
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = True
            risk_event.notification_status = "sent"
            db.commit()
            db.refresh(notification_event)
            logger.info(f"[NOTIFICATION] Successfully sent {risk_level} alert for user {user_id} via {provider_name}.")
            return notification_event

        except NotificationDeliveryError as exc:
            logger.error(f"[NOTIFICATION] Delivery failure for user {user_id}: {exc}")
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=trusted_contact.id,
                recipient_phone=trusted_contact.phone_number,
                provider=provider_name,
                status="failed",
                notification_level=trusted_contact.notification_level,
                risk_level=risk_level,
                attempt_count=1,
                attempted_at=datetime.now(timezone.utc),
                delivered_at=None,
                error_category=exc.category,
                error_message=str(exc),
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = False
            risk_event.notification_status = "failed"
            db.commit()
            db.refresh(notification_event)
            return notification_event
        except Exception as exc:
            logger.exception(f"[NOTIFICATION] Unexpected exception dispatching notification for user {user_id}: {exc}")
            notification_event = NotificationEvent(
                risk_event_id=risk_event.id,
                user_id=user_id,
                trusted_contact_id=trusted_contact.id,
                recipient_phone=trusted_contact.phone_number,
                provider=provider_name,
                status="failed",
                notification_level=trusted_contact.notification_level,
                risk_level=risk_level,
                attempt_count=1,
                attempted_at=datetime.now(timezone.utc),
                delivered_at=None,
                error_category="UNEXPECTED_SYSTEM_ERROR",
                error_message=str(exc),
            )
            db.add(notification_event)
            risk_event.trusted_contact_notified = False
            risk_event.notification_status = "failed"
            db.commit()
            db.refresh(notification_event)
            return notification_event
