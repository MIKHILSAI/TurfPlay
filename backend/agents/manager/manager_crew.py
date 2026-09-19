from crewai import Crew, Process

from backend.agents.manager.manager_agent import REQUEST_CATEGORIES
from backend.agents.manager.manager_task import create_manager_task
from backend.agents.manager.manager_agent import manager_agent

from backend.agents.knowledge.knowledge_process import (
    process_knowledge_request_with_details
)

from backend.agents.booking.booking_process import (
    prepare_booking_request
)



from backend.agents.cancellation.cancellation_process import (
    prepare_cancellation_request
)

from backend.agents.rescheduling.rescheduling_process import (
    prepare_rescheduling_request
)

from backend.agents.customer.customer_process import (
    process_customer_request_with_details
)

from backend.agents.equipment.equipment_agent_runner import (
    process_equipment_request_with_details
)


# ============================================================
# CLEAN MODEL OUTPUT
# ============================================================

def clean_category(result):
    """
    Extract a category from the LLM output.

    Returns (category, general_reply):
    - If LLM returned a single category, reply is None.
    - If LLM returned 'general' + reply text, both are returned.
    """

    text = str(result).strip()
    text = text.replace("<think>", "").replace("</think>", "")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # --------------------------------------------------------
    # 1. Look for exact category on any line (any position)
    # --------------------------------------------------------

    for idx, line in enumerate(lines):
        lower = line.lower()

        # exact match
        for category in REQUEST_CATEGORIES:
            if lower == category:
                if category == "general":
                    reply = "\n".join(lines[idx + 1:]).strip()
                    return "general", (reply or None)
                return category, None

        # "category: <reply>" on same line
        for category in REQUEST_CATEGORIES:
            if lower.startswith(f"{category}:") or lower.startswith(f"{category} "):
                if category == "general":
                    reply = line[len(category):].lstrip(": ").strip()
                    if not reply:
                        reply = "\n".join(lines[idx + 1:]).strip()
                    return "general", (reply or None)
                return category, None

    # --------------------------------------------------------
    # 2. Look for "final selection: X" or "decision: X"
    # --------------------------------------------------------

    for line in reversed(lines):
        lower = line.lower()
        for category in REQUEST_CATEGORIES:
            if (
                f"final selection: {category}" in lower
                or f"decision: {category}" in lower
            ):
                return category, None

    # --------------------------------------------------------
    # 3. Fallback
    # --------------------------------------------------------

    return "unknown", None
import re

GREETING_WORDS = {
    "hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening", "good day", "howdy", "sup", "yo"
}

def is_greeting(message):
    cleaned = re.sub(r"[^\w\s]", "", message).strip().lower()
    return cleaned in GREETING_WORDS or any(cleaned.startswith(g + " ") for g in ["hi", "hello", "hey", "good morning", "good evening"])

# ============================================================
# MANAGER CLASSIFICATION
# ============================================================

def classify_request(user_message):

    manager_task = create_manager_task(user_message)

    manager_crew = Crew(
        agents=[manager_agent],
        tasks=[manager_task],
        process=Process.sequential,
        verbose=True
    )

    result = manager_crew.kickoff()

    category, general_reply = clean_category(result)

    return category, general_reply


# ============================================================
# MANAGER ROUTER
# ============================================================

def route_request(user_message, session):
    """
    Classify the customer request and route it to
    the appropriate specialist agent.
    """

    # ---------------------------------------------------------
    # Get request category
    # ---------------------------------------------------------

    category, general_reply = classify_request(user_message)

    print()
    print("Manager Classification:")
    print(category)
    if general_reply:
        print(f"General reply: {general_reply[:80]}...")
    print()

    return route_classified_request(
        category=category,
        user_message=user_message,
        session=session
    )


def route_classified_request(category, user_message, session):
    """Route a request after the manager has already classified it."""

    print(f"Manager route -> {category}")

    if category == "greeting":
        return {
            "success": True,
            "message": "Hi there! How can I help you today? I can help you check court availability, book a turf, rent equipment, or view your bookings.",
            "answer": "Hi there! How can I help you today? I can help you check court availability, book a turf, rent equipment, or view your bookings.",
        }

    # ---------------------------------------------------------
    # BOOKING
    # ---------------------------------------------------------

    if category == "booking":

        return prepare_booking_request(
            user_message,
            session=session,
        )
    # ---------------------------------------------------------
    # EQUIPMENT
    # ---------------------------------------------------------

    if category == "equipment":

        message_lower = user_message.lower()

        # Customer wants to view their rented equipment
        if (
            "my rented equipment" in message_lower
            or "my equipment" in message_lower
            or "equipment i rented" in message_lower
            or "equipment i have rented" in message_lower
        ):

            return process_customer_request_with_details(
                user_message,
                session
            )

        # Other equipment operations:
        # Only extract details here. The chat route
        # (chat.py) handles the actual flow (info, rent,
        # reserve, return) without blocking on input().
        details = process_equipment_request_with_details(
            user_message
        )

        return {
            "success": True,
            "details": details,
            "request_message": user_message,
        }
    # ---------------------------------------------------------
    # CANCELLATION
    # ---------------------------------------------------------

    if category == "cancellation":
        return prepare_cancellation_request(
            session=session,
            user_message=user_message
        )

    # ---------------------------------------------------------
    # RESCHEDULING
    # ---------------------------------------------------------

    if category == "rescheduling":

        return prepare_rescheduling_request(
            user_message=user_message,
            session=session
        )

    # ---------------------------------------------------------
    # CUSTOMER
    # ---------------------------------------------------------

    if category == "customer":

        return process_customer_request_with_details(
            user_message,
            session
        )

    # ---------------------------------------------------------
    # KNOWLEDGE
    # ---------------------------------------------------------

    if category == "knowledge":
        return process_knowledge_request_with_details(
            user_message
        )
    # ---------------------------------------------------------
    # GENERAL
    # ---------------------------------------------------------

    if category == "general":
        return {
            "success": True,
            "category": "general",
            "message": general_reply or (
                "Hi! I'm the TurfPlay assistant. "
                "I can help you book courts, rent equipment, "
                "check availability, or answer questions "
                "about our facility. What would you like to do?"
            )
        }

    # ---------------------------------------------------------
    # UNKNOWN
    # ---------------------------------------------------------

    return {
        "success": False,
        "error_code": "UNKNOWN_REQUEST",
        "message": (
            "I could not understand your request. "
            "Please try again."
        )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("TURF BOOKING - MANAGER AGENT")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":

            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            category = classify_request(
                user_message
            )

            print()
            print("Manager Classification:")
            print(category)
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