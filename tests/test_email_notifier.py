from backend.database.mongodb import db
from backend.services.booking_notifier import (
    send_booking_confirmation,
    send_reschedule_confirmation,
    send_cancellation_email,
    send_equipment_confirmation,
)


def test_booking_confirmation():
    customer = db.customers.find_one()
    if not customer:
        print("No customer found")
        return

    booking = db.bookings.find_one({"customer_id": customer["_id"]})
    if not booking:
        print("No booking found")
        return

    result = send_booking_confirmation(
        customer_id=customer["_id"],
        booking={**booking, "id": booking["_id"]}
    )
    print("Booking confirmation:", result)


def test_reschedule():
    customer = db.customers.find_one()
    booking = db.bookings.find_one({"customer_id": customer["_id"]})

    result = send_reschedule_confirmation(
        customer_id=customer["_id"],
        booking={**booking, "id": booking["_id"]}
    )
    print("Reschedule:", result)


def test_cancellation():
    customer = db.customers.find_one()
    booking = db.bookings.find_one({"customer_id": customer["_id"]})

    result = send_cancellation_email(
        customer_id=customer["_id"],
        booking={**booking, "id": booking["_id"]},
        refund_info={
            "refund_eligible": True,
            "refund_amount": 500.0,
            "refund_status": "pending"
        }
    )
    print("Cancellation:", result)


def test_equipment():
    customer = db.customers.find_one()
    rental = db.equipment_rentals.find_one()
    if not rental:
        print("No rental found")
        return

    result = send_equipment_confirmation(
        customer_id=customer["_id"],
        booking_id=rental.get("booking_id", "BKG-TEST"),
        rental=rental
    )
    print("Equipment:", result)


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING EMAIL NOTIFICATIONS")
    print("=" * 60)
    test_booking_confirmation()
    test_reschedule()
    test_cancellation()
    test_equipment()