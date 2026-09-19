from backend.agents.equipment.equipment_agent_runner import (
    process_equipment_request_with_details
)
from backend.services.booking_notifier import send_equipment_confirmation
from backend.services.equipment_service import (
    get_available_equipment,
    check_equipment_availability,
    calculate_rental_amount,
    reserve_equipment,
    release_equipment,
    get_booking_equipment,
    calculate_booking_equipment_total,
)


# ============================================================
# FIND EQUIPMENT
# ============================================================

def find_equipment(equipment_name=None):
    """
    Find active equipment matching the requested name.

    If equipment_name is provided, return matching equipment.
    Otherwise return all active equipment.
    """

    result = get_available_equipment()

    if not result.get("success"):
        return result

    equipment_list = result.get("equipment", [])

    if not equipment_name:
        return {
            "success": True,
            "equipment": equipment_list
        }

    search_name = equipment_name.strip().lower()

    matches = []

    for equipment in equipment_list:

        name = str(
            equipment.get("name", "")
        ).lower()

        if search_name in name or name in search_name:
            matches.append(equipment)

    if not matches:
        return {
            "success": False,
            "error_code": "EQUIPMENT_NOT_FOUND",
            "message": (
                f"No active equipment found for "
                f"'{equipment_name}'."
            )
        }

    return {
        "success": True,
        "equipment": matches
    }


# ============================================================
# PROCESS EQUIPMENT REQUEST
# ============================================================

