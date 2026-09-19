from backend.database.mongodb import db
from backend.services.auth_service import (
    register_customer,
    login_customer,
    set_current_customer
)
from backend.services.booking_service import (
    create_booking
)


# ============================================================
# TEST CONFIGURATION
# ============================================================

TEST_EMAIL = "booking_test@example.com"
TEST_PHONE = "+919999999999"
TEST_PASSWORD = "test123456"

TEST_BOOKING_DATE = "2026-09-20"


# ============================================================
# CLEAN OLD TEST CUSTOMER
# ============================================================

db.customers.delete_one({
    "email": TEST_EMAIL
})


# ============================================================
# REGISTER TEST CUSTOMER
# ============================================================

print("\n")
print("=" * 50)
print("STEP 1 — REGISTER TEST CUSTOMER")
print("=" * 50)

register_result = register_customer(
    name="Booking Test User",
    email=TEST_EMAIL,
    phone=TEST_PHONE,
    password=TEST_PASSWORD
)

print(register_result)


# ============================================================
# LOGIN
# ============================================================

print("\n")
print("=" * 50)
print("STEP 2 — LOGIN")
print("=" * 50)

login_result = login_customer(
    email_or_phone=TEST_EMAIL,
    password=TEST_PASSWORD
)

print(login_result)


# ============================================================
# CREATE SESSION
# ============================================================

session = {}

set_current_customer(
    session,
    login_result["customer"]
)

print("\n")
print("SESSION:")
print(session)


# ============================================================
# TEST 1 — CREATE BOOKING
# ============================================================

print("\n")
print("=" * 50)
print("TEST 1 — CREATE BOOKING")
print("=" * 50)

result = create_booking(
    session=session,
    resource_id="BC1",
    booking_date=TEST_BOOKING_DATE,
    start_time="10:00",
    end_time="11:00"
)

print(result)


# ============================================================
# TEST 2 — DUPLICATE BOOKING
# ============================================================

print("\n")
print("=" * 50)
print("TEST 2 — DUPLICATE BOOKING")
print("=" * 50)

result = create_booking(
    session=session,
    resource_id="BC1",
    booking_date=TEST_BOOKING_DATE,
    start_time="10:00",
    end_time="11:00"
)

print(result)


# ============================================================
# TEST 3 — DIFFERENT AVAILABLE SLOT
# ============================================================

print("\n")
print("=" * 50)
print("TEST 3 — DIFFERENT AVAILABLE SLOT")
print("=" * 50)

result = create_booking(
    session=session,
    resource_id="BC1",
    booking_date=TEST_BOOKING_DATE,
    start_time="12:00",
    end_time="13:00"
)

print(result)


# ============================================================
# TEST 4 — UNAUTHENTICATED USER
# ============================================================

print("\n")
print("=" * 50)
print("TEST 4 — UNAUTHENTICATED USER")
print("=" * 50)

empty_session = {}

result = create_booking(
    session=empty_session,
    resource_id="BC1",
    booking_date=TEST_BOOKING_DATE,
    start_time="14:00",
    end_time="15:00"
)

print(result)


# ============================================================
# TEST 5 — INVALID RESOURCE
# ============================================================

print("\n")
print("=" * 50)
print("TEST 5 — INVALID RESOURCE")
print("=" * 50)

result = create_booking(
    session=session,
    resource_id="XYZ999",
    booking_date=TEST_BOOKING_DATE,
    start_time="14:00",
    end_time="15:00"
)

print(result)


# ============================================================
# TEST 6 — OUTSIDE OPENING HOURS
# ============================================================

print("\n")
print("=" * 50)
print("TEST 6 — OUTSIDE OPENING HOURS")
print("=" * 50)

result = create_booking(
    session=session,
    resource_id="BC1",
    booking_date=TEST_BOOKING_DATE,
    start_time="05:00",
    end_time="06:00"
)

print(result)


# ============================================================
# SHOW CREATED BOOKINGS
# ============================================================

print("\n")
print("=" * 50)
print("CREATED TEST BOOKINGS")
print("=" * 50)

bookings = db.bookings.find({
    "customer_id": login_result["customer"]["id"]
})

for booking in bookings:
    print({
        "id": booking.get("_id"),
        "resource_id": booking.get(
            "resource_id"
        ),
        "date": booking.get(
            "booking_date"
        ),
        "start_time": booking.get(
            "start_time"
        ),
        "end_time": booking.get(
            "end_time"
        ),
        "status": booking.get(
            "status"
        ),
        "total_amount": booking.get(
            "price_breakdown",
            {}
        ).get(
            "total_amount"
        )
    })


# ============================================================
# CLEANUP
# ============================================================

db.bookings.delete_many({
    "customer_id": login_result["customer"]["id"]
})

db.audit_events.delete_many({
    "customer_id": login_result["customer"]["id"]
})

db.customers.delete_one({
    "_id": login_result["customer"]["id"]
})

print("\n")
print("=" * 50)
print("TEST DATA CLEANED UP")
print("=" * 50)