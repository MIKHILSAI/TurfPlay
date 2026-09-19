from crewai import Task

from backend.agents.customer.customer_agent import (
    customer_agent
)


def create_customer_task(user_message):

    task = Task(
        description=f"""
Understand the customer request below.

User:
{user_message}

Identify the customer-related operation being requested.

Return exactly 2 lines:

Action: <action>
Details: <short description>

Allowed actions:

- profile
- bookings
- membership
- equipment
- unknown

Rules:

- Use profile when the customer asks about their profile or account details.
- Use bookings when the customer asks to view, list, or check their bookings.
- Use membership when the customer asks about membership information.
- Use equipment when the customer asks about equipment they have rented or reserved.
- Use unknown when the request does not match any allowed action.
- Do not access MongoDB.
- Do not execute database queries.
- Do not modify customer data.
- Do not invent customer information.
- Return ONLY the requested 2 lines.

Example:

Action: bookings
Details: Customer wants to view their bookings.
""",

        expected_output=(
            "Exactly 2 lines: Action and Details."
        ),

        agent=customer_agent
    )

    return task
