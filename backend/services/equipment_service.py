from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
from backend.services.booking_notifier import send_equipment_confirmation
from backend.database.mongodb import db


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")

ACTIVE_RENTAL_STATUSES = [
    "pending",
    "confirmed",
    "rescheduled",
]


def equipment_matches_facility_type(equipment_type, facility_type):
    """Match sport-specific equipment to a facility type."""

    normalized_equipment = str(equipment_type or "").strip().lower()
    normalized_facility = str(facility_type or "").strip().lower()
    if normalized_facility in ["multipurpose", "multipurpose room"]:
        return normalized_equipment.startswith("multipurpose_room_")
    return normalized_equipment.split("_", 1)[0] == normalized_facility


# ============================================================
# GET EQUIPMENT
# ============================================================

def get_equipment(equipment_id):
    """
    Get one equipment item by ID.
    """

    if not equipment_id:
        return {
            "success": False,
            "error_code": "INVALID_EQUIPMENT",
            "message": "Equipment ID is required.",
        }

    equipment = db.equipment.find_one({
        "_id": equipment_id
    })

    if not equipment:
        return {
            "success": False,
            "error_code": "EQUIPMENT_NOT_FOUND",
            "message": "Equipment was not found.",
        }

    return {
        "success": True,
        "equipment": equipment,
    }


# ============================================================
# LIST ACTIVE EQUIPMENT
# ============================================================

def get_available_equipment():
    """
    Return all active equipment.
    """

    equipment_list = list(
        db.equipment.find({
            "active": True
        })
    )

    for equipment in equipment_list:
        equipment["quantity_available"] = get_live_available_quantity(
            equipment.get("_id"),
        )

    return {
        "success": True,
        "equipment": equipment_list,
    }


# ============================================================
# GET RESERVED QUANTITY
# ============================================================

def get_reserved_quantity(equipment_id):
    """
    Calculate currently reserved equipment quantity.

    Active reservations:
    - pending
    - confirmed
    - rescheduled
    """

    rentals = db.equipment_rentals.find({
        "equipment_id": equipment_id,
        "status": {
            "$in": ACTIVE_RENTAL_STATUSES
        }
    })

    reserved_quantity = 0

    now = datetime.now(TIMEZONE)
    for rental in rentals:
        booking = db.bookings.find_one({"_id": rental.get("booking_id")})
        if not booking or booking.get("status") not in ["pending", "confirmed", "rescheduled"]:
            continue

        try:
            booking_end = datetime.strptime(
                f"{booking['booking_date']} {booking['end_time']}",
                "%Y-%m-%d %H:%M",
            ).replace(tzinfo=TIMEZONE)
        except (KeyError, TypeError, ValueError):
            continue

        if booking_end > now:
            reserved_quantity += int(rental.get("quantity", 0))

    return reserved_quantity


def get_live_available_quantity(equipment_id):
    """Return total stock minus active current or future rentals."""

    equipment = db.equipment.find_one({"_id": equipment_id})
    if not equipment:
        return 0

    total_quantity = int(
        equipment.get("available_quantity", equipment.get("quantity", 0))
    )
    reserved_quantity = get_reserved_quantity(equipment_id)
    return max(0, total_quantity - reserved_quantity)


# ============================================================
# CHECK EQUIPMENT AVAILABILITY
# ============================================================

