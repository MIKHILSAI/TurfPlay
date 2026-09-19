from crewai.tools import tool

from backend.services.availability_service import check_availability


# ============================================================
# AVAILABILITY TOOL
# ============================================================

@tool("check_availability")
def check_availability_tool(arguments):
    """
    Check whether a turf or court is available.

    Expected arguments:

    {
        "resource_id": "BC1",
        "booking_date": "2026-09-20",
        "start_time": "10:00",
        "duration_mins": 60
    }
    """

    # --------------------------------------------------------
    # Handle CrewAI dictionary input
    # --------------------------------------------------------

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_INPUT",
            "message": "Availability input must be a dictionary."
        }

    resource_id = arguments.get("resource_id")
    booking_date = arguments.get("booking_date")
    start_time = arguments.get("start_time")
    duration_mins = arguments.get("duration_mins")

    # --------------------------------------------------------
    # Validate required fields
    # --------------------------------------------------------

    if not resource_id:
        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_INPUT",
            "message": "Resource ID is required."
        }

    if not booking_date:
        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_INPUT",
            "message": "Booking date is required."
        }

    if not start_time:
        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_INPUT",
            "message": "Start time is required."
        }

    if duration_mins is None:
        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_INPUT",
            "message": "Duration is required."
        }

    # --------------------------------------------------------
    # Call backend service
    # --------------------------------------------------------

    result = check_availability(
        resource_id=resource_id,
        booking_date=booking_date,
        start_time=start_time,
        duration_mins=duration_mins
    )

    return result