import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import get_current_customer
from backend.database.mongodb import db
from backend.services.auth_service import (
    login_customer,
    register_customer,
)
from backend.services.booking_service import get_max_advance_booking_days


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class SignupRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


def customer_payload(customer_doc):
    if not customer_doc:
        return None
    customer_id = customer_doc.get("_id") or customer_doc.get("id")
    return {
        "_id": customer_id,
        "id": customer_id,
        "name": customer_doc.get("name"),
        "email": customer_doc.get("email"),
        "phone": customer_doc.get("phone"),
        "created_at": customer_doc.get("created_at"),
        "max_advance_booking_days": get_max_advance_booking_days(customer_id),
    }


def login_response_for_customer(customer_doc):
    token = uuid.uuid4().hex
    db.customers.update_one({"_id": customer_doc["_id"]}, {"$set": {"token": token}})
    return {
        "token": token,
        "customer": customer_payload(customer_doc),
    }


@router.post("/signup")
def signup(request: SignupRequest):
    result = register_customer(
        name=request.name,
        email=request.email,
        phone=request.phone,
        password=request.password,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "SIGNUP_FAILED", "message": result.get("message", "Signup failed.")},
        )

    customer = db.customers.find_one({"_id": result["customer_id"]})
    return login_response_for_customer(customer)


@router.post("/login")
def login(request: LoginRequest):
    result = login_customer(
        email_or_phone=request.identifier,
        password=request.password,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTHENTICATION_FAILED", "message": result.get("message", "Invalid credentials.")},
        )

    customer = db.customers.find_one({"_id": result["customer"]["id"]})
    return login_response_for_customer(customer)


@router.get("/me")
def me(current_customer=Depends(get_current_customer)):
    return customer_payload(current_customer)


@router.post("/logout")
def logout(current_customer=Depends(get_current_customer)):
    db.customers.update_one({"_id": current_customer["_id"]}, {"$unset": {"token": ""}})
    return {"success": True, "message": "Logged out successfully."}