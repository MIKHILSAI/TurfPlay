from backend.services.auth_service import (
    login_customer,
    set_current_customer
)

from backend.agents.booking.booking_confirmation import (
    confirm_and_create_booking,
    print_booking_result
)


# ============================================================
# CONFIGURATION
# ============================================================

EMAIL_OR_PHONE = "reschedule_test_3@example.com"
PASSWORD = "Test@12345"


# ============================================================
# LOGIN
# ============================================================

login_result = login_customer(
    EMAIL_OR_PHONE,
    PASSWORD
)

if not login_result.get("success"):
    print("Login failed:")
    print(login_result.get("message"))
    exit()


customer = login_result["customer"]


# ============================================================
# CREATE APPLICATION SESSION
# ============================================================

session = {}

set_current_customer(
    session,
    customer
)

print()
print("Customer logged in successfully.")
print(f"Customer ID: {customer['id']}")


# ============================================================
# BOOKING DETAILS
# ============================================================

resource_id = "BC1"
booking_date = "2026-09-20"
start_time = "12:00"
end_time = "13:00"


# ============================================================
# CUSTOMER CONFIRMATION
# ============================================================

print()
print("Booking:")
print(f"Resource : {resource_id}")
print(f"Date     : {booking_date}")
print(f"Time     : {start_time} - {end_time}")

confirmation = input(
    "Confirm this booking? (yes/no): "
).strip().lower()


confirmed = confirmation == "yes"


# ============================================================
# CREATE BOOKING
# ============================================================

result = confirm_and_create_booking(
    session=session,
    resource_id=resource_id,
    booking_date=booking_date,
    start_time=start_time,
    end_time=end_time,
    confirmed=confirmed
)


# ============================================================
# DISPLAY RESULT
# ============================================================

print(result)