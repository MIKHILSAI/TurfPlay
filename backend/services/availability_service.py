from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.database.mongodb import db


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")

BUFFER_MINUTES = 10

ACTIVE_BOOKING_STATUSES = [
    "pending",
    "confirmed"
]


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


def combine_date_time(date_value, time_value):
    """
    Combine date and time using Asia/Kolkata timezone.
    """

    return datetime(
        date_value.year,
        date_value.month,
        date_value.day,
        time_value.hour,
        time_value.minute,
        tzinfo=TIMEZONE
    )


def format_time(time_value):
    """
    Convert time object to HH:MM.
    """

    return time_value.strftime("%H:%M")


# ============================================================
# CHECK RESOURCE
# ============================================================

def get_resource(resource_id):
    """
    Find a resource by ID.
    """

    return db.resources.find_one({
        "_id": resource_id
    })


# ============================================================
# CHECK OPENING HOURS
# ============================================================

def check_opening_hours(
    resource,
    start_time,
    end_time
):
    """
    Check whether requested time is inside
    the facility's opening and closing hours.
    """

    opening_time = parse_time(
        resource.get("open_time")
    )

    closing_time = parse_time(
        resource.get("close_time")
    )

    if not opening_time or not closing_time:

        return {
            "valid": False,
            "error_code": "INVALID_OPENING_HOURS",
            "message": "Facility opening hours are not configured correctly."
        }


    # Requested start must be >= opening time
    if start_time < opening_time:

        return {
            "valid": False,
            "error_code": "OUTSIDE_OPENING_HOURS",
            "message": (
                f"The facility opens at "
                f"{format_time(opening_time)}."
            )
        }


    # Requested end must be <= closing time
    if end_time > closing_time:

        return {
            "valid": False,
            "error_code": "OUTSIDE_OPENING_HOURS",
            "message": (
                f"The facility closes at "
                f"{format_time(closing_time)}."
            )
        }


    return {
        "valid": True
    }


# ============================================================
# CHECK FACILITY CLOSURE
# ============================================================

def check_facility_closure(
    resource_id,
    booking_date,
    start_time,
    end_time
):
    """
    Check whether the requested time overlaps
    with a facility closure.

    booking_date is a Python date object,
    but MongoDB stores closure_date as YYYY-MM-DD string.
    """

    # Convert Python date to the same string format
    # used in MongoDB.
    booking_date_string = booking_date.strftime("%Y-%m-%d")

    closures = db.facility_closures.find({
        "resource_id": resource_id,
        "closure_date": booking_date_string
    })

    for closure in closures:

        closure_start = parse_time(
            closure.get("start_time")
        )

        closure_end = parse_time(
            closure.get("end_time")
        )

        if not closure_start or not closure_end:
            continue

        # Requested time:
        #
        # start_time -------- end_time
        #
        # Closure:
        #
        # closure_start -------- closure_end
        #
        # They overlap when:
        #
        # start_time < closure_end
        # AND
        # end_time > closure_start

        overlaps = (
            start_time < closure_end
            and
            end_time > closure_start
        )

        if overlaps:

            reason = closure.get(
                "reason",
                "Facility closure"
            )

            return {
                "closed": True,
                "error_code": "FACILITY_CLOSED",
                "message": (
                    f"The facility is closed during the "
                    f"requested time. Reason: {reason}"
                ),
                "closure": {
                    "start_time": format_time(
                        closure_start
                    ),
                    "end_time": format_time(
                        closure_end
                    ),
                    "reason": reason
                }
            }

    return {
        "closed": False
    }
# ============================================================
# CHECK EXISTING BOOKINGS
# ============================================================

