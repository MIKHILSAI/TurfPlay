from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.services.booking_notifier import send_membership_welcome
from backend.database.mongodb import db
from backend.services.booking_notifier import send_membership_welcome

# ============================================================
# CONFIGURATION
# ============================================================

TIMEZONE = ZoneInfo("Asia/Kolkata")

MEMBERSHIP_PLANS = {
    "monthly": {
        "price": 1500,
        "duration_days": 30,
        "discount_percent": 15,
        "benefits": [
            "15% discount on eligible facility bookings",
            "Priority access during peak hours",
        ],
    },
    "annual": {
        "price": 15000,
        "duration_days": 365,
        "discount_percent": 15,
        "benefits": [
            "15% discount on eligible facility bookings",
            "Priority access during peak hours",
        ],
    },
}


# ============================================================
# GET MEMBERSHIP PLANS
# ============================================================

def get_membership_plans():
    """
    Return all available membership plans.
    """

    plans = []

    for membership_type, plan in MEMBERSHIP_PLANS.items():

        plans.append({
            "type": membership_type,
            "price": plan["price"],
            "duration_days": plan["duration_days"],
            "discount_percent": plan["discount_percent"],
            "benefits": plan["benefits"],
        })

    return {
        "success": True,
        "plans": plans,
    }


# ============================================================
# GET CUSTOMER MEMBERSHIP
# ============================================================

def get_customer_membership(customer_id):
    """
    Get the customer's latest membership.
    """

    if not customer_id:
        return {
            "success": False,
            "error_code": "AUTHENTICATION_FAILED",
            "message": "Customer authentication is required.",
        }

    membership = db.memberships.find_one(
        {
            "customer_id": customer_id
        },
        sort=[
            ("created_at", -1)
        ]
    )

    if not membership:

        return {
            "success": True,
            "has_membership": False,
            "membership": None,
        }

    membership["_id"] = str(membership["_id"])

    return {
        "success": True,
        "has_membership": True,
        "membership": membership,
    }


# ============================================================
# CHECK ACTIVE MEMBERSHIP
# ============================================================

def check_active_membership(customer_id):
    """
    Check whether the customer currently has an active membership.

    Membership benefits are applied only when:
    - status is active
    - current date is between start_date and end_date
    """

    if not customer_id:
        return {
            "success": False,
            "error_code": "AUTHENTICATION_FAILED",
            "message": "Customer authentication is required.",
        }

    membership = db.memberships.find_one(
        {
            "customer_id": customer_id,
            "status": "active",
        },
        sort=[
            ("created_at", -1)
        ]
    )

    if not membership:

        return {
            "success": True,
            "active": False,
            "membership": None,
            "discount_percent": 0,
        }

    today = datetime.now(TIMEZONE).date()

    try:
        start_date = datetime.strptime(
            membership["start_date"],
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            membership["end_date"],
            "%Y-%m-%d"
        ).date()

    except (KeyError, ValueError):

        return {
            "success": False,
            "error_code": "INVALID_MEMBERSHIP",
            "message": "Membership contains invalid date information.",
        }

    # Membership has expired
    if today > end_date:

        db.memberships.update_one(
            {
                "_id": membership["_id"]
            },
            {
                "$set": {
                    "status": "expired",
                    "updated_at": datetime.now(TIMEZONE),
                }
            }
        )

        return {
            "success": True,
            "active": False,
            "membership": None,
            "discount_percent": 0,
        }

    # Membership has not started yet
    if today < start_date:

        return {
            "success": True,
            "active": False,
            "membership": None,
            "discount_percent": 0,
        }

    membership["_id"] = str(membership["_id"])

    return {
        "success": True,
        "active": True,
        "membership": membership,
        "discount_percent": float(
            membership.get("discount_percent", 15)
        ),
    }


# ============================================================
# CREATE MEMBERSHIP
# ============================================================

