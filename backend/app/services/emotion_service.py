"""Emotion and Distress Analysis Service (Phase 3).

Analyzes user chat messages to extract conversational emotion and distress signals.

CRITICAL SAFETY & GOVERNANCE RULES:
1. NOT A CLINICAL DIAGNOSIS SYSTEM: System prompt explicitly prohibits diagnosing depression or disorders.
2. NON-AUTHORITATIVE RISK LEVEL: llm_suggested_risk_level is an LLM suggestion ONLY. It is NOT authoritative and MUST NOT be shown to users or used directly for escalation decisions.
3. ROBUST FALLBACKS: Any JSON parsing error, invalid enum, or Mistral API failure safely falls back to default unknown/normal assessment states.
4. ZERO CODE EXECUTION / ZERO DIRECT NOTIFICATIONS: No arbitrary execution, eval(), or direct trigger side-effects.
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import json
import re
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.emotional_assessment import EmotionalAssessment
from app.models.conversation import ChatMessage, Conversation
from app.schemas.emotion import (
    EmotionType,
    DistressLevel,
    LLMSuggestedRiskLevel,
    EmotionAnalysisLLMOutput,
    EmotionalAssessmentResponse,
)


EMOTION_ANALYSIS_SYSTEM_PROMPT = """You are an expert NLP emotion and distress analysis classifier for a health & wellness app.
Analyze the user's message and estimate their conversational emotional state and distress level.

CRITICAL SAFETY DIRECTIVE:
- This is NOT a depression or psychiatric diagnosis system.
- Do NOT output clinical diagnoses or medical labels.
- Output ONLY a single raw valid JSON object with NO surrounding markdown text or explanations.

JSON SCHEMA REQUIREMENT:
{
  "emotion": "neutral" | "stressed" | "anxious_distress" | "low_mood" | "positive" | "overwhelmed" | "unknown",
  "distress_level": 0 | 1 | 2 | 3,
  "llm_suggested_risk_level": "normal" | "elevated" | "high" | "critical",
  "crisis_indicator": true | false,
  "confidence": 0.0 to 1.0,
  "reason_category": "string or null"
}

FIELD GUIDELINES:
1. emotion:
   - "neutral": standard query or calm statement ("What is HRV?", "Hello")
   - "stressed": workload, deadline, pressure ("I have too much work", "Feeling under pressure")
   - "anxious_distress": worry, fear, panic, somatic tension ("I am scared", "Heart racing with anxiety")
   - "low_mood": sadness, exhaustion, feeling down ("Feeling empty", "Unmotivated and sad")
   - "positive": happy, hopeful, relaxed ("I slept great", "Feeling good today")
   - "overwhelmed": unable to cope, completely burnt out ("Everything is piling up and I can't handle it")
   - "unknown": ambiguous or unclear text

2. distress_level:
   - 0: none/minimal distress
   - 1: mild distress (mild concern/stress)
   - 2: moderate distress (significant anxiety, overwhelm, low mood)
   - 3: severe distress (intense panic, despair, acute crisis signal)

3. llm_suggested_risk_level:
   - "normal": standard healthy conversation
   - "elevated": noticeable stress or anxiety
   - "high": heavy distress or burn-out
   - "critical": explicit mention of self-harm, severe despair, or crisis

4. crisis_indicator:
   - true ONLY if acute harm or crisis keywords are present, otherwise false.

5. confidence:
   - float between 0.0 and 1.0 representing classification confidence.

6. reason_category:
   - short snake_case category like "work_or_life_stress", "health_concerns", "sleep_or_fatigue", "interpersonal", "general_query", or null.
