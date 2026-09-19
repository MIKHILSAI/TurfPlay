from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import get_current_customer
from backend.database.mongodb import db
from backend.services.booking_service import create_booking
from backend.services.cancellation_service import cancel_booking, cancel_booking_preview
from backend.services.reschedule_service import reschedule_booking, reschedule_booking_preview
from backend.services.equipment_service import get_booking_equipment, reserve_equipment


router = APIRouter(tags=["Bookings"])


class BookingCreateRequest(BaseModel):
    resource_id: str
    date: str
    start_time: str
    end_time: str
    equipment: list[dict] = []
    apply_membership: bool = False


class RescheduleRequest(BaseModel):
    new_resource_id: str
    new_date: str
    new_start_time: str
    new_end_time: str


class EquipmentRentalRequest(BaseModel):
    equipment_id: str
    quantity: int


def serialize_booking(doc):
    if not doc:
        return None
    resource = db.resources.find_one({"_id": doc.get("resource_id")})
    equipment_rentals = get_booking_equipment(doc.get("_id"))
    equipment_list = []
    if equipment_rentals.get("success"):
        for item in equipment_rentals.get("equipment", []):
            item_dict = dict(item)
            if not item_dict.get("equipment_name"):
                eq_doc = db.equipment.find_one({"_id": item_dict.get("equipment_id")})
                if eq_doc:
                    item_dict["equipment_name"] = eq_doc.get("name")
            equipment_list.append(item_dict)
    return {
        "_id": doc.get("_id"),
        "customer_id": doc.get("customer_id"),
        "resource_id": doc.get("resource_id"),
        "booking_date": doc.get("booking_date"),
        "start_time": doc.get("start_time"),
        "end_time": doc.get("end_time"),
        "blocked_end_time": doc.get("blocked_end_time"),
        "duration_mins": doc.get("duration_mins", 0),
        "status": doc.get("status"),
        "payment_status": doc.get("payment_status"),
        "price_breakdown": doc.get("price_breakdown", {}),
        "reschedule_count": doc.get("reschedule_count", 0),
        "created_at": doc.get("created_at"),
        "resource": resource,
        "total_amount": doc.get("total_amount", doc.get("price_breakdown", {}).get("total_amount", 0)),
        "equipment": equipment_list,
    }


@router.post("/bookings")
def create_booking_route(request: BookingCreateRequest, current_customer=Depends(get_current_customer)):
    session = {"customer_id": current_customer["id"], "logged_in": True}
    result = create_booking(
        session=session,
        resource_id=request.resource_id,
        booking_date=request.date,
        start_time=request.start_time,
        end_time=request.end_time,
        equipment_items=request.equipment,
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": result.get("error_code", "BOOKING_FAILED"), "message": result.get("message", "Unable to create booking.")})
    booking = db.bookings.find_one({"_id": result["booking"]["id"]})
    return serialize_booking(booking)


@router.get("/bookings")
def list_bookings(status: str | None = None, current_customer=Depends(get_current_customer)):
    customer_id = current_customer["id"]
    query = {"customer_id": customer_id}
    if status == "upcoming":
        query["status"] = {"$in": ["pending", "confirmed", "rescheduled"]}
        query["booking_date"] = {"$gte": datetime.utcnow().strftime("%Y-%m-%d")}
    elif status == "past":
        query["status"] = {"$in": ["completed", "cancelled"]}
    elif status == "cancelled":
        query["status"] = "cancelled"
    elif status:
        query["status"] = status
    bookings = list(db.bookings.find(query).sort("booking_date", 1))
    return [serialize_booking(booking) for booking in bookings]


@router.get("/bookings/{booking_id}")
def get_booking(booking_id: str, current_customer=Depends(get_current_customer)):
    booking = db.bookings.find_one({"_id": booking_id, "customer_id": current_customer["id"]})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "BOOKING_NOT_FOUND", "message": "Booking not found."})
    return serialize_booking(booking)