def create_membership(customer_id, membership_type):
    """
    Create a membership for a customer.

    Supported:
    monthly -> ₹1500
    annual  -> ₹15000
    """

    if not customer_id:

        return {
            "success": False,
            "error_code": "AUTHENTICATION_FAILED",
            "message": "Customer authentication is required.",
        }

    membership_type = str(
        membership_type
    ).strip().lower()

    if membership_type not in MEMBERSHIP_PLANS:

        return {
            "success": False,
            "error_code": "INVALID_MEMBERSHIP",
            "message": "Invalid membership type. Use monthly or annual.",
        }

    # --------------------------------------------------------
    # Check for existing active membership
    # --------------------------------------------------------

    active_membership = check_active_membership(
        customer_id
    )

    if not active_membership["success"]:
        return active_membership

    if active_membership["active"]:

        return {
            "success": False,
            "error_code": "MEMBERSHIP_ALREADY_ACTIVE",
            "message": "Customer already has an active membership.",
        }

    # --------------------------------------------------------
    # Plan
    # --------------------------------------------------------

    plan = MEMBERSHIP_PLANS[membership_type]

    today = datetime.now(TIMEZONE).date()

    if membership_type == "monthly":

        end_date = today + timedelta(days=30)

    else:
        end_date = today + timedelta(days=365)

    now = datetime.now(TIMEZONE)

    membership_id = (
        f"MEM{customer_id[-6:]}"
    )

    # --------------------------------------------------------
    # Avoid duplicate membership ID
    # --------------------------------------------------------

    existing = db.memberships.find_one(
        {
            "_id": membership_id
        }
    )

    if existing:

        membership_id = (
            f"MEM{customer_id[-4:]}"
            f"{int(now.timestamp())}"
        )

    membership = {
        "_id": membership_id,
        "customer_id": customer_id,
        "type": membership_type,
        "price": plan["price"],
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "status": "active",
        "discount_percent": plan["discount_percent"],
        "benefits": plan["benefits"],
        "payment_method": "mock",
        "created_at": now,
        "updated_at": now,
    }

    db.memberships.insert_one(
        membership
    )

    # --------------------------------------------------------
    # Update customer membership ID
    # --------------------------------------------------------

    db.customers.update_one(
        {
            "_id": customer_id
        },
        {
            "$set": {
                "membership_id": membership_id,
                "updated_at": now,
            }
        }
    )

    # --------------------------------------------------------
    # Send membership welcome email (non-blocking)
    # --------------------------------------------------------

    try:
        email_result = send_membership_welcome(
            customer_id=customer_id,
            membership={
                **membership,
                "_id": membership_id,
            }
        )

        if not email_result.get("sent"):
            print(
                f"[EMAIL] Membership welcome failed: "
                f"{email_result.get('error')}"
            )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return {
        "success": True,
        "message": "Membership created successfully.",
        "membership": {
            **membership,
            "_id": membership_id,
        },
    }

# ============================================================
# CANCEL MEMBERSHIP
# ============================================================

def cancel_membership(customer_id):
    """
    Cancel the customer's active membership.
    """

    if not customer_id:

        return {
            "success": False,
            "error_code": "AUTHENTICATION_FAILED",
            "message": "Customer authentication is required.",
        }

    membership = db.memberships.find_one(
        {
            "customer_id": customer_id,
            "status": "active",
        }
    )

    if not membership:

        return {
            "success": False,
            "error_code": "INVALID_MEMBERSHIP",
            "message": "No active membership found.",
        }

    now = datetime.now(TIMEZONE)

    db.memberships.update_one(
        {
            "_id": membership["_id"]
        },
        {
            "$set": {
                "status": "cancelled",
                "updated_at": now,
            }
        }
    )

    db.customers.update_one(
        {
            "_id": customer_id
        },
        {
            "$set": {
                "membership_id": None,
                "updated_at": now,
            }
        }
    )

    response = {
        "success": True,
        "message": "Membership created successfully.",
        "membership": {
            **membership,
            "_id": membership["id"],
        },
    }

    # --------------------------------------------------------
    # Send membership welcome email (non-blocking)
    # --------------------------------------------------------

    try:
        from backend.services.booking_notifier import send_membership_welcome

        email_result = send_membership_welcome(
            customer_id=customer_id,
            membership=membership
        )

        if not email_result.get("sent"):
            print(
                f"[EMAIL] Membership email failed: "
                f"{email_result.get('error')}"
            )
    except Exception as e:
        print(f"[EMAIL] Unexpected error: {e}")

    return response