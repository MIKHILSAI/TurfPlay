from fastapi import HTTPException, Request, status

from backend.database.mongodb import db


def get_current_customer(request: Request):
    authorization = request.headers.get("Authorization", "")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTHENTICATION_FAILED", "message": "Authentication required."},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTHENTICATION_FAILED", "message": "Authorization header must use Bearer token."},
        )

    customer = db.customers.find_one({"token": token})
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTHENTICATION_FAILED", "message": "Invalid or expired session token."},
        )

    if customer.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "AUTHENTICATION_FAILED", "message": "Customer account is inactive."},
        )

    payload = {
        "_id": customer.get("_id"),
        "id": customer.get("_id"),
        "name": customer.get("name"),
        "email": customer.get("email"),
        "phone": customer.get("phone"),
        "membership_id": customer.get("membership_id"),
    }
    return payload
