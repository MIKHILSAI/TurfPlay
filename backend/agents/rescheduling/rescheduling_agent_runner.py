import re
import calendar
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.agents.rescheduling.rescheduling_crew import (
    process_rescheduling_request
)

from backend.utils.date_utils import normalize_booking_date


TIMEZONE = ZoneInfo("Asia/Kolkata")


def clean_result(text):
    """
    Remove CrewAI/Qwen thinking output.

    We mainly use the original user message for
    deterministic date/time/duration extraction,
    so the LLM output is only used as a fallback.
    """

    text = str(text).strip()

    if "<think>" in text and "</think>" in text:
        text = text.split("</think>", 1)[1].strip()

    elif "<think>" in text:
        match = re.search(
            r"Action:\s*reschedule",
            text,
            re.IGNORECASE
        )

        if match:
            text = text[match.start():].strip()
        else:
            text = ""

    return text


def get_field_value(text, field_name):
    """
    Extract a field from agent output.
    """

    match = re.search(
        rf"{re.escape(field_name)}:\s*([^\n]+)",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1).strip()

    if value.lower() in [
        "missing",
        "<value>",
        "value",
        "<value or missing>",
        "value or missing"
    ]:
        return None

    return value


def extract_booking_id_from_text(text):
    """
    Extract a booking ID directly from text.
    """

    match = re.search(
        r"\bBKG[A-Za-z0-9]+\b",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    return match.group(0).upper()


def extract_booking_id(text):
    """
    Extract booking ID.

    First try direct extraction from the text.
    """

    return extract_booking_id_from_text(text)


def normalize_time(time_value):
    """
    Convert time into HH:MM format.
    """

    if not time_value:
        return None

    value = str(time_value).strip()

    # 24-hour format
    match = re.match(
        r"^(\d{1,2}):(\d{2})$",
        value
    )

    if match:

        hour = int(match.group(1))
        minute = int(match.group(2))

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

        return None

    # 12-hour format
    match = re.match(
        r"^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$",
        value,
        re.IGNORECASE
    )

    if match:

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        period = match.group(3).upper()

        if hour < 1 or hour > 12:
            return None

        if minute < 0 or minute > 59:
            return None

        if period == "AM":

            if hour == 12:
                hour = 0

        else:

            if hour != 12:
                hour += 12

        return f"{hour:02d}:{minute:02d}"

    return None


def extract_time_from_message(message):
    """
    Extract time directly from the user's message.

    Examples:
        2 PM     -> 14:00
        7 PM     -> 19:00
        10 AM    -> 10:00
        18:00    -> 18:00
    """

    # 12-hour time
    match = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\b",
        message,
        re.IGNORECASE
    )

    if match:

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        period = match.group(3)

        return normalize_time(
            f"{hour}:{minute:02d} {period}"
        )

    # 24-hour time
    match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        message
    )

    if match:

        return normalize_time(
            f"{match.group(1)}:{match.group(2)}"
        )

    return None


def extract_duration_from_message(message):
    """
    Extract duration directly from the user's message.

    Examples:
        1 hour       -> 60
        2 hours      -> 120
        90 minutes   -> 90
        30 mins      -> 30
    """

    # Hours
    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(hours?|hrs?)\b",
        message,
        re.IGNORECASE
    )

    if match:

        hours = float(match.group(1))

        return int(hours * 60)

    # Minutes
    match = re.search(
        r"\b(\d+)\s*(minutes?|mins?)\b",
        message,
        re.IGNORECASE
    )

    if match:

        return int(match.group(1))

    return None


