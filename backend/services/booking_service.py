
import uuid
from datetime import datetime, timezone

from backend.database.mongodb import db
from backend.services.auth_service import get_current_customer
from backend.services.availability_service import check_availability
from backend.services.pricing_service import calculate_price
from backend.services.booking_notifier import send_booking_confirmation


# ============================================================
# CONFIGURATION
# ============================================================

ACTIVE_BOOKING_STATUSES = [
    "pending",
    "confirmed"
]

# ============================================================
# BOOKING WINDOW CONFIGURATION
# ============================================================

MAX_ADVANCE_BOOKING_DAYS = 30


def get_max_advance_booking_days(customer_id=None):
    """
    Return the maximum number of days in advance
    that a booking can be made.

    Currently the same for all customers.
    The customer_id parameter is accepted for
    future per-customer rules (e.g., VIP extended windows).
    """
    return MAX_ADVANCE_BOOKING_DAYS

def get_current_booking_date():
    """
    Return today's date in Asia/Kolkata timezone
    as a datetime.date object.

    Used by booking_process.py and reschedule_service.py
    to enforce booking date rules via date arithmetic.
    """

    from zoneinfo import ZoneInfo

    TIMEZONE = ZoneInfo("Asia/Kolkata")

    return datetime.now(TIMEZONE).date()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_booking_id():
    """
    Generate a unique booking ID.

    Example:
    BKG7A91F23C
    """

    return "BKG" + uuid.uuid4().hex[:8].upper()


def get_current_timestamp():
    """
    Return current UTC timestamp.
    """

    return datetime.now(timezone.utc)


def get_customer(customer_id):
    """
    Get customer from MongoDB.
    """

    return db.customers.find_one({
        "_id": customer_id
    })


def create_audit_event(
    customer_id,
    event_type,
    entity_type,
    entity_id,
    metadata=None
):
    """
    Store an audit event.

    Important booking actions must be auditable.
    """

    audit_document = {
        "_id": "AUDIT" + uuid.uuid4().hex[:8].upper(),

        "customer_id": customer_id,

        "event_type": event_type,

        "entity_type": entity_type,

        "entity_id": entity_id,

        "metadata": metadata or {},

        "created_at": get_current_timestamp()
    }

    db.audit_events.insert_one(
        audit_document
    )

    return audit_document


# ============================================================
# DUPLICATE BOOKING CHECK
# ============================================================

def check_duplicate_booking(
    customer_id,
    resource_id,
    booking_date,
    start_time,
    end_time
):
    """
    Check whether the same customer already has
    an active booking for the exact same slot.
    """

    existing_booking = db.bookings.find_one({
        "customer_id": customer_id,

        "resource_id": resource_id,

        "booking_date": booking_date,

        "start_time": start_time,

        "end_time": end_time,

        "status": {
            "$in": ACTIVE_BOOKING_STATUSES
        }
    })

    return existing_booking


# ============================================================
# CREATE BOOKING
# ============================================================

