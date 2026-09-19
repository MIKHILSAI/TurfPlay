import re

from backend.agents.booking.booking_crew import process_booking_request
from backend.utils.date_utils import normalize_booking_date


def clean_result(text):
    """
    Clean the Booking Agent result.

    Qwen may include <think> output before the actual answer.
    Since the useful booking fields can sometimes appear inside
    the thinking output, we keep the full text and let the
    field extractors select the correct values.
    """

    return str(text).strip()


def get_field_value(text, field_name):
    """
    Find the last useful value for a field.

    Example:

    Sport: <value or missing>
    Sport: badminton

    Returns:
        badminton
    """

    matches = list(
        re.finditer(
            rf"{field_name}:\s*([^\n]+)",
            text,
            re.IGNORECASE
        )
    )

    if not matches:
        return None

    valid_values = []

    invalid_values = [
        "missing",
        "<value or missing>",
        "value or missing",
        "<value>",
        "value"
    ]

    for match in matches:

        value = match.group(1).strip()

        if value.lower() in invalid_values:
            continue

        valid_values.append(value)

    if valid_values:
        return valid_values[-1]

    return None


def normalize_time(time_value):
    """
    Normalize time into HH:MM format.

    Examples:

    18:0  -> 18:00
    9:5   -> 09:05
    18:00 -> 18:00
    """

    if not time_value:
        return None

    match = re.match(
        r"^\s*(\d{1,2}):(\d{1,2})\s*$",
        time_value
    )

    if not match:
        return time_value

    hour = int(match.group(1))
    minute = int(match.group(2))

    return f"{hour:02d}:{minute:02d}"


def extract_booking_details(result):
    """
    Convert Booking Agent output into a Python dictionary.
    """

    text = clean_result(result)

    details = {
        "sport": None,
        "date": None,
        "start_time": None,
        "duration_mins": None,
        "players": None
    }

    # ============================================================
    # SPORT
    # ============================================================

    sport_value = get_field_value(
        text,
        "Sport"
    )

    if sport_value:
        details["sport"] = sport_value.lower()

    # ============================================================
    # DATE
    # ============================================================

    date_value = get_field_value(
        text,
        "Date"
    )

    if date_value:
        details["date"] = normalize_booking_date(
            date_value
        )

    # ============================================================
    # START TIME
    # ============================================================

    time_value = get_field_value(
        text,
        "Start Time"
    )

    if time_value:
        details["start_time"] = normalize_time(
            time_value
        )

    # ============================================================
    # DURATION
    # ============================================================

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
            details["duration_mins"] = int(
                number_match.group()
            )

    # ============================================================
    # PLAYERS
    # ============================================================

    players_value = get_field_value(
        text,
        "Players"
    )

    if players_value:

        number_match = re.search(
            r"\d+",
            players_value
        )

        if number_match:
            details["players"] = int(
                number_match.group()
            )

    return details


def process_booking_request_with_details(user_message):
    """
    Send the customer request to the Booking Agent
    and return structured booking details.
    """

    result = process_booking_request(
        user_message
    )

    return extract_booking_details(
        result
    )


def main():

    print("=" * 60)
    print("BOOKING AGENT RUNNER")
    print("=" * 60)

    user_message = input(
        "You: "
    ).strip()

    if not user_message:
        print("No request provided.")
        return

    details = process_booking_request_with_details(
        user_message
    )

    print()
    print("Extracted Booking Details:")
    print("-" * 40)

    print(
        f"sport: {details['sport']}"
    )

    print(
        f"date: {details['date']}"
    )

    print(
        f"start_time: {details['start_time']}"
    )

    print(
        f"duration_mins: {details['duration_mins']}"
    )

    print(
        f"players: {details['players']}"
    )


if __name__ == "__main__":
    main()