from backend.services.booking_service import create_booking
from backend.services.booking_notifier import send_booking_confirmation


def confirm_and_create_booking(
    session,
    resource_id,
    booking_date,
    start_time,
    end_time,
    confirmed
):
    """
    Create a booking only after the customer explicitly confirms.

    The actual booking creation is handled by booking_service.py.
    """

    # ============================================================
    # 1. Check confirmation
    # ============================================================

    if confirmed is not True:
        return {
            "success": False,
            "booking_created": False,
            "error_code": "BOOKING_NOT_CONFIRMED",
            "message": "Booking was not confirmed by the customer."
        }

    # ============================================================
    # 2. Create booking through backend service
    # ============================================================

    result = create_booking(
        session=session,
        resource_id=resource_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time
    )

    # ============================================================
    # 3. Handle failure
    # ============================================================

    if not result.get("success"):
        return {
            "success": False,
            "booking_created": False,
            "error_code": result.get(
                "error_code",
                "BOOKING_FAILED"
            ),
            "message": result.get(
                "message",
                "Unable to create booking."
            )
        }

    # ============================================================
    # 4. Send confirmation email (non-blocking)
    # ============================================================

    booking = result.get("booking")

    try:
        customer_id = booking.get("customer_id")
        if customer_id and booking:
            email_result = send_booking_confirmation(
                customer_id=customer_id,
                booking=booking
            )
            if not email_result.get("sent"):
                print(
                    f"[EMAIL] Booking confirmation failed: "
                    f"{email_result.get('error')}"
                )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    # ============================================================
    # 5. Return success
    # ============================================================

    return {
        "success": True,
        "booking_created": True,
        "message": "Booking created successfully.",
        "booking": booking
    }


def print_booking_result(result):
    """
    Display the final booking result.
    """

    print()

    if not result.get("success"):
        print("=" * 50)
        print("BOOKING NOT CREATED")
        print("=" * 50)
        print(result.get("message"))
        print("=" * 50)
        return

    booking = result.get("booking", {})

    print("=" * 50)
    print("BOOKING CONFIRMED")
    print("=" * 50)

    print(
        f"Booking ID  : "
        f"{booking.get('id', 'N/A')}"
    )

    print(
        f"Resource    : "
        f"{booking.get('resource_id', 'N/A')}"
    )

    print(
        f"Date        : "
        f"{booking.get('booking_date', 'N/A')}"
    )

    print(
        f"Time        : "
        f"{booking.get('start_time', 'N/A')} - "
        f"{booking.get('end_time', 'N/A')}"
    )

    print(
        f"Status      : "
        f"{booking.get('status', 'N/A')}"
    )

    print("=" * 50)