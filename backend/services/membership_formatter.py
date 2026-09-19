def format_membership(result):
    if not result.get("success"):
        return "Sorry, I could not retrieve your membership details."

    if not result.get("has_membership"):
        return "You don't have an active membership."

    membership = result.get("membership")

    if not membership:
        return "You don't have an active membership."

    response = "Your membership details:\n\n"

    response += f"Membership: {membership.get('name', 'N/A')}\n"

    if membership.get("status"):
        response += f"Status: {membership['status']}\n"

    if membership.get("start_date"):
        response += f"Start Date: {membership['start_date']}\n"

    if membership.get("end_date"):
        response += f"End Date: {membership['end_date']}\n"

    return response.strip()