"""xAI (Grok) Wellness Intelligence Service.

Acts as the single secure backend proxy between the Sanjeevni client and the xAI API.
Enforces the strict ZERO-MOCK / NO-INVENTED-DATA policy:
- Injects a clinical wellness system prompt ensuring non-diagnostic guidance.
- Distinguishes verified physiological telemetry from general advice.
- Strictly instructs Grok to NEVER fabricate heart rate, HRV, EDA, skin temperature, or stress percentages.
- Manages timeouts, rate limits, and network errors gracefully without leaking keys.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import SanjeevniException, ErrorCode
from app.schemas.ai import ChatMessage, AIChatResponse
from app.models.user import User
from app.services.dashboard_service import DashboardService


SANJEEVNI_SYSTEM_PROMPT = """You are Sanjeevni AI, an evidence-based autonomic nervous system wellness companion.
You provide clear, supportive, and scientifically grounded guidance on somatic stress, vagal nerve regulation, restorative breathing, sleep hygiene, and mindfulness.

IMPORTANT CLINICAL & DATA RULES:
1. You are NOT a medical doctor and you DO NOT provide clinical diagnosis, medical prescriptions, or medical treatment plans.
2. In situations suggesting medical emergencies, acute chest pain, severe depression, or crisis, clearly urge the user to seek immediate professional medical assistance or call emergency services.
3. ABSOLUTE ZERO FAKE SENSOR DATA RULE:
   - NEVER invent, simulate, or assume numerical physiological vitals (Heart Rate, HRV, Temperature, Skin Conductance / GSR, or Motion).
   - If the user asks about their vitals or stress and verified data is NOT provided in the [REAL BIOMETRIC CONTEXT] below, explicitly state that no current sensor data is available from their wearable.
   - Never say things like "I see your heart rate is 78 BPM" unless that exact figure appears in the verified context provided below.
4. If real physiological data IS provided in the context, refer ONLY to those exact measurements and explain their physiological significance (e.g. higher RMSSD indicating parasympathetic recovery).
5. Always maintain a calm, professional, empathetic, and encouraging tone. Keep answers structured and practical.
"""


class AIService:
    @staticmethod
    def _build_health_context(db: Session, user: User, device_id: Optional[str] = None) -> str:
        """Extracts genuine real-time telemetry context if available for the user."""
        try:
            # Find user's active device if not provided
            target_device_id = device_id
            if not target_device_id and user.devices:
                target_device_id = user.devices[0].device_id

            if not target_device_id:
                return "[REAL BIOMETRIC CONTEXT]: NO_DEVICE_REGISTERED. No wearable currently linked to this profile."

            dashboard_data = DashboardService.get_dashboard_summary(db, target_device_id)
            if not dashboard_data:
                return "[REAL BIOMETRIC CONTEXT]: NO_CURRENT_SENSOR_DATA. Wearable has not streamed data recently."

            vitals = dashboard_data.vitals
            stress = dashboard_data.stress
            status = dashboard_data.data_status

            context_lines = [
                f"[REAL BIOMETRIC CONTEXT]:",
                f"- Data Status: {status}",
                f"- Device: {target_device_id}",
            ]

            if vitals:
                if vitals.heart_rate_bpm is not None:
                    context_lines.append(f"- Heart Rate: {vitals.heart_rate_bpm:.1f} BPM")
                if vitals.hrv_rmssd_ms is not None:
                    context_lines.append(f"- HRV (RMSSD): {vitals.hrv_rmssd_ms:.1f} ms")
                if vitals.temperature_f is not None:
                    celsius = (vitals.temperature_f - 32) * 5 / 9
                    context_lines.append(f"- Skin Temperature: {celsius:.1f} °C")
                if vitals.skin_conductance_us is not None:
                    context_lines.append(f"- Electrodermal Activity (EDA): {vitals.skin_conductance_us:.2f} µS")
            else:
                context_lines.append("- Vitals: NO_CURRENT_SENSOR_DATA")

            if stress and stress.stress_score is not None:
                context_lines.append(f"- Estimated Stress Score: {stress.stress_score:.1f}%")
                context_lines.append(f"- Stress Level Classification: {stress.stress_level}")
            else:
                context_lines.append("- Estimated Stress: NO_PREDICTION_AVAILABLE")

            return "\n".join(context_lines)
        except Exception as exc:
            logger.warning(f"Failed to gather biometric context for AI: {exc}")
            return "[REAL BIOMETRIC CONTEXT]: NO_CURRENT_SENSOR_DATA."

    @classmethod
    async def chat(
        cls,
        db: Session,
        user: User,
        message: str,
        conversation_history: List[ChatMessage],
        include_health_context: bool = True,
        device_id: Optional[str] = None,
    ) -> AIChatResponse:
        """Sends a structured request to xAI Grok with safe context and returns assistant message."""
        api_key = settings.XAI_API_KEY
        if not api_key:
            logger.warning("xAI API key not configured on backend.")
            raise SanjeevniException(
                status_code=503,
                error_code=ErrorCode.MODEL_UNAVAILABLE,
                message="Sanjeevni AI is temporarily unavailable. Server configuration pending.",
            )

        # Build message payload
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SANJEEVNI_SYSTEM_PROMPT}
        ]

        # Add health context if enabled
        health_context_included = False
        if include_health_context:
            context_str = cls._build_health_context(db, user, device_id)
            messages.append({"role": "system", "content": context_str})
            health_context_included = True

        # Append conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 turns max for security & token conservation
            if msg.role in ("user", "assistant", "system"):
                messages.append({"role": msg.role, "content": msg.content})

        # Append current user message
        messages.append({"role": "user", "content": message})

        endpoint_url = f"{settings.XAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.XAI_MODEL,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 800,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.XAI_TIMEOUT_SECONDS) as client:
                response = await client.post(endpoint_url, headers=headers, json=payload)

            if response.status_code == 429:
                logger.warning("xAI API rate limit encountered.")
                raise SanjeevniException(
                    status_code=429,
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="Sanjeevni AI is experiencing high demand. Please try again shortly.",
                )

            if response.status_code != 200:
                logger.error(f"xAI API error response: {response.status_code} - {response.text}")
                raise SanjeevniException(
                    status_code=503,
                    error_code=ErrorCode.MODEL_UNAVAILABLE,
                    message="Sanjeevni AI is currently unavailable.",
                )

            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()

            return AIChatResponse(
                reply=reply,
                model=settings.XAI_MODEL,
                timestamp=datetime.now(timezone.utc).isoformat(),
                health_context_included=health_context_included,
                status="success",
            )

        except httpx.TimeoutException:
            logger.warning("xAI API request timed out.")
            raise SanjeevniException(
                status_code=504,
                error_code=ErrorCode.MODEL_UNAVAILABLE,
                message="Unable to connect to Sanjeevni AI. Request timed out.",
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error communicating with xAI API: {exc}")
            raise SanjeevniException(
                status_code=503,
                error_code=ErrorCode.MODEL_UNAVAILABLE,
                message="Unable to connect to Sanjeevni AI.",
            )
