from crewai import Task

from backend.agents.booking.booking_agent import booking_agent


# ============================================================
# BOOKING TASK
# ============================================================

def create_booking_task(user_message):

    task = Task(
        description=f"""
Understand the customer's booking request.

Customer request:
{user_message}

Identify the following information if it is provided:

1. Sport or facility
   Examples:
   - badminton
   - football
   - tennis

2. Date
   The customer may provide:
   - an exact date, such as 2026-09-15
   - today
   - tomorrow
   - a relative date

   Preserve relative dates such as "tomorrow" instead of marking
   them as missing.

3. Start time
   Convert times to 24-hour format.
   Example:
   - 6 PM -> 18:00
   - 7:30 PM -> 19:30

4. Duration
   Convert the duration into minutes.
   Examples:
   - 1 hour -> 60 minutes
   - 90 minutes -> 90 minutes

5. Number of players
   If the customer provides it.

IMPORTANT:

- Do not create a booking.
- Do not access MongoDB.
- Do not calculate the final price.
- Do not claim that a booking was successful.
- Do not invent missing information.
- Preserve relative dates such as "tomorrow".
- If the date is not provided at all, mark it as missing.

Return the extracted information in this format:

Sport: <value or missing>
Date: <value or missing>
Start Time: <value or missing>
Duration: <value or missing>
Players: <value or missing>
""",

        expected_output=(
            "The customer's booking information containing "
            "sport, date, start time, duration, and players."
        ),

        agent=booking_agent
    )

    return task