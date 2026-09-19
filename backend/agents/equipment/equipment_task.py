from crewai import Task

from backend.agents.equipment.equipment_agent import equipment_agent


def create_equipment_task(user_message):

    task = Task(
        description=f"""
Understand the user's equipment request and extract the required information.

User:
{user_message}

Return exactly 6 lines:

Action: rent/reserve/return/info
Equipment: equipment name
Quantity: number
Date: today/tomorrow/YYYY-MM-DD
Start Time: HH:MM
Duration: minutes

Rules:

1. ACTION
- Use "info" when the user is asking about equipment, prices,
  rental rates, available equipment, or what equipment can be rented.
- Use "rent" when the user explicitly wants to rent equipment.
- Use "reserve" when the user explicitly wants to reserve equipment.
- Use "return" when the user wants to return equipment.

Examples:
"What equipment can I rent for football?"
Action: info

"What football equipment is available?"
Action: info

"How much does a badminton racket cost?"
Action: info

"I want to rent a badminton racket."
Action: rent

"Reserve one football."
Action: reserve

"I want to return my football."
Action: return

2. EQUIPMENT
- Extract the equipment name.
- If the user asks about a sport, use the sport as the equipment
  category when appropriate.
- Example:
  "What equipment can I rent for football?"
  Equipment: football

3. QUANTITY
- Extract the requested quantity.
- If not provided, write missing.

4. DATE
- Convert dates into YYYY-MM-DD when possible.
- If not provided, write missing.

5. START TIME
- Convert times such as 6 PM to 18:00.
- If not provided, write missing.

6. DURATION
- Convert 1 hour to 60.
- Convert 2 hours to 120.
- If not provided, write missing.

7. DO NOT INVENT INFORMATION.

8. Return ONLY the 6 lines.
""",
        expected_output=(
            "Exactly 6 lines: Action, Equipment, Quantity, "
            "Date, Start Time, Duration."
        ),
        agent=equipment_agent
    )

    return task