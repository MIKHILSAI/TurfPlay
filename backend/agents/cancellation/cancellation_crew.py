from crewai import Crew, Process

from backend.agents.cancellation.cancellation_agent import (
    cancellation_agent
)

from backend.agents.cancellation.cancellation_task import (
    create_cancellation_task
)


def process_cancellation_request(user_message):

    cancellation_task = create_cancellation_task(
        user_message
    )

    cancellation_crew = Crew(
        agents=[cancellation_agent],
        tasks=[cancellation_task],
        process=Process.sequential,
        verbose=True
    )

    result = cancellation_crew.kickoff()

    return str(result)


def main():

    print("=" * 60)
    print("TURF BOOKING - CANCELLATION AGENT")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":
            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            result = process_cancellation_request(
                user_message
            )

            print()
            print("Cancellation Agent Result:")
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