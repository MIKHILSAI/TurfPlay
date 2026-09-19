import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.database.mongodb import db

client = TestClient(app)


def test_equipment_flow_end_to_end():
    # 1. Sign up a new customer
    unique = uuid.uuid4().hex[:8]
    email = f"equip-test-{unique}@example.com"
    phone = f"+156{uuid.uuid4().int % 100000000:08d}"
    signup = client.post(
        "/auth/signup",
        json={"name": "Equipment Tester", "email": email, "phone": phone, "password": "secret123"},
    )
    assert signup.status_code == 200, signup.text
    token = signup.json()["token"]
    customer_id = signup.json()["customer"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ask to rent equipment with NO upcoming bookings
    chat_no_booking = client.post(
        "/assistant/chat",
        json={"message": "I want to rent 2 badminton rackets"},
        headers=headers,
    )
    assert chat_no_booking.status_code == 200
    res1 = chat_no_booking.json()
    assert res1["type"] == "text"
    assert "upcoming booking" in res1["message"].lower() or "linked to an active booking" in res1["message"].lower()

    # 3. Ask for equipment availability
    chat_avail = client.post(
        "/assistant/chat",
        json={"message": "What equipment is available?"},
        headers=headers,
    )
    assert chat_avail.status_code == 200
    res_avail = chat_avail.json()
    assert "available" in res_avail["message"].lower()

    # 4. Create an upcoming booking
    resource = db.resources.find_one()
    assert resource is not None
    future_date = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
    create_res = client.post(
        "/bookings",
        json={
            "resource_id": resource["_id"],
            "date": future_date,
            "start_time": "14:00",
            "end_time": "15:00",
            "equipment": [],
            "apply_membership": False,
        },
        headers=headers,
    )
    assert create_res.status_code == 200, create_res.text
    booking_id = create_res.json()["_id"]
    initial_total = create_res.json()["total_amount"]

    # 5. Ask with an invalid booking ID explicitly
    chat_invalid_bkg = client.post(
        "/assistant/chat",
        json={"message": "I want to rent 2 badminton rackets for booking BKG99999999"},
        headers=headers,
    )
    assert chat_invalid_bkg.status_code == 200
    res_inv = chat_invalid_bkg.json()
    assert res_inv["type"] == "text"
    assert "couldn't find a booking with id bkg99999999" in res_inv["message"].lower()

    # 6. Ask to rent 2 badminton rackets specifying the exact booking ID
    chat_with_booking = client.post(
        "/assistant/chat",
        json={"message": f"I want to rent 2 badminton rackets for booking {booking_id}"},
        headers=headers,
    )
    assert chat_with_booking.status_code == 200
    res2 = chat_with_booking.json()
    assert res2["type"] == "price_breakdown"
    assert "actions" in res2
    assert len(res2["actions"]) > 0
    confirm_action = next((a for a in res2["actions"] if a["action"] == "confirm_equipment"), None)
    assert confirm_action is not None
    assert confirm_action["payload"]["booking_id"] == booking_id
    assert confirm_action["payload"]["quantity"] == 2

    # 6. Execute confirm_equipment via POST /bookings/{id}/equipment
    equip_id = confirm_action["payload"]["equipment_id"]
    add_res = client.post(
        f"/bookings/{booking_id}/equipment",
        json={"equipment_id": equip_id, "quantity": 2},
        headers=headers,
    )
    assert add_res.status_code == 200, add_res.text
    updated_booking = add_res.json()
    assert len(updated_booking["equipment"]) > 0
    assert updated_booking["equipment"][0]["equipment_name"] == "Badminton Racket"
    assert updated_booking["total_amount"] > initial_total

    # 7. Verify GET /bookings/{id} returns equipment + updated total
    get_res = client.get(f"/bookings/{booking_id}", headers=headers)
    assert get_res.status_code == 200
    b_data = get_res.json()
    assert len(b_data["equipment"]) > 0
    assert b_data["equipment"][0]["equipment_name"] == "Badminton Racket"
    assert b_data["equipment"][0]["quantity"] == 2
    assert b_data["total_amount"] == updated_booking["total_amount"]
