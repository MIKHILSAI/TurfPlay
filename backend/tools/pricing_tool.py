from crewai.tools import tool

from backend.services.pricing_service import calculate_price


# ============================================================
# PRICING TOOL
# ============================================================

@tool("calculate_booking_price")
def calculate_booking_price_tool(arguments):
    """
    Calculate the complete booking price.

    The backend pricing service is responsible for:
    - base facility price
    - peak surcharge
    - weekend surcharge
    - membership discount
    - equipment rental
    - equipment deposit
    - final total

    The backend is the source of truth for pricing.

    Expected input:

    {
        "resource_id": "BC1",
        "booking_date": "2026-09-20",
        "start_time": "10:00",
        "end_time": "11:00",
        "customer_id": null,
        "equipment_items": []
    }

    This tool calculates price only.
    It does NOT create a booking.
    """

    # --------------------------------------------------------
    # Handle CrewAI dictionary input
    # --------------------------------------------------------

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "error_code": "INVALID_INPUT",
            "message": "Pricing input must be a dictionary."
        }

    resource_id = arguments.get("resource_id")
    booking_date = arguments.get("booking_date")
    start_time = arguments.get("start_time")
    end_time = arguments.get("end_time")
    customer_id = arguments.get("customer_id")
    equipment_items = arguments.get(
        "equipment_items",
        []
    )

    # --------------------------------------------------------
    # Validate required fields
    # --------------------------------------------------------

    if not resource_id:
        return {
            "success": False,
            "error_code": "INVALID_INPUT",
            "message": "Resource ID is required."
        }

    if not booking_date:
        return {
            "success": False,
            "error_code": "INVALID_INPUT",
            "message": "Booking date is required."
        }

    if not start_time:
        return {
            "success": False,
            "error_code": "INVALID_INPUT",
            "message": "Start time is required."
        }

    if not end_time:
        return {
            "success": False,
            "error_code": "INVALID_INPUT",
            "message": "End time is required."
        }

    # --------------------------------------------------------
    # Calculate price using backend service
    # --------------------------------------------------------

    result = calculate_price(
        resource_id=resource_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        customer_id=customer_id,
        equipment_items=equipment_items
    )

    return result