def extract_date_from_message(message):
    """
    Extract booking date directly from the user's message.

    Supported examples:

        today
        tomorrow
        September 15
        September 15, 2026
        15 September
        15 September 2026
        2026-09-15
    """

    message_lower = message.lower()

    # ---------------------------------------------
    # Today
    # ---------------------------------------------

    if re.search(
        r"\btoday\b",
        message_lower
    ):

        return normalize_booking_date(
            "today"
        )

    # ---------------------------------------------
    # Tomorrow
    # ---------------------------------------------

    if re.search(
        r"\btomorrow\b",
        message_lower
    ):

        return normalize_booking_date(
            "tomorrow"
        )

    # ---------------------------------------------
    # YYYY-MM-DD
    # ---------------------------------------------

    match = re.search(
        r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b",
        message
    )

    if match:

        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        try:

            date_value = datetime(
                year,
                month,
                day
            ).date()

            return date_value.strftime(
                "%Y-%m-%d"
            )

        except ValueError:

            return None

    # ---------------------------------------------
    # Month names
    # ---------------------------------------------

    month_names = {
        name.lower(): number
        for number, name
        in enumerate(
            calendar.month_name
        )
        if name
    }

    abbreviated_months = {
        name.lower(): number
        for number, name
        in enumerate(
            calendar.month_abbr
        )
        if name
    }

    month_names.update(
        abbreviated_months
    )

    month_pattern = (
        r"(january|february|march|april|may|june|"
        r"july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    )

    # September 15, 2026
    match = re.search(
        month_pattern +
        r"\s+(\d{1,2})"
        r"(?:st|nd|rd|th)?"
        r"(?:,\s*|\s+)(20\d{2})?",
        message,
        re.IGNORECASE
    )

    if match:

        month_text = match.group(1).lower()
        day = int(match.group(2))
        year_text = match.group(3)

        if month_text == "sept":
            month = 9
        else:
            month = month_names.get(
                month_text
            )

        year = (
            int(year_text)
            if year_text
            else datetime.now(TIMEZONE).year
        )

        try:

            date_value = datetime(
                year,
                month,
                day
            ).date()

            return date_value.strftime(
                "%Y-%m-%d"
            )

        except ValueError:

            return None

    # 15 September 2026
    match = re.search(
        r"(\d{1,2})"
        r"(?:st|nd|rd|th)?\s+"
        + month_pattern +
        r"(?:,\s*|\s+)(20\d{2})?",
        message,
        re.IGNORECASE
    )

    if match:

        day = int(match.group(1))
        month_text = match.group(2).lower()
        year_text = match.group(3)

        if month_text == "sept":
            month = 9
        else:
            month = month_names.get(
                month_text
            )

        year = (
            int(year_text)
            if year_text
            else datetime.now(TIMEZONE).year
        )

        try:

            date_value = datetime(
                year,
                month,
                day
            ).date()

            return date_value.strftime(
                "%Y-%m-%d"
            )

        except ValueError:

            return None

    return None


def extract_rescheduling_details(
    result,
    user_message=None
):
    """
    Convert the Rescheduling Agent response
    into structured information.

    Deterministic values are extracted from the
    original user message first.
    """

    text = clean_result(result)

    details = {
        "action": None,
        "booking_id": None,
        "date": None,
        "start_time": None,
        "duration_mins": None
    }

    # ---------------------------------------------
    # Action
    # ---------------------------------------------

    if re.search(
        r"\breschedul",
        str(user_message),
        re.IGNORECASE
    ):

        details["action"] = "reschedule"

    else:

        action = get_field_value(
            text,
            "Action"
        )

        if action:
            details["action"] = action.lower()

    # ---------------------------------------------
    # Booking ID
    # ---------------------------------------------

    if user_message:

        details["booking_id"] = (
            extract_booking_id_from_text(
                user_message
            )
        )

    if not details["booking_id"]:

        details["booking_id"] = (
            extract_booking_id(text)
        )

    # ---------------------------------------------
    # Date
    # ---------------------------------------------

    if user_message:

        details["date"] = (
            extract_date_from_message(
                user_message
            )
        )

    if not details["date"]:

        date_value = get_field_value(
            text,
            "Date"
        )

        if date_value:

            details["date"] = (
                normalize_booking_date(
                    date_value
                )
            )

    # ---------------------------------------------
    # Start time
    # ---------------------------------------------

    if user_message:

        details["start_time"] = (
            extract_time_from_message(
                user_message
            )
        )

    if not details["start_time"]:

        time_value = get_field_value(
            text,
            "Start Time"
        )

        if time_value:

            details["start_time"] = (
                normalize_time(
                    time_value
                )
            )

    # ---------------------------------------------
    # Duration
    # ---------------------------------------------

    if user_message:

        details["duration_mins"] = (
            extract_duration_from_message(
                user_message
            )
        )

    if not details["duration_mins"]:

        duration_value = get_field_value(
            text,
            "Duration"
        )

        if duration_value:

            number_match = re.search(
                r"\d+",
                duration_value
            )

            if number_match:

                details["duration_mins"] = (
                    int(
                        number_match.group()
                    )
                )

    return details


def process_rescheduling_request_with_details(
    user_message
):
    """
    Run the Rescheduling Agent and return
    structured rescheduling information.
    """

    result = process_rescheduling_request(
        user_message
    )

    return extract_rescheduling_details(
        result,
        user_message
    )


def main():

    print("=" * 60)
    print("TURF BOOKING - RESCHEDULING AGENT RUNNER")
    print("=" * 60)

    while True:

        user_message = input(
            "You: "
        ).strip()

        if user_message.lower() == "exit":

            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            details = (
                process_rescheduling_request_with_details(
                    user_message
                )
            )

            print()
            print("Rescheduling Details:")
            print(
                f"Action      : "
                f"{details['action']}"
            )
            print(
                f"Booking ID  : "
                f"{details['booking_id']}"
            )
            print(
                f"Date        : "
                f"{details['date']}"
            )
            print(
                f"Start Time  : "
                f"{details['start_time']}"
            )
            print(
                f"Duration    : "
                f"{details['duration_mins']} minutes"
            )
            print()

        except KeyboardInterrupt:

            print()
            print("Stopped by user.")
            break

        except Exception as e:

            print()
            print(f"Error: {e}")
            print()


if __name__ == "__main__":
    main()