@router.post("/bookings/{booking_id}/equipment")
def add_equipment_to_booking(
    booking_id: str,
    body: EquipmentRentalRequest,
    current_customer=Depends(get_current_customer),
):
    booking = db.bookings.find_one({"_id": booking_id, "customer_id": current_customer["id"]})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "BOOKING_NOT_FOUND", "message": "Booking not found."},
        )

    reservation = reserve_equipment(
        booking_id=booking_id,
        equipment_id=body.equipment_id,
        quantity=body.quantity,
    )
    if not reservation.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": reservation.get("error_code", "EQUIPMENT_RESERVATION_FAILED"),
                "message": reservation.get("message", "Unable to reserve equipment."),
            },
        )

    rentals = get_booking_equipment(booking_id).get("equipment", [])
    equipment_amount = round(sum(float(item.get("rental_amount", 0)) for item in rentals), 2)
    deposit_amount = round(sum(float(item.get("deposit_amount", 0)) for item in rentals), 2)
    old_breakdown = booking.get("price_breakdown", {})
    total_amount = round(
        float(old_breakdown.get("base_amount", booking.get("base_amount", 0)))
        + float(old_breakdown.get("peak_surcharge", 0))
        + float(old_breakdown.get("weekend_surcharge", 0))
        - float(old_breakdown.get("discount_amount", booking.get("discount_amount", 0)))
        + equipment_amount
        + deposit_amount,
        2,
    )
    db.bookings.update_one(
        {"_id": booking_id},
        {"$set": {
            "equipment_amount": equipment_amount,
            "deposit_amount": deposit_amount,
            "total_amount": total_amount,
            "price_breakdown.equipment_amount": equipment_amount,
            "price_breakdown.deposit_amount": deposit_amount,
            "price_breakdown.total_amount": total_amount,
        }},
    )
    return serialize_booking(db.bookings.find_one({"_id": booking_id}))


@router.post("/bookings/{booking_id}/cancel-preview")
def cancel_preview(booking_id: str, current_customer=Depends(get_current_customer)):
    session = {"customer_id": current_customer["id"], "logged_in": True}
    result = cancel_booking_preview(session=session, booking_id=booking_id)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": result.get("error_code", "CANCELLATION_FAILED"), "message": result.get("message", "Unable to generate cancellation preview.")})
    return {
        "eligible": bool(result.get("refund_eligible", False)),
        "refund_amount": float(result.get("refund_amount", 0)),
        "message": result.get("refund_message") or result.get("message", "Cancellation preview generated."),
    }


@router.post("/bookings/{booking_id}/cancel")
def cancel_booking_route(booking_id: str, current_customer=Depends(get_current_customer)):
    session = {"customer_id": current_customer["id"], "logged_in": True}
    result = cancel_booking(session=session, booking_id=booking_id, confirmed=True, reason="Cancelled via API")
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": result.get("error_code", "CANCELLATION_FAILED"), "message": result.get("message", "Unable to cancel booking.")})
    booking = db.bookings.find_one({"_id": booking_id})
    return serialize_booking(booking)


@router.post("/bookings/{booking_id}/reschedule-preview")
def reschedule_preview(booking_id: str, body: RescheduleRequest, current_customer=Depends(get_current_customer)):
    session = {"customer_id": current_customer["id"], "logged_in": True}
    result = reschedule_booking_preview(
        session=session,
        booking_id=booking_id,
        new_date=body.new_date,
        new_start_time=body.new_start_time,
        new_end_time=body.new_end_time,
        equipment_items=[],
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": result.get("error_code", "RESCHEDULE_FAILED"), "message": result.get("message", "Unable to generate reschedule preview.")})
    price_diff = result.get("price_difference", {})
    return {
        "eligible": True,
        "slot_available": True,
        "remaining_reschedule_count": max(0, 1 - int(result.get("reschedule_count", 0))),
        "price_difference": float(price_diff.get("difference", 0)),
        "message": result.get("message", "Reschedule preview generated."),
    }


@router.post("/bookings/{booking_id}/reschedule")
def reschedule_booking_route(booking_id: str, body: RescheduleRequest, current_customer=Depends(get_current_customer)):
    session = {"customer_id": current_customer["id"], "logged_in": True}
    result = reschedule_booking(
        session=session,
        booking_id=booking_id,
        new_date=body.new_date,
        new_start_time=body.new_start_time,
        new_end_time=body.new_end_time,
        confirmed=True,
        equipment_items=[],
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": result.get("error_code", "RESCHEDULE_FAILED"), "message": result.get("message", "Unable to reschedule booking.")})
    booking = db.bookings.find_one({"_id": booking_id})
    return serialize_booking(booking)
