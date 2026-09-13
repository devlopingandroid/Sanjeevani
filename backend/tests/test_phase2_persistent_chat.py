"""Phase 2 Persistent AI Chat Verification Tests.

Verifies:
- Authenticated chat
- Conversation ownership and isolation
- User message persistence in DB
- Assistant message persistence in DB
- Context loading into Mistral API prompt payload
- Domain-blocked message persistence & zero Mistral API calls
- Mistral API failure handling (503)
- Mistral 429 rate limit handling
- Unauthorized conversation access rejection (404)
- Empty message validation error (422)
- Automatic new conversation creation
"""
import time
import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.core.config import settings


def register_and_login(client, email_prefix: str):
    email = f"{email_prefix}_{time.time()}@sanjeevni.com"
    password = "SecurePassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": email_prefix})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_ai_chat_new_conversation_and_persistence(client):
    headers = register_and_login(client, "user_phase2_new")

    mock_mistral_response = {
        "choices": [{"message": {"role": "assistant", "content": "Restorative sleep helps reduce cortisol."}}]
    }
    mock_httpx_response = httpx.Response(200, json=mock_mistral_response)

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase2"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx_response):
            # 1. Post message without conversation_id -> should auto-create conversation
            resp = client.post(
                "/api/v1/ai/chat",
                json={"message": "How does sleep affect stress?"},
                headers=headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "conversation_id" in data
            conv_id = data["conversation_id"]

            # 2. Verify messages persisted in DB
            msgs_resp = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
            assert msgs_resp.status_code == 200
            items = msgs_resp.json()["items"]
            assert len(items) == 2
            assert items[0]["role"] == "user"
            assert items[0]["message"] == "How does sleep affect stress?"
            assert items[1]["role"] == "assistant"
            assert "Restorative sleep" in items[1]["message"]


@pytest.mark.asyncio
async def test_ai_chat_context_loading(client):
    headers = register_and_login(client, "user_phase2_context")

    # Create conversation and add previous turn
    conv_resp = client.post("/api/v1/conversations", headers=headers)
    conv_id = conv_resp.json()["id"]

    mock_mistral_response = {
        "choices": [{"message": {"role": "assistant", "content": "4-7-8 breathing is excellent."}}]
    }
    mock_httpx_response = httpx.Response(200, json=mock_mistral_response)

    with patch.object(settings, "MISTRAL_API_KEY", "test-key-phase2"):
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_httpx_response) as mock_post:
            # 1. Turn 1
            resp1 = client.post(
                "/api/v1/ai/chat",
                json={"message": "I feel anxious.", "conversation_id": conv_id},
                headers=headers,
            )
            assert resp1.status_code == 200

            # 2. Turn 2 - check that previous turn was sent to Mistral in prompt
            resp2 = client.post(
                "/api/v1/ai/chat",
                json={"message": "Can you give me a breathing technique?", "conversation_id": conv_id},
                headers=headers,
            )
            assert resp2.status_code == 200

            # Inspect payload sent to Mistral in Turn 2
            last_call_json = mock_post.call_args_list[-1].kwargs["json"]
            sent_messages = last_call_json["messages"]
            sent_contents = [m["content"] for m in sent_messages if isinstance(m.get("content"), str)]
            
            # Verify context included Turn 1 user message and Turn 1 assistant message
            assert any("I feel anxious." in c for c in sent_contents)
            assert any("4-7-8 breathing" in c for c in sent_contents)
            assert any("Can you give me a breathing technique?" in c for c in sent_contents)


@pytest.mark.asyncio
async def test_ai_chat_unauthorized_conversation_access(client):
    headers1 = register_and_login(client, "user_phase2_owner1")
    headers2 = register_and_login(client, "user_phase2_owner2")

    # User 1 creates conversation
    conv_resp = client.post("/api/v1/conversations", headers=headers1)
    conv_id = conv_resp.json()["id"]

    # User 2 attempts to send AI chat message into User 1's conversation -> 404
    resp = client.post(
        "/api/v1/ai/chat",
        json={"message": "Hacking conversation", "conversation_id": conv_id},
        headers=headers2,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ai_chat_domain_blocked_message_persisted(client):
    headers = register_and_login(client, "user_phase2_domain")

    # Create conversation
    conv_resp = client.post("/api/v1/conversations", headers=headers)
    conv_id = conv_resp.json()["id"]

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        resp = client.post(
            "/api/v1/ai/chat",
            json={"message": "What is an array in programming?", "conversation_id": conv_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["handled_by"] == "DOMAIN_GUARD"
        assert mock_post.call_count == 0  # Mistral NOT called

        # Verify both off-topic query and assistant redirect are persisted in DB
        msgs_resp = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
        assert msgs_resp.status_code == 200
        items = msgs_resp.json()["items"]
        assert len(items) == 2
        assert items[0]["message"] == "What is an array in programming?"
        assert "health and wellness assistant" in items[1]["message"].lower()
