from backend.database.mongodb import db
from backend.services.equipment_service import get_booking_equipment
from backend.services.booking_notifier import send_cancellation_email

def get_customer_bookings(session):
    """
    Get all bookings belonging to the logged-in customer.
    """

    customer_id = session.get("customer_id")

    if not customer_id:
        return {
            "success": False,
            "error_code": "AUTH_REQUIRED",
            "message": "Customer is not logged in."
        }

    bookings = list(
        db.bookings.find(
            {"customer_id": customer_id},
            {"_id": 0}
        ).sort("booking_date", 1)
    )

    return {
        "success": True,
        "customer_id": customer_id,
        "count": len(bookings),
        "bookings": bookings
    }


def get_customer_equipment(session):
    """
    Get all equipment rented/reserved by the logged-in customer.

    The customer does not need to provide a booking ID.
    We first find the customer's bookings and then retrieve
    equipment associated with those bookings.
    """

    customer_id = session.get("customer_id")

    if not customer_id:
        return {
            "success": False,
            "error_code": "AUTH_REQUIRED",
            "message": "Customer is not logged in."
        }

    # ---------------------------------------------------------
    # Get customer's bookings
    # ---------------------------------------------------------

    bookings = list(
        db.bookings.find(
            {"customer_id": customer_id},
            {
                "_id": 0,
                "booking_id": 1
            }
        )
    )

    # ---------------------------------------------------------
    # Get equipment for each booking
    # ---------------------------------------------------------

    equipment = []

    for booking in bookings:

        booking_id = booking.get("booking_id")

        if not booking_id:
            continue

        result = get_booking_equipment(booking_id)

        if not result.get("success"):
            continue

        for rental in result.get("equipment", []):

            rental["_id"] = str(rental.get("_id"))

            equipment.append(rental)

    # ---------------------------------------------------------
    # Return result
    # ---------------------------------------------------------

    return {
        "success": True,
        "customer_id": customer_id,
        "count": len(equipment),
        "equipment": equipment
    }