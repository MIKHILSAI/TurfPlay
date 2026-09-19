from crewai import Task

from backend.agents.cancellation.cancellation_agent import (
    cancellation_agent
)


def create_cancellation_task(user_message):

    task = Task(
        description=f"""
Extract cancellation information from this request.

User:
{user_message}

Return exactly 2 lines:

Action: cancel
Booking ID: booking ID

Rules:
- Identify the booking ID from the user's request.
- Booking IDs normally look like BKG followed by characters or numbers.
- Do not invent a booking ID.
- If the booking ID is missing, write missing.
- Do not cancel the booking.
- Do not access MongoDB.
- Do not calculate refunds.
- Return ONLY the 2 lines.

Example:

Action: cancel
Booking ID: BKG93285D3F
""",
        expected_output=(
            "Exactly 2 lines: Action and Booking ID."
        ),
        agent=cancellation_agent
    )

    return task