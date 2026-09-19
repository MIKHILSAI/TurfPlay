import re

from backend.agents.cancellation.cancellation_crew import (
    process_cancellation_request
)


def clean_result(text):
    """
    Remove CrewAI/Qwen thinking output
    and return only the useful final answer.
    """

    text = str(text).strip()

    if "<think>" in text:

        if "</think>" in text:
            text = text.split("</think>", 1)[1].strip()

        else:
            text = text.split("<think>", 1)[0].strip()

    return text


def extract_booking_id(text):
    """
    Extract a booking ID from the agent response.

    Expected format:
    BKG93285D3F
    """

    match = re.search(
        r"Booking ID:\s*(BKG[A-Za-z0-9]+)",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    return match.group(1).upper()


def extract_cancellation_details(result):
    """
    Convert the Cancellation Agent response
    into structured information.
    """

    text = clean_result(result)

    action = None

    action_match = re.search(
        r"Action:\s*([^\n]+)",
        text,
        re.IGNORECASE
    )

    if action_match:
        action = action_match.group(1).strip().lower()

    booking_id = extract_booking_id(text)

    return {
        "action": action,
        "booking_id": booking_id
    }


def process_cancellation_request_with_details(user_message):
    """
    Run the Cancellation Agent and return
    structured cancellation information.
    """

    result = process_cancellation_request(
        user_message
    )

    return extract_cancellation_details(result)


def main():

    print("=" * 60)
    print("TURF BOOKING - CANCELLATION AGENT RUNNER")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":
            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            details = (
                process_cancellation_request_with_details(
                    user_message
                )
            )

            print()
            print("Cancellation Details:")
            print(
                f"Action     : {details['action']}"
            )
            print(
                f"Booking ID : {details['booking_id']}"
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