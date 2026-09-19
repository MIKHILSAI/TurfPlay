from backend.agents.customer.customer_crew import process_customer_request
from backend.services.booking_formatter import format_bookings
from backend.services.membership_formatter import format_membership
from backend.services.membership_service import get_customer_membership
import re
from backend.services.customer_service import (
    get_customer_bookings,
    get_customer_equipment
)
from backend.services.auth_service import get_current_customer


def process_customer_request_with_details(user_message, session):
    """
    Process a customer request and call the appropriate
    backend service.
    """

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    customer_id = session.get("customer_id")

    if not customer_id:
        return {
            "success": False,
            "error_code": "AUTH_REQUIRED",
            "message": "Customer login is required."
        }

    # ---------------------------------------------------------
    # Run Customer Agent
    # ---------------------------------------------------------

    agent_result = process_customer_request(user_message)

    print()
    print("Customer Agent Result:")
    print("-" * 60)
    print(agent_result)
    print("-" * 60)

    action = clean_customer_action(agent_result)

    print("Clean Customer Action:", action)

    # ---------------------------------------------------------
    # BOOKINGS
    # ---------------------------------------------------------

    if action == "bookings":
        result = get_customer_bookings(session)
        return format_bookings(result)

    # ---------------------------------------------------------
    # MEMBERSHIP
    # ---------------------------------------------------------

    if action == "membership":
        result = get_customer_membership(customer_id)
        return format_membership(result)

    # ---------------------------------------------------------
    # PROFILE
    # ---------------------------------------------------------

    if action == "profile":

        customer = get_current_customer(session)

        if not customer:
            return {
                "success": False,
                "error_code": "CUSTOMER_NOT_FOUND",
                "message": "Customer account could not be found."
            }

        return {
            "success": True,
            "customer": customer
        }

    # ---------------------------------------------------------
    # EQUIPMENT
    # ---------------------------------------------------------

    if action == "equipment":
        return get_customer_equipment(session)

    # ---------------------------------------------------------
    # Unsupported operation
    # ---------------------------------------------------------

    return {
        "success": False,
        "error_code": "UNSUPPORTED_CUSTOMER_ACTION",
        "message": "This customer operation is not implemented yet."
    }
def clean_customer_action(result):
    """
    Extract the final customer action from the agent response.
    Ignore Qwen's <think>...</think> reasoning.
    """

    text = str(result)

    # Remove Qwen thinking section
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Find the final Action line
    for line in text.splitlines():
        line = line.strip()

        if line.lower().startswith("action:"):
            return line.split(":", 1)[1].strip().lower()

    return "unknown"