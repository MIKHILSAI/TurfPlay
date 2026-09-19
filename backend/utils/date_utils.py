from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_booking_date(date_value):
    """
    Convert a user-friendly date into YYYY-MM-DD.

    Examples:

    today
        -> today's date

    tomorrow
        -> tomorrow's date

    2026-09-15
        -> 2026-09-15

    Returns:
        YYYY-MM-DD string
        or None if the date is invalid
    """

    if not date_value:
        return None

    value = str(date_value).strip().lower()

    # Get today's date using India timezone
    today = datetime.now(TIMEZONE).date()

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    if value == "today":
        return today.strftime("%Y-%m-%d")

    # --------------------------------------------------------
    # TOMORROW
    # --------------------------------------------------------

    if value == "tomorrow":
        tomorrow = today + timedelta(days=1)

        return tomorrow.strftime("%Y-%m-%d")

    # --------------------------------------------------------
    # EXACT DATE
    # --------------------------------------------------------

    try:
        parsed_date = datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

        return parsed_date.strftime("%Y-%m-%d")

    except ValueError:
        return None