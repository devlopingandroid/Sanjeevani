"""Tests for Sanjeevni AI Health/Wellness Domain Guard — Natural Emotional & Wellbeing Conversations.

Verifies:
1. ALLOWED state for natural stress, pressure, emotional wellbeing, anxiety/worry, sleep, and lifestyle expressions.
2. AMBIGUOUS state for open-ended personal state expressions (returns gentle clarification, NOT blocked).
3. BLOCKED state for explicit off-topic requests (coding, math, sports, jokes, politics).
4. Full integration through API /api/v1/ai/chat ensuring emotion/distress pipeline is reached for allowed/ambiguous messages.
"""
import time
import pytest
import httpx
from unittest.mock import patch, AsyncMock

from app.services.domain_guard import DomainGuard, DomainGuardStatus
from app.core.config import settings


def test_domain_guard_unit_evaluation():
    """Direct unit test of DomainGuard.evaluate on the 12 explicit prompt test cases."""
    
    # 1. Stress and pressure → ALLOWED
    status1, _ = DomainGuard.evaluate("I've been feeling stressed lately.")
    assert status1 == DomainGuardStatus.ALLOWED

    status2, _ = DomainGuard.evaluate("Work has been overwhelming.")
    assert status2 == DomainGuardStatus.ALLOWED

    # 2. Ambiguous open-ended state → AMBIGUOUS (not blocked)
    status3, msg3 = DomainGuard.evaluate("I don't know what's happening with me lately.")
    assert status3 == DomainGuardStatus.AMBIGUOUS
    assert "Tell me a little more" in msg3 or "experiencing" in msg3

    # 3. Anxiety-like & sleep → ALLOWED
    status4, _ = DomainGuard.evaluate("I can't relax at night.")
    assert status4 == DomainGuardStatus.ALLOWED

    status5, _ = DomainGuard.evaluate("My thoughts keep racing.")
    assert status5 == DomainGuardStatus.ALLOWED

    status6, _ = DomainGuard.evaluate("I've been feeling low recently.")
    assert status6 == DomainGuardStatus.ALLOWED

    status7, _ = DomainGuard.evaluate("I'm irritated all the time.")
    assert status7 == DomainGuardStatus.ALLOWED

    status8, _ = DomainGuard.evaluate("I've been sleeping badly.")
    assert status8 == DomainGuardStatus.ALLOWED

    # 4. Off-topic queries → BLOCKED
    status9, msg9 = DomainGuard.evaluate("Write Python code.")
    assert status9 == DomainGuardStatus.BLOCKED
    assert "health and wellness assistant" in msg9.lower()

    status10, msg10 = DomainGuard.evaluate("Tell me a joke.")
    assert status10 == DomainGuardStatus.BLOCKED
    assert "health and wellness assistant" in msg10.lower()

    status11, msg11 = DomainGuard.evaluate("Who won the match?")
    assert status11 == DomainGuardStatus.BLOCKED
    assert "health and wellness assistant" in msg11.lower()

    status12, msg12 = DomainGuard.evaluate("What is 17 x 25?")
    assert status12 == DomainGuardStatus.BLOCKED
    assert "health and wellness assistant" in msg12.lower()


@pytest.mark.asyncio
async def test_ai_chat_natural_emotional_conversations_allowed(client):
    """Verifies that natural emotional conversations reach Mistral AI."""
    email = f"ai_nat_allowed_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "Emotional Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    allowed_emotional_messages = [
        "I've been feeling stressed lately.",
        "Work has been overwhelming.",
        "I can't relax at night.",
        "My thoughts keep racing.",
        "I've been feeling low recently.",
        "I'm irritated all the time.",
        "I've been sleeping badly.",
    ]

    mock_mistral_response = {
        "choices": [{"message": {"content": "I hear you. Let's talk about restorative relaxation and sleep hygiene."}}]
    }
    mock_httpx_response = httpx.Response(200, json=mock_mistral_response)

    with patch.object(settings, "MISTRAL_API_KEY", "test-key"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx_response) as mock_post:
            for msg in allowed_emotional_messages:
                resp = client.post(
                    "/api/v1/ai/chat",
                    json={"message": msg},
                    headers=headers,
                )
                assert resp.status_code == 200
                data = resp.json()
                assert data["handled_by"] == "MISTRAL_AI"
                assert data["scope"] == "HEALTH_WELLNESS"


@pytest.mark.asyncio
async def test_ai_chat_ambiguous_wellness_conversation(client):
    """Verifies that ambiguous open-ended state ('I don't know what's happening with me lately') is NOT rejected."""
    email = f"ai_ambig_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "Ambiguous Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ambiguous_msg = "I don't know what's happening with me lately."

    resp = client.post(
        "/api/v1/ai/chat",
        json={"message": ambiguous_msg},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "health and wellness assistant" not in data["reply"].lower()
    assert "tell me a little more" in data["reply"].lower() or "experiencing" in data["reply"].lower()


@pytest.mark.asyncio
async def test_ai_chat_offtopic_blocked(client):
    """Verifies that explicit coding, math, sports, and trivia remain strictly BLOCKED."""
    email = f"ai_blocked_{time.time()}@sanjeevni.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!", "full_name": "Blocked Tester"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    blocked_messages = [
        "Write Python code.",
        "Tell me a joke.",
        "Who won the match?",
        "What is 17 x 25?",
    ]

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        for msg in blocked_messages:
            resp = client.post(
                "/api/v1/ai/chat",
                json={"message": msg},
                headers=headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["handled_by"] == "DOMAIN_GUARD"
            assert "health and wellness assistant" in data["reply"].lower()
            assert mock_post.call_count == 0
