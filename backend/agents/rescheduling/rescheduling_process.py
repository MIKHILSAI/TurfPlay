from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.services.booking_notifier import send_reschedule_confirmation
from backend.agents.rescheduling.rescheduling_agent_runner import (
    process_rescheduling_request_with_details
)

from backend.services.reschedule_service import (
    reschedule_booking_preview,
    reschedule_booking
)


TIMEZONE = ZoneInfo("Asia/Kolkata")


def calculate_end_time(start_time, duration_mins):
    """
    Calculate end time from start time and duration.
    """

    start_datetime = datetime.strptime(
        start_time,
        "%H:%M"
    )

    end_datetime = (
        start_datetime
        + timedelta(minutes=duration_mins)
    )

    return end_datetime.strftime("%H:%M")


def print_preview(preview):
    """
    Display the rescheduling preview.
    """

    print()
    print("Rescheduling Preview")
    print("-" * 60)

    print(
        f"Booking ID : "
        f"{preview.get('booking_id')}"
    )

    current_booking = preview.get(
        "current_booking",
        {}
    )

    new_booking = preview.get(
        "new_booking",
        {}
    )

    print()
    print("Current Booking:")

    print(
        f"Date       : "
        f"{current_booking.get('booking_date')}"
    )

    print(
        f"Time       : "
        f"{current_booking.get('start_time')} - "
        f"{current_booking.get('end_time')}"
    )

    print(
        f"Amount     : "
        f"₹{current_booking.get('total_amount', 0):.2f}"
    )

    print()
    print("New Booking:")

    print(
        f"Date       : "
        f"{new_booking.get('booking_date')}"
    )

    print(
        f"Time       : "
        f"{new_booking.get('start_time')} - "
        f"{new_booking.get('end_time')}"
    )

    print(
        f"Amount     : "
        f"₹{new_booking.get('total_amount', 0):.2f}"
    )

    price_difference = preview.get(
        "price_difference",
        {}
    )

    print()
    print("Price Difference:")

    print(
        f"Difference        : "
        f"₹{price_difference.get('difference', 0):.2f}"
    )

    print(
        f"Additional Amount : "
        f"₹{price_difference.get('additional_amount', 0):.2f}"
    )

    print(
        f"Refund Amount     : "
        f"₹{price_difference.get('refund_amount', 0):.2f}"
    )

    print("-" * 60)


def prepare_rescheduling_request(user_message, session):
    """
    Create a rescheduling preview without changing the booking.
    """

    details = process_rescheduling_request_with_details(
        user_message
    )

    if details.get("action") != "reschedule":
        return {
            "success": False,
            "stage": "validation",
            "error_code": "INVALID_RESCHEDULING_ACTION",
            "message": "Unable to understand the rescheduling request.",
            "details": details
        }

    booking_id = details.get("booking_id")
    new_date = details.get("date")
    new_start_time = details.get("start_time")
    duration_mins = details.get("duration_mins")

    if not booking_id:
        return {
            "success": False,
            "stage": "validation",
            "error_code": "BOOKING_ID_REQUIRED",
            "message": "Please provide the booking ID you want to reschedule.",
            "details": details
        }

    if not new_date:
        return {
            "success": False,
            "stage": "validation",
            "error_code": "DATE_REQUIRED",
            "message": "Please provide the new booking date.",
            "details": details
        }

    if not new_start_time:
        return {
            "success": False,
            "stage": "validation",
            "error_code": "START_TIME_REQUIRED",
            "message": "Please provide the new start time.",
            "details": details
        }

    if not duration_mins:
        return {
            "success": False,
            "stage": "validation",
            "error_code": "DURATION_REQUIRED",
            "message": "Please provide the booking duration.",
            "details": details
        }

    new_end_time = calculate_end_time(
        new_start_time,
        duration_mins
    )

    preview = reschedule_booking_preview(
        session=session,
        booking_id=booking_id,
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time
    )

    if not preview.get("success"):
        return {
            "success": False,
            "stage": "preview",
            "error_code": preview.get(
                "error_code",
                "RESCHEDULING_PREVIEW_FAILED"
            ),
            "message": preview.get(
                "message",
                "Unable to create rescheduling preview."
            ),
            "details": details
        }

    return {
        "success": True,
        "stage": "confirmation",
        "message": "Rescheduling preview created.",
        "details": details,
        "preview": preview
    }


def confirm_rescheduling(details, preview, session):
    """
    Confirm and execute the rescheduling.
    """

    if not details:
        return {
            "success": False,
            "error_code": "RESCHEDULING_DETAILS_MISSING",
            "message": "Rescheduling details are missing."
        }

    booking_id = details.get("booking_id")
    new_date = details.get("date")
    new_start_time = details.get("start_time")
    duration_mins = details.get("duration_mins")

    if not booking_id:
        return {
            "success": False,
            "error_code": "BOOKING_ID_REQUIRED",
            "message": "Booking ID is required."
        }

    new_end_time = calculate_end_time(
        new_start_time,
        duration_mins
    )

    result = reschedule_booking(
        session=session,
        booking_id=booking_id,
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time,
        confirmed=True
    )

    if not result.get("success"):
        return result

    # --------------------------------------------------------
    # Send reschedule email (non-blocking)
    # --------------------------------------------------------

    try:
        customer_id = session.get("customer_id")
        updated_booking = result.get("booking", {})

        if customer_id and updated_booking:
            updated_booking["id"] = result.get("booking_id", booking_id)

            email_result = send_reschedule_confirmation(
                customer_id=customer_id,
                booking=updated_booking
            )

            if not email_result.get("sent"):
                print(
                    f"[EMAIL] Reschedule confirmation failed: "
                    f"{email_result.get('error')}"
                )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return {
        **result,
        "stage": "rescheduling"
    }


