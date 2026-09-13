"""Deterministic Distress Risk Engine Service (Phase 4).

Converts emotional assessment signals into an authoritative escalation decision.

CRITICAL GOVERNANCE & ARCHITECTURE RULES:
1. LLM IS NOT AUTHORITATIVE: Mistral/LLM suggested risk level is an input signal ONLY.
   It is NEVER copied directly into risk_events.risk_level without passing through deterministic rules.
2. AUTHORITATIVE RISK LEVEL: risk_events.risk_level (NORMAL | ELEVATED | HIGH | CRITICAL) is the ONLY authoritative risk state.
3. MORE RESTRICTIVE LOOKBACK WINDOW:
   Considers the last N assessments (default N=5) OR last T minutes (default T=60m),
   whichever yields the smaller/more restrictive set of assessments.
4. AUDITABLE & EXPLAINABLE: Stores clean reason_category without revealing raw chain-of-thought.
5. NO TRUSTED CONTACT NOTIFICATIONS SENT YET: Default notification_status is "no_trusted_contact_configured" or "pending".
"""
from typing import List, Tuple, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from app.models.emotional_assessment import EmotionalAssessment
from app.models.risk_event import RiskEvent
from app.schemas.risk import AuthoritativeRiskLevel


def _to_utc(dt: datetime) -> datetime:
    """Ensures datetime is timezone-aware UTC for safe comparisons."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class RiskEngineService:
    @classmethod
    def get_lookback_assessments(
        cls, db: Session, user_id: int, cutoff_time: Optional[datetime] = None
    ) -> List[EmotionalAssessment]:
        """Fetches lookback assessments using N (count) and T (minutes) window logic.

        Window rule: Takes the last N assessments OR assessments within the last T minutes,
        whichever produces the smaller (more restrictive) set.
        """
        N = max(1, settings.RISK_ENGINE_LOOKBACK_COUNT)
        T_minutes = max(1, settings.RISK_ENGINE_LOOKBACK_MINUTES)

        now = _to_utc(cutoff_time) if cutoff_time else datetime.now(timezone.utc)
        time_boundary = now - timedelta(minutes=T_minutes)

        # 1. Fetch last N assessments for user ordered by created_at DESC
        n_assessments = (
            db.query(EmotionalAssessment)
            .filter(EmotionalAssessment.user_id == user_id)
            .order_by(EmotionalAssessment.created_at.desc())
            .limit(N)
            .all()
        )

        # 2. Filter to keep only those within time_boundary (T minutes)
        # This intersection guarantees we take the smaller/more restrictive subset
        restricted_window = [a for a in n_assessments if _to_utc(a.created_at) >= time_boundary]
        return restricted_window


    @classmethod
    def evaluate_risk(
        cls,
        current_assessment: Optional[EmotionalAssessment],
        window_assessments: List[EmotionalAssessment],
    ) -> Tuple[AuthoritativeRiskLevel, str, str]:
        """Evaluates deterministic risk rules on current assessment and window history.

        Returns (risk_level, reason_category, action_taken).
        """
        if not current_assessment:
            return (AuthoritativeRiskLevel.NORMAL, "no_assessment_data", "none")

        # Extract current signals
        crisis = bool(current_assessment.crisis_indicator)
        distress = current_assessment.distress_level
        llm_suggested = str(current_assessment.llm_suggested_risk_level).lower()
        emotion = str(current_assessment.emotion).lower()

        # Count concerning history in lookback window (including current)
        moderate_or_above_count = sum(
            1 for a in window_assessments if a.distress_level >= 2 or a.llm_suggested_risk_level in ("elevated", "high", "critical")
        )
        any_distress_count = sum(1 for a in window_assessments if a.distress_level >= 1)

        # RULE 1: CRITICAL
        if crisis or llm_suggested == "critical" or (distress == 3 and crisis):
            return (
                AuthoritativeRiskLevel.CRITICAL,
                "acute_crisis_indicator_detected",
                "crisis_resources_and_emergency_support_provided",
            )

        # RULE 2: HIGH
        if distress == 3 or llm_suggested == "high" or moderate_or_above_count >= 3:
            reason = (
                "persistent_distress_in_lookback_window"
                if moderate_or_above_count >= 3 and distress < 3 and llm_suggested != "high"
                else "severe_distress_signal_detected"
            )
            return (
                AuthoritativeRiskLevel.HIGH,
                reason,
                "supportive_guidance_provided",
            )

        # RULE 3: ELEVATED
        if (
            distress == 2
            or llm_suggested == "elevated"
            or emotion in ("stressed", "anxious_distress", "low_mood", "overwhelmed")
            or any_distress_count >= 2
        ):
            reason = (
                "repeated_mild_distress_in_lookback_window"
                if any_distress_count >= 2 and distress < 2 and llm_suggested != "elevated"
                else "moderate_distress_signal_detected"
            )
            return (
                AuthoritativeRiskLevel.ELEVATED,
                reason,
                "monitored_wellness_support",
            )

        # RULE 4: NORMAL
        return (
            AuthoritativeRiskLevel.NORMAL,
            "routine_wellness_monitoring",
            "none",
        )

    @classmethod
    def evaluate_and_record(
        cls,
        db: Session,
        user: User,
        conversation_id: str,
        assessment: Optional[EmotionalAssessment],
    ) -> RiskEvent:
        """Evaluates deterministic risk rules and records an authoritative RiskEvent in DB."""
        user_id = user.id
        window_assessments = cls.get_lookback_assessments(db, user_id=user_id)

        risk_level, reason_cat, action_taken = cls.evaluate_risk(
            current_assessment=assessment, window_assessments=window_assessments
        )

        assessment_id = assessment.id if assessment else None

        risk_event = RiskEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            assessment_id=assessment_id,
            risk_level=risk_level.value,
            reason_category=reason_cat,
            detected_at=datetime.now(timezone.utc),
            action_taken=action_taken,
            trusted_contact_notified=False,
            notification_status="no_trusted_contact_configured",
        )

        db.add(risk_event)
        db.commit()
        db.refresh(risk_event)

        # Trigger Phase 6 Trusted Contact Notification Evaluation
        try:
            from app.services.notification_service import NotificationService
            NotificationService.evaluate_and_dispatch(db, risk_event)
            db.refresh(risk_event)
        except Exception as exc:
            logger.error(f"[RISK_ENGINE] Error evaluating trusted contact notification for risk_event {risk_event.id}: {exc}")

        return risk_event

    @classmethod
    def get_risk_events_for_conversation(
        cls, db: Session, conversation_id: str, user_id: int
    ) -> List[RiskEvent]:
        """Retrieves all risk events for a conversation with strict ownership verification."""
        from app.models.conversation import Conversation
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if not conv:
            return []

        return (
            db.query(RiskEvent)
            .filter(RiskEvent.conversation_id == conversation_id, RiskEvent.user_id == user_id)
            .order_by(RiskEvent.created_at.asc())
            .all()
        )
