import os

from dotenv import load_dotenv
from crewai import Agent
from crewai.llm import LLM


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in .env")


# ============================================================
# GROQ LLM
# ============================================================

llm = LLM(
    model="openai/gpt-oss-20b",
    provider="openai",
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
    temperature=0,
    max_tokens=800
)


# ============================================================
# KNOWLEDGE AGENT
# ============================================================

knowledge_agent = Agent(
    role="Turf Knowledge Specialist",

    goal=(
        "Understand the customer's knowledge-related question "
        "and identify what information should be retrieved "
        "from the turf booking knowledge base."
    ),

    backstory=(
        "You are a knowledge specialist for a turf booking system. "
        "You handle questions about opening hours, pricing, "
        "membership benefits, cancellation policies, equipment "
        "information, and facility rules. "
        "You do not access MongoDB and you do not modify bookings."
    ),

    llm=llm,

    verbose=True,

    allow_delegation=False
)