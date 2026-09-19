from backend.services.resource_service import get_available_resources
from backend.services.availability_service import check_availability


# ============================================================
# BOOKING FLOW
# ============================================================

def find_available_resources(
    sport,
    booking_date,
    start_time,
    duration_mins
):
    """
    Find all active resources for the requested sport
    and check which ones are available.

    This function does NOT create a booking.
    """

    # --------------------------------------------------------
    # 1. Find resources for the requested sport
    # --------------------------------------------------------

    resources = get_available_resources(
        sport
    )

    if not resources:
        return {
            "success": False,
            "available_resources": [],
            "message": (
                f"No active resources found for "
                f"'{sport}'."
            )
        }

    # --------------------------------------------------------
    # 2. Check availability of every resource
    # --------------------------------------------------------

    available_resources = []

    for resource in resources:

        result = check_availability(
            resource_id=resource["resource_id"],
            booking_date=booking_date,
            start_time=start_time,
            duration_mins=duration_mins
        )

        if result.get("success") and result.get("available"):

            available_resources.append({
                "resource_id": resource["resource_id"],
                "name": resource["name"],
                "type": resource["type"],
                "capacity": resource["capacity"],
                "hourly_rate": resource["hourly_rate"],
                "booking": result["booking"]
            })

    # --------------------------------------------------------
    # 3. No available resources
    # --------------------------------------------------------

    if not available_resources:

        return {
            "success": True,
            "available_resources": [],
            "message": (
                "No resources are available for "
                "the requested time."
            )
        }

    # --------------------------------------------------------
    # 4. Return ALL available resources
    # --------------------------------------------------------

    return {
        "success": True,
        "available_resources": available_resources,
        "message": (
            f"{len(available_resources)} resource(s) "
            "are available."
        )
    }