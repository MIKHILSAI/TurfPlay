from backend.database.mongodb import db
from backend.services.pricing_service import calculate_price


# ============================================================
# TEST DATA
# ============================================================

TEST_CUSTOMER_ID = "TEST_CUSTOMER_PRICING"
TEST_EQUIPMENT_ID = "TEST_RACKET_PRICING"


# ============================================================
# CREATE TEST DATA
# ============================================================

# Create temporary active equipment
db.equipment.update_one(
    {"_id": TEST_EQUIPMENT_ID},
    {
        "$set": {
            "_id": TEST_EQUIPMENT_ID,
            "name": "Test Badminton Racket",
            "type": "badminton_racket",
            "rental_rate": 50,
            "deposit": 0,
            "available_quantity": 10,
            "active": True
        }
    },
    upsert=True
)


# Create temporary active membership
db.memberships.update_one(
    {
        "_id": "TEST_MEMBERSHIP_PRICING"
    },
    {
        "$set": {
            "_id": "TEST_MEMBERSHIP_PRICING",
            "customer_id": TEST_CUSTOMER_ID,
            "type": "monthly",
            "price": 1500,
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "status": "active",
            "discount_percent": 15
        }
    },
    upsert=True
)


# ============================================================
# TEST 1 — NORMAL BOOKING
# ============================================================

print("\n")
print("=" * 50)
print("TEST 1 — NORMAL BOOKING")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-09",
    start_time="10:00",
    end_time="11:00"
)

print(result)


# ============================================================
# TEST 2 — PEAK WEEKDAY
# ============================================================

print("\n")
print("=" * 50)
print("TEST 2 — PEAK WEEKDAY")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-09",
    start_time="18:00",
    end_time="19:00"
)

print(result)


# ============================================================
# TEST 3 — WEEKEND SURCHARGE
# ============================================================

print("\n")
print("=" * 50)
print("TEST 3 — WEEKEND SURCHARGE")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-12",
    start_time="10:00",
    end_time="11:00"
)

print(result)


# ============================================================
# TEST 4 — ACTIVE MEMBERSHIP
# ============================================================

print("\n")
print("=" * 50)
print("TEST 4 — ACTIVE MEMBERSHIP")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-09",
    start_time="10:00",
    end_time="11:00",
    customer_id=TEST_CUSTOMER_ID
)

print(result)


# ============================================================
# TEST 5 — EQUIPMENT RENTAL
# ============================================================

print("\n")
print("=" * 50)
print("TEST 5 — EQUIPMENT RENTAL")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-09",
    start_time="10:00",
    end_time="11:00",
    equipment_items=[
        {
            "equipment_id": TEST_EQUIPMENT_ID,
            "quantity": 2
        }
    ]
)

print(result)


# ============================================================
# TEST 6 — COMBINED PRICING
# ============================================================

print("\n")
print("=" * 50)
print("TEST 6 — COMBINED PRICING")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-09",
    start_time="18:00",
    end_time="19:00",
    customer_id=TEST_CUSTOMER_ID,
    equipment_items=[
        {
            "equipment_id": TEST_EQUIPMENT_ID,
            "quantity": 2
        }
    ]
)

print(result)


# ============================================================
# TEST 7 — NO MEMBERSHIP
# ============================================================

print("\n")
print("=" * 50)
print("TEST 7 — NO MEMBERSHIP")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-09",
    start_time="10:00",
    end_time="11:00",
    customer_id="CUSTOMER_WITHOUT_MEMBERSHIP"
)

print(result)


# ============================================================
# TEST 8 — INVALID RESOURCE
# ============================================================

print("\n")
print("=" * 50)
print("TEST 8 — INVALID RESOURCE")
print("=" * 50)

result = calculate_price(
    resource_id="XYZ999",
    booking_date="2026-09-09",
    start_time="10:00",
    end_time="11:00"
)

print(result)


# ============================================================
# TEST 9 — INVALID TIME
# ============================================================

print("\n")
print("=" * 50)
print("TEST 9 — INVALID TIME")
print("=" * 50)

result = calculate_price(
    resource_id="BC1",
    booking_date="2026-09-09",
    start_time="invalid",
    end_time="11:00"
)

print(result)


# ============================================================
# CLEANUP TEST DATA
# ============================================================

db.equipment.delete_one({
    "_id": TEST_EQUIPMENT_ID
})

db.memberships.delete_one({
    "_id": "TEST_MEMBERSHIP_PRICING"
})

print("\n")
print("=" * 50)
print("TEST DATA CLEANED UP")
print("=" * 50)