def check_equipment_availability(equipment_id, quantity):
    """
    Check whether the requested quantity is available.
    """

    # --------------------------------------------------------
    # Validate quantity
    # --------------------------------------------------------

    if quantity is None:
        return {
            "success": False,
            "error_code": "INVALID_QUANTITY",
            "message": "Equipment quantity is required.",
        }

    try:
        quantity = int(quantity)

    except (TypeError, ValueError):
        return {
            "success": False,
            "error_code": "INVALID_QUANTITY",
            "message": "Equipment quantity must be a number.",
        }

    if quantity <= 0:
        return {
            "success": False,
            "error_code": "INVALID_QUANTITY",
            "message": "Equipment quantity must be greater than zero.",
        }

    # --------------------------------------------------------
    # Get equipment
    # --------------------------------------------------------

    equipment_result = get_equipment(equipment_id)

    if not equipment_result["success"]:
        return equipment_result

    equipment = equipment_result["equipment"]

    # --------------------------------------------------------
    # Check active status
    # --------------------------------------------------------

    if not equipment.get("active", False):
        return {
            "success": False,
            "error_code": "EQUIPMENT_UNAVAILABLE",
            "message": "This equipment is currently unavailable.",
        }

    # --------------------------------------------------------
    # IMPORTANT:
    # MongoDB uses available_quantity
    # --------------------------------------------------------

    total_quantity = int(
        equipment.get("available_quantity", equipment.get("quantity", 0))
    )

    # --------------------------------------------------------
    # Get currently reserved quantity
    # --------------------------------------------------------

    reserved_quantity = get_reserved_quantity(
        equipment_id
    )

    # --------------------------------------------------------
    # Calculate remaining quantity
    # --------------------------------------------------------

    available_quantity = (
        total_quantity - reserved_quantity
    )

    # Prevent negative availability
    if available_quantity < 0:
        available_quantity = 0

    # --------------------------------------------------------
    # Check requested quantity
    # --------------------------------------------------------

    if quantity > available_quantity:
        return {
            "success": False,
            "error_code": "INSUFFICIENT_EQUIPMENT",
            "message": (
                f"Only {available_quantity} "
                f"unit(s) of this equipment are available."
            ),
            "available_quantity": available_quantity,
        }

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    return {
        "success": True,
        "available": True,
        "requested_quantity": quantity,
        "available_quantity": available_quantity,
        "reserved_quantity": reserved_quantity,
    }


# ============================================================
# CALCULATE RENTAL AMOUNT
# ============================================================

def calculate_rental_amount(equipment_id, quantity):
    """
    Calculate equipment rental charge.

    Membership discount does NOT apply
    to equipment charges.

    MongoDB fields:
    - rental_rate
    - deposit
    - available_quantity
    """

    # --------------------------------------------------------
    # Check availability first
    # --------------------------------------------------------

    availability = check_equipment_availability(
        equipment_id,
        quantity
    )

    if not availability["success"]:
        return availability

    # --------------------------------------------------------
    # Get equipment
    # --------------------------------------------------------

    equipment = db.equipment.find_one({
        "_id": equipment_id
    })

    if not equipment:
        return {
            "success": False,
            "error_code": "EQUIPMENT_NOT_FOUND",
            "message": "Equipment was not found.",
        }

    # --------------------------------------------------------
    # Get PRD field: rental_rate
    # --------------------------------------------------------

    rental_rate = float(
        equipment.get("rental_rate", 0)
    )

    # --------------------------------------------------------
    # Calculate rental amount
    # --------------------------------------------------------

    quantity = int(quantity)

    rental_amount = (
        rental_rate * quantity
    )

    # --------------------------------------------------------
    # Calculate deposit
    # --------------------------------------------------------

    deposit_amount = (
        float(equipment.get("deposit", 0))
        * quantity
    )

    total_amount = (
        rental_amount + deposit_amount
    )

    # --------------------------------------------------------
    # Return calculation
    # --------------------------------------------------------

    return {
        "success": True,
        "equipment_id": equipment_id,
        "equipment_name": equipment.get("name"),
        "quantity": quantity,
        "rental_rate": rental_rate,
        "rental_amount": rental_amount,
        "deposit_amount": deposit_amount,
        "total_amount": total_amount,
    }


# ============================================================
# RESERVE EQUIPMENT
# ============================================================

