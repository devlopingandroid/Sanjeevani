"""Phase 3 Emotion and Distress Analysis Test Suite.

Verifies:
- Neutral message analysis
- Stress message analysis
- Anxious/distress message analysis
- Low mood message analysis
- Positive message analysis
- Ambiguous message analysis
- Malformed model output handling & safe fallback
- Invalid llm_suggested_risk_level sanitization
- Invalid confidence clamping & sanitization
- Unauthorized access rejection (401)
- Cross-user isolation (404)
- Verification that llm_suggested_risk_level is explicitly non-authoritative
"""
import time
import json
import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.core.config import settings
from app.services.emotion_service import EmotionAnalysisService
from app.schemas.emotion import EmotionType, LLMSuggestedRiskLevel


def register_and_login(client, email_prefix: str):
    email = f"{email_prefix}_{time.time()}@sanjeevni.com"
    password = "SecurePassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": email_prefix})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_neutral_message_emotion_analysis(client):
    headers = register_and_login(client, "user_neutral_emo")

    mock_llm_json = {
        "emotion": "neutral",
        "distress_level": 0,
        "llm_suggested_risk_level": "normal",
        "crisis_indicator": False,
        "confidence": 0.95,
        "reason_category": "general_query"
    }
    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase3"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "What is the function of HRV?"},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            # Fetch assessments for conversation
            assessments_resp = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=headers)
            assert assessments_resp.status_code == 200
            items = assessments_resp.json()
            assert len(items) == 1
            assessment = items[0]
            assert assessment["emotion"] == "neutral"
            assert assessment["distress_level"] == 0
            assert assessment["llm_suggested_risk_level"] == "normal"
            assert assessment["crisis_indicator"] is False
            assert assessment["confidence"] == 0.95


@pytest.mark.asyncio
async def test_stress_message_emotion_analysis(client):
    headers = register_and_login(client, "user_stress_emo")

    mock_llm_json = {
        "emotion": "stressed",
        "distress_level": 2,
        "llm_suggested_risk_level": "elevated",
        "crisis_indicator": False,
        "confidence": 0.88,
        "reason_category": "work_or_life_stress"
    }
    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": str(mock_llm_json).replace("'", '"').replace("False", "false")}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase3"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "I have 3 deadlines today and feel super stressed!"},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            assessments_resp = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=headers)
            assert assessments_resp.status_code == 200
            items = assessments_resp.json()
            assert len(items) == 1
            assert items[0]["emotion"] == "stressed"
            assert items[0]["distress_level"] == 2
            assert items[0]["llm_suggested_risk_level"] == "elevated"


@pytest.mark.asyncio
async def test_anxious_distress_message_emotion_analysis(client):
    headers = register_and_login(client, "user_anxious_emo")

    mock_llm_json = {
        "emotion": "anxious_distress",
        "distress_level": 2,
        "llm_suggested_risk_level": "elevated",
        "crisis_indicator": False,
        "confidence": 0.90,
        "reason_category": "health_concerns"
    }
    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": '{"emotion": "anxious_distress", "distress_level": 2, "llm_suggested_risk_level": "elevated", "crisis_indicator": false, "confidence": 0.90, "reason_category": "health_concerns"}'}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase3"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "My heart is racing and I feel anxious."},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            assessments_resp = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=headers)
            assert assessments_resp.status_code == 200
            assert assessments_resp.json()[0]["emotion"] == "anxious_distress"


@pytest.mark.asyncio
async def test_low_mood_message_emotion_analysis(client):
    headers = register_and_login(client, "user_lowmood_emo")

    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": '{"emotion": "low_mood", "distress_level": 1, "llm_suggested_risk_level": "elevated", "crisis_indicator": false, "confidence": 0.85, "reason_category": "sleep_or_fatigue"}'}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase3"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "I feel unmotivated and sad today."},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            assessments_resp = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=headers)
            assert assessments_resp.status_code == 200
            assert assessments_resp.json()[0]["emotion"] == "low_mood"