def process_equipment_request_flow(user_message, session=None):
    """
    Run the Equipment Agent and process the
    extracted equipment information.
    """

    # --------------------------------------------------------
    # STEP 1: Understand the request using the agent
    # --------------------------------------------------------

    details = process_equipment_request_with_details(
        user_message
    )

    action = details.get("action")
    equipment_name = details.get("equipment")
    quantity = details.get("quantity")
    booking_id = None

    # --------------------------------------------------------
    # STEP 2: Validate action
    # --------------------------------------------------------

    valid_actions = [
        "rent",
        "reserve",
        "return",
        "info"
    ]

    if action not in valid_actions:
        return {
            "success": False,
            "error_code": "INVALID_EQUIPMENT_ACTION",
            "message": "Unable to understand the equipment action.",
            "details": details
        }

    # --------------------------------------------------------
    # STEP 3: Information request
    # --------------------------------------------------------

    if action == "info":

        result = find_equipment(
            equipment_name
        )

        return {
            "success": result.get("success", False),
            "action": action,
            "details": details,
            "equipment": result.get("equipment", []),
            "message": result.get(
                "message",
                "Equipment information retrieved."
            )
        }

    # --------------------------------------------------------
    # STEP 4: Return request
    # --------------------------------------------------------

    if action == "return":

        booking_id = input(
            "Enter Booking ID: "
        ).strip()

        if not booking_id:
            return {
                "success": False,
                "error_code": "INVALID_BOOKING",
                "message": "Booking ID is required.",
                "details": details
            }

        result = release_equipment(
            booking_id
        )

        return {
            "success": result.get("success", False),
            "action": action,
            "details": details,
            "result": result,
            "message": result.get("message")
        }

    # --------------------------------------------------------
    # STEP 5: Validate quantity
    # --------------------------------------------------------

    if quantity is None:
        return {
            "success": False,
            "error_code": "QUANTITY_REQUIRED",
            "message": "Equipment quantity is required.",
            "details": details
        }

    # --------------------------------------------------------
    # STEP 6: Find equipment
    # --------------------------------------------------------

    equipment_result = find_equipment(
        equipment_name
    )

    if not equipment_result.get("success"):
        return {
            "success": False,
            "error_code": equipment_result.get(
                "error_code",
                "EQUIPMENT_NOT_FOUND"
            ),
            "message": equipment_result.get(
                "message",
                "Equipment was not found."
            ),
            "details": details
        }

    equipment_list = equipment_result.get(
        "equipment",
        []
    )

    # --------------------------------------------------------
    # STEP 7: Select equipment
    # --------------------------------------------------------

    if len(equipment_list) == 1:

        equipment = equipment_list[0]

    else:

        print()
        print("Available Equipment:")
        print("-" * 60)

        for index, item in enumerate(
            equipment_list,
            start=1
        ):

            print(
                f"{index}. "
                f"{item.get('name')} "
                f"(ID: {item.get('_id')})"
            )

        print()

        try:
            selection = int(
                input("Select equipment: ").strip()
            )

            if selection < 1 or selection > len(
                equipment_list
            ):
                return {
                    "success": False,
                    "error_code": "INVALID_SELECTION",
                    "message": "Invalid equipment selection.",
                    "details": details
                }

            equipment = equipment_list[
                selection - 1
            ]

        except ValueError:

            return {
                "success": False,
                "error_code": "INVALID_SELECTION",
                "message": "Please enter a valid number.",
                "details": details
            }

    equipment_id = equipment.get("_id")

    # --------------------------------------------------------
    # STEP 8: Check availability
    # --------------------------------------------------------

    availability = check_equipment_availability(
        equipment_id,
        quantity
    )

    if not availability.get("success"):

        return {
            "success": False,
            "error_code": availability.get(
                "error_code",
                "EQUIPMENT_UNAVAILABLE"
            ),
            "message": availability.get(
                "message",
                "Equipment is unavailable."
            ),
            "details": details
        }

    # --------------------------------------------------------
    # STEP 9: Calculate rental amount
    # --------------------------------------------------------

    calculation = calculate_rental_amount(
        equipment_id,
        quantity
    )

    if not calculation.get("success"):

        return {
            "success": False,
            "error_code": calculation.get(
                "error_code",
                "EQUIPMENT_PRICING_FAILED"
            ),
            "message": calculation.get(
                "message",
                "Unable to calculate equipment price."
            ),
            "details": details
        }

    # --------------------------------------------------------
    # STEP 10: Ask for booking ID
    # --------------------------------------------------------

    print()
    print("Equipment Rental Summary")
    print("-" * 60)
    print(
        f"Equipment : "
        f"{calculation.get('equipment_name')}"
    )
    print(
        f"Quantity  : "
        f"{calculation.get('quantity')}"
    )
    print(
        f"Rental    : "
        f"₹{calculation.get('rental_amount', 0):.2f}"
    )
    print(
        f"Deposit   : "
        f"₹{calculation.get('deposit_amount', 0):.2f}"
    )
    print(
        f"Total     : "
        f"₹{calculation.get('total_amount', 0):.2f}"
    )
    print("-" * 60)

    booking_id = input(
        "Enter Booking ID for this equipment: "
    ).strip()

    if not booking_id:

        return {
            "success": False,
            "error_code": "INVALID_BOOKING",
            "message": (
                "A booking ID is required to reserve equipment."
            ),
            "details": details
        }

    # --------------------------------------------------------
    # STEP 11: Confirmation
    # --------------------------------------------------------

    confirmation = input(
        "Confirm equipment reservation? (yes/no): "
    ).strip().lower()

    if confirmation not in ["yes", "y"]:

        return {
            "success": False,
            "error_code": "EQUIPMENT_NOT_CONFIRMED",
            "message": (
                "Equipment reservation was not confirmed."
            ),
            "details": details
        }

    # --------------------------------------------------------
    # STEP 12: Final backend reservation
    # --------------------------------------------------------

    reservation = reserve_equipment(
        booking_id=booking_id,
        equipment_id=equipment_id,
        quantity=quantity
    )

    if not reservation.get("success"):

        return {
            "success": False,
            "error_code": reservation.get(
                "error_code",
                "EQUIPMENT_RESERVATION_FAILED"
            ),
            "message": reservation.get(
                "message",
                "Unable to reserve equipment."
            ),
            "details": details
        }

    # --------------------------------------------------------
    # STEP 13: Success
    # --------------------------------------------------------

    rental = reservation.get("rental")

    # --------------------------------------------------------
    # Send equipment confirmation email (non-blocking)
    # --------------------------------------------------------

    try:
        customer_id = session.get("customer_id") if session else None

        if customer_id and rental:
            email_result = send_equipment_confirmation(
                customer_id=customer_id,
                booking_id=booking_id,
                rental=rental
            )

            if not email_result.get("sent"):
                print(
                    f"[EMAIL] Equipment confirmation failed: "
                    f"{email_result.get('error')}"
                )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return {
        "success": True,
        "action": action,
        "message": "Equipment reserved successfully.",
        "details": details,
        "equipment": equipment,
        "calculation": calculation,
        "reservation": rental
    }

# ============================================================
# CLI TEST
# ============================================================

def main():

    print("=" * 60)
    print("TURF BOOKING - EQUIPMENT PROCESS")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":

            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            result = process_equipment_request_flow(
                user_message
            )

            print()
            print("Result:")
            print(result)
            print()

        except KeyboardInterrupt:

            print()
            print("Stopped by user.")
            break

        except Exception as e:

            print()
            print(f"Error: {e}")
            print()


if __name__ == "__main__":
    main()