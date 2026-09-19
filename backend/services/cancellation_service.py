from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from backend.database.mongodb import db
from backend.services.auth_service import get_current_customer
from backend.services.booking_notifier import send_cancellation_email


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")

CANCELLATION_WINDOW_MINUTES = 120

CANCELLABLE_STATUSES = [
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
    Return current time in Asia/Kolkata.
    """
    return datetime.now(TIMEZONE)


def get_booking(booking_id):
    """
    Retrieve a booking by ID.
    """
    return db.bookings.find_one({
        "_id": booking_id
    })


def get_booking_start_datetime(booking):
    """
    Convert booking date + start time into
    timezone-aware datetime.
    """

    booking_date = booking["booking_date"]
    start_time = booking["start_time"]

    date_part = datetime.strptime(
        booking_date,
        "%Y-%m-%d"
    ).date()

    time_part = datetime.strptime(
        start_time,
        "%H:%M"
    ).time()

    return datetime.combine(
        date_part,
        time_part,
        tzinfo=TIMEZONE
    )


def calculate_minutes_until_booking(booking):
    """
    Calculate how many minutes remain before
    the booking starts.
    """

    booking_start = get_booking_start_datetime(booking)

    current_time = get_current_local_time()

    difference = booking_start - current_time

    return difference.total_seconds() / 60


def calculate_refund_eligibility(booking):
    """
    Determine whether the booking is eligible
    for a refund.
    """

    minutes_remaining = calculate_minutes_until_booking(
        booking
    )

    eligible = (
        minutes_remaining >= CANCELLATION_WINDOW_MINUTES
    )

    total_amount = float(
        booking.get("total_amount", 0)
    )

    if eligible:
        refund_amount = total_amount
    else:
        refund_amount = 0.0

    return {
        "refund_eligible": eligible,
        "refund_amount": refund_amount,
        "minutes_until_booking": round(
            minutes_remaining,
            2
        )
    }


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


# ============================================================
# CANCELLATION PREVIEW
# ============================================================

def cancel_booking_preview(
    session,
    booking_id
):
    """
    Check whether a booking can be cancelled.

    IMPORTANT:
    This function does NOT cancel the booking.

    It only generates the cancellation preview.
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
    # 2. Booking ID validation
    # --------------------------------------------------------

    if not booking_id:
        return {
            "success": False,
            "error_code": "INVALID_BOOKING_ID",
            "message": "Booking ID is required."
        }

    # --------------------------------------------------------
    # 3. Retrieve booking
    # --------------------------------------------------------

    booking = get_booking(booking_id)

    if not booking:
        return {
            "success": False,
            "error_code": "BOOKING_NOT_FOUND",
            "message": "Booking was not found."
        }

    # --------------------------------------------------------
    # 4. Ownership validation
    # --------------------------------------------------------

    if booking.get("customer_id") != customer_id:
        return {
            "success": False,
            "error_code": "UNAUTHORIZED_BOOKING_ACCESS",
            "message": "You are not authorized to access this booking."
        }

    # --------------------------------------------------------
    # 5. Check booking status
    # --------------------------------------------------------

    booking_status = booking.get("status")

    if booking_status == "cancelled":
        return {
            "success": False,
            "error_code": "ALREADY_CANCELLED",
            "message": "This booking has already been cancelled."
        }

    if booking_status not in CANCELLABLE_STATUSES:
        return {
            "success": False,
            "error_code": "BOOKING_NOT_CANCELLABLE",
            "message": (
                f"Booking with status '{booking_status}' "
                "cannot be cancelled."
            )
        }

    # --------------------------------------------------------
    # 6. Calculate refund eligibility
    # --------------------------------------------------------

    refund_info = calculate_refund_eligibility(
        booking
    )

    # --------------------------------------------------------
    # 7. Return preview
    # --------------------------------------------------------

    return {
        "success": True,
        "message": "Cancellation preview generated.",
        "booking": {
            "id": booking["_id"],
            "resource_id": booking.get("resource_id"),
            "booking_date": booking.get("booking_date"),
            "start_time": booking.get("start_time"),
            "end_time": booking.get("end_time"),
            "status": booking.get("status"),
            "total_amount": float(
                booking.get("total_amount", 0)
            )
        },
        "refund_eligible": refund_info[
            "refund_eligible"
        ],
        "refund_amount": refund_info[
            "refund_amount"
        ],
        "minutes_until_booking": refund_info[
            "minutes_until_booking"
        ],
        "requires_confirmation": True,
        "refund_message": (
            "Refund will be returned to the original "
            "payment method and may take 3–5 business days."
            if refund_info["refund_eligible"]
            else
            "This booking is less than 2 hours away "
            "and is non-refundable."
        )
    }


# ============================================================
# FINAL CANCELLATION
# ============================================================

def cancel_booking(
    session,
    booking_id,
    confirmed=False,
    reason=None
):
    """
    Cancel a booking after explicit confirmation.

    The service performs the eligibility checks again
    before changing the booking.
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
    # 2. Explicit confirmation
    # --------------------------------------------------------

    if confirmed is not True:
        return {
            "success": False,
            "error_code": "CONFIRMATION_REQUIRED",
            "message": (
                "Cancellation requires explicit confirmation."
            )
        }

    # --------------------------------------------------------
    # 3. Retrieve booking
    # --------------------------------------------------------

    booking = get_booking(booking_id)

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
            "message": "You are not authorized to cancel this booking."
        }

    # --------------------------------------------------------
    # 5. Prevent duplicate cancellation
    # --------------------------------------------------------

    if booking.get("status") == "cancelled":
        return {
            "success": False,
            "error_code": "ALREADY_CANCELLED",
            "message": "This booking has already been cancelled."
        }

    if booking.get("status") not in CANCELLABLE_STATUSES:
        return {
            "success": False,
            "error_code": "BOOKING_NOT_CANCELLABLE",
            "message": (
                f"Booking with status "
                f"'{booking.get('status')}' cannot be cancelled."
            )
        }

    # --------------------------------------------------------
    # 6. FINAL refund eligibility check
    # --------------------------------------------------------

    refund_info = calculate_refund_eligibility(
        booking
    )

    refund_amount = refund_info[
        "refund_amount"
    ]

    refund_eligible = refund_info[
        "refund_eligible"
    ]

    # --------------------------------------------------------
    # 7. Update booking
    # --------------------------------------------------------

    cancellation_time = get_current_timestamp()

    update_result = db.bookings.update_one(
        {
            "_id": booking_id,
            "customer_id": customer_id,
            "status": {
                "$in": CANCELLABLE_STATUSES
            }
        },
        {
            "$set": {
                "status": "cancelled",
                "cancelled_at": cancellation_time,
                "cancellation_reason": reason,
                "refund_eligible": refund_eligible,
                "refund_amount": refund_amount,
                "updated_at": cancellation_time
            }
        }
    )

    # --------------------------------------------------------
    # 8. Final write validation
    # --------------------------------------------------------

    if update_result.modified_count != 1:
        return {
            "success": False,
            "error_code": "CANCELLATION_FAILED",
            "message": (
                "The booking could not be cancelled. "
                "It may have already changed."
            )
        }

    # --------------------------------------------------------
    # 9. Update payment/refund status
    # --------------------------------------------------------

    payment = db.payments.find_one({
        "booking_id": booking_id
    })

    if payment:

        if refund_amount > 0:

            db.payments.update_one(
                {
                    "_id": payment["_id"]
                },
                {
                    "$set": {
                        "status": "refund_pending",
                        "refund_amount": refund_amount,
                        "refund_status": "pending",
                        "refunded_at": None,
                        "updated_at": cancellation_time
                    }
                }
            )

        else:

            db.payments.update_one(
                {
                    "_id": payment["_id"]
                },
                {
                    "$set": {
                        "refund_amount": 0,
                        "refund_status": "not_eligible",
                        "updated_at": cancellation_time
                    }
                }
            )

    # --------------------------------------------------------
    # 10. Audit event
    # --------------------------------------------------------

    create_audit_event(
        customer_id=customer_id,
        event_type="booking_cancelled",
        entity_type="booking",
        entity_id=booking_id,
        metadata={
            "refund_eligible": refund_eligible,
            "refund_amount": refund_amount,
            "reason": reason
        }
    )

    # --------------------------------------------------------
    # 11. Build response
    # --------------------------------------------------------

    response = {
        "success": True,
        "message": "Booking cancelled successfully.",
        "booking_id": booking_id,
        "status": "cancelled",
        "refund_eligible": refund_eligible,
        "refund_amount": refund_amount,
        "refund_status": (
            "pending"
            if refund_amount > 0
            else "not_eligible"
        ),
        "refund_message": (
            "Refund will be returned to the original "
            "payment method and may take 3–5 business days."
            if refund_amount > 0
            else
            "This booking is non-refundable."
        )
    }

    # --------------------------------------------------------
    # 12. Send cancellation email (non-blocking)
    # --------------------------------------------------------

    try:
        booking["id"] = booking["_id"]

        email_result = send_cancellation_email(
            customer_id=customer_id,
            booking=booking,
            refund_info={
                "refund_eligible": refund_eligible,
                "refund_amount": refund_amount,
                "refund_status": response["refund_status"],
            }
        )

        if not email_result.get("sent"):
            print(
                f"[EMAIL] Cancellation email failed: "
                f"{email_result.get('error')}"
            )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return response