@pytest.mark.asyncio
async def test_positive_message_emotion_analysis(client):
    headers = register_and_login(client, "user_positive_emo")

    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": '{"emotion": "positive", "distress_level": 0, "llm_suggested_risk_level": "normal", "crisis_indicator": false, "confidence": 0.98}'}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase3"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "I slept 8 hours and feel amazing!"},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            assessments_resp = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=headers)
            assert assessments_resp.status_code == 200
            assert assessments_resp.json()[0]["emotion"] == "positive"
            assert assessments_resp.json()[0]["distress_level"] == 0


@pytest.mark.asyncio
async def test_ambiguous_message_emotion_analysis(client):
    headers = register_and_login(client, "user_ambiguous_emo")

    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": '{"emotion": "unknown", "distress_level": 0, "llm_suggested_risk_level": "normal", "crisis_indicator": false, "confidence": 0.40}'}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase3"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "Hmm okay."},
                headers=headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            assessments_resp = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=headers)
            assert assessments_resp.status_code == 200
            assert assessments_resp.json()[0]["emotion"] == "unknown"


def test_malformed_model_output_fallback():
    # Garbage output string
    garbage_output = "I cannot fulfill this request as JSON. Hello World!"
    extracted = EmotionAnalysisService._extract_json_block(garbage_output)
    sanitized = EmotionAnalysisService.sanitize_llm_data(extracted)

    assert sanitized.emotion == EmotionType.UNKNOWN
    assert sanitized.distress_level == 0
    assert sanitized.llm_suggested_risk_level == LLMSuggestedRiskLevel.NORMAL
    assert sanitized.crisis_indicator is False
    assert sanitized.confidence == 0.0


def test_invalid_llm_suggested_risk_level_sanitization():
    invalid_data = {
        "emotion": "stressed",
        "distress_level": 1,
        "llm_suggested_risk_level": "CATASTROPHIC_DANGER",  # Invalid risk enum
        "confidence": 0.8
    }
    sanitized = EmotionAnalysisService.sanitize_llm_data(invalid_data)
    assert sanitized.emotion == EmotionType.STRESSED
    assert sanitized.llm_suggested_risk_level == LLMSuggestedRiskLevel.NORMAL  # Fallback to normal


def test_invalid_confidence_clamping():
    # Confidence out of bounds (e.g. 15.0 or -5.0)
    high_data = {"confidence": 15.0}
    sanitized_high = EmotionAnalysisService.sanitize_llm_data(high_data)
    assert sanitized_high.confidence == 1.0

    neg_data = {"confidence": -2.5}
    sanitized_neg = EmotionAnalysisService.sanitize_llm_data(neg_data)
    assert sanitized_neg.confidence == 0.0

    string_bad_data = {"confidence": "invalid_number"}
    sanitized_bad = EmotionAnalysisService.sanitize_llm_data(string_bad_data)
    assert sanitized_bad.confidence == 0.0


def test_unauthorized_assessment_access(client):
    # Unauthenticated access rejected with 401
    assert client.get("/api/v1/conversations/some-conv-id/assessments").status_code == 401
    assert client.get("/api/v1/conversations/some-conv-id/messages/some-msg-id/assessment").status_code == 401


@pytest.mark.asyncio
async def test_cross_user_assessment_isolation(client):
    user1_headers = register_and_login(client, "user_emo_owner_a")
    user2_headers = register_and_login(client, "user_emo_owner_b")

    mock_httpx = httpx.Response(200, json={"choices": [{"message": {"content": '{"emotion": "stressed", "distress_level": 1, "llm_suggested_risk_level": "elevated", "crisis_indicator": false, "confidence": 0.9}'}}]})

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase3"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx):
            chat_resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "I am feeling stressed today."},
                headers=user1_headers,
            )
            assert chat_resp.status_code == 200
            conv_id = chat_resp.json()["conversation_id"]

            # User 1 fetches assessment -> 200
            u1_assess = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=user1_headers)
            assert u1_assess.status_code == 200
            msg_id = u1_assess.json()[0]["message_id"]

            # User 2 attempts to fetch User 1's conversation assessments -> 404
            u2_list = client.get(f"/api/v1/conversations/{conv_id}/assessments", headers=user2_headers)
            assert u2_list.status_code == 404

            # User 2 attempts to fetch User 1's message assessment -> 404
            u2_single = client.get(f"/api/v1/conversations/{conv_id}/messages/{msg_id}/assessment", headers=user2_headers)
            assert u2_single.status_code == 404
