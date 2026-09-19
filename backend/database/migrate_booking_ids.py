from pathlib import Path
import sys

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2])
)

from backend.database.mongodb import db


def migrate_booking_ids():
    bookings = db.bookings.find({
        "booking_id": {
            "$exists": False
        }
    })

    updated_count = 0

    for booking in bookings:

        booking_id = booking.get("_id")

        if not booking_id:
            continue

        result = db.bookings.update_one(
            {
                "_id": booking_id
            },
            {
                "$set": {
                    "booking_id": booking_id
                }
            }
        )

        if result.modified_count == 1:
            updated_count += 1

    print(
        f"Booking IDs added to {updated_count} existing booking(s)."
    )


if __name__ == "__main__":
    migrate_booking_ids()
