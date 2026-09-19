from backend.agents.cancellation.cancellation_agent_runner import (
    process_cancellation_request_with_details
)
from backend.services.booking_notifier import send_cancellation_email
from backend.database.mongodb import db
from backend.services.cancellation_service import (
    cancel_booking_preview,
    cancel_booking
)


# ============================================================
# PREPARE CANCELLATION REQUEST
# ============================================================

def prepare_cancellation_request(
    session,
    user_message
):
    """
    Prepare a cancellation request.

    Flow:

    User
        ↓
    Cancellation Agent
        ↓
    Extract Booking ID
        ↓
    Cancellation Preview
        ↓
    Return preview to UI
    """

    # ========================================================
    # 1. Extract cancellation details
    # ========================================================

    details = process_cancellation_request_with_details(
        user_message
    )

    action = details.get("action")
    booking_id = details.get("booking_id")

    # ========================================================
    # 2. Validate action
    # ========================================================

    if action != "cancel":

        return {
            "success": False,
            "stage": "validation",
            "error_code": "INVALID_CANCELLATION_ACTION",
            "message": (
                "Unable to understand the cancellation request."
            ),
            "details": details
        }

    # ========================================================
    # 3. Validate booking ID
    # ========================================================

    if not booking_id:

        return {
            "success": False,
            "stage": "validation",
            "error_code": "BOOKING_ID_REQUIRED",
            "message": (
                "Please provide the booking ID "
                "you want to cancel."
            ),
            "details": details
        }

    # ========================================================
    # 4. Generate cancellation preview
    # ========================================================

    preview = cancel_booking_preview(
        session=session,
        booking_id=booking_id
    )

    if not preview.get("success"):

        return {
            "success": False,
            "stage": "preview",
            "error_code": preview.get(
                "error_code",
                "CANCELLATION_PREVIEW_FAILED"
            ),
            "message": preview.get(
                "message",
                "Unable to generate cancellation preview."
            ),
            "details": details
        }

    # ========================================================
    # 5. Return preview
    # ========================================================

    return {
        "success": True,
        "stage": "confirmation",
        "message": "Cancellation preview created.",
        "details": details,
        "preview": preview
    }


# ============================================================
# CONFIRM CANCELLATION
# ============================================================

def confirm_cancellation(
    details,
    preview,
    session
):
    """
    Perform final cancellation after
    explicit customer confirmation.
    """

    booking_id = details.get(
        "booking_id"
    )

    if not booking_id:

        return {
            "success": False,
            "error_code": "BOOKING_ID_REQUIRED",
            "message": "Booking ID is required."
        }

    # ========================================================
    # Final cancellation
    # ========================================================

    result = cancel_booking(
        session=session,
        booking_id=booking_id,
        confirmed=True,
        reason="Customer requested cancellation"
    )

    # ========================================================
    # Validate final result
    # ========================================================

    if not result.get("success"):

        return {
            "success": False,
            "stage": "cancellation",
            "error_code": result.get(
                "error_code",
                "CANCELLATION_FAILED"
            ),
            "message": result.get(
                "message",
                "Unable to cancel booking."
            ),
            "details": details,
            "preview": preview
        }

    # ========================================================
    # Successful result
    # ========================================================

    response = {
        "success": True,
        "stage": "cancellation",
        "message": result.get("message", "Booking cancelled successfully."),
        "booking_id": result.get("booking_id"),
        "status": result.get("status"),
        "refund_eligible": result.get("refund_eligible"),
        "refund_amount": result.get("refund_amount"),
        "refund_status": result.get("refund_status"),
        "refund_message": result.get("refund_message"),
        "details": details
    }

    # --------------------------------------------------------
    # Send cancellation email (non-blocking)
    # --------------------------------------------------------

    try:
        customer_id = session.get("customer_id")
        cancelled_booking_id = result.get("booking_id")

        if customer_id and cancelled_booking_id:
            booking = db.bookings.find_one(
                {"_id": cancelled_booking_id}
            )

            if booking:
                booking["id"] = booking["_id"]

                refund_info = {
                    "refund_eligible": result.get("refund_eligible", False),
                    "refund_amount": result.get("refund_amount", 0),
                    "refund_status": result.get("refund_status", "not_eligible"),
                }

                email_result = send_cancellation_email(
                    customer_id=customer_id,
                    booking=booking,
                    refund_info=refund_info
                )

                if not email_result.get("sent"):
                    print(
                        f"[EMAIL] Cancellation email failed: "
                        f"{email_result.get('error')}"
                    )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return response

# ============================================================
# TERMINAL TEST
# ============================================================

def main():

    print("=" * 60)
    print("TURF BOOKING - CANCELLATION PROCESS")
    print("=" * 60)

    session = {}

    customer_id = input(
        "Enter Customer ID: "
    ).strip()

    if not customer_id:

        print("Customer ID is required.")
        return

    session["customer_id"] = customer_id
    session["logged_in"] = True

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

            # ------------------------------------------------
            # Prepare
            # ------------------------------------------------

            result = prepare_cancellation_request(
                session=session,
                user_message=user_message
            )

            print()
            print("Cancellation Result:")
            print(result)
            print()

            # ------------------------------------------------
            # Terminal confirmation for testing only
            # ------------------------------------------------

            if (
                result.get("success")
                and result.get("stage") == "confirmation"
            ):

                confirmation = input(
                    "Confirm cancellation? (yes/no): "
                ).strip().lower()

                if confirmation in ["yes", "y"]:

                    final_result = confirm_cancellation(
                        details=result.get(
                            "details",
                            {}
                        ),
                        preview=result.get(
                            "preview",
                            {}
                        ),
                        session=session
                    )

                    print()
                    print("Final Result:")
                    print(final_result)
                    print()

                else:

                    print(
                        "Booking cancellation was not confirmed."
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