def check_booking_overlap(
    resource_id,
    booking_date,
    start_datetime,
    end_datetime
):
    """
    Check whether the requested slot overlaps
    with an existing active booking.

    The 10-minute buffer is included.

    Existing booking:

        18:00 - 19:00
                   |
                   +-- 10 minute buffer
                       |
                       19:10

    Therefore another booking cannot start before 19:10.
    """

    existing_bookings = db.bookings.find({

        "resource_id": resource_id,

        "booking_date": booking_date.strftime(
            "%Y-%m-%d"
        ),

        "status": {
            "$in": ACTIVE_BOOKING_STATUSES
        }

    })


    for booking in existing_bookings:

        # ----------------------------------------------------
        # Existing booking start
        # ----------------------------------------------------

        existing_start_time = parse_time(
            booking.get("start_time")
        )

        # ----------------------------------------------------
        # Existing booking end
        # ----------------------------------------------------

        existing_end_time = parse_time(
            booking.get("end_time")
        )


        if not existing_start_time or not existing_end_time:

            continue


        # ----------------------------------------------------
        # Convert existing booking times to datetime
        # ----------------------------------------------------

        existing_start_datetime = combine_date_time(
            booking_date,
            existing_start_time
        )


        existing_end_datetime = combine_date_time(
            booking_date,
            existing_end_time
        )


        # ----------------------------------------------------
        # Determine blocked end time
        # ----------------------------------------------------
        #
        # If blocked_end_time exists in MongoDB,
        # use it.
        #
        # Otherwise calculate:
        #
        # end time + 10 minutes
        #
        # ----------------------------------------------------

        blocked_end_time = parse_time(
            booking.get("blocked_end_time")
        )


        if blocked_end_time:

            existing_blocked_end_datetime = combine_date_time(
                booking_date,
                blocked_end_time
            )

        else:

            existing_blocked_end_datetime = (
                existing_end_datetime
                + timedelta(minutes=BUFFER_MINUTES)
            )


        # ----------------------------------------------------
        # Check overlap
        # ----------------------------------------------------
        #
        # Requested booking:
        #
        # start_datetime -> end_datetime
        #
        # Existing blocked slot:
        #
        # existing_start -> existing_blocked_end
        #
        # Overlap occurs when:
        #
        # requested_start < existing_blocked_end
        #
        # AND
        #
        # requested_end > existing_start
        #
        # ----------------------------------------------------

        overlaps = (
            start_datetime < existing_blocked_end_datetime
            and
            end_datetime > existing_start_datetime
        )


        if overlaps:

            return {
                "available": False,
                "error_code": "SLOT_UNAVAILABLE",
                "message": (
                    "The requested facility is already booked "
                    "during or immediately before the requested slot."
                ),
                "conflicting_booking": {
                    "booking_id": booking.get("_id"),
                    "start_time": format_time(
                        existing_start_time
                    ),
                    "end_time": format_time(
                        existing_end_time
                    ),
                    "blocked_end_time": (
                        existing_blocked_end_datetime
                        .astimezone(TIMEZONE)
                        .strftime("%H:%M")
                    )
                }
            }


    return {
        "available": True
    }


# ============================================================
# MAIN AVAILABILITY FUNCTION
# ============================================================

