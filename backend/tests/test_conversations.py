"""Unit and Integration tests for Sanjeevni Conversations and Chat Database Foundation."""
import time
import pytest
from app.models.conversation import ChatMessage


def register_and_login(client, email_prefix: str):
    email = f"{email_prefix}_{time.time()}@sanjeevni.com"
    password = "SecurePassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": email_prefix})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthorized_access_rejected(client):
    # All endpoints require authentication
    assert client.post("/api/v1/conversations").status_code == 401
    assert client.get("/api/v1/conversations").status_code == 401
    assert client.get("/api/v1/conversations/some-id").status_code == 401
    assert client.delete("/api/v1/conversations/some-id").status_code == 401
    assert client.post("/api/v1/conversations/some-id/messages", json={"role": "user", "message": "hi"}).status_code == 401
    assert client.get("/api/v1/conversations/some-id/messages").status_code == 401


def test_create_and_get_conversation(client):
    headers = register_and_login(client, "user_conv_create")

    # Create conversation without title
    resp = client.post("/api/v1/conversations", json={}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["status"] == "active"
    conv_id = data["id"]

    # Fetch conversation details
    get_resp = client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conv_id

    # Create conversation with explicit title
    resp_titled = client.post("/api/v1/conversations", json={"title": "Breathing Guidance"}, headers=headers)
    assert resp_titled.status_code == 201
    assert resp_titled.json()["title"] == "Breathing Guidance"


def test_list_own_conversations_and_pagination(client):
    headers = register_and_login(client, "user_conv_list")

    # Create 5 conversations
    created_ids = []
    for i in range(5):
        resp = client.post("/api/v1/conversations", json={"title": f"Session {i}"}, headers=headers)
        assert resp.status_code == 201
        created_ids.append(resp.json()["id"])

    # List conversations with limit=2
    list_resp = client.get("/api/v1/conversations?limit=2&offset=0", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    # Page 2 (offset=2, limit=2)
    list_page2 = client.get("/api/v1/conversations?limit=2&offset=2", headers=headers)
    assert list_page2.status_code == 200
    assert len(list_page2.json()["items"]) == 2


def test_create_and_list_chat_messages(client):
    headers = register_and_login(client, "user_msg_create")

    # Create conversation
    conv_resp = client.post("/api/v1/conversations", headers=headers)
    conv_id = conv_resp.json()["id"]

    # Post user message
    msg1_resp = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "user", "message": "How can I lower stress before sleep?"},
        headers=headers,
    )
    assert msg1_resp.status_code == 201
    msg1_data = msg1_resp.json()
    assert msg1_data["role"] == "user"
    assert msg1_data["message"] == "How can I lower stress before sleep?"
    assert msg1_data["conversation_id"] == conv_id

    # Verify conversation title was auto-updated from first user message
    conv_get = client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert "How can I lower stress" in conv_get.json()["title"]

    # Post assistant response
    msg2_resp = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "assistant", "message": "Try 4-7-8 breathing exercises for 3 minutes."},
        headers=headers,
    )
    assert msg2_resp.status_code == 201

    # List messages
    msgs_get = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    assert msgs_get.status_code == 200
    m_data = msgs_get.json()
    assert m_data["total"] == 2
    assert len(m_data["items"]) == 2
    # Verify chronological ordering ASC
    assert m_data["items"][0]["role"] == "user"
    assert m_data["items"][1]["role"] == "assistant"


def test_message_pagination(client):
    headers = register_and_login(client, "user_msg_page")
    conv_id = client.post("/api/v1/conversations", headers=headers).json()["id"]

    # Add 15 messages
    for i in range(15):
        role = "user" if i % 2 == 0 else "assistant"
        client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"role": role, "message": f"Message {i}"},
            headers=headers,
        )

    # Fetch page 1 (limit=5)
    p1 = client.get(f"/api/v1/conversations/{conv_id}/messages?limit=5&offset=0", headers=headers).json()
    assert p1["total"] == 15
    assert len(p1["items"]) == 5
    assert p1["items"][0]["message"] == "Message 0"

    # Fetch page 2 (limit=5, offset=5)
    p2 = client.get(f"/api/v1/conversations/{conv_id}/messages?limit=5&offset=5", headers=headers).json()
    assert len(p2["items"]) == 5
    assert p2["items"][0]["message"] == "Message 5"


def test_cross_user_isolation_enforced(client):
    user1_headers = register_and_login(client, "user_owner_a")
    user2_headers = register_and_login(client, "user_owner_b")

    # User 1 creates conversation
    conv_u1 = client.post("/api/v1/conversations", json={"title": "Private User 1 Notes"}, headers=user1_headers).json()["id"]
    client.post(f"/api/v1/conversations/{conv_u1}/messages", json={"role": "user", "message": "Secret data"}, headers=user1_headers)

    # User 2 attempts to read User 1's conversation -> 404
    assert client.get(f"/api/v1/conversations/{conv_u1}", headers=user2_headers).status_code == 404

    # User 2 attempts to list messages of User 1's conversation -> 404
    assert client.get(f"/api/v1/conversations/{conv_u1}/messages", headers=user2_headers).status_code == 404

    # User 2 attempts to post a message into User 1's conversation -> 404
    assert client.post(f"/api/v1/conversations/{conv_u1}/messages", json={"role": "user", "message": "Hacked"}, headers=user2_headers).status_code == 404

    # User 2 attempts to delete User 1's conversation -> 404
    assert client.delete(f"/api/v1/conversations/{conv_u1}", headers=user2_headers).status_code == 404


def test_invalid_conversation_id_returns_404(client):
    headers = register_and_login(client, "user_invalid_id")
    fake_id = "00000000-0000-0000-0000-000000000000"

    assert client.get(f"/api/v1/conversations/{fake_id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/conversations/{fake_id}/messages", headers=headers).status_code == 404
    assert client.delete(f"/api/v1/conversations/{fake_id}", headers=headers).status_code == 404


def test_invalid_role_rejected(client):
    headers = register_and_login(client, "user_invalid_role")
    conv_id = client.post("/api/v1/conversations", headers=headers).json()["id"]

    # Role 'admin' or 'system' should fail Pydantic validation (422)
    resp_admin = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "admin", "message": "Hello"},
        headers=headers,
    )
    assert resp_admin.status_code == 422

    resp_system = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "system", "message": "Hello"},
        headers=headers,
    )
    assert resp_system.status_code == 422


def test_empty_message_rejected(client):
    headers = register_and_login(client, "user_empty_msg")
    conv_id = client.post("/api/v1/conversations", headers=headers).json()["id"]

    # Empty or whitespace-only messages should be rejected (422)
    resp_empty = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "user", "message": ""},
        headers=headers,
    )
    assert resp_empty.status_code == 422

    resp_blank = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "user", "message": "   \n\t  "},
        headers=headers,
    )
    assert resp_blank.status_code == 422


def test_delete_conversation(client):
    headers = register_and_login(client, "user_del_conv")

    conv_id = client.post("/api/v1/conversations", json={"title": "To Delete"}, headers=headers).json()["id"]
    client.post(f"/api/v1/conversations/{conv_id}/messages", json={"role": "user", "message": "Deleting soon"}, headers=headers)

    # Delete conversation
    del_resp = client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert del_resp.status_code == 200

    # Subsequent GET returns 404
    assert client.get(f"/api/v1/conversations/{conv_id}", headers=headers).status_code == 404
