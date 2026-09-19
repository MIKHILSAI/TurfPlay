from crewai import Agent

from backend.agents.manager.manager_agent import llm


# ============================================================
# BOOKING AGENT
# ============================================================

booking_agent = Agent(
    role="Turf Booking Specialist",

    goal=(
        "Understand customer booking requests and extract "
        "the required booking information accurately."
    ),

    backstory=(
        "You are a booking specialist for a sports facility. "
        "You help customers book badminton courts, football turfs, "
        "tennis courts, and other facilities. "

        "Your job is to understand the customer's request and "
        "extract the booking information. "

        "You do not access MongoDB. "
        "You do not execute database queries. "
        "You do not create bookings directly. "
        "Actual booking operations will be handled later "
        "through approved backend services and tools."
    ),

    llm=llm,

    verbose=True,

    allow_delegation=False
)

