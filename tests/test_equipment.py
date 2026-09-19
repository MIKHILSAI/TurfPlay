from backend.database.mongodb import db

from backend.services.equipment_service import (
    get_equipment,
    get_available_equipment,
    check_equipment_availability,
    calculate_rental_amount,
    reserve_equipment,
    release_equipment,
    get_booking_equipment,
    calculate_booking_equipment_total,
)


# ============================================================
# CONFIGURATION
# ============================================================

EQUIPMENT_ID = "EQ001"

TEST_BOOKING_ID = "TEST_BKG_EQUIPMENT_001"


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

    # ========================================================
    # TEST 1 — GET EQUIPMENT
    # ========================================================

    print_step("TEST 1 — GET EQUIPMENT")

    result = get_equipment(EQUIPMENT_ID)

    print(result)

    # ========================================================
    # TEST 2 — GET AVAILABLE EQUIPMENT
    # ========================================================

    print_step("TEST 2 — GET AVAILABLE EQUIPMENT")

    result = get_available_equipment()

    print(result)

    # ========================================================
    # TEST 3 — CHECK AVAILABILITY
    # ========================================================

    print_step("TEST 3 — CHECK EQUIPMENT AVAILABILITY")

    result = check_equipment_availability(
        equipment_id=EQUIPMENT_ID,
        quantity=2,
    )

    print(result)

    # ========================================================
    # TEST 4 — INVALID QUANTITY
    # ========================================================

    print_step("TEST 4 — INVALID QUANTITY")

    result = check_equipment_availability(
        equipment_id=EQUIPMENT_ID,
        quantity=0,
    )

    print(result)

    # ========================================================
    # TEST 5 — EXCESSIVE QUANTITY
    # ========================================================

    print_step("TEST 5 — EXCESSIVE QUANTITY")

    result = check_equipment_availability(
        equipment_id=EQUIPMENT_ID,
        quantity=100,
    )

    print(result)

    # ========================================================
    # TEST 6 — CALCULATE RENTAL
    # ========================================================

    print_step("TEST 6 — CALCULATE RENTAL AMOUNT")

    result = calculate_rental_amount(
        equipment_id=EQUIPMENT_ID,
        quantity=2,
    )

    print(result)

    # ========================================================
    # TEST 7 — RESERVE EQUIPMENT
    # ========================================================

    print_step("TEST 7 — RESERVE EQUIPMENT")

    result = reserve_equipment(
        booking_id=TEST_BOOKING_ID,
        equipment_id=EQUIPMENT_ID,
        quantity=2,
    )

    print(result)

    # ========================================================
    # TEST 8 — CHECK RESERVED QUANTITY
    # ========================================================

    print_step("TEST 8 — CHECK RESERVED QUANTITY")

    result = check_equipment_availability(
        equipment_id=EQUIPMENT_ID,
        quantity=9,
    )

    print(result)

    # ========================================================
    # TEST 9 — DUPLICATE RESERVATION
    # ========================================================

    print_step("TEST 9 — DUPLICATE RESERVATION")

    result = reserve_equipment(
        booking_id=TEST_BOOKING_ID,
        equipment_id=EQUIPMENT_ID,
        quantity=1,
    )

    print(result)

    # ========================================================
    # TEST 10 — GET BOOKING EQUIPMENT
    # ========================================================

    print_step("TEST 10 — GET BOOKING EQUIPMENT")

    result = get_booking_equipment(
        TEST_BOOKING_ID
    )

    print(result)

    # ========================================================
    # TEST 11 — CALCULATE BOOKING EQUIPMENT TOTAL
    # ========================================================

    print_step("TEST 11 — CALCULATE BOOKING EQUIPMENT TOTAL")

    result = calculate_booking_equipment_total(
        TEST_BOOKING_ID
    )

    print(result)

    # ========================================================
    # TEST 12 — RELEASE EQUIPMENT
    # ========================================================

    print_step("TEST 12 — RELEASE EQUIPMENT")

    result = release_equipment(
        TEST_BOOKING_ID
    )

    print(result)

    # ========================================================
    # TEST 13 — VERIFY RELEASE
    # ========================================================

    print_step("TEST 13 — VERIFY RELEASE")

    result = get_booking_equipment(
        TEST_BOOKING_ID
    )

    print(result)

    # ========================================================
    # CLEANUP
    # ========================================================

    print_step("CLEANING TEST DATA")

    db.equipment_rentals.delete_many({
        "booking_id": TEST_BOOKING_ID
    })

    print("TEST DATA CLEANED UP")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    run_tests()