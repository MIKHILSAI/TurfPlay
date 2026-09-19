from backend.database.mongodb import db

from backend.services.membership_service import (
    get_membership_plans,
    get_customer_membership,
    check_active_membership,
    create_membership,
    cancel_membership,
)


# ============================================================
# TEST DATA
# ============================================================

TEST_CUSTOMER_ID = "TEST_CUST_MEMBERSHIP_001"


# ============================================================
# HELPER
# ============================================================

def print_step(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


# ============================================================
# TESTS
# ============================================================

def run_tests():

    # --------------------------------------------------------
    # CLEAN OLD TEST DATA
    # --------------------------------------------------------

    db.memberships.delete_many({
        "customer_id": TEST_CUSTOMER_ID
    })

    db.customers.delete_many({
        "_id": TEST_CUSTOMER_ID
    })

    # --------------------------------------------------------
    # CREATE TEST CUSTOMER
    # --------------------------------------------------------

    print_step("SETUP — CREATE TEST CUSTOMER")

    db.customers.insert_one({
        "_id": TEST_CUSTOMER_ID,
        "name": "Membership Test Customer",
        "email": "membership_test@example.com",
        "phone": "+919999999999",
        "status": "active",
    })

    print("Test customer created.")

    # --------------------------------------------------------
    # TEST 1 — GET MEMBERSHIP PLANS
    # --------------------------------------------------------

    print_step("TEST 1 — GET MEMBERSHIP PLANS")

    result = get_membership_plans()

    print(result)

    assert result["success"] is True
    assert "plans" in result

    plan_types = [plan["type"] for plan in result["plans"]]

    assert "monthly" in plan_types
    assert "annual" in plan_types

    # --------------------------------------------------------
    # TEST 2 — CHECK MEMBERSHIP BEFORE CREATION
    # --------------------------------------------------------

    print_step("TEST 2 — CHECK MEMBERSHIP BEFORE CREATION")

    result = check_active_membership(
        TEST_CUSTOMER_ID
    )

    print(result)

    assert result["success"] is True
    assert result["active"] is False

    # --------------------------------------------------------
    # TEST 3 — CREATE MONTHLY MEMBERSHIP
    # --------------------------------------------------------

    print_step("TEST 3 — CREATE MONTHLY MEMBERSHIP")

    result = create_membership(
        TEST_CUSTOMER_ID,
        "monthly"
    )

    print(result)

    assert result["success"] is True
    assert result["membership"]["type"] == "monthly"
    assert result["membership"]["status"] == "active"
    assert result["membership"]["price"] == 1500
    assert result["membership"]["discount_percent"] == 15

    membership_id = result["membership"]["_id"]

    # --------------------------------------------------------
    # TEST 4 — GET CUSTOMER MEMBERSHIP
    # --------------------------------------------------------

    print_step("TEST 4 — GET CUSTOMER MEMBERSHIP")

    result = get_customer_membership(
        TEST_CUSTOMER_ID
    )

    print(result)

    assert result["success"] is True
    assert result["membership"]["_id"] == membership_id

    # --------------------------------------------------------
    # TEST 5 — CHECK ACTIVE MEMBERSHIP
    # --------------------------------------------------------

    print_step("TEST 5 — CHECK ACTIVE MEMBERSHIP")

    result = check_active_membership(
        TEST_CUSTOMER_ID
    )

    print(result)

    assert result["success"] is True
    assert result["active"] is True
    assert result["membership"]["_id"] == membership_id

    # --------------------------------------------------------
    # TEST 6 — PREVENT DUPLICATE ACTIVE MEMBERSHIP
    # --------------------------------------------------------

    print_step("TEST 6 — DUPLICATE ACTIVE MEMBERSHIP")

    result = create_membership(
        TEST_CUSTOMER_ID,
        "monthly"
    )

    print(result)

    assert result["success"] is False
    assert result["error_code"] == "INVALID_MEMBERSHIP"

    # --------------------------------------------------------
    # TEST 7 — INVALID MEMBERSHIP TYPE
    # --------------------------------------------------------

    print_step("TEST 7 — INVALID MEMBERSHIP TYPE")

    # First cancel the current membership so
    # the validation reaches membership type.

    cancel_result = cancel_membership(
        TEST_CUSTOMER_ID
    )

    print("Membership cancelled:")
    print(cancel_result)

    result = create_membership(
        TEST_CUSTOMER_ID,
        "invalid_plan"
    )

    print(result)

    assert result["success"] is False
    assert result["error_code"] == "INVALID_MEMBERSHIP"

    # --------------------------------------------------------
    # TEST 8 — CREATE ANNUAL MEMBERSHIP
    # --------------------------------------------------------

    print_step("TEST 8 — CREATE ANNUAL MEMBERSHIP")

    result = create_membership(
        TEST_CUSTOMER_ID,
        "annual"
    )

    print(result)

    assert result["success"] is True
    assert result["membership"]["type"] == "annual"
    assert result["membership"]["status"] == "active"
    assert result["membership"]["price"] == 15000
    assert result["membership"]["discount_percent"] == 15

    # --------------------------------------------------------
    # TEST 9 — CANCEL MEMBERSHIP
    # --------------------------------------------------------

    print_step("TEST 9 — CANCEL MEMBERSHIP")

    result = cancel_membership(
        TEST_CUSTOMER_ID
    )

    print(result)

    assert result["success"] is True
    assert result["status"] == "cancelled"

    # --------------------------------------------------------
    # TEST 10 — VERIFY MEMBERSHIP IS NOT ACTIVE
    # --------------------------------------------------------

    print_step("TEST 10 — VERIFY MEMBERSHIP AFTER CANCELLATION")

    result = check_active_membership(
        TEST_CUSTOMER_ID
    )

    print(result)

    assert result["success"] is True
    assert result["active"] is False

    # --------------------------------------------------------
    # CLEANUP
    # --------------------------------------------------------

    print_step("CLEANING TEST DATA")

    db.memberships.delete_many({
        "customer_id": TEST_CUSTOMER_ID
    })

    db.customers.delete_many({
        "_id": TEST_CUSTOMER_ID
    })

    print("TEST DATA CLEANED UP")

    print("\n" + "=" * 50)
    print("ALL MEMBERSHIP TESTS PASSED")
    print("=" * 50)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    run_tests()