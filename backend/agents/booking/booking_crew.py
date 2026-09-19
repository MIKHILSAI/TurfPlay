from crewai import Crew, Process

from backend.agents.booking.booking_agent import booking_agent
from backend.agents.booking.booking_task import create_booking_task


# ============================================================
# BOOKING CREW
# ============================================================

def process_booking_request(user_message):

    booking_task = create_booking_task(user_message)

    booking_crew = Crew(
        agents=[booking_agent],
        tasks=[booking_task],
        process=Process.sequential,
        verbose=True
    )

    result = booking_crew.kickoff()

    return str(result).strip()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("TURF BOOKING - BOOKING AGENT")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":
            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            result = process_booking_request(user_message)

            print()
            print("Booking Agent Result:")
            print(result)
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