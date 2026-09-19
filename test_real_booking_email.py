from backend.database.mongodb import db
from backend.services.cancellation_service import cancel_booking


def main():
    print("=" * 60)
    print("REAL CANCELLATION TEST")
    print("=" * 60)

    # Find a CONFIRMED booking (not cancelled)
    booking = db.bookings.find_one({"status": "confirmed"})

    if not booking:
        print("NO CONFIRMED BOOKING FOUND")
        print("Book a new court from the app first, then run this.")
        return

    booking_id = booking["_id"]
    customer_id = booking["customer_id"]

    print(f"Booking ID: {booking_id}")
    print(f"Customer:   {customer_id}")
    print()

    session = {
        "customer_id": customer_id,
        "logged_in": True,
    }

    print("Calling cancel_booking()...")
    print()

    result = cancel_booking(
        session=session,
        booking_id=booking_id,
        confirmed=True,
        reason="Test cancellation",
    )

    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()