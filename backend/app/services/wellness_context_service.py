"""Multimodal Wellness Context Service (Phase 7).

Combines physiological stress signals (from ESP32 biosensors and ML model)
and conversational distress signals (from the authoritative RiskEngine)
into a unified, non-diagnostic wellness context.

DETERMINISTIC CONFLICT RESOLUTION PRIORITY ORDER (EXPLICIT):
--------------------------------------------------------------------------------
1. PRIORITY 1 — CRISIS LANGUAGE OVERRIDE:
   If risk_events.risk_level is CRITICAL or crisis_indicator is True on the
   underlying assessment, the wellness context is CRITICAL ("critical_concern")
   regardless of physiological stress reading. Chat-derived crisis signals always
   take priority over sensor data, because biosensors cannot detect explicit
   crisis language.

2. PRIORITY 2 — SENSOR HIGH CAPPING:
   If physiological stress is HIGH but chat-derived risk_level is NORMAL (or unassessed),
   the wellness context is capped at "elevated concern" ("elevated_concern") — do not
   escalate to "high concern" or above from sensor data alone without a corroborating
   chat signal.

3. PRIORITY 3 — AGREEMENT & MAX EVALUATION:
   If both signals agree or complement each other (e.g., both "ELEVATED" -> elevated_concern;
   sensor "HIGH" + chat "HIGH" -> high_concern), use the higher / more severe of the two signals.

4. PRIORITY 4 — CODE COMMENT DOCUMENTATION:
   This priority order is explicitly documented directly in code comments per Phase 7 specification.
--------------------------------------------------------------------------------

NEUTRAL NON-DIAGNOSTIC TERMINOLOGY:
- Uses strictly neutral terms: stress_signal, distress_signal, wellness_concern
  ("normal_wellness", "elevated_concern", "high_concern", "critical_concern").
- Never uses clinical labels such as "depression", "anxiety disorder", or "mental illness".
"""
from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.device import Device
from app.models.stress_prediction import StressPrediction
from app.models.risk_event import RiskEvent
from app.models.emotional_assessment import EmotionalAssessment
from app.schemas.wellness_context import MultimodalWellnessResponse