def create_booking(
    session,
    resource_id,
    booking_date,
    start_time,
    end_time,
    equipment_items=None
):
    """
    Create a new turf booking.

    Booking flow:

    Customer
        ↓
    Validate authentication
        ↓
    Validate inputs
        ↓
    Validate facility
        ↓
    Check duplicate booking
        ↓
    Check availability
        ↓
    Calculate price
        ↓
    Create booking
        ↓
    Create audit event
        ↓
    Send confirmation email
        ↓
    Return booking
    """

    # ========================================================
    # 1. VALIDATE AUTHENTICATION
    # ========================================================

    customer = get_current_customer(
        session
    )

    if not customer:

        return {
            "success": False,

            "error_code": "AUTHENTICATION_FAILED",

            "message": (
                "You must be logged in to create "
                "a booking."
            )
        }

    customer_id = customer["id"]


    # ========================================================
    # 2. VALIDATE BASIC INPUTS
    # ========================================================

    if not resource_id:

        return {
            "success": False,

            "error_code": "INVALID_RESOURCE",

            "message": "Resource ID is required."
        }


    if not booking_date:

        return {
            "success": False,

            "error_code": "INVALID_DATE",

            "message": "Booking date is required."
        }


    if not start_time:

        return {
            "success": False,

            "error_code": "INVALID_TIME",

            "message": "Start time is required."
        }


    if not end_time:

        return {
            "success": False,

            "error_code": "INVALID_TIME",

            "message": "End time is required."
        }


    # ========================================================
    # 3. VALIDATE FACILITY
    # ========================================================

    resource = db.resources.find_one({
        "_id": resource_id
    })

    if not resource:

        return {
            "success": False,

            "error_code": "RESOURCE_NOT_FOUND",

            "message": (
                f"Resource '{resource_id}' "
                "was not found."
            )
        }


    if not resource.get(
        "active",
        False
    ):

        return {
            "success": False,

            "error_code": "RESOURCE_INACTIVE",

            "message": (
                f"{resource.get('name', resource_id)} "
                "is currently inactive."
            )
        }


    # ========================================================
    # 4. PREVENT DUPLICATE BOOKING
    # ========================================================
    #
    # This is intentionally checked BEFORE availability.
    #
    # Otherwise an existing exact booking would be reported
    # as SLOT_UNAVAILABLE instead of DUPLICATE_BOOKING.
    #

    duplicate_booking = check_duplicate_booking(
        customer_id=customer_id,

        resource_id=resource_id,

        booking_date=booking_date,

        start_time=start_time,

        end_time=end_time
    )

    if duplicate_booking:

        return {
            "success": False,

            "available": False,

            "error_code": "DUPLICATE_BOOKING",

            "message": (
                "You already have a booking "
                "for this exact slot."
            ),

            "booking_id": duplicate_booking.get(
                "_id"
            )
        }


    # ========================================================
    # 5. FINAL AVAILABILITY CHECK
    # ========================================================
    #
    # This checks:
    #
    # - date
    # - time
    # - opening hours
    # - facility closure
    # - existing bookings
    # - booking buffer
    #
    # This check happens immediately before
    # price calculation and booking creation.
    #

    availability_result = check_availability(
        resource_id=resource_id,

        booking_date=booking_date,

        start_time=start_time,

        end_time=end_time
    )

    if not availability_result.get(
        "available",
        False
    ):

        return {
            "success": False,

            "available": False,

            "error_code": availability_result.get(
                "error_code",
                "SLOT_UNAVAILABLE"
            ),

            "message": availability_result.get(
                "message",
                "The requested slot is unavailable."
            )
        }


    # ========================================================
    # 6. CALCULATE PRICE
    # ========================================================

    pricing_result = calculate_price(
        resource_id=resource_id,

        booking_date=booking_date,

        start_time=start_time,

        end_time=end_time,

        customer_id=customer_id,

        equipment_items=equipment_items
    )

    if not pricing_result.get(
        "success",
        False
    ):

        return {
            "success": False,

            "error_code": pricing_result.get(
                "error_code",
                "PRICING_ERROR"
            ),

            "message": pricing_result.get(
                "message",
                "Unable to calculate booking price."
            )
        }


    # ========================================================
    # 7. EXTRACT PRICING
    # ========================================================

    pricing = pricing_result.get(
        "pricing",
        {}
    )

    base_amount = pricing.get(
        "base_amount",
        0
    )

    peak_surcharge = pricing.get(
        "peak_surcharge",
        0
    )

    weekend_surcharge = pricing.get(
        "weekend_surcharge",
        0
    )

    surcharge_amount = pricing.get(
        "surcharge_amount",
        0
    )

    discount_amount = pricing.get(
        "discount_amount",
        0
    )

    equipment_amount = pricing.get(
        "equipment_amount",
        0
    )

    deposit_amount = pricing.get(
        "deposit_amount",
        0
    )

    total_amount = pricing.get(
        "total_amount",
        0
    )


    # ========================================================
    # 8. EXTRACT BOOKING INFORMATION
    # ========================================================

    booking_information = availability_result.get(
        "booking",
        {}
    )

    duration_mins = booking_information.get(
        "duration_mins"
    )

    blocked_end_time = booking_information.get(
        "blocked_end_time"
    )


    # ========================================================
    # 9. GENERATE BOOKING ID
    # ========================================================

    booking_id = generate_booking_id()

    created_at = get_current_timestamp()


    # ========================================================
    # 10. GET MEMBERSHIP INFORMATION
    # ========================================================

    membership = pricing_result.get(
        "membership",
        {}
    )

    membership_id = membership.get(
        "membership_id"
    )


    # ========================================================
    # 11. CREATE BOOKING DOCUMENT
    # ========================================================
    #
    # Monetary values are stored at the top level.
    #
    # This makes the document easier to query and matches
    # the PRD booking structure.
    #
    # price_breakdown is also retained for detailed display.
    #

    booking_document = {

        # ----------------------------------------------------
        # IDENTIFICATION
        # ----------------------------------------------------

        "_id": booking_id,

        "booking_id": booking_id,

        "customer_id": customer_id,

        "resource_id": resource_id,


        # ----------------------------------------------------
        # DATE AND TIME
        # ----------------------------------------------------

        "booking_date": booking_date,

        "start_time": start_time,

        "end_time": end_time,

        "blocked_end_time": blocked_end_time,

        "duration_mins": duration_mins,


        # ----------------------------------------------------
        # BOOKING STATUS
        # ----------------------------------------------------

        "status": "confirmed",

        "payment_status": "pending",


        # ----------------------------------------------------
        # PRICING — TOP LEVEL
        # ----------------------------------------------------

        "base_amount": base_amount,

        "surcharge_amount": surcharge_amount,

        "discount_amount": discount_amount,

        "equipment_amount": equipment_amount,

        "deposit_amount": deposit_amount,

        "total_amount": total_amount,


        # ----------------------------------------------------
        # DETAILED PRICE BREAKDOWN
        # ----------------------------------------------------

        "price_breakdown": {

            "base_amount": base_amount,

            "peak_surcharge": peak_surcharge,

            "weekend_surcharge": weekend_surcharge,

            "surcharge_amount": surcharge_amount,

            "discount_amount": discount_amount,

            "equipment_amount": equipment_amount,

            "deposit_amount": deposit_amount,

            "total_amount": total_amount
        },


        # ----------------------------------------------------
        # MEMBERSHIP
        # ----------------------------------------------------

        "membership_id": membership_id,


        # ----------------------------------------------------
        # RESCHEDULING
        # ----------------------------------------------------

        "reschedule_count": 0,


        # ----------------------------------------------------
        # TIMESTAMPS
        # ----------------------------------------------------

        "created_at": created_at,

        "updated_at": created_at
    }


    # ========================================================
    # 12. INSERT BOOKING
    # ========================================================

    try:

        db.bookings.insert_one(
            booking_document
        )

    except Exception:

        return {
            "success": False,

            "error_code": "BOOKING_CREATION_FAILED",

            "message": (
                "Unable to create the booking. "
                "Please try again."
            )
        }


    # ========================================================
    # 13. CREATE AUDIT EVENT
    # ========================================================

    try:

        create_audit_event(

            customer_id=customer_id,

            event_type="booking_created",

            entity_type="booking",

            entity_id=booking_id,

            metadata={

                "resource_id": resource_id,

                "booking_date": booking_date,

                "start_time": start_time,

                "end_time": end_time,

                "total_amount": total_amount
            }
        )

    except Exception:

        # Booking has already been created.
        #
        # Do not expose internal database details.
        #
        # The booking remains valid.

        return {
            "success": False,

            "error_code": "AUDIT_LOG_FAILED",

            "message": (
                "The booking was created, but "
                "the audit record could not be saved."
            ),

            "booking_id": booking_id
        }


    # ========================================================
    # 14. BUILD RESPONSE
    # ========================================================

    response = {

        "success": True,

        "message": (
            "Booking created successfully."
        ),

        "booking": {

            "id": booking_id,

            "customer_id": customer_id,

            "resource_id": resource_id,

            "resource_name": resource.get(
                "name"
            ),

            "booking_date": booking_date,

            "start_time": start_time,

            "end_time": end_time,

            "blocked_end_time": blocked_end_time,

            "duration_mins": duration_mins,

            "status": "confirmed",

            "payment_status": "pending",


            # ------------------------------------------------
            # TOP LEVEL PRICING
            # ------------------------------------------------

            "base_amount": base_amount,

            "surcharge_amount": surcharge_amount,

            "discount_amount": discount_amount,

            "equipment_amount": equipment_amount,

            "deposit_amount": deposit_amount,

            "total_amount": total_amount,


            # ------------------------------------------------
            # DETAILED PRICE BREAKDOWN
            # ------------------------------------------------

            "price_breakdown": {

                "base_amount": base_amount,

                "peak_surcharge": peak_surcharge,

                "weekend_surcharge": weekend_surcharge,

                "surcharge_amount": surcharge_amount,

                "discount_amount": discount_amount,

                "equipment_amount": equipment_amount,

                "deposit_amount": deposit_amount,

                "total_amount": total_amount
            },

            "membership_id": membership_id,

            "reschedule_count": 0,

            "created_at": created_at
        }
    }


    # ========================================================
    # 15. SEND BOOKING CONFIRMATION EMAIL (non-blocking)
    # ========================================================

    try:

        email_result = send_booking_confirmation(
            customer_id=customer_id,
            booking=response["booking"]
        )

        if not email_result.get("sent"):
            print(
                f"[EMAIL] Booking confirmation failed: "
                f"{email_result.get('error')}"
            )

    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")


    # ========================================================
    # 16. RETURN
    # ========================================================

    return response