from crewai import Task

from backend.agents.rescheduling.rescheduling_agent import (
    rescheduling_agent
)


def create_rescheduling_task(user_message):

    task = Task(
        description=f"""
Extract rescheduling information from this request.

User:
{user_message}

Return exactly 4 lines:

Action: reschedule
Booking ID: booking ID
Date: today/tomorrow/YYYY-MM-DD
Start Time: HH:MM
Duration: minutes

Rules:

- Identify the booking ID from the user's request.
- Booking IDs normally start with BKG.
- Do not invent a booking ID.
- If the booking ID is missing, write missing.
- Identify the new requested date.
- Convert "today" or "tomorrow" literally.
- Convert dates to YYYY-MM-DD only when the exact date is provided.
- Convert 6 PM to 18:00.
- Convert 7 PM to 19:00.
- Convert 6 AM to 06:00.
- Convert 1 hour to 60.
- Convert 90 minutes to 90.
- Do not invent missing date, time, or duration.
- If a value is missing, write missing.
- Do not access MongoDB.
- Do not check availability.
- Do not calculate pricing.
- Do not reschedule the booking.
- Return ONLY the requested lines.

Example:

Action: reschedule
Booking ID: BKG93285D3F
Date: tomorrow
Start Time: 19:00
Duration: 60
""",
        expected_output=(
            "Exactly 5 lines: Action, Booking ID, Date, "
            "Start Time, and Duration."
        ),
        agent=rescheduling_agent
    )

    return task