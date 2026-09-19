from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_customer
from backend.database.mongodb import db
from backend.services.availability_service import check_availability


router = APIRouter(prefix="/resources", tags=["Resources"])


def serialize_resource(resource):
    if not resource:
        return None
    return {
        "_id": resource.get("_id"),
        "name": resource.get("name"),
        "type": resource.get("type"),
        "capacity": resource.get("capacity"),
        "hourly_rate": resource.get("hourly_rate"),
        "open_time": resource.get("open_time"),
        "close_time": resource.get("close_time"),
        "active": resource.get("active", True),
    }


@router.get("")
def list_resources(current_customer=Depends(get_current_customer)):
    resources = list(db.resources.find({"active": True}).sort("_id", 1))
    return [serialize_resource(resource) for resource in resources]


@router.get("/{resource_id}")
def get_resource(resource_id: str, current_customer=Depends(get_current_customer)):
    resource = db.resources.find_one({"_id": resource_id})
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "RESOURCE_NOT_FOUND", "message": "Resource not found."})
    return serialize_resource(resource)


@router.get("/{resource_id}/availability")
def get_availability(
    resource_id: str,
    date: str,
    start_time: str,
    end_time: str,
    current_customer=Depends(get_current_customer),
):
    result = check_availability(resource_id=resource_id, booking_date=date, start_time=start_time, end_time=end_time)
    if result.get("available"):
        return {"available": True, "message": result.get("message", "Available."), "alternatives": []}
    return {
        "available": False,
        "message": result.get("message", "The requested slot is unavailable."),
        "alternatives": result.get("alternatives", []),
    }
