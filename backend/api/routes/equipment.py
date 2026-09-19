from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.dependencies import get_current_customer
from backend.database.mongodb import db
from backend.services.equipment_service import check_equipment_availability, get_available_equipment


router = APIRouter(tags=["Equipment"])


def serialize_equipment(item):
    return {
        "_id": item.get("_id"),
        "name": item.get("name"),
        "type": item.get("type"),
        "price": item.get("rental_rate", item.get("price", 0)),
        "deposit": item.get("deposit", 0),
        "quantity_available": item.get("quantity_available", item.get("available_quantity", 0)),
        "active": item.get("active", True),
    }


@router.get("/equipment")
def list_equipment(current_customer=Depends(get_current_customer)):
    result = get_available_equipment()
    equipment = result.get("equipment", [])
    return [serialize_equipment(item) for item in equipment]


@router.get("/equipment/availability")
def equipment_availability(
    equipment_id: str = Query(...),
    quantity: int = Query(...),
    current_customer=Depends(get_current_customer),
):
    result = check_equipment_availability(equipment_id, quantity)
    if not result.get("success"):
        detail = {
            "error_code": result.get("error_code", "EQUIPMENT_UNAVAILABLE"),
            "message": result.get("message", "Equipment is unavailable."),
        }
        if "available_quantity" in result:
            detail["available_quantity"] = result["available_quantity"]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    return {
        "available": bool(result.get("available", False)),
        "available_quantity": result.get("available_quantity", 0),
        "reserved_quantity": result.get("reserved_quantity", 0),
    }
