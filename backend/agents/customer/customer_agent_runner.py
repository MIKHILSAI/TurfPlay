from backend.agents.customer.customer_crew import (
    process_customer_request
)


def main():

    print("=" * 60)
    print("TURF BOOKING - CUSTOMER AGENT")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":

            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            result = process_customer_request(
                user_message
            )

            print()
            print("Customer Agent Result:")
            print("-" * 60)
            print(result)
            print("-" * 60)
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
