from crewai import Crew, Process

from backend.agents.customer.customer_agent import (
    customer_agent
)

from backend.agents.customer.customer_task import (
    create_customer_task
)


def process_customer_request(user_message):
    """
    Run the Customer Agent for a user request.
    """

    customer_task = create_customer_task(
        user_message
    )

    customer_crew = Crew(
        agents=[customer_agent],
        tasks=[customer_task],
        process=Process.sequential,
        verbose=True
    )

    result = customer_crew.kickoff()

    return str(result)