def process_rescheduling(
    session,
    user_message
):
    """
    Complete rescheduling workflow.

    Flow:

    User request
        ↓
    Rescheduling Agent
        ↓
    Extract details
        ↓
    Backend preview
        ↓
    Customer confirmation
        ↓
    Backend reschedule
    """

    # --------------------------------------------------
    # STEP 1
    # Understand the CURRENT user request
    # --------------------------------------------------

    details = process_rescheduling_request_with_details(
        user_message
    )

    print()
    print("Extracted Rescheduling Details")
    print("-" * 60)

    print(
        f"Action      : "
        f"{details.get('action')}"
    )

    print(
        f"Booking ID  : "
        f"{details.get('booking_id')}"
    )

    print(
        f"Date        : "
        f"{details.get('date')}"
    )

    print(
        f"Start Time  : "
        f"{details.get('start_time')}"
    )

    print(
        f"Duration    : "
        f"{details.get('duration_mins')} minutes"
    )

    print("-" * 60)

    # --------------------------------------------------
    # STEP 2
    # Validate extracted information
    # --------------------------------------------------

    if details.get("action") != "reschedule":

        return {
            "success": False,
            "error_code": "INVALID_RESCHEDULING_ACTION",
            "message": (
                "Unable to understand the "
                "rescheduling request."
            ),
            "details": details
        }

    booking_id = details.get(
        "booking_id"
    )

    new_date = details.get(
        "date"
    )

    new_start_time = details.get(
        "start_time"
    )

    duration_mins = details.get(
        "duration_mins"
    )

    if not booking_id:

        return {
            "success": False,
            "error_code": "BOOKING_ID_REQUIRED",
            "message": (
                "Please provide the booking ID "
                "you want to reschedule."
            ),
            "details": details
        }

    if not new_date:

        return {
            "success": False,
            "error_code": "DATE_REQUIRED",
            "message": (
                "Please provide the new booking date."
            ),
            "details": details
        }

    if not new_start_time:

        return {
            "success": False,
            "error_code": "START_TIME_REQUIRED",
            "message": (
                "Please provide the new start time."
            ),
            "details": details
        }

    if not duration_mins:

        return {
            "success": False,
            "error_code": "DURATION_REQUIRED",
            "message": (
                "Please provide the booking duration."
            ),
            "details": details
        }

    # --------------------------------------------------
    # STEP 3
    # Calculate end time using Python
    # --------------------------------------------------

    new_end_time = calculate_end_time(
        new_start_time,
        duration_mins
    )

    print()
    print(
        f"Calculated New Time: "
        f"{new_start_time} - {new_end_time}"
    )

    # --------------------------------------------------
    # STEP 4
    # Ask backend for preview
    # --------------------------------------------------

    preview = reschedule_booking_preview(
        session=session,
        booking_id=booking_id,
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time
    )

    if not preview.get("success"):

        print()
        print("Rescheduling Preview Failed")
        print("-" * 60)
        print(
            preview.get(
                "message",
                "Unable to reschedule booking."
            )
        )
        print("-" * 60)

        return preview

    # --------------------------------------------------
    # STEP 5
    # Display preview
    # --------------------------------------------------

    print_preview(preview)

    # --------------------------------------------------
    # STEP 6
    # Ask customer for confirmation
    # --------------------------------------------------

    confirmation = input(
        "Confirm rescheduling? (yes/no): "
    ).strip().lower()

    if confirmation not in [
        "yes",
        "y"
    ]:

        print()
        print("Rescheduling cancelled.")

        return {
            "success": False,
            "error_code": "RESCHEDULING_NOT_CONFIRMED",
            "message": (
                "Rescheduling was not confirmed."
            ),
            "details": details
        }

    # --------------------------------------------------
    # STEP 7
    # Final backend rescheduling
    # --------------------------------------------------

    result = reschedule_booking(
        session=session,
        booking_id=booking_id,
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time,
        confirmed=True
    )

    # --------------------------------------------------
    # STEP 7.5
    # Send reschedule email (non-blocking)
    # --------------------------------------------------

    if result.get("success"):
        try:
            customer_id = session.get("customer_id")
            updated_booking = result.get("booking", {})

            if customer_id and updated_booking:
                updated_booking["id"] = result.get("booking_id", booking_id)

                email_result = send_reschedule_confirmation(
                    customer_id=customer_id,
                    booking=updated_booking
                )

                if not email_result.get("sent"):
                    print(
                        f"[EMAIL] Reschedule confirmation failed: "
                        f"{email_result.get('error')}"
                    )
        except Exception as e:
            print(f"[EMAIL] Unexpected error: {e}")

    # --------------------------------------------------
    # STEP 8
    # Display final result
    # --------------------------------------------------

    print()
    print("Result:")
    print(result)

    return result


def main():

    print("=" * 60)
    print("TURF BOOKING - RESCHEDULING PROCESS")
    print("=" * 60)

    # --------------------------------------------------
    # Temporary session for terminal testing
    # --------------------------------------------------

    customer_id = input(
        "Enter Customer ID: "
    ).strip()

    session = {
        "customer_id": customer_id,
        "logged_in": True
    }

    while True:

        user_message = input(
            "You: "
        ).strip()

        if user_message.lower() == "exit":

            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            process_rescheduling(
                session=session,
                user_message=user_message
            )

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