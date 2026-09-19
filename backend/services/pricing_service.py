from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from backend.database.mongodb import db


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")

MEMBERSHIP_DISCOUNT_PERCENT = 15
WEEKEND_SURCHARGE_PERCENT = 10

PEAK_START_HOUR = 18
PEAK_END_HOUR = 21

PEAK_SURCHARGE_PER_HOUR = 30


def round_money(value):
    """Round one monetary line item to the displayed whole rupee."""

    return float(
        Decimal(str(value or 0)).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_date(date_string):
    """
    Convert YYYY-MM-DD string into a date object.
    """
    try:
        return datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return None


def parse_time(time_string):
    """
    Convert HH:MM string into a time object.
    """
    try:
        return datetime.strptime(
            time_string,
            "%H:%M"
        ).time()

    except (ValueError, TypeError):
        return None


def get_resource(resource_id):
    """
    Get resource from MongoDB.
    """
    return db.resources.find_one({
        "_id": resource_id
    })


def get_active_membership(customer_id):
    """
    Get the customer's active membership.
    """

    if not customer_id:
        return None

    return db.memberships.find_one({
        "customer_id": customer_id,
        "status": "active"
    })


# ============================================================
# DURATION
# ============================================================

def calculate_duration_minutes(start_time, end_time):
    """
    Calculate booking duration in minutes.
    """

    start = parse_time(start_time)
    end = parse_time(end_time)

    if not start or not end:
        raise ValueError(
            "Invalid start_time or end_time."
        )

    start_minutes = (
        start.hour * 60
        + start.minute
    )

    end_minutes = (
        end.hour * 60
        + end.minute
    )

    duration = end_minutes - start_minutes

    if duration <= 0:
        raise ValueError(
            "end_time must be later than start_time."
        )

    return duration


# ============================================================
# FACILITY PRICE
# ============================================================

def calculate_base_amount(
    resource,
    duration_minutes
):
    """
    Calculate base facility price.

    Example:

    ₹300/hour × 60 minutes
    = ₹300
    """

    hourly_rate = resource.get(
        "hourly_rate",
        0
    )

    if hourly_rate <= 0:
        raise ValueError(
            "Resource hourly rate is invalid."
        )

    base_amount = (
        hourly_rate
        * duration_minutes
        / 60
    )

    return round_money(base_amount)


# ============================================================
# PEAK SURCHARGE
# ============================================================

def calculate_peak_surcharge(
    booking_date,
    start_time,
    end_time,
    resource
):
    """
    Calculate weekday peak surcharge.

    Peak period:
    Monday-Friday
    18:00-21:00

    PRD example:
    ₹30/hour surcharge.
    """

    date_value = parse_date(booking_date)

    start = parse_time(start_time)
    end = parse_time(end_time)

    if not date_value or not start or not end:
        return 0

    # Monday = 0
    # Sunday = 6
    is_weekday = date_value.weekday() < 5

    if not is_weekday:
        return 0

    peak_start = PEAK_START_HOUR * 60
    peak_end = PEAK_END_HOUR * 60

    requested_start = (
        start.hour * 60
        + start.minute
    )

    requested_end = (
        end.hour * 60
        + end.minute
    )

    # Calculate overlap with 18:00-21:00
    overlap_start = max(
        requested_start,
        peak_start
    )

    overlap_end = min(
        requested_end,
        peak_end
    )

    overlap_minutes = (
        overlap_end - overlap_start
    )

    if overlap_minutes <= 0:
        return 0

    surcharge = (
        PEAK_SURCHARGE_PER_HOUR
        * overlap_minutes
        / 60
    )

    return round_money(surcharge)


# ============================================================
# WEEKEND SURCHARGE
# ============================================================

def calculate_weekend_surcharge(
    booking_date,
    base_amount
):
    """
    Calculate 10% weekend surcharge.
    """

    date_value = parse_date(booking_date)

    if not date_value:
        return 0

    # Saturday = 5
    # Sunday = 6
    is_weekend = date_value.weekday() >= 5

    if not is_weekend:
        return 0

    surcharge = (
        base_amount
        * WEEKEND_SURCHARGE_PERCENT
        / 100
    )

    return round_money(surcharge)


# ============================================================
# MEMBERSHIP DISCOUNT
# ============================================================

def calculate_membership_discount(
    customer_id,
    base_amount,
    peak_surcharge,
    weekend_surcharge
):
    """
    Calculate membership discount.

    Important:
    Membership discount applies only to
    facility charges.

    Equipment rental and deposits are
    not discounted.
    """

    membership = get_active_membership(
        customer_id
    )

    if not membership:
        return {
            "discount_amount": 0,
            "membership_id": None,
            "discount_percent": 0
        }

    discount_percent = membership.get(
        "discount_percent",
        MEMBERSHIP_DISCOUNT_PERCENT
    )

    facility_amount = (
        base_amount
        + peak_surcharge
        + weekend_surcharge
    )

    discount_amount = (
        facility_amount
        * discount_percent
        / 100
    )

    return {
        "discount_amount": round_money(discount_amount),
        "membership_id": membership.get(
            "_id"
        ),
        "discount_percent": discount_percent
    }


# ============================================================
# EQUIPMENT RENTAL
# ============================================================

def calculate_equipment_amount(
    equipment_items=None
):
    """
    Calculate equipment rental amount.

    equipment_items example:

    [
        {
            "equipment_id": "EQ001",
            "quantity": 2
        }
    ]
    """

    if not equipment_items:
        return 0

    total = 0

    for item in equipment_items:

        equipment_id = item.get(
            "equipment_id"
        )

        quantity = item.get(
            "quantity",
            0
        )

        if not equipment_id:
            raise ValueError(
                "Equipment ID is required."
            )

        if quantity <= 0:
            raise ValueError(
                "Equipment quantity must be greater than 0."
            )

        equipment = db.equipment.find_one({
            "_id": equipment_id,
            "active": True
        })

        if not equipment:
            raise ValueError(
                f"Equipment '{equipment_id}' "
                "was not found or is inactive."
            )

        rental_rate = equipment.get(
            "rental_rate",
            0
        )

        total += (
            rental_rate
            * quantity
        )

    return round_money(total)


# ============================================================
# EQUIPMENT DEPOSIT
# ============================================================

def calculate_equipment_deposit(
    equipment_items=None
):
    """
    Calculate equipment deposit.

    Deposits are added to the final amount
    but are NOT discounted.
    """

    if not equipment_items:
        return 0

    total = 0

    for item in equipment_items:

        equipment_id = item.get(
            "equipment_id"
        )

        quantity = item.get(
            "quantity",
            0
        )

        equipment = db.equipment.find_one({
            "_id": equipment_id,
            "active": True
        })

        if not equipment:
            raise ValueError(
                f"Equipment '{equipment_id}' "
                "was not found or is inactive."
            )

        deposit = equipment.get(
            "deposit",
            0
        )

        total += (
            deposit
            * quantity
        )

    return round_money(total)


# ============================================================
# FINAL PRICE
# ============================================================

def calculate_price(
    resource_id,
    booking_date,
    start_time,
    end_time,
    customer_id=None,
    equipment_items=None
):
    """
    Calculate the complete booking price.

    Formula:

    Base facility price
        +
    Peak surcharge
        +
    Weekend surcharge
        -
    Membership discount
        +
    Equipment rental
        +
    Equipment deposit
        =
    Final price

    This function is completely deterministic.
    """

    # --------------------------------------------------------
    # Get resource
    # --------------------------------------------------------

    resource = get_resource(
        resource_id
    )

    if not resource:
        return {
            "success": False,
            "error_code": "RESOURCE_NOT_FOUND",
            "message": (
                f"Resource '{resource_id}' "
                "was not found."
            )
        }

    # --------------------------------------------------------
    # Validate resource
    # --------------------------------------------------------

    if not resource.get("active", False):
        return {
            "success": False,
            "error_code": "RESOURCE_INACTIVE",
            "message": (
                f"{resource.get('name', resource_id)} "
                "is currently inactive."
            )
        }

    # --------------------------------------------------------
    # Calculate duration
    # --------------------------------------------------------

    try:

        duration_minutes = (
            calculate_duration_minutes(
                start_time,
                end_time
            )
        )

    except ValueError as e:

        return {
            "success": False,
            "error_code": "INVALID_TIME",
            "message": str(e)
        }

    # --------------------------------------------------------
    # Base amount
    # --------------------------------------------------------

    base_amount = calculate_base_amount(
        resource,
        duration_minutes
    )

    # --------------------------------------------------------
    # Peak surcharge
    # --------------------------------------------------------

    peak_surcharge = 0

    # --------------------------------------------------------
    # Weekend surcharge
    # --------------------------------------------------------

    weekend_surcharge = calculate_weekend_surcharge(
        booking_date,
        base_amount
    )

    # --------------------------------------------------------
    # Total surcharge
    # --------------------------------------------------------

    surcharge_amount = peak_surcharge + weekend_surcharge

    # --------------------------------------------------------
    # Membership discount
    # --------------------------------------------------------

    membership_result = (
        calculate_membership_discount(
            customer_id,
            base_amount,
            peak_surcharge,
            weekend_surcharge
        )
    )

    discount_amount = membership_result[
        "discount_amount"
    ]

    # --------------------------------------------------------
    # Equipment
    # --------------------------------------------------------

    try:

        equipment_amount = (
            calculate_equipment_amount(
                equipment_items
            )
        )

        deposit_amount = (
            calculate_equipment_deposit(
                equipment_items
            )
        )

    except ValueError as e:

        return {
            "success": False,
            "error_code": "INVALID_EQUIPMENT",
            "message": str(e)
        }

    # --------------------------------------------------------
    # Final amount
    # --------------------------------------------------------

    total_amount = (
        base_amount
        + surcharge_amount
        - discount_amount
        + equipment_amount
        + deposit_amount
    )

    # --------------------------------------------------------
    # Return complete pricing breakdown
    # --------------------------------------------------------

    return {
        "success": True,

        "resource": {
            "id": resource.get("_id"),
            "name": resource.get("name"),
            "type": resource.get("type"),
            "hourly_rate": resource.get(
                "hourly_rate"
            )
        },

        "booking": {
            "date": booking_date,
            "start_time": start_time,
            "end_time": end_time,
            "duration_mins": duration_minutes
        },

        "pricing": {
            "base_amount": base_amount,
            "peak_surcharge": peak_surcharge,
            "weekend_surcharge": weekend_surcharge,
            "surcharge_amount": surcharge_amount,
            "discount_amount": discount_amount,
            "equipment_amount": equipment_amount,
            "deposit_amount": deposit_amount,
            "total_amount": total_amount
        },

        "membership": {
            "membership_id": membership_result[
                "membership_id"
            ],
            "discount_percent": membership_result[
                "discount_percent"
            ]
        }
    }