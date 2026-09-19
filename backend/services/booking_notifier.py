"""
Booking notification service.

Sends automatic emails when:
- booking confirmed
- booking rescheduled
- booking cancelled
- equipment reserved

All functions are designed to NEVER raise exceptions.
Email failure must not break the caller's flow.
"""

from backend.database.mongodb import db
from backend.services.email_service import send_email


# ============================================================
# HELPERS
# ============================================================

def _get_customer(customer_id):
    if not customer_id:
        return None
    try:
        return db.customers.find_one({"_id": customer_id})
    except Exception:
        return None


def _get_resource_name(resource_id):
    if not resource_id:
        return resource_id or "N/A"
    try:
        resource = db.resources.find_one({"_id": resource_id})
        if resource:
            return resource.get("name", resource_id)
    except Exception:
        pass
    return resource_id


def _safe_send(to_email, subject, body):
    try:
        result = send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )
        if result.get("success"):
            return {"sent": True, "error": None}
        return {"sent": False, "error": result.get("message", "unknown")}
    except Exception as e:
        return {"sent": False, "error": str(e)}


def _format_currency(amount):
    try:
        return f"Rs.{float(amount):.2f}"
    except (ValueError, TypeError):
        return "Rs.0.00"


# ============================================================
# 1. BOOKING CONFIRMED
# ============================================================

def send_booking_confirmation(customer_id, booking):
    customer = _get_customer(customer_id)
    if not customer or not customer.get("email"):
        return {"sent": False, "error": "customer email not found"}

    resource_name = _get_resource_name(booking.get("resource_id"))

    subject = f"Booking Confirmed - {booking.get('id', 'N/A')}"

    body = f"""
Hi {customer.get('name', 'Customer')},

Your booking has been confirmed!

-------------------------------------
BOOKING DETAILS
-------------------------------------
Booking ID   : {booking.get('id', 'N/A')}
Facility     : {resource_name}
Date         : {booking.get('booking_date', 'N/A')}
Time         : {booking.get('start_time', 'N/A')} - {booking.get('end_time', 'N/A')}
Duration     : {booking.get('duration_mins', 'N/A')} minutes
-------------------------------------

PAYMENT
-------------------------------------
Base Amount      : {_format_currency(booking.get('base_amount', 0))}
Surcharges       : {_format_currency(booking.get('surcharge_amount', 0))}
Equipment        : {_format_currency(booking.get('equipment_amount', 0))}
Deposit          : {_format_currency(booking.get('deposit_amount', 0))}
Discounts        : -{_format_currency(booking.get('discount_amount', 0))}
Total            : {_format_currency(booking.get('total_amount', 0))}
Payment          : {str(booking.get('payment_status', 'pending')).upper()}
-------------------------------------

Please arrive 10 minutes before your slot.

Thank you for booking with us!
"""

    return _safe_send(customer["email"], subject, body)


# ============================================================
# 2. BOOKING RESCHEDULED
# ============================================================

def send_reschedule_confirmation(customer_id, booking):
    customer = _get_customer(customer_id)
    if not customer or not customer.get("email"):
        return {"sent": False, "error": "customer email not found"}

    resource_name = _get_resource_name(booking.get("resource_id"))

    subject = f"Booking Rescheduled - {booking.get('id', 'N/A')}"

    history = booking.get("reschedule_history", {}) or {}
    old_date = history.get("old_booking_date", "N/A")
    old_start = history.get("old_start_time", "N/A")
    old_end = history.get("old_end_time", "N/A")

    body = f"""
Hi {customer.get('name', 'Customer')},

Your booking has been rescheduled.

-------------------------------------
BOOKING DETAILS
-------------------------------------
Booking ID   : {booking.get('id', 'N/A')}
Facility     : {resource_name}
-------------------------------------

OLD SCHEDULE
-------------------------------------
Date         : {old_date}
Time         : {old_start} - {old_end}
-------------------------------------

NEW SCHEDULE
-------------------------------------
Date         : {booking.get('booking_date', 'N/A')}
Time         : {booking.get('start_time', 'N/A')} - {booking.get('end_time', 'N/A')}
Total        : {_format_currency(booking.get('total_amount', 0))}
-------------------------------------

Thank you for booking with us!
"""

    return _safe_send(customer["email"], subject, body)


# ============================================================
# 3. BOOKING CANCELLED
# ============================================================