def check_availability(
    resource_id,
    booking_date,
    start_time,
    end_time=None,
    duration_mins=None
):
    """
    Check whether a resource is available.

    Parameters
    ----------
    resource_id : str
        Example: BC1

    booking_date : str
        Format: YYYY-MM-DD

    start_time : str
        Format: HH:MM

    end_time : str, optional
        Format: HH:MM

    duration_mins : int, optional
        Booking duration in minutes.

    Either end_time OR duration_mins must be supplied.
    """

    # ========================================================
    # 1. VALIDATE RESOURCE ID
    # ========================================================

    if not resource_id:

        return {
            "success": False,
            "available": False,
            "error_code": "RESOURCE_NOT_FOUND",
            "message": "Resource ID is required."
        }


    # ========================================================
    # 2. FIND RESOURCE
    # ========================================================

    resource = get_resource(
        resource_id
    )


    if not resource:

        return {
            "success": False,
            "available": False,
            "error_code": "RESOURCE_NOT_FOUND",
            "message": (
                f"Resource '{resource_id}' was not found."
            )
        }


    # ========================================================
    # 3. CHECK RESOURCE ACTIVE
    # ========================================================

    if resource.get("active") is not True:

        return {
            "success": False,
            "available": False,
            "error_code": "RESOURCE_INACTIVE",
            "message": (
                f"{resource.get('name', resource_id)} "
                "is currently inactive."
            )
        }


    # ========================================================
    # 4. VALIDATE DATE
    # ========================================================

    parsed_date = parse_date(
        booking_date
    )


    if not parsed_date:

        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_DATE",
            "message": (
                "Invalid booking date. "
                "Use YYYY-MM-DD format."
            )
        }


    # ========================================================
    # 5. VALIDATE START TIME
    # ========================================================

    parsed_start_time = parse_time(
        start_time
    )


    if not parsed_start_time:

        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_TIME",
            "message": (
                "Invalid start time. "
                "Use HH:MM format."
            )
        }


    # ========================================================
    # 6. VALIDATE END TIME / DURATION
    # ========================================================

    parsed_end_time = None


    if end_time:

        parsed_end_time = parse_time(
            end_time
        )

        if not parsed_end_time:

            return {
                "success": False,
                "available": False,
                "error_code": "INVALID_TIME",
                "message": (
                    "Invalid end time. "
                    "Use HH:MM format."
                )
            }


    elif duration_mins:

        # Validate duration
        try:

            duration_mins = int(
                duration_mins
            )

        except (ValueError, TypeError):

            return {
                "success": False,
                "available": False,
                "error_code": "INVALID_DURATION",
                "message": "Duration must be a valid number."
            }


        if duration_mins <= 0:

            return {
                "success": False,
                "available": False,
                "error_code": "INVALID_DURATION",
                "message": (
                    "Duration must be greater than zero."
                )
            }


        start_datetime_temp = combine_date_time(
            parsed_date,
            parsed_start_time
        )


        end_datetime_temp = (
            start_datetime_temp
            + timedelta(minutes=duration_mins)
        )


        # Prevent crossing midnight
        if end_datetime_temp.date() != parsed_date:

            return {
                "success": False,
                "available": False,
                "error_code": "INVALID_DURATION",
                "message": (
                    "Booking cannot extend into the next day."
                )
            }


        parsed_end_time = end_datetime_temp.time()


    else:

        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_DURATION",
            "message": (
                "Provide either end_time or duration_mins."
            )
        }


    # ========================================================
    # 7. START MUST BE BEFORE END
    # ========================================================

    if parsed_start_time >= parsed_end_time:

        return {
            "success": False,
            "available": False,
            "error_code": "INVALID_TIME",
            "message": (
                "Start time must be earlier than end time."
            )
        }


    # ========================================================
    # 8. CREATE DATETIME OBJECTS
    # ========================================================

    requested_start_datetime = combine_date_time(
        parsed_date,
        parsed_start_time
    )


    requested_end_datetime = combine_date_time(
        parsed_date,
        parsed_end_time
    )


    # ========================================================
    # 9. CHECK PAST DATE / TIME
    # ========================================================

    now = datetime.now(
        TIMEZONE
    )


    if requested_start_datetime <= now:

        return {
            "success": False,
            "available": False,
            "error_code": "PAST_BOOKING",
            "message": (
                "Bookings cannot be made for a past date or time."
            )
        }


    # ========================================================
    # 10. CHECK OPENING HOURS
    # ========================================================

    opening_result = check_opening_hours(
        resource,
        parsed_start_time,
        parsed_end_time
    )


    if not opening_result["valid"]:

        return {
            "success": False,
            "available": False,
            "error_code": opening_result["error_code"],
            "message": opening_result["message"]
        }


    # ========================================================
    # 11. CHECK FACILITY CLOSURE
    # ========================================================

    closure_result = check_facility_closure(
        resource_id,
        parsed_date,
        parsed_start_time,
        parsed_end_time
    )


    if closure_result["closed"]:

        return {
            "success": False,
            "available": False,
            "error_code": closure_result["error_code"],
            "message": closure_result["message"],
            "closure": closure_result.get("closure")
        }


    # ========================================================
    # 12. CHECK EXISTING BOOKINGS + 10 MINUTE BUFFER
    # ========================================================

    booking_result = check_booking_overlap(
        resource_id,
        parsed_date,
        requested_start_datetime,
        requested_end_datetime
    )


    if not booking_result["available"]:

        return {
            "success": False,
            "available": False,
            "error_code": booking_result["error_code"],
            "message": booking_result["message"],
            "conflicting_booking": booking_result.get(
                "conflicting_booking"
            )
        }


    # ========================================================
    # 13. CALCULATE BLOCKED END TIME
    # ========================================================

    blocked_end_datetime = (
        requested_end_datetime
        + timedelta(minutes=BUFFER_MINUTES)
    )


    # ========================================================
    # 14. SUCCESS
    # ========================================================

    return {

        "success": True,

        "available": True,

        "error_code": None,

        "message": (
            f"{resource['name']} is available."
        ),

        "resource": {

            "id": resource["_id"],

            "name": resource["name"],

            "type": resource["type"],

            "hourly_rate": resource["hourly_rate"]

        },

        "booking": {

            "date": parsed_date.strftime(
                "%Y-%m-%d"
            ),

            "start_time": parsed_start_time.strftime(
                "%H:%M"
            ),

            "end_time": parsed_end_time.strftime(
                "%H:%M"
            ),

            "duration_mins": int(
                (
                    requested_end_datetime
                    - requested_start_datetime
                ).total_seconds() / 60
            ),

            "blocked_end_time": blocked_end_datetime.strftime(
                "%H:%M"
            )

        }

    }