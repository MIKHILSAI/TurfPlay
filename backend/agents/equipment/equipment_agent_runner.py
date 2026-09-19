import re

from backend.agents.equipment.equipment_crew import process_equipment_request
from backend.utils.date_utils import normalize_booking_date


def clean_result(text):
    """
    Remove CrewAI/Qwen thinking output and return
    only the useful final answer.
    """
    text = str(text).strip()

    if "<think>" in text:
        if "</think>" in text:
            text = text.split("</think>", 1)[1].strip()
        else:
            text = text.split("<think>", 1)[1].strip()

    return text


def get_field_value(text, field_name):
    """
    Extract a field value from the agent response.
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
    Convert HH:MM into a consistent 24-hour format.
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


def extract_equipment_details(result):
    """
    Convert the Equipment Agent response
    into a structured dictionary.
    """

    text = clean_result(result)

    details = {
        "action": None,
        "equipment": None,
        "quantity": None,
        "date": None,
        "start_time": None,
        "duration_mins": None
    }

    # Action
    action_value = get_field_value(text, "Action")

    if action_value:
        details["action"] = action_value.lower()

    # Equipment
    equipment_value = get_field_value(text, "Equipment")

    if equipment_value:
        details["equipment"] = equipment_value.lower()

    # Quantity
    quantity_value = get_field_value(text, "Quantity")

    if quantity_value:
        number_match = re.search(r"\d+", quantity_value)

        if number_match:
            details["quantity"] = int(number_match.group())

    # Date
    date_value = get_field_value(text, "Date")

    if date_value:
        details["date"] = normalize_booking_date(date_value)

    # Start time
    time_value = get_field_value(text, "Start Time")

    if time_value:
        details["start_time"] = normalize_time(time_value)

    # Duration
    duration_value = get_field_value(text, "Duration")

    if duration_value:
        number_match = re.search(r"\d+", duration_value)

        if number_match:
            details["duration_mins"] = int(number_match.group())

    return details


def process_equipment_request_with_details(user_message):
    """
    Run the Equipment Agent and return
    structured equipment information.
    """

    result = process_equipment_request(user_message)

    return extract_equipment_details(result)


def main():

    print("=" * 60)
    print("TURF BOOKING - EQUIPMENT AGENT RUNNER")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":
            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            details = process_equipment_request_with_details(
                user_message
            )

            print()
            print("Equipment Details:")
            print(f"Action      : {details['action']}")
            print(f"Equipment   : {details['equipment']}")
            print(f"Quantity    : {details['quantity']}")
            print(f"Date        : {details['date']}")
            print(f"Start Time  : {details['start_time']}")
            print(f"Duration    : {details['duration_mins']} minutes")
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