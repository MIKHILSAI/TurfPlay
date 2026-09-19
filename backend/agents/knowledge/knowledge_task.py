from crewai import Task

from backend.agents.knowledge.knowledge_agent import knowledge_agent


def create_knowledge_task(user_message):
    """
    Create a task for the Knowledge Agent.

    The agent only identifies the user's knowledge question.
    It does not access MongoDB or perform database operations.
    """

    return Task(
        description=f"""
Understand the customer's knowledge-related request.

Customer request:
{user_message}

Determine what information the customer is asking about.

The request may involve:
- opening hours
- pricing
- membership
- cancellation policy
- equipment information
- facility rules
- payment information
- other information available in the knowledge base

IMPORTANT RULES:

- Do not access MongoDB.
- Do not execute database queries.
- Do not modify bookings.
- Do not invent information.
- Do not answer using outside knowledge.
- Do not perform any booking operation.
- Identify the customer's question clearly.

Return exactly 2 lines:

Action: knowledge
Question: <the customer's question>

Do not return explanations.
Do not return reasoning.
Do not return JSON.
Do not use markdown.
""",

        expected_output=(
            "Exactly 2 lines:\n"
            "Action: knowledge\n"
            "Question: <customer question>"
        ),

        agent=knowledge_agent
    )