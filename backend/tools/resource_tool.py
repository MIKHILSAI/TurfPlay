from crewai.tools import tool

from backend.services.resource_service import get_available_resources


# ============================================================
# RESOURCE TOOL
# ============================================================

@tool("find_resources")
def find_resources_tool(resource_type):
    """
    Find active turf/court resources for a sport or facility type.
    """

    # CrewAI .run() may pass tool arguments as a dictionary.
    if isinstance(resource_type, dict):
        resource_type = resource_type.get("resource_type")

    if not resource_type:
        return {
            "success": False,
            "resources": [],
            "message": "Resource type is required."
        }

    resources = get_available_resources(
        resource_type
    )

    if not resources:
        return {
            "success": False,
            "resources": [],
            "message": (
                f"No active resources found for "
                f"'{resource_type}'."
            )
        }

    return {
        "success": True,
        "resources": resources
    }