from backend.agents.booking.booking_agent_runner import (
    process_booking_request_with_details
)

from backend.agents.booking.booking_flow import (
    find_available_resources
)

from backend.agents.booking.booking_summary import (
    create_booking_summary
)

from backend.agents.booking.booking_confirmation import (
    confirm_and_create_booking
)
from backend.services.booking_service import (
    get_current_booking_date,
    get_max_advance_booking_days,
)
from backend.services.pricing_service import parse_date


# ============================================================
# STEP 1 — PREPARE BOOKING
# ============================================================

def prepare_booking_request(user_message, session=None):
    """
    Extract booking details and find available resources.

    This function does NOT ask for user input.
    Streamlit will handle selection and confirmation.
    """

    # --------------------------------------------------------
    # Extract booking details
    # --------------------------------------------------------

    details = process_booking_request_with_details(
        user_message
    )

    sport = details.get("sport")
    booking_date = details.get("date")
    start_time = details.get("start_time")
    duration_mins = details.get("duration_mins")

    # --------------------------------------------------------
    # Validate required information
    # --------------------------------------------------------

    missing_fields = []

    if not sport:
        missing_fields.append("sport")

    if not booking_date:
        missing_fields.append("date")

    if not start_time:
        missing_fields.append("start time")

    if not duration_mins:
        missing_fields.append("duration")

    if missing_fields:

        return {
            "success": False,
            "stage": "validation",
            "message": (
                "The following information is required: "
                + ", ".join(missing_fields)
            ),
            "details": details,
            "available_resources": [],
            "summary": None
        }

    customer_id = (session or {}).get("customer_id")
    max_advance_days = get_max_advance_booking_days(customer_id)
    requested_date = parse_date(booking_date)
    if (
        max_advance_days is not None
        and requested_date is not None
        and (requested_date - get_current_booking_date()).days > max_advance_days
    ):
        return {
            "success": False,
            "stage": "advance_booking",
            "error_code": "ADVANCE_BOOKING_LIMIT_EXCEEDED",
            "message": (
                f"Your account can book up to {max_advance_days} days ahead. "
                "Please choose a date within that window."
            ),
            "details": details,
            "available_resources": [],
            "summary": None,
        }

    # --------------------------------------------------------
    # Find available resources
    # --------------------------------------------------------

    availability_result = find_available_resources(
        sport=sport,
        booking_date=booking_date,
        start_time=start_time,
        duration_mins=duration_mins
    )

    if not availability_result.get("success"):

        return {
            "success": False,
            "stage": "availability",
            "message": availability_result.get(
                "message",
                "Unable to check availability."
            ),
            "details": details,
            "available_resources": [],
            "summary": None
        }

    available_resources = availability_result.get(
        "available_resources",
        []
    )

    # --------------------------------------------------------
    # No availability
    # --------------------------------------------------------

    if not available_resources:

        return {
            "success": True,
            "stage": "availability",
            "message": availability_result.get(
                "message",
                "No resources are available."
            ),
            "details": details,
            "available_resources": [],
            "summary": None
        }

    # --------------------------------------------------------
    # Return available resources
    # --------------------------------------------------------

    return {
        "success": True,
        "stage": "selection",
        "message": (
            "Available resources found."
        ),
        "details": details,
        "available_resources": available_resources,
        "summary": None
    }


# ============================================================
# STEP 2 — CREATE BOOKING SUMMARY
# ============================================================

def create_selected_booking_summary(
    details,
    selected_resource
):
    """
    Create the price/booking summary after
    the customer selects a resource.
    """

    sport = details.get("sport")
    booking_date = details.get("date")
    start_time = details.get("start_time")
    duration_mins = details.get("duration_mins")

    resource_id = selected_resource.get(
        "resource_id"
    )

    if not resource_id:

        return {
            "success": False,
            "stage": "selection",
            "message": "Invalid resource selected.",
            "summary": None
        }

    summary_result = create_booking_summary(
        sport=sport,
        booking_date=booking_date,
        start_time=start_time,
        duration_mins=duration_mins,
        resource_id=resource_id
    )

    if not summary_result.get("success"):

        return {
            "success": False,
            "stage": "pricing",
            "message": summary_result.get(
                "message",
                "Unable to create booking summary."
            ),
            "summary": None
        }

    return {
        "success": True,
        "stage": "confirmation",
        "message": "Booking summary created.",
        "summary": summary_result.get("summary")
    }


# ============================================================
# STEP 3 — CONFIRM BOOKING
# ============================================================

def confirm_selected_booking(
    details,
    selected_resource,
    summary,
    session
):
    """
    Create the booking after the customer
    explicitly confirms.
    """

    resource_id = selected_resource.get(
        "resource_id"
    )

    booking = summary.get(
        "booking",
        {}
    )

    booking_date = details.get(
        "date"
    )

    start_time = details.get(
        "start_time"
    )

    end_time = booking.get(
        "end_time"
    )

    # --------------------------------------------------------
    # Final backend validation + booking creation
    # --------------------------------------------------------

    confirmation_result = confirm_and_create_booking(
        session=session,
        resource_id=resource_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        confirmed=True
    )

    return {
        "success": confirmation_result.get(
            "success",
            False
        ),
        "stage": "booking",
        "message": confirmation_result.get(
            "message"
        ),
        "booking": confirmation_result.get(
            "booking"
        )
    }