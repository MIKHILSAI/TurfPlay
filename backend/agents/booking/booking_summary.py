from backend.agents.booking.booking_flow import find_available_resources
from backend.services.pricing_service import calculate_price


def create_booking_summary(
    sport,
    booking_date,
    start_time,
    duration_mins,
    resource_id
):
    """
    Create a booking summary after availability and pricing checks.

    This function does NOT create the booking.
    """

    # ============================================================
    # 1. Find available resources
    # ============================================================

    availability_result = find_available_resources(
        sport=sport,
        booking_date=booking_date,
        start_time=start_time,
        duration_mins=duration_mins
    )

    if not availability_result.get("success"):
        return availability_result

    available_resources = availability_result.get(
        "available_resources",
        []
    )

    # ============================================================
    # 2. Check whether selected resource is available
    # ============================================================

    selected_resource = None

    for resource in available_resources:
        if resource["resource_id"] == resource_id:
            selected_resource = resource
            break

    if not selected_resource:
        return {
            "success": False,
            "error_code": "RESOURCE_NOT_AVAILABLE",
            "message": (
                f"Resource '{resource_id}' is not available "
                "for the requested time."
            )
        }

    # ============================================================
    # 3. Calculate end time
    # ============================================================

    booking_details = selected_resource["booking"]

    end_time = booking_details["end_time"]

    # ============================================================
    # 4. Calculate price
    # ============================================================

    pricing_result = calculate_price(
        resource_id=resource_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        customer_id=None,
        equipment_items=[]
    )

    if not pricing_result.get("success"):
        return {
            "success": False,
            "error_code": "PRICING_FAILED",
            "message": pricing_result.get(
                "message",
                "Unable to calculate booking price."
            )
        }

    # ============================================================
    # 5. Build booking summary
    # ============================================================

    pricing = pricing_result["pricing"]

    summary = {
        "sport": sport,
        "resource": {
            "resource_id": selected_resource["resource_id"],
            "name": selected_resource["name"],
            "type": selected_resource["type"]
        },
        "booking": {
            "date": booking_date,
            "start_time": start_time,
            "end_time": end_time,
            "duration_mins": duration_mins
        },
        "pricing": {
            "base_amount": pricing["base_amount"],
            "peak_surcharge": pricing["peak_surcharge"],
            "weekend_surcharge": pricing["weekend_surcharge"],
            "discount_amount": pricing["discount_amount"],
            "equipment_amount": pricing["equipment_amount"],
            "deposit_amount": pricing["deposit_amount"],
            "total_amount": pricing["total_amount"]
        },
        "confirmation_required": True
    }

    return {
        "success": True,
        "message": "Booking summary created successfully.",
        "summary": summary
    }


def print_booking_summary(result):
    """
    Display the booking summary in a user-friendly format.
    """

    if not result.get("success"):
        print()
        print("Booking Summary Error:")
        print(result.get("message"))
        return

    summary = result["summary"]

    print()
    print("=" * 50)
    print("BOOKING SUMMARY")
    print("=" * 50)

    print(f"Sport       : {summary['sport']}")
    print(
        f"Court/Turf  : "
        f"{summary['resource']['name']}"
    )
    print(
        f"Resource ID : "
        f"{summary['resource']['resource_id']}"
    )

    print()

    print(f"Date        : {summary['booking']['date']}")
    print(
        f"Time        : "
        f"{summary['booking']['start_time']} - "
        f"{summary['booking']['end_time']}"
    )
    print(
        f"Duration    : "
        f"{summary['booking']['duration_mins']} minutes"
    )

    print()

    print("PRICE")
    print("-" * 50)

    print(
        f"Base Amount       : "
        f"₹{summary['pricing']['base_amount']:.2f}"
    )

    print(
        f"Peak Surcharge    : "
        f"₹{summary['pricing']['peak_surcharge']:.2f}"
    )

    print(
        f"Weekend Surcharge : "
        f"₹{summary['pricing']['weekend_surcharge']:.2f}"
    )

    print(
        f"Discount          : "
        f"-₹{summary['pricing']['discount_amount']:.2f}"
    )

    print(
        f"Equipment         : "
        f"₹{summary['pricing']['equipment_amount']:.2f}"
    )

    print(
        f"Deposit           : "
        f"₹{summary['pricing']['deposit_amount']:.2f}"
    )

    print("-" * 50)

    print(
        f"TOTAL             : "
        f"₹{summary['pricing']['total_amount']:.2f}"
    )

    print("=" * 50)

    print()
    print("Confirmation required: YES")