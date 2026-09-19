from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from backend.services.booking_notifier import send_reschedule_confirmation
from backend.agents import booking
from backend.database.mongodb import db
from backend.services.auth_service import get_current_customer
from backend.services.booking_service import (
    get_current_booking_date,
    get_max_advance_booking_days,
)
from backend.services.availability_service import check_availability
from backend.services.pricing_service import calculate_price, parse_date


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")

RESCHEDULE_WINDOW_MINUTES = 120

RESCHEDULABLE_STATUSES = [
    "pending",
    "confirmed"
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_current_timestamp():
    """
    Return current UTC timestamp.
    """
    return datetime.now(timezone.utc)


def get_current_local_time():
    """
    Return current Asia/Kolkata time.
    """
    return datetime.now(TIMEZONE)


def get_booking(booking_id):
    """
    Retrieve booking by ID.
    """
    return db.bookings.find_one({
        "_id": booking_id
    })


def get_booking_start_datetime(booking):
    """
    Convert booking date and start time
    into timezone-aware datetime.
    """

    booking_date = datetime.strptime(
        booking["booking_date"],
        "%Y-%m-%d"
    ).date()

    start_time = datetime.strptime(
        booking["start_time"],
        "%H:%M"
    ).time()

    return datetime.combine(
        booking_date,
        start_time,
        tzinfo=TIMEZONE
    )


def calculate_minutes_until_booking(booking):
    """
    Calculate minutes remaining before
    the original booking starts.
    """

    booking_start = get_booking_start_datetime(
        booking
    )

    current_time = get_current_local_time()

    difference = booking_start - current_time

    return difference.total_seconds() / 60


def create_audit_event(
    customer_id,
    event_type,
    entity_type,
    entity_id,
    metadata=None
):
    """
    Create an audit event.
    """

    audit_document = {
        "_id": "AUDIT" + datetime.now(
            timezone.utc
        ).strftime("%Y%m%d%H%M%S%f"),

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


def calculate_price_difference(
    old_total,
    new_total
):
    """
    Calculate price difference.

    Positive:
        Customer must pay additional amount.

    Negative:
        Customer receives refund/credit.

    Zero:
        No price difference.
    """

    difference = round(
        float(new_total) - float(old_total),
        2
    )

    if difference > 0:

        return {
            "difference": difference,
            "additional_amount": difference,
            "refund_amount": 0.0
        }

    if difference < 0:

        return {
            "difference": difference,
            "additional_amount": 0.0,
            "refund_amount": abs(difference)
        }

    return {
        "difference": 0.0,
        "additional_amount": 0.0,
        "refund_amount": 0.0
    }


# ============================================================
# RESCHEDULE PREVIEW
# ============================================================

def reschedule_booking_preview(
    session,
    booking_id,
    new_date,
    new_start_time,
    new_end_time,
    equipment_items=None
):
    """
    Generate a rescheduling preview.

    This function does NOT modify the booking.
    """

    # --------------------------------------------------------
    # 1. Authentication
    # --------------------------------------------------------

    customer = get_current_customer(session)

    if not customer:

        return {
            "success": False,
            "error_code": "AUTHENTICATION_FAILED",
            "message": "You must be logged in."
        }

    customer_id = customer["id"]

    # --------------------------------------------------------
    # 2. Retrieve booking
    # --------------------------------------------------------

    booking = get_booking(
        booking_id
    )

    if not booking:

        return {
            "success": False,
            "error_code": "BOOKING_NOT_FOUND",
            "message": "Booking was not found."
        }

    # --------------------------------------------------------
    # 3. Ownership
    # --------------------------------------------------------

    if booking.get("customer_id") != customer_id:

        return {
            "success": False,
            "error_code": "UNAUTHORIZED_BOOKING_ACCESS",
            "message": (
                "You are not authorized "
                "to access this booking."
            )
        }

    # --------------------------------------------------------
    # 4. Reschedule count
    # --------------------------------------------------------

    reschedule_count = int(
        booking.get(
            "reschedule_count",
            0
        )
    )

    if reschedule_count >= 1:

        return {
            "success": False,
            "error_code": "RESCHEDULE_LIMIT_EXCEEDED",
            "message": (
                "This booking has already "
                "been rescheduled once."
            )
        }

    max_advance_days = get_max_advance_booking_days(customer_id)
    requested_date = parse_date(new_date)
    if (
        max_advance_days is not None
        and requested_date is not None
        and (requested_date - get_current_booking_date()).days > max_advance_days
    ):
        return {
            "success": False,
            "error_code": "ADVANCE_BOOKING_LIMIT_EXCEEDED",
            "message": (
                f"Your account can book up to {max_advance_days} days ahead. "
                "Please choose a date within that window."
            ),
        }

    # --------------------------------------------------------
    # 5. Status
    # --------------------------------------------------------

    if booking.get("status") == "cancelled":

        return {
            "success": False,
            "error_code": "BOOKING_CANCELLED",
            "message": (
                "Cancelled bookings cannot be rescheduled."
            )
        }

    if booking.get("status") == "completed":

        return {
            "success": False,
            "error_code": "BOOKING_COMPLETED",
            "message": (
                "Completed bookings cannot be rescheduled."
            )
        }

    if booking.get("status") not in RESCHEDULABLE_STATUSES:

        return {
            "success": False,
            "error_code": "BOOKING_NOT_RESCHEDULABLE",
            "message": (
                f"Booking with status "
                f"'{booking.get('status')}' "
                f"cannot be rescheduled."
            )
        }
    # --------------------------------------------------------
    # 6. Two-hour rule
    # --------------------------------------------------------

    minutes_remaining = calculate_minutes_until_booking(
        booking
    )

    if minutes_remaining < RESCHEDULE_WINDOW_MINUTES:

        return {
            "success": False,
            "error_code": "RESCHEDULE_WINDOW_EXPIRED",
            "message": (
                "Rescheduling is allowed only "
                "at least 2 hours before "
                "the original booking."
            ),
            "minutes_until_booking": round(
                minutes_remaining,
                2
            )
        }

    # --------------------------------------------------------
    # 7. Check new slot availability
    # --------------------------------------------------------

    availability_result = check_availability(
        resource_id=booking["resource_id"],
        booking_date=new_date,
        start_time=new_start_time,
        end_time=new_end_time
    )

    if not availability_result.get("success"):

        return availability_result

    if not availability_result.get("available"):

        return {
            "success": False,
            "error_code": "SLOT_UNAVAILABLE",
            "message": (
                "The new requested slot "
                "is not available."
            )
        }

    # --------------------------------------------------------
    # 8. Calculate new price
    # --------------------------------------------------------

    pricing_result = calculate_price(
        customer_id=customer_id,
        resource_id=booking["resource_id"],
        booking_date=new_date,
        start_time=new_start_time,
        end_time=new_end_time,
        equipment_items=equipment_items
    )

    if not pricing_result.get("success"):

        return pricing_result

    # --------------------------------------------------------
    # IMPORTANT
    #
    # pricing_service returns:
    #
    # {
    #     "success": True,
    #     "pricing": {
    #         "total_amount": ...
    #     }
    # }
    #
    # Therefore we extract the nested pricing object.
    # --------------------------------------------------------

    new_pricing = pricing_result.get(
        "pricing",
        {}
    )

    # --------------------------------------------------------
    # 9. Old price
    # --------------------------------------------------------

    if "total_amount" in booking:

        old_total = float(
            booking.get(
                "total_amount",
                0
            )
        )

    else:

        old_total = float(
            booking.get(
                "price_breakdown",
                {}
            ).get(
                "total_amount",
                0
            )
        )

    # --------------------------------------------------------
    # 10. New price
    # --------------------------------------------------------

    new_total = float(
        new_pricing.get(
            "total_amount",
            0
        )
    )

    # --------------------------------------------------------
    # 11. Price difference
    # --------------------------------------------------------

    difference = calculate_price_difference(
        old_total,
        new_total
    )

    # --------------------------------------------------------
    # 12. Return preview
    # --------------------------------------------------------

    return {

        "success": True,

        "message": (
            "Rescheduling preview generated."
        ),

        "booking_id": booking_id,

        "current_booking": {

            "resource_id": booking["resource_id"],

            "booking_date": booking["booking_date"],

            "start_time": booking["start_time"],

            "end_time": booking["end_time"],

            "total_amount": old_total
        },

        "new_booking": {

            "resource_id": booking["resource_id"],

            "booking_date": new_date,

            "start_time": new_start_time,

            "end_time": new_end_time,

            "total_amount": new_total,

            "price_breakdown": new_pricing
        },

        "price_difference": difference,

        "reschedule_count": reschedule_count,

        "remaining_reschedules": (
            1 - reschedule_count
        ),

        "requires_confirmation": True
    }


# ============================================================
# FINAL RESCHEDULE
# ============================================================

def reschedule_booking(
    session,
    booking_id,
    new_date,
    new_start_time,
    new_end_time,
    confirmed=False,
    equipment_items=None
):
    """
    Reschedule a booking after explicit confirmation.

    All important validations are repeated
    before modifying the database.
    """

    # --------------------------------------------------------
    # 1. Authentication
    # --------------------------------------------------------

    customer = get_current_customer(session)

    if not customer:

        return {
            "success": False,
            "error_code": "AUTHENTICATION_FAILED",
            "message": "You must be logged in."
        }

    customer_id = customer["id"]

    # --------------------------------------------------------
    # 2. Confirmation
    # --------------------------------------------------------

    if confirmed is not True:

        return {
            "success": False,
            "error_code": "CONFIRMATION_REQUIRED",
            "message": (
                "Rescheduling requires "
                "explicit confirmation."
            )
        }

    # --------------------------------------------------------
    # 3. Retrieve booking
    # --------------------------------------------------------

    booking = get_booking(
        booking_id
    )

    if not booking:

        return {
            "success": False,
            "error_code": "BOOKING_NOT_FOUND",
            "message": "Booking was not found."
        }

    # --------------------------------------------------------
    # 4. Ownership
    # --------------------------------------------------------

    if booking.get("customer_id") != customer_id:

        return {
            "success": False,
            "error_code": "UNAUTHORIZED_BOOKING_ACCESS",
            "message": (
                "You are not authorized "
                "to reschedule this booking."
            )
        }

    # --------------------------------------------------------
    # 5. Status
    # --------------------------------------------------------

    if booking.get("status") in [
        "cancelled",
        "completed"
    ]:

        return {
            "success": False,
            "error_code": "BOOKING_NOT_RESCHEDULABLE",
            "message": (
                "Cancelled or completed bookings "
                "cannot be rescheduled."
            )
        }

    if booking.get("status") not in RESCHEDULABLE_STATUSES:

        return {
            "success": False,
            "error_code": "BOOKING_NOT_RESCHEDULABLE",
            "message": (
                f"Booking with status "
                f"'{booking.get('status')}' "
                f"cannot be rescheduled."
            )
        }

    # --------------------------------------------------------
    # 6. Reschedule count
    # --------------------------------------------------------

    if int(
        booking.get(
            "reschedule_count",
            0
        )
    ) >= 1:

        return {
            "success": False,
            "error_code": "RESCHEDULE_LIMIT_EXCEEDED",
            "message": (
                "This booking has already "
                "been rescheduled once."
            )
        }

    max_advance_days = get_max_advance_booking_days(customer_id)
    requested_date = parse_date(new_date)
    if (
        max_advance_days is not None
        and requested_date is not None
        and (requested_date - get_current_booking_date()).days > max_advance_days
    ):
        return {
            "success": False,
            "error_code": "ADVANCE_BOOKING_LIMIT_EXCEEDED",
            "message": (
                f"Your account can book up to {max_advance_days} days ahead. "
                "Please choose a date within that window."
            ),
        }

    # --------------------------------------------------------
    # 7. Two-hour rule
    # --------------------------------------------------------

    minutes_remaining = calculate_minutes_until_booking(
        booking
    )

    if minutes_remaining < RESCHEDULE_WINDOW_MINUTES:

        return {
            "success": False,
            "error_code": "RESCHEDULE_WINDOW_EXPIRED",
            "message": (
                "Rescheduling is allowed only "
                "at least 2 hours before "
                "the original booking."
            )
        }

    # --------------------------------------------------------
    # 8. FINAL availability check
    # --------------------------------------------------------

    availability_result = check_availability(
        resource_id=booking["resource_id"],
        booking_date=new_date,
        start_time=new_start_time,
        end_time=new_end_time
    )

    if not availability_result.get("success"):

        return availability_result

    if not availability_result.get("available"):

        return {
            "success": False,
            "error_code": "SLOT_UNAVAILABLE",
            "message": (
                "The new requested slot "
                "is no longer available."
            )
        }

    # --------------------------------------------------------
    # 9. Recalculate price
    # --------------------------------------------------------

    pricing_result = calculate_price(
        customer_id=customer_id,
        resource_id=booking["resource_id"],
        booking_date=new_date,
        start_time=new_start_time,
        end_time=new_end_time,
        equipment_items=equipment_items
    )

    if not pricing_result.get("success"):

        return pricing_result

    # --------------------------------------------------------
    # IMPORTANT:
    # Extract nested pricing object.
    # --------------------------------------------------------

    new_pricing = pricing_result.get(
        "pricing",
        {}
    )

    # --------------------------------------------------------
    # 10. Old total
    # --------------------------------------------------------

    if "total_amount" in booking:

        old_total = float(
            booking.get(
                "total_amount",
                0
            )
        )

    else:

        old_total = float(
            booking.get(
                "price_breakdown",
                {}
            ).get(
                "total_amount",
                0
            )
        )

    # --------------------------------------------------------
    # 11. New total
    # --------------------------------------------------------

    new_total = float(
        new_pricing.get(
            "total_amount",
            0
        )
    )

    # --------------------------------------------------------
    # 12. Calculate price difference
    # --------------------------------------------------------

    difference = calculate_price_difference(
        old_total,
        new_total
    )

    # --------------------------------------------------------
    # 13. Preserve reschedule history
    # --------------------------------------------------------

    history_entry = {

        "rescheduled_at": get_current_timestamp(),

        "old_booking_date": booking[
            "booking_date"
        ],

        "old_start_time": booking[
            "start_time"
        ],

        "old_end_time": booking[
            "end_time"
        ],

        "old_total_amount": old_total,

        "new_booking_date": new_date,

        "new_start_time": new_start_time,

        "new_end_time": new_end_time,

        "new_total_amount": new_total,

        "price_difference": difference
    }

    # --------------------------------------------------------
    # 14. Final database update
    # --------------------------------------------------------

    update_result = db.bookings.update_one(

        {
            "_id": booking_id,

            "customer_id": customer_id,

            "status": {
                "$in": RESCHEDULABLE_STATUSES
            },

            "reschedule_count": 0
        },

        {
            "$set": {

                "booking_date": new_date,

                "start_time": new_start_time,

                "end_time": new_end_time,

                "blocked_end_time": (
                    availability_result.get(
                        "blocked_end_time"
                    )
                ),

                "duration_mins": (
                    new_pricing.get(
                        "duration_mins",
                        0
                    )
                ),

                "base_amount": (
                    new_pricing.get(
                        "base_amount",
                        0
                    )
                ),

                "surcharge_amount": (
                    new_pricing.get(
                        "surcharge_amount",
                        0
                    )
                ),

                "discount_amount": (
                    new_pricing.get(
                        "discount_amount",
                        0
                    )
                ),

                "equipment_amount": (
                    new_pricing.get(
                        "equipment_amount",
                        0
                    )
                ),

                "deposit_amount": (
                    new_pricing.get(
                        "deposit_amount",
                        0
                    )
                ),

                "total_amount": new_total,

                "price_breakdown": {

                    "base_amount": (
                        new_pricing.get(
                            "base_amount",
                            0
                        )
                    ),

                    "peak_surcharge": (
                        new_pricing.get(
                            "peak_surcharge",
                            0
                        )
                    ),

                    "weekend_surcharge": (
                        new_pricing.get(
                            "weekend_surcharge",
                            0
                        )
                    ),

                    "surcharge_amount": (
                        new_pricing.get(
                            "surcharge_amount",
                            0
                        )
                    ),

                    "discount_amount": (
                        new_pricing.get(
                            "discount_amount",
                            0
                        )
                    ),

                    "equipment_amount": (
                        new_pricing.get(
                            "equipment_amount",
                            0
                        )
                    ),

                    "deposit_amount": (
                        new_pricing.get(
                            "deposit_amount",
                            0
                        )
                    ),

                    "total_amount": new_total
                },

                "reschedule_count": 1,

                "reschedule_history": history_entry,

                "status": "rescheduled",

                "updated_at": get_current_timestamp()
            }
        }
    )

    # --------------------------------------------------------
    # 15. Verify update
    # --------------------------------------------------------

    if update_result.modified_count != 1:

        return {
            "success": False,
            "error_code": "RESCHEDULE_FAILED",
            "message": (
                "The booking could not be rescheduled. "
                "It may have already been changed."
            )
        }

    # --------------------------------------------------------
    # 16. Audit event
    # --------------------------------------------------------

    create_audit_event(

        customer_id=customer_id,

        event_type="booking_rescheduled",

        entity_type="booking",

        entity_id=booking_id,

        metadata={

            "old_booking_date": booking[
                "booking_date"
            ],

            "old_start_time": booking[
                "start_time"
            ],

            "old_end_time": booking[
                "end_time"
            ],

            "new_booking_date": new_date,

            "new_start_time": new_start_time,

            "new_end_time": new_end_time,

            "old_total_amount": old_total,

            "new_total_amount": new_total,

            "price_difference": difference
        }
    )

    # --------------------------------------------------------
    # 17. Return result
    # --------------------------------------------------------

    response = {
        "success": True,
        "message": "Booking rescheduled successfully.",
        "booking_id": booking_id,
        "booking": {
            "id": booking_id,
            "customer_id": customer_id,
            "resource_id": booking.get("resource_id"),
            "booking_date": new_date,
            "start_time": new_start_time,
            "end_time": new_end_time,
            "total_amount": new_total,
            "status": "rescheduled",
            "reschedule_count": 1,
            "reschedule_history": history_entry,
        },
        "price_difference": difference
    }

    # --------------------------------------------------------
    # Send reschedule email (non-blocking)
    # --------------------------------------------------------

    try:
        from backend.services.booking_notifier import send_reschedule_confirmation

        email_result = send_reschedule_confirmation(
            customer_id=customer_id,
            booking=response["booking"]
        )

        if not email_result.get("sent"):
            print(
                f"[EMAIL] Reschedule email failed: "
                f"{email_result.get('error')}"
            )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return response