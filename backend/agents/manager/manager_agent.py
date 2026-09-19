import os

from dotenv import load_dotenv
from crewai import Agent
from crewai.llm import LLM


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in .env")


# ============================================================
# CREWAI + GROQ LLM
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
# MANAGER AGENT
# ============================================================

manager_agent = Agent(
    role="Turf Booking Manager",

    goal=(
        "Understand the customer's request and classify it "
        "into the correct operation category."
    ),

    backstory=(
        "You are the manager of a turf booking system. "
        "You understand customer requests and route each "
        "request to the correct specialist agent."
    ),

    llm=llm,

    verbose=True,

    allow_delegation=False
)


# ============================================================
# REQUEST CATEGORIES
# ============================================================

REQUEST_CATEGORIES = [
    "booking",
    "equipment",
    "cancellation",
    "rescheduling",
    "customer",
    "knowledge",
    "general",
    "unknown"
]


# ============================================================
# VALIDATE CATEGORY
# ============================================================

def validate_category(category):
    """
    Make sure the manager returns
    one of the allowed categories.
    """

    category = category.strip().lower()

    for valid_category in REQUEST_CATEGORIES:

        if valid_category in category:
            return valid_category

    return "unknown"