class WellnessContextService:
    @classmethod
    def evaluate_context(
        cls,
        db: Session,
        user: User,
        conversation_id: Optional[str] = None,
    ) -> MultimodalWellnessResponse:
        """Evaluates multimodal wellness context combining sensor and chat signals."""
        user_id = user.id

        # 1. Fetch latest RiskEvent for user (and optional conversation_id)
        risk_query = db.query(RiskEvent).filter(RiskEvent.user_id == user_id)
        if conversation_id:
            risk_query = risk_query.filter(RiskEvent.conversation_id == conversation_id)
        latest_risk_event = risk_query.order_by(desc(RiskEvent.created_at)).first()

        # Extract conversational signals
        conversational_risk = latest_risk_event.risk_level.upper() if latest_risk_event else "NO_DATA"
        
        # Check underlying assessment for crisis_indicator
        crisis_indicator = False
        if latest_risk_event and latest_risk_event.assessment_id:
            assessment = db.query(EmotionalAssessment).filter(EmotionalAssessment.id == latest_risk_event.assessment_id).first()
            if assessment and assessment.crisis_indicator:
                crisis_indicator = True

        # 2. Fetch user's registered device & latest StressPrediction
        device = db.query(Device).filter(Device.user_id == user_id).first()
        device_id = device.device_id if device else None

        latest_stress_pred = None
        if device_id:
            latest_stress_pred = (
                db.query(StressPrediction)
                .filter(StressPrediction.device_id == device_id)
                .order_by(desc(StressPrediction.timestamp))
                .first()
            )

        physiological_stress_level = (
            latest_stress_pred.stress_level.upper() if latest_stress_pred and latest_stress_pred.stress_level else None
        )
        physiological_stress_score = (
            latest_stress_pred.stress_score if latest_stress_pred else None
        )

        # 3. Apply Deterministic Conflict Resolution Priority Rules
        concern_level, rule_applied, explanation = cls.resolve_multimodal_priority(
            conversational_risk=conversational_risk,
            crisis_indicator=crisis_indicator,
            physiological_stress_level=physiological_stress_level,
            physiological_stress_score=physiological_stress_score,
        )

        return MultimodalWellnessResponse(
            user_id=user_id,
            conversation_id=conversation_id,
            device_id=device_id,
            physiological_stress_level=physiological_stress_level,
            physiological_stress_score=physiological_stress_score,
            conversational_risk_level=conversational_risk if conversational_risk != "NO_DATA" else None,
            crisis_indicator=crisis_indicator,
            wellness_concern_level=concern_level,
            rule_applied=rule_applied,
            explanation=explanation,
            evaluated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def resolve_multimodal_priority(
        cls,
        conversational_risk: str,
        crisis_indicator: bool,
        physiological_stress_level: Optional[str],
        physiological_stress_score: Optional[float],
    ) -> Tuple[str, str, str]:
        """Core deterministic priority evaluation algorithm.

        DETERMINISTIC CONFLICT RESOLUTION PRIORITY ORDER:
        --------------------------------------------------------------------------------
        1. PRIORITY 1 — CRISIS LANGUAGE OVERRIDE:
           If risk_events.risk_level is CRITICAL or crisis_indicator is True on the
           underlying assessment, the wellness context is CRITICAL ("critical_concern")
           regardless of physiological stress reading. Chat-derived crisis signals always
           take priority over sensor data, because biosensors cannot detect explicit
           crisis language.

        2. PRIORITY 2 — SENSOR HIGH CAPPING:
           If physiological stress is HIGH but chat-derived risk_level is NORMAL (or unassessed),
           the wellness context is capped at "elevated concern" ("elevated_concern") — do not
           escalate to "high concern" or above from sensor data alone without a corroborating
           chat signal.

        3. PRIORITY 3 — AGREEMENT & MAX EVALUATION:
           If both signals agree or complement each other (e.g., both "ELEVATED" -> elevated_concern;
           sensor "HIGH" + chat "HIGH" -> high_concern), use the higher / more severe of the two signals.

        4. PRIORITY 4 — CODE COMMENT DOCUMENTATION:
           This priority order is explicitly documented directly in code comments per Phase 7 specification.
        --------------------------------------------------------------------------------
        """
        conv_risk = str(conversational_risk).upper() if conversational_risk else "NO_DATA"
        sensor_level = str(physiological_stress_level).upper() if physiological_stress_level else "NO_DATA"

        # ------------------------------------------------------------------------------
        # RULE 1: CRISIS LANGUAGE OVERRIDE
        # If chat risk is CRITICAL or crisis_indicator is True -> CRITICAL concern regardless of sensor data.
        # ------------------------------------------------------------------------------
        if conv_risk == "CRITICAL" or crisis_indicator:
            return (
                "critical_concern",
                "CRISIS_LANGUAGE_OVERRIDE",
                "Critical distress or crisis language detected in chat assessment. Explicit crisis signals take absolute precedence over sensor data.",
            )

        # ------------------------------------------------------------------------------
        # RULE 2: SENSOR HIGH CAPPING
        # If sensor stress is HIGH but chat risk is NORMAL (or NO_DATA/unassessed) -> Capped at elevated_concern.
        # Sensor data alone cannot escalate a user to high_concern without corroborating chat distress.
        # ------------------------------------------------------------------------------
        is_sensor_high = sensor_level in ("HIGH", "STRESS") or (
            physiological_stress_score is not None and physiological_stress_score >= 70.0
        )
        if is_sensor_high and conv_risk in ("NORMAL", "NO_DATA"):
            return (
                "elevated_concern",
                "SENSOR_HIGH_CAPPED_AT_ELEVATED",
                "High physiological stress detected by biosensors without corroborating conversational distress. Capped at elevated concern to prevent false escalation.",
            )

        # ------------------------------------------------------------------------------
        # RULE 3: AGREEMENT & MAX EVALUATION
        # Map both signals to ordinal severity (0=NO_DATA/NORMAL, 1=MODERATE/ELEVATED, 2=HIGH, 3=CRITICAL)
        # ------------------------------------------------------------------------------
        conv_severity_map = {
            "NO_DATA": 0,
            "NORMAL": 0,
            "ELEVATED": 1,
            "HIGH": 2,
            "CRITICAL": 3,
        }
        sensor_severity_map = {
            "NO_DATA": 0,
            "BASELINE": 0,
            "LOW": 0,
            "MODERATE": 1,
            "HIGH": 2,
            "STRESS": 2,
        }

        conv_sev = conv_severity_map.get(conv_risk, 0)
        sensor_sev = sensor_severity_map.get(sensor_level, 0)
        max_sev = max(conv_sev, sensor_sev)

        if max_sev >= 2:
            return (
                "high_concern",
                "BOTH_SIGNALS_AGREE",
                "Corroborated high distress or high stress signals detected across multimodal modalities.",
            )
        elif max_sev == 1:
            return (
                "elevated_concern",
                "BOTH_SIGNALS_AGREE",
                "Elevated concern level indicated by moderate physiological stress or elevated conversational signal.",
            )
        else:
            return (
                "normal_wellness",
                "ROUTINE_MONITORING",
                "All multimodal signals remain within baseline wellness parameters.",
            )
