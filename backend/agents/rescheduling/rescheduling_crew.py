from crewai import Crew, Process

from backend.agents.rescheduling.rescheduling_agent import (
    rescheduling_agent
)

from backend.agents.rescheduling.rescheduling_task import (
    create_rescheduling_task
)


def process_rescheduling_request(user_message):

    rescheduling_task = create_rescheduling_task(
        user_message
    )

    rescheduling_crew = Crew(
        agents=[rescheduling_agent],
        tasks=[rescheduling_task],
        process=Process.sequential,
        verbose=True
    )

    result = rescheduling_crew.kickoff()

    return str(result)


def main():

    print("=" * 60)
    print("TURF BOOKING - RESCHEDULING AGENT")
    print("=" * 60)

    while True:

        user_message = input("You: ").strip()

        if user_message.lower() == "exit":
            print("Goodbye!")
            break

        if not user_message:
            continue

        try:

            result = process_rescheduling_request(
                user_message
            )

            print()
            print("Rescheduling Agent Result:")
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