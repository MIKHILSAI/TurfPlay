from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import get_current_customer
from backend.services.pricing_service import calculate_price


router = APIRouter(prefix="/pricing", tags=["Pricing"])


class QuoteRequest(BaseModel):
    resource_id: str
    date: str
    start_time: str
    end_time: str
    equipment: list[dict] = []
    apply_membership: bool = False


@router.post("/quote")
def quote(request: QuoteRequest, current_customer=Depends(get_current_customer)):
    result = calculate_price(
        resource_id=request.resource_id,
        booking_date=request.date,
        start_time=request.start_time,
        end_time=request.end_time,
        customer_id=current_customer["id"],
        equipment_items=request.equipment,
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": result.get("error_code", "PRICING_ERROR"), "message": result.get("message", "Unable to calculate price.")})
    pricing = result.get("pricing", {})
    return {
        "base_amount": pricing.get("base_amount", 0),
        "peak_surcharge": pricing.get("peak_surcharge", 0),
        "weekend_surcharge": pricing.get("weekend_surcharge", 0),
        "membership_discount": pricing.get("discount_amount", 0),
        "discount_amount": pricing.get("discount_amount", 0),
        "equipment_amount": pricing.get("equipment_amount", 0),
        "deposit_amount": pricing.get("deposit_amount", 0),
        "total_amount": pricing.get("total_amount", 0),
    }
