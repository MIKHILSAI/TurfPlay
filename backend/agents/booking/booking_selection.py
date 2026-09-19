def select_booking_resource(available_resources):
    """
    Show available courts/turfs and let the customer
    select one.

    This function does NOT create a booking.
    """

    if not available_resources:
        print()
        print("No courts or turfs are available.")
        return None

    print()
    print("=" * 60)
    print("SELECT A COURT / TURF")
    print("=" * 60)

    for index, resource in enumerate(
        available_resources,
        start=1
    ):
        booking = resource.get("booking", {})

        print(
            f"{index}. "
            f"{resource.get('name')} "
            f"({resource.get('resource_id')})"
        )

        print(
            f"   Time : "
            f"{booking.get('start_time')} - "
            f"{booking.get('end_time')}"
        )

        print(
            f"   Rate : "
            f"₹{resource.get('hourly_rate')}/hour"
        )

        print()

    while True:

        choice = input(
            "Select a court/turf number: "
        ).strip()

        try:
            choice_number = int(choice)

        except ValueError:
            print(
                "Please enter a valid number."
            )
            continue

        if choice_number < 1 or choice_number > len(
            available_resources
        ):
            print(
                "Invalid selection. "
                "Please choose one of the numbers shown."
            )
            continue

        selected_resource = available_resources[
            choice_number - 1
        ]

        print()
        print(
            f"Selected: "
            f"{selected_resource.get('name')} "
            f"({selected_resource.get('resource_id')})"
        )

        return selected_resource


def main():

    print(
        "This file is used by the booking process "
        "to select an available resource."
    )


if __name__ == "__main__":
    main()