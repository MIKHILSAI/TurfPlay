from backend.database.mongodb import db


# ============================================================
# RESOURCE SERVICE
# ============================================================

def get_resource(resource_id):
    """
    Get a resource using its resource ID.
    """

    if not resource_id:
        return None

    return db.resources.find_one({
        "_id": resource_id
    })


def get_resources_by_type(resource_type):
    """
    Get all active resources of a particular type.

    Examples:
        badminton -> BC1, BC2
        football  -> FT1
        tennis    -> TC1
    """

    if not resource_type:
        return []

    resource_type = resource_type.strip().lower()

    resources = db.resources.find({
        "type": resource_type,
        "active": True
    })

    return list(resources)


def get_available_resources(resource_type):
    """
    Return active resources for the requested sport/facility type.
    """

    resources = get_resources_by_type(resource_type)

    return [
        {
            "resource_id": resource.get("_id"),
            "name": resource.get("name"),
            "type": resource.get("type"),
            "capacity": resource.get("capacity"),
            "hourly_rate": resource.get("hourly_rate"),
            "open_time": resource.get("open_time"),
            "close_time": resource.get("close_time")
        }
        for resource in resources
    ]