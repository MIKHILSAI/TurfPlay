from backend.services.availability_service import (
    check_availability
)
from backend.database.mongodb import db



# ============================================================
# TEST 1 — AVAILABLE SLOT
# ============================================================

print("\n")
print("==================================================")
print("TEST 1 — AVAILABLE SLOT")
print("==================================================")


result = check_availability(
    resource_id="BC1",
    booking_date="2026-09-20",
    start_time="10:00",
    end_time="11:00"
)


print(result)


# ============================================================
# TEST 2 — USING DURATION
# ============================================================

print("\n")
print("==================================================")
print("TEST 2 — USING DURATION")
print("==================================================")


result = check_availability(
    resource_id="BC1",
    booking_date="2026-09-20",
    start_time="12:00",
    duration_mins=60
)


print(result)


# ============================================================
# TEST 3 — OUTSIDE OPENING HOURS
# ============================================================

print("\n")
print("==================================================")
print("TEST 3 — OUTSIDE OPENING HOURS")
print("==================================================")


result = check_availability(
    resource_id="BC1",
    booking_date="2026-09-20",
    start_time="05:00",
    end_time="06:00"
)


print(result)


# ============================================================
# TEST 4 — RESOURCE DOES NOT EXIST
# ============================================================

print("\n")
print("==================================================")
print("TEST 4 — RESOURCE DOES NOT EXIST")
print("==================================================")


result = check_availability(
    resource_id="XYZ999",
    booking_date="2026-09-20",
    start_time="10:00",
    end_time="11:00"
)


print(result)


# ============================================================
# TEST 5 — RESOURCE INACTIVE
# ============================================================

print("\n")
print("=" * 50)
print("TEST 5 — RESOURCE INACTIVE")
print("=" * 50)

# Create a temporary inactive resource
db.resources.update_one(
    {"_id": "TEST_INACTIVE"},
    {
        "$set": {
            "_id": "TEST_INACTIVE",
            "name": "Test Inactive Court",
            "type": "badminton",
            "capacity": 4,
            "hourly_rate": 300,
            "open_time": "06:00",
            "close_time": "22:00",
            "active": False
        }
    },
    upsert=True
)

result = check_availability(
    resource_id="TEST_INACTIVE",
    booking_date="2026-09-20",
    start_time="10:00",
    end_time="11:00"
)

print(result)

# Remove temporary test resource
db.resources.delete_one(
    {"_id": "TEST_INACTIVE"}
)

# ============================================================
# TEST 6 — INVALID TIME
# ============================================================

print("\n")
print("==================================================")
print("TEST 6 — INVALID TIME")
print("==================================================")


result = check_availability(
    resource_id="BC1",
    booking_date="2026-09-20",
    start_time="abc",
    end_time="11:00"
)


print(result)


# ============================================================
# TEST 7 — START AFTER END
# ============================================================

print("\n")
print("==================================================")
print("TEST 7 — START AFTER END")
print("==================================================")


result = check_availability(
    resource_id="BC1",
    booking_date="2026-09-20",
    start_time="18:00",
    end_time="17:00"
)


print(result)


# ============================================================
# TEST 8 — INVALID DURATION
# ============================================================

print("\n")
print("==================================================")
print("TEST 8 — INVALID DURATION")
print("==================================================")


result = check_availability(
    resource_id="BC1",
    booking_date="2026-09-20",
    start_time="10:00",
    duration_mins=0
)


print(result)