"""

VALID_EMOTIONS = {e.value for e in EmotionType}
VALID_RISK_LEVELS = {r.value for r in LLMSuggestedRiskLevel}


class EmotionAnalysisService:
    @staticmethod
    def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON object safely from LLM output string."""
        if not text or not text.strip():
            return None

        clean_text = text.strip()
        # Remove markdown code fences if present
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```[a-zA-Z]*\n?", "", clean_text)
            clean_text = re.sub(r"\n?```$", "", clean_text).strip()

        # Find first '{' and last '}'
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            clean_text = clean_text[start_idx : end_idx + 1]

        try:
            parsed = json.loads(clean_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception as exc:
            logger.warning(f"Failed to parse LLM emotion JSON output: {exc}")
        return None

    @classmethod
    def sanitize_llm_data(cls, data: Optional[Dict[str, Any]]) -> EmotionAnalysisLLMOutput:
        """Sanitizes and validates raw dictionary against enums and constraints."""
        if not data:
            return EmotionAnalysisLLMOutput()

        # 1. Validate emotion
        raw_emotion = str(data.get("emotion", "unknown")).strip().lower()
        if raw_emotion not in VALID_EMOTIONS:
            raw_emotion = EmotionType.UNKNOWN.value

        # 2. Validate distress level (0..3)
        try:
            raw_distress = int(data.get("distress_level", 0))
            raw_distress = max(0, min(3, raw_distress))
        except (ValueError, TypeError):
            raw_distress = 0

        # 3. Validate llm_suggested_risk_level
        raw_risk = str(data.get("llm_suggested_risk_level", "normal")).strip().lower()
        if raw_risk not in VALID_RISK_LEVELS:
            raw_risk = LLMSuggestedRiskLevel.NORMAL.value

        # 4. Validate crisis_indicator
        raw_crisis = bool(data.get("crisis_indicator", False))

        # 5. Validate & clamp confidence (0.0 .. 1.0)
        try:
            raw_conf = float(data.get("confidence", 0.0))
            raw_conf = max(0.0, min(1.0, raw_conf))
        except (ValueError, TypeError):
            raw_conf = 0.0

        # 6. Reason category
        raw_reason = data.get("reason_category")
        if raw_reason is not None:
            raw_reason = str(raw_reason).strip()[:100]

        return EmotionAnalysisLLMOutput(
            emotion=EmotionType(raw_emotion),
            distress_level=raw_distress,
            llm_suggested_risk_level=LLMSuggestedRiskLevel(raw_risk),
            crisis_indicator=raw_crisis,
            confidence=raw_conf,
            reason_category=raw_reason,
        )

    @classmethod
    async def analyze_message(
        cls,
        db: Session,
        user_id: int,
        conversation_id: str,
        message_id: str,
        message_text: str,
    ) -> EmotionalAssessment:
        """Analyzes a user chat message using Mistral AI and persists the assessment record."""
        sanitized_output = EmotionAnalysisLLMOutput()  # Safe default fallback

        api_key = settings.MISTRAL_API_KEY
        if api_key and message_text and message_text.strip():
            base_url = settings.MISTRAL_BASE_URL.rstrip('/')
            endpoint_url = f"{base_url}/v1/chat/completions" if not base_url.endswith("/v1") else f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.MISTRAL_MODEL,
                "messages": [
                    {"role": "system", "content": EMOTION_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this user message: \"{message_text}\""},
                ],
                "temperature": 0.1,
                "max_tokens": 150,
            }

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(endpoint_url, headers=headers, json=payload)
                    if response.status_code == 200:
                        resp_json = response.json()
                        raw_content = resp_json["choices"][0]["message"]["content"]
                        parsed_dict = cls._extract_json_block(raw_content)
                        sanitized_output = cls.sanitize_llm_data(parsed_dict)
                    else:
                        logger.warning(f"Emotion analysis Mistral API returned HTTP {response.status_code}")
            except Exception as exc:
                logger.warning(f"Error calling Mistral for emotion analysis: {exc}")

        # Persist to database
        assessment = EmotionalAssessment(
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
            emotion=sanitized_output.emotion.value,
            distress_level=sanitized_output.distress_level,
            llm_suggested_risk_level=sanitized_output.llm_suggested_risk_level.value,
            crisis_indicator=sanitized_output.crisis_indicator,
            confidence=sanitized_output.confidence,
            reason_category=sanitized_output.reason_category,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @classmethod
    def get_assessment_by_message(
        cls, db: Session, message_id: str, user_id: int
    ) -> Optional[EmotionalAssessment]:
        """Retrieves emotional assessment for a message with strict ownership verification."""
        return (
            db.query(EmotionalAssessment)
            .filter(
                EmotionalAssessment.message_id == message_id,
                EmotionalAssessment.user_id == user_id,
            )
            .first()
        )

    @classmethod
    def list_assessments_for_conversation(
        cls, db: Session, conversation_id: str, user_id: int
    ) -> list[EmotionalAssessment]:
        """Retrieves all emotional assessments in a conversation with ownership verification."""
        # Check conversation ownership first
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if not conv:
            return []

        return (
            db.query(EmotionalAssessment)
            .filter(
                EmotionalAssessment.conversation_id == conversation_id,
                EmotionalAssessment.user_id == user_id,
            )
            .order_by(EmotionalAssessment.created_at.asc())
            .all()
        )
