from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import get_current_customer
from backend.database.mongodb import db
from backend.services.membership_service import create_membership, get_membership_plans


router = APIRouter(tags=["Membership"])


class SubscribeRequest(BaseModel):
    plan_type: str


def serialize_membership(membership_doc):
    if not membership_doc:
        return None
    status = membership_doc.get("status")
    return {
        "type": membership_doc.get("type"),
        "status": "active" if status == "active" else "inactive",
        "start_date": membership_doc.get("start_date"),
        "expiry_date": membership_doc.get("end_date") or membership_doc.get("expiry_date"),
        "discount_percent": membership_doc.get("discount_percent"),
        "priority_access": True if membership_doc.get("status") == "active" else False,
    }


@router.get("/membership")
def get_membership(current_customer=Depends(get_current_customer)):
    membership = db.memberships.find_one({"customer_id": current_customer["id"]}, sort=[("created_at", -1)])
    if not membership:
        return None
    return serialize_membership(membership)


@router.get("/membership/plans")
def get_membership_plans_route(current_customer=Depends(get_current_customer)):
    result = get_membership_plans()
    plans = result.get("plans", [])
    return [
        {
            "_id": f"plan-{plan.get('type')}",
            "name": plan.get("type", "").title(),
            "price": plan.get("price", 0),
            "duration": f"{plan.get('duration_days', 30)} days",
            "discount_percent": plan.get("discount_percent", 0),
        }
        for plan in plans
    ]


@router.post("/membership/subscribe")
def subscribe(request: SubscribeRequest, current_customer=Depends(get_current_customer)):
    result = create_membership(
        customer_id=current_customer["id"],
        membership_type=request.plan_type,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT
            if result.get("error_code") == "MEMBERSHIP_ALREADY_ACTIVE"
            else status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": result.get("error_code", "MEMBERSHIP_SUBSCRIPTION_FAILED"),
                "message": result.get("message", "Unable to subscribe to membership."),
            },
        )

    return serialize_membership(result.get("membership"))