def send_cancellation_email(customer_id, booking, refund_info):
    customer = _get_customer(customer_id)
    if not customer or not customer.get("email"):
        return {"sent": False, "error": "customer email not found"}

    resource_name = _get_resource_name(booking.get("resource_id"))

    subject = f"Booking Cancelled - {booking.get('id', 'N/A')}"

    refund_eligible = refund_info.get("refund_eligible", False)
    refund_amount = refund_info.get("refund_amount", 0)

    if refund_eligible and refund_amount > 0:
        refund_section = f"""
REFUND
-------------------------------------
Refund Amount  : {_format_currency(refund_amount)}
Refund Status  : {str(refund_info.get('refund_status', 'pending')).upper()}
Note           : Refund will be processed within 3-5 business days.
-------------------------------------
"""
    else:
        refund_section = """
REFUND
-------------------------------------
This booking is not eligible for a refund
(cancelled less than 2 hours before start time).
-------------------------------------
"""

    body = f"""
Hi {customer.get('name', 'Customer')},

Your booking has been cancelled.

-------------------------------------
CANCELLED BOOKING
-------------------------------------
Booking ID   : {booking.get('id', 'N/A')}
Facility     : {resource_name}
Date         : {booking.get('booking_date', 'N/A')}
Time         : {booking.get('start_time', 'N/A')} - {booking.get('end_time', 'N/A')}
Total        : {_format_currency(booking.get('total_amount', 0))}
-------------------------------------

{refund_section}

We hope to see you again soon!
"""

    return _safe_send(customer["email"], subject, body)


# ============================================================
# 4. EQUIPMENT RESERVED
# ============================================================

def send_equipment_confirmation(customer_id, booking_id, rental):
    customer = _get_customer(customer_id)
    if not customer or not customer.get("email"):
        return {"sent": False, "error": "customer email not found"}

    equipment_name = _get_resource_name(rental.get("equipment_id"))

    total = (
        float(rental.get("rental_amount", 0))
        + float(rental.get("deposit_amount", 0))
    )

    subject = f"Equipment Reserved - {booking_id}"

    body = f"""
Hi {customer.get('name', 'Customer')},

Your equipment has been reserved.

-------------------------------------
EQUIPMENT DETAILS
-------------------------------------
Booking ID     : {booking_id}
Equipment      : {equipment_name}
Quantity       : {rental.get('quantity', 0)}
-------------------------------------

CHARGES
-------------------------------------
Rental Amount  : {_format_currency(rental.get('rental_amount', 0))}
Deposit        : {_format_currency(rental.get('deposit_amount', 0))}
Total          : {_format_currency(total)}
-------------------------------------

Please collect your equipment at the facility.

Thank you!
"""

    return _safe_send(customer["email"], subject, body)


# ============================================================
# 5. MEMBERSHIP WELCOME (optional)
# ============================================================

def send_membership_welcome(customer_id, membership):
    customer = _get_customer(customer_id)
    if not customer or not customer.get("email"):
        return {"sent": False, "error": "customer email not found"}

    subject = f"Welcome - {str(membership.get('type', 'Membership')).title()} Plan"

    body = f"""
Hi {customer.get('name', 'Customer')},

Welcome to Turf Booking! Your membership is now active.

-------------------------------------
MEMBERSHIP DETAILS
-------------------------------------
Type         : {str(membership.get('type', 'N/A')).title()}
Start Date   : {membership.get('start_date', 'N/A')}
End Date     : {membership.get('end_date', 'N/A')}
Discount     : {membership.get('discount_percent', 0)}% on facility bookings
-------------------------------------

Your discount is automatically applied at checkout.

Thank you for joining!
"""

    return _safe_send(customer["email"], subject, body)

# ============================================================
# 5. MEMBERSHIP WELCOME
# ============================================================

def send_membership_welcome(customer_id, membership):
    """
    Send welcome email after a successful membership purchase.

    Called from: membership_service.create_membership()
    """

    customer = _get_customer(customer_id)
    if not customer or not customer.get("email"):
        return {"sent": False, "error": "customer email not found"}

    subject = (
        f"Welcome - "
        f"{str(membership.get('type', 'Membership')).title()} Plan"
    )

    body = f"""
Hi {customer.get('name', 'Customer')},

Welcome to Turf Booking! Your membership is now active.

-------------------------------------
MEMBERSHIP DETAILS
-------------------------------------
Membership ID : {membership.get('_id', 'N/A')}
Type          : {str(membership.get('type', 'N/A')).title()}
Price         : {_format_currency(membership.get('price', 0))}
Start Date    : {membership.get('start_date', 'N/A')}
End Date      : {membership.get('end_date', 'N/A')}
Discount      : {membership.get('discount_percent', 0)}% on facility bookings
-------------------------------------

BENEFITS
-------------------------------------
"""

    benefits = membership.get("benefits", [])
    if benefits:
        for benefit in benefits:
            body += f"- {benefit}\n"
    else:
        body += "- Member discounts on facility bookings\n"

    body += """
-------------------------------------

Your discount is automatically applied at checkout.

Thank you for joining!
"""

    return _safe_send(customer["email"], subject, body)