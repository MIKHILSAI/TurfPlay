import uuid

from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def test_auth_and_contract_round_trip():
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"contract-{unique_suffix}@example.com"
    payload = {
        "name": "Contract User",
        "email": email,
        "phone": f"+155{uuid.uuid4().int % 100000000:08d}",
        "password": "secret123",
    }

    signup = client.post("/auth/signup", json=payload)
    assert signup.status_code == 200, signup.text
    body = signup.json()
    assert "token" in body
    assert body["customer"]["email"] == email

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200, me.text
    assert me.json()["email"] == email

    resources = client.get("/resources", headers={"Authorization": f"Bearer {body['token']}"})
    assert resources.status_code == 200, resources.text
    assert isinstance(resources.json(), list)


def test_assistant_chat_is_non_destructive():
    email = f"contract-{uuid.uuid4().hex[:8]}@example.com"
    signup = client.post(
        "/auth/signup",
        json={
            "name": "Contract User",
            "email": email,
            "phone": f"+155{uuid.uuid4().int % 100000000:08d}",
            "password": "secret123",
        },
    )
    token = signup.json()["token"]

    response = client.post(
        "/assistant/chat",
        json={"message": "I want to book a badminton court tomorrow at 6pm"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["type"] in {"text", "availability", "booking_summary", "confirmation", "action_buttons"}
    assert "message" in payload
