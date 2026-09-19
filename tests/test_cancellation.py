from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.database.mongodb import db
from backend.services.auth_service import (
    register_customer,
    login_customer,
    set_current_customer
)
from backend.services.booking_service import create_booking
from backend.services.cancellation_service import (
    cancel_booking_preview,
    cancel_booking
)


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")

TEST_EMAIL = "cancel_test@example.com"
TEST_PHONE = "+919888888888"
TEST_PASSWORD = "test123456"

TEST_DATE = "2026-09-20"


# ============================================================
# CLEAN OLD TEST DATA
# ============================================================

db.customers.delete_many({
    "email": {
        "$in": [
            TEST_EMAIL,
            "cancel_other@example.com"
        ]
    }
})


# ============================================================
# STEP 1 — REGISTER CUSTOMER
# ============================================================

print("\n" + "=" * 50)
print("STEP 1 — REGISTER TEST CUSTOMER")
print("=" * 50)

register_result = register_customer(
    name="Cancellation Test User",
    email=TEST_EMAIL,
    phone=TEST_PHONE,
    password=TEST_PASSWORD
)

print(register_result)


# ============================================================
# STEP 2 — LOGIN
# ============================================================

print("\n" + "=" * 50)
print("STEP 2 — LOGIN")
print("=" * 50)

login_result = login_customer(
    email_or_phone=TEST_EMAIL,
    password=TEST_PASSWORD
)

print(login_result)

session = {}

set_current_customer(
    session,
    login_result["customer"]
)

print("\nSESSION:")
print(session)


# ============================================================
# STEP 3 — CREATE BOOKING
# ============================================================

print("\n" + "=" * 50)
print("STEP 3 — CREATE BOOKING")
print("=" * 50)

booking_result = create_booking(
    session=session,
    resource_id="BC1",
    booking_date=TEST_DATE,
    start_time="10:00",
    end_time="11:00"
)

print(booking_result)

booking_id = booking_result["booking"]["id"]

print("\nBOOKING ID:")
print(booking_id)


# ============================================================
# TEST 1 — CANCELLATION PREVIEW
# ============================================================

print("\n" + "=" * 50)
print("TEST 1 — CANCELLATION PREVIEW")
print("=" * 50)

preview_result = cancel_booking_preview(
    session=session,
    booking_id=booking_id
)

print(preview_result)


# ============================================================
# TEST 2 — CANCELLATION WITHOUT CONFIRMATION
# ============================================================

print("\n" + "=" * 50)
print("TEST 2 — CANCELLATION WITHOUT CONFIRMATION")
print("=" * 50)

result = cancel_booking(
    session=session,
    booking_id=booking_id,
    confirmed=False
)

print(result)


# ============================================================
# TEST 3 — CONFIRMED CANCELLATION
# ============================================================

print("\n" + "=" * 50)
print("TEST 3 — CONFIRMED CANCELLATION")
print("=" * 50)

result = cancel_booking(
    session=session,
    booking_id=booking_id,
    confirmed=True,
    reason="Customer changed plans"
)

print(result)


# ============================================================
# TEST 4 — DUPLICATE CANCELLATION
# ============================================================

print("\n" + "=" * 50)
print("TEST 4 — DUPLICATE CANCELLATION")
print("=" * 50)

result = cancel_booking(
    session=session,
    booking_id=booking_id,
    confirmed=True
)

print(result)


# ============================================================
# TEST 5 — CANCELLED BOOKING PREVIEW
# ============================================================

print("\n" + "=" * 50)
print("TEST 5 — CANCELLED BOOKING PREVIEW")
print("=" * 50)

result = cancel_booking_preview(
    session=session,
    booking_id=booking_id
)

print(result)


# ============================================================
# TEST 6 — UNAUTHENTICATED USER
# ============================================================

print("\n" + "=" * 50)
print("TEST 6 — UNAUTHENTICATED USER")
print("=" * 50)

empty_session = {}

result = cancel_booking_preview(
    session=empty_session,
    booking_id=booking_id
)

print(result)


# ============================================================
# TEST 7 — NON-EXISTENT BOOKING
# ============================================================

print("\n" + "=" * 50)
print("TEST 7 — NON-EXISTENT BOOKING")
print("=" * 50)

result = cancel_booking_preview(
    session=session,
    booking_id="BKG_DOES_NOT_EXIST"
)

print(result)


# ============================================================
# SHOW AUDIT EVENTS
# ============================================================

print("\n" + "=" * 50)
print("AUDIT EVENTS")
print("=" * 50)

audit_events = list(
    db.audit_events.find({
        "customer_id": login_result["customer"]["id"]
    })
)

for event in audit_events:
    print({
        "event_type": event.get("event_type"),
        "entity_id": event.get("entity_id"),
        "metadata": event.get("metadata")
    })


# ============================================================
# CLEANUP
# ============================================================

print("\n" + "=" * 50)
print("CLEANING TEST DATA")
print("=" * 50)

customer_id = login_result["customer"]["id"]

db.bookings.delete_many({
    "customer_id": customer_id
})

db.audit_events.delete_many({
    "customer_id": customer_id
})

db.payments.delete_many({
    "customer_id": customer_id
})

db.customers.delete_one({
    "_id": customer_id
})

print("TEST DATA CLEANED UP")