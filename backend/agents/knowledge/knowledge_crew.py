from crewai import Crew, Process

from backend.agents.knowledge.knowledge_agent import knowledge_agent
from backend.agents.knowledge.knowledge_task import create_knowledge_task


def process_knowledge_request(user_message):
    """
    Run the Knowledge Agent to understand the user's question.
    """

    knowledge_task = create_knowledge_task(user_message)

    knowledge_crew = Crew(
        agents=[knowledge_agent],
        tasks=[knowledge_task],
        process=Process.sequential,
        verbose=True
    )

    result = knowledge_crew.kickoff()

    return str(result)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TURF BOOKING - KNOWLEDGE AGENT")
    print("=" * 60)

    user_message = input("You: ").strip()

    if user_message:

        result = process_knowledge_request(user_message)

        print()
        print("Knowledge Agent Result:")
        print("-" * 60)
        print(result)
        print("-" * 60)