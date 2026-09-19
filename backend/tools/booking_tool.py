from crewai.tools import tool

from backend.services.booking_service import create_booking
from backend.agents.booking.booking_confirmation import confirm_and_create_booking


# ============================================================
# BOOKING TOOL
# ============================================================

@tool("create_booking")
def create_booking_tool(
    session,
    resource_id,
    booking_date,
    start_time,
    end_time
):
    """
    Create a turf or court booking using the backend
    booking service.

    The backend service is responsible for:
    - authentication
    - resource validation
    - duplicate booking checks
    - availability checks
    - price calculation
    - MongoDB booking creation
    - audit logging
    """

    return confirm_and_create_booking(
        session=session,
        resource_id=resource_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        confirmed=True
    )

    return result
