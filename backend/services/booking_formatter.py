def format_bookings(result):
    if not result.get("success"):
        return "Sorry, I could not retrieve your bookings."

    bookings = result.get("bookings", [])

    if not bookings:
        return "You don't have any bookings."

    response = f"You have {len(bookings)} bookings:\n\n"

    for i, booking in enumerate(bookings, start=1):
        response += (
            f"{i}. {booking['resource_id']} - "
            f"{booking['booking_date']} "
            f"{booking['start_time']} to {booking['end_time']}\n"
            f"   Status: {booking['status']}\n"
            f"   Total: ₹{booking['total_amount']:.0f}\n\n"
        )

    return response.strip()