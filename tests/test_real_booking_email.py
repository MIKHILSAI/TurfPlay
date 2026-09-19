"""
Test email notification for the real booking BKGBB68EF98.

Run:
    cd "C:\Turf Booking Agent"
    python test_real_booking_email.py
"""

from backend.database.mongodb import db
from backend.services.booking_notifier import send_booking_confirmation


CUSTOMER_ID = "CUSF1B0DE1C"
BOOKING_ID = "BKGBB68EF98"


def main():

    print("=" * 60)
    print("REAL BOOKING EMAIL TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load customer
    # --------------------------------------------------------

    customer = db.customers.find_one({"_id": CUSTOMER_ID})

    if not customer:
        print(f"❌ Customer '{CUSTOMER_ID}' not found in MongoDB.")
        return

    print()
    print("CUSTOMER:")
    print(f"  ID    : {customer.get('_id')}")
    print(f"  Name  : {customer.get('name')}")
    print(f"  Email : {customer.get('email')}")

    if not customer.get("email"):
        print()
        print("❌ Customer has no email in MongoDB. Aborting.")
        return

    # --------------------------------------------------------
    # 2. Load booking
    # --------------------------------------------------------

    booking = db.bookings.find_one({"_id": BOOKING_ID})

    if not booking:
        print()
        print(f"❌ Booking '{BOOKING_ID}' not found in MongoDB.")
        return

    print()
    print("BOOKING:")
    print(f"  ID         : {booking.get('_id')}")
    print(f"  Resource   : {booking.get('resource_id')}")
    print(f"  Date       : {booking.get('booking_date')}")
    print(f"  Time       : {booking.get('start_time')} - {booking.get('end_time')}")
    print(f"  Total      : {booking.get('total_amount')}")
    print(f"  Status     : {booking.get('status')}")

    # --------------------------------------------------------
    # 3. Prepare the booking dict for the notifier
    # --------------------------------------------------------

    booking_for_email = {
        "id": booking.get("_id"),
        "customer_id": booking.get("customer_id"),
        "resource_id": booking.get("resource_id"),
        "booking_date": booking.get("booking_date"),
        "start_time": booking.get("start_time"),
        "end_time": booking.get("end_time"),
        "duration_mins": booking.get("duration_mins"),
        "base_amount": booking.get("base_amount", 0),
        "surcharge_amount": booking.get("surcharge_amount", 0),
        "discount_amount": booking.get("discount_amount", 0),
        "total_amount": booking.get("total_amount", 0),
        "payment_status": booking.get("payment_status", "pending"),
    }

    # --------------------------------------------------------
    # 4. Send the email
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("Sending email...")
    print("-" * 60)

    result = send_booking_confirmation(
        customer_id=CUSTOMER_ID,
        booking=booking_for_email
    )

    # --------------------------------------------------------
    # 5. Show result
    # --------------------------------------------------------

    print()
    print("RESULT:")
    print(result)
    print()

    if result.get("sent"):
        print(f"✅ Email sent to: {customer.get('email')}")
        print("   Check the inbox.")
    else:
        print(f"❌ Email failed: {result.get('error')}")


if __name__ == "__main__":
    main()