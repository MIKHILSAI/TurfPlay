from backend.database.mongodb import db

from backend.services.auth_service import (
    register_customer,
    login_customer,
    set_current_customer,
)

from backend.services.booking_service import create_booking

from backend.services.reschedule_service import (
    reschedule_booking_preview,
    reschedule_booking,
)

from backend.services.cancellation_service import cancel_booking


# ============================================================
# CONFIGURATION
# ============================================================

TEST_EMAIL = "reschedule_test_4@example.com"
TEST_PHONE = "+919777777780"
TEST_PASSWORD = "Test@12345"

SECOND_EMAIL = "reschedule_other@example.com"
SECOND_PHONE = "+919666666666"

RESOURCE_ID = "BC1"

# Changed to a fresh date to avoid old test bookings
BOOKING_DATE = "2026-09-24"


# ============================================================
# HELPER
# ============================================================

def print_step(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


# ============================================================
# MAIN TEST
# ============================================================

def run_tests():

    customer_id = None
    second_customer_id = None

    booking_id = None
    occupied_booking_id = None
    cancelled_booking_id = None

    # ========================================================
    # STEP 1 — REGISTER TEST CUSTOMER
    # ========================================================

    print_step("STEP 1 — REGISTER TEST CUSTOMER")

    register_result = register_customer(
        name="Reschedule Test User",
        email=TEST_EMAIL,
        phone=TEST_PHONE,
        password=TEST_PASSWORD,
    )

    print(register_result)

    if not register_result["success"]:
        print("Registration failed.")
        return

    customer_id = register_result["customer_id"]

    # ========================================================
    # STEP 2 — LOGIN
    # ========================================================

    print_step("STEP 2 — LOGIN")

    login_result = login_customer(
        email_or_phone=TEST_EMAIL,
        password=TEST_PASSWORD,
    )

    print(login_result)

    if not login_result["success"]:
        print("Login failed.")
        return

    # --------------------------------------------------------
    # Create session
    # --------------------------------------------------------

    session = {}

    set_current_customer(
        session,
        login_result["customer"]
    )

    print("\nSESSION:")
    print(session)

    # ========================================================
    # STEP 3 — CREATE ORIGINAL BOOKING
    # ========================================================

    print_step("STEP 3 — CREATE ORIGINAL BOOKING")

    booking_result = create_booking(
        session=session,
        resource_id=RESOURCE_ID,
        booking_date=BOOKING_DATE,
        start_time="10:00",
        end_time="11:00",
        equipment_items=None,
    )

    print(booking_result)

    if not booking_result["success"]:
        print("Original booking creation failed.")
        return

    booking_id = booking_result["booking"]["id"]

    print("\nORIGINAL BOOKING ID:")
    print(booking_id)

    # ========================================================
    # TEST 1 — RESCHEDULE PREVIEW
    # ========================================================

    print_step("TEST 1 — RESCHEDULE PREVIEW")

    preview_result = reschedule_booking_preview(
        session=session,
        booking_id=booking_id,
        new_date=BOOKING_DATE,
        new_start_time="12:00",
        new_end_time="13:00",
    )

    print(preview_result)

    # ========================================================
    # TEST 2 — CONFIRMATION REQUIRED
    # ========================================================

    print_step("TEST 2 — RESCHEDULE WITHOUT CONFIRMATION")

    no_confirmation_result = reschedule_booking(
        session=session,
        booking_id=booking_id,
        new_date=BOOKING_DATE,
        new_start_time="12:00",
        new_end_time="13:00",
        confirmed=False,
    )

    print(no_confirmation_result)

    # ========================================================
    # TEST 3 — CONFIRMED RESCHEDULE
    # ========================================================

    print_step("TEST 3 — CONFIRMED RESCHEDULE")

    reschedule_result = reschedule_booking(
        session=session,
        booking_id=booking_id,
        new_date=BOOKING_DATE,
        new_start_time="12:00",
        new_end_time="13:00",
        confirmed=True,
    )

    print(reschedule_result)

    # ========================================================
    # TEST 4 — VERIFY DATABASE RECORD
    # ========================================================

    print_step("TEST 4 — VERIFY RESCHEDULED BOOKING")

    booking = db.bookings.find_one({
        "_id": booking_id
    })

    if booking:

        print({
            "booking_id": booking.get("_id"),
            "booking_date": booking.get("booking_date"),
            "start_time": booking.get("start_time"),
            "end_time": booking.get("end_time"),
            "blocked_end_time": booking.get("blocked_end_time"),
            "status": booking.get("status"),
            "reschedule_count": booking.get("reschedule_count"),
            "reschedule_history": booking.get("reschedule_history"),
            "total_amount": booking.get("total_amount"),
        })

    # ========================================================
    # TEST 5 — SECOND RESCHEDULE
    # ========================================================

    print_step("TEST 5 — SECOND RESCHEDULE SHOULD FAIL")

    second_reschedule_result = reschedule_booking_preview(
        session=session,
        booking_id=booking_id,
        new_date=BOOKING_DATE,
        new_start_time="14:00",
        new_end_time="15:00",
    )

    print(second_reschedule_result)

    # ========================================================
    # STEP 6 — CREATE BOOKING FOR UNAVAILABLE SLOT
    # ========================================================

    print_step("STEP 6 — CREATE BOOKING FOR UNAVAILABLE SLOT")

    occupied_booking_result = create_booking(
        session=session,
        resource_id=RESOURCE_ID,
        booking_date=BOOKING_DATE,
        start_time="16:00",
        end_time="17:00",
        equipment_items=None,
    )

    print(occupied_booking_result)

    if occupied_booking_result["success"]:

        occupied_booking_id = occupied_booking_result["booking"]["id"]

    # ========================================================
    # TEST 6 — UNAVAILABLE SLOT
    # ========================================================

    print_step("TEST 6 — RESCHEDULE TO UNAVAILABLE SLOT")

    if occupied_booking_id:

        unavailable_result = reschedule_booking_preview(
            session=session,
            booking_id=occupied_booking_id,
            new_date=BOOKING_DATE,
            new_start_time="16:00",
            new_end_time="17:00",
        )

        print(unavailable_result)

    # ========================================================
    # STEP 7 — REGISTER SECOND CUSTOMER
    # ========================================================

    print_step("STEP 7 — REGISTER SECOND CUSTOMER")

    second_register = register_customer(
        name="Another Customer",
        email=SECOND_EMAIL,
        phone=SECOND_PHONE,
        password=TEST_PASSWORD,
    )

    print(second_register)

    if second_register["success"]:

        second_customer_id = second_register["customer_id"]

    # ========================================================
    # TEST 7 — UNAUTHORIZED ACCESS
    # ========================================================

    print_step("TEST 7 — UNAUTHORIZED RESCHEDULE")

    if second_customer_id:

        second_login_result = login_customer(
            email_or_phone=SECOND_EMAIL,
            password=TEST_PASSWORD,
        )

        print("\nSECOND LOGIN:")
        print(second_login_result)

        second_session = {}

        if second_login_result["success"]:

            set_current_customer(
                second_session,
                second_login_result["customer"]
            )

            unauthorized_result = reschedule_booking_preview(
                session=second_session,
                booking_id=booking_id,
                new_date=BOOKING_DATE,
                new_start_time="18:00",
                new_end_time="19:00",
            )

            print(unauthorized_result)

    # ========================================================
    # STEP 8 — CREATE BOOKING FOR CANCELLED BOOKING TEST
    # ========================================================

    print_step("STEP 8 — CREATE BOOKING FOR CANCELLED BOOKING TEST")

    cancelled_booking_result = create_booking(
        session=session,
        resource_id=RESOURCE_ID,
        booking_date=BOOKING_DATE,
        start_time="19:00",
        end_time="20:00",
        equipment_items=None,
    )

    print(cancelled_booking_result)

    if cancelled_booking_result["success"]:

        cancelled_booking_id = (
            cancelled_booking_result["booking"]["id"]
        )

    # ========================================================
    # CANCEL BOOKING
    # ========================================================

    if cancelled_booking_id:

        print_step("CANCEL TEST BOOKING")

        cancel_result = cancel_booking(
            session=session,
            booking_id=cancelled_booking_id,
            confirmed=True,
            reason="Testing reschedule of cancelled booking",
        )

        print(cancel_result)

    # ========================================================
    # TEST 8 — RESCHEDULE CANCELLED BOOKING
    # ========================================================

    print_step("TEST 8 — RESCHEDULE CANCELLED BOOKING")

    if cancelled_booking_id:

        cancelled_reschedule_result = (
            reschedule_booking_preview(
                session=session,
                booking_id=cancelled_booking_id,
                new_date=BOOKING_DATE,
                new_start_time="20:00",
                new_end_time="21:00",
            )
        )

        print(cancelled_reschedule_result)

    # ========================================================
    # CLEANUP
    # ========================================================

    print_step("CLEANING TEST DATA")

    customer_ids = []

    if customer_id:
        customer_ids.append(customer_id)

    if second_customer_id:
        customer_ids.append(second_customer_id)

    if customer_ids:

        db.bookings.delete_many({
            "customer_id": {
                "$in": customer_ids
            }
        })

        db.customers.delete_many({
            "_id": {
                "$in": customer_ids
            }
        })

    booking_ids = []

    if booking_id:
        booking_ids.append(booking_id)

    if occupied_booking_id:
        booking_ids.append(occupied_booking_id)

    if cancelled_booking_id:
        booking_ids.append(cancelled_booking_id)

    if booking_ids:

        db.audit_events.delete_many({
            "entity_id": {
                "$in": booking_ids
            }
        })

    print("TEST DATA CLEANED UP")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    run_tests()