def reserve_equipment(
    booking_id,
    equipment_id,
    quantity
):
    """
    Reserve equipment for a booking.
    """

    # --------------------------------------------------------
    # Validate booking ID
    # --------------------------------------------------------

    if not booking_id:
        return {
            "success": False,
            "error_code": "INVALID_BOOKING",
            "message": "Booking ID is required.",
        }

    # --------------------------------------------------------
    # Calculate rental
    # --------------------------------------------------------

    calculation = calculate_rental_amount(
        equipment_id,
        quantity
    )

    if not calculation["success"]:
        return calculation

    # --------------------------------------------------------
    # Prevent duplicate active reservation
    # --------------------------------------------------------

    existing = db.equipment_rentals.find_one({
        "booking_id": booking_id,
        "equipment_id": equipment_id,
        "status": {
            "$in": ACTIVE_RENTAL_STATUSES
        }
    })

    if existing:
        return {
            "success": False,
            "error_code": "EQUIPMENT_ALREADY_RESERVED",
            "message": (
                "This equipment is already reserved "
                "for this booking."
            ),
        }

    # --------------------------------------------------------
    # Generate unique rental ID
    # --------------------------------------------------------

    rental_id = (
        "RENT"
        + uuid.uuid4().hex[:10].upper()
    )

    now = datetime.now(TIMEZONE)

    # --------------------------------------------------------
    # Create rental document
    # --------------------------------------------------------

    rental = {
        "_id": rental_id,
        "booking_id": booking_id,
        "equipment_id": equipment_id,
        "quantity": calculation["quantity"],
        "rental_rate": calculation["rental_rate"],
        "rental_amount": calculation["rental_amount"],
        "deposit_amount": calculation["deposit_amount"],
        "status": "confirmed",
        "created_at": now,
        "updated_at": now,
    }

    db.equipment_rentals.insert_one(
        rental
    )

    return {
        "success": True,
        "message": "Equipment reserved successfully.",
        "rental": rental,
    }


# ============================================================
# RELEASE EQUIPMENT
# ============================================================

def release_equipment(booking_id):
    """
    Release all equipment associated with a booking.
    """

    if not booking_id:
        return {
            "success": False,
            "error_code": "INVALID_BOOKING",
            "message": "Booking ID is required.",
        }

    now = datetime.now(TIMEZONE)

    result = db.equipment_rentals.update_many(
        {
            "booking_id": booking_id,
            "status": {
                "$in": ACTIVE_RENTAL_STATUSES
            }
        },
        {
            "$set": {
                "status": "released",
                "updated_at": now,
            }
        }
    )

    return {
        "success": True,
        "message": "Equipment released successfully.",
        "released_count": result.modified_count,
    }


# ============================================================
# GET BOOKING EQUIPMENT
# ============================================================

def get_booking_equipment(booking_id):
    """
    Get all equipment rented for a booking.
    """

    if not booking_id:
        return {
            "success": False,
            "error_code": "INVALID_BOOKING",
            "message": "Booking ID is required.",
        }

    rentals = list(
        db.equipment_rentals.find({
            "booking_id": booking_id
        })
    )

    return {
        "success": True,
        "booking_id": booking_id,
        "equipment": rentals,
    }


# ============================================================
# CALCULATE TOTAL EQUIPMENT CHARGES
# ============================================================

def calculate_booking_equipment_total(booking_id):
    """
    Calculate total equipment rental and deposit
    for a booking.

    Membership discount is NOT applied.
    """

    if not booking_id:
        return {
            "success": False,
            "error_code": "INVALID_BOOKING",
            "message": "Booking ID is required.",
        }

    rentals = list(
        db.equipment_rentals.find({
            "booking_id": booking_id,
            "status": {
                "$in": ACTIVE_RENTAL_STATUSES
            }
        })
    )

    rental_amount = 0.0
    deposit_amount = 0.0

    for rental in rentals:

        rental_amount += float(
            rental.get("rental_amount", 0)
        )

        deposit_amount += float(
            rental.get("deposit_amount", 0)
        )

    total_equipment_amount = (
        rental_amount + deposit_amount
    )
    response = {
        "success": True,
        "message": "Equipment reserved successfully.",
        "rental": rental,
    }

    # --------------------------------------------------------
    # Send equipment confirmation email (non-blocking)
    # --------------------------------------------------------

    try:
        from backend.services.booking_notifier import send_equipment_confirmation
        from backend.database.mongodb import db as _db

        booking = _db.bookings.find_one({"_id": booking_id})
        if booking and booking.get("customer_id"):
            email_result = send_equipment_confirmation(
                customer_id=booking["customer_id"],
                booking_id=booking_id,
                rental=rental
            )

            if not email_result.get("sent"):
                print(
                    f"[EMAIL] Equipment email failed: "
                    f"{email_result.get('error')}"
                )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return response