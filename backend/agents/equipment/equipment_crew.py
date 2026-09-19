from crewai import Crew, Process

from backend.agents.equipment.equipment_agent import equipment_agent
from backend.agents.equipment.equipment_task import create_equipment_task


def process_equipment_request(user_message):
    equipment_task = create_equipment_task(user_message)

    equipment_crew = Crew(
        agents=[equipment_agent],
        tasks=[equipment_task],
        process=Process.sequential,
        verbose=True
    )

    result = equipment_crew.kickoff()

    return str(result).strip()


def main():
    print("=" * 60)
    print("TURF BOOKING - EQUIPMENT AGENT")
    print("=" * 60)

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() == "exit":
            print("Goodbye!")
            break

        if not user_message:
            continue

        try:
            result = process_equipment_request(user_message)

            print()
            print("Equipment Agent Result:")
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