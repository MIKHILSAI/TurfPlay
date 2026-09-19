import bcrypt
import uuid

from datetime import datetime, timezone

from backend.database.mongodb import db


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def hash_password(password):
    """
    Convert a plain-text password into a bcrypt password hash.
    """

    if not password:
        raise ValueError("Password cannot be empty")

    password_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(
        password_bytes,
        salt
    )

    return hashed_password.decode("utf-8")


def verify_password(password, password_hash):
    """
    Check whether a plain-text password matches
    the stored bcrypt password hash.
    """

    if not password or not password_hash:
        return False

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def generate_customer_id():
    """
    Generate a unique customer ID.
    Example: CUS8A21F4B2
    """

    return "CUS" + uuid.uuid4().hex[:8].upper()


# ============================================================
# REGISTER CUSTOMER
# ============================================================

def register_customer(name, email, phone, password):
    """
    Register a new customer.

    Returns:
        {
            "success": True/False,
            "message": "...",
            "customer_id": "..."
        }
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not name or not name.strip():
        return {
            "success": False,
            "message": "Name is required"
        }

    if not email or not email.strip():
        return {
            "success": False,
            "message": "Email is required"
        }

    if not phone or not phone.strip():
        return {
            "success": False,
            "message": "Phone is required"
        }

    if not password:
        return {
            "success": False,
            "message": "Password is required"
        }

    if len(password) < 6:
        return {
            "success": False,
            "message": "Password must contain at least 6 characters"
        }


    # --------------------------------------------------------
    # Clean input
    # --------------------------------------------------------

    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()


    # --------------------------------------------------------
    # Check duplicate email
    # --------------------------------------------------------

    existing_email = db.customers.find_one({
        "email": email
    })

    if existing_email:

        return {
            "success": False,
            "message": "Email already registered"
        }


    # --------------------------------------------------------
    # Check duplicate phone
    # --------------------------------------------------------

    existing_phone = db.customers.find_one({
        "phone": phone
    })

    if existing_phone:

        return {
            "success": False,
            "message": "Phone already registered"
        }


    # --------------------------------------------------------
    # Generate customer ID
    # --------------------------------------------------------

    customer_id = generate_customer_id()


    # --------------------------------------------------------
    # Hash password
    # --------------------------------------------------------

    password_hash = hash_password(password)


    # --------------------------------------------------------
    # Current UTC timestamp
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)


    # --------------------------------------------------------
    # Create customer document
    # --------------------------------------------------------

    customer = {

        "_id": customer_id,

        "name": name,

        "email": email,

        "phone": phone,

        "password_hash": password_hash,

        "membership_id": None,

        "status": "active",

        "created_at": now,

        "updated_at": now
    }


    # --------------------------------------------------------
    # Insert customer into MongoDB
    # --------------------------------------------------------

    try:

        db.customers.insert_one(customer)

    except Exception as e:

        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }


    # --------------------------------------------------------
    # Return success
    # --------------------------------------------------------

    return {

        "success": True,

        "message": "Customer registered successfully",

        "customer_id": customer_id
    }


# ============================================================
# LOGIN CUSTOMER
# ============================================================

def login_customer(email_or_phone, password):
    """
    Login using either email or phone number.
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not email_or_phone:

        return {
            "success": False,
            "message": "Email/phone is required"
        }

    if not password:

        return {
            "success": False,
            "message": "Password is required"
        }


    # --------------------------------------------------------
    # Clean login input
    # --------------------------------------------------------

    email_or_phone = email_or_phone.strip()


    # --------------------------------------------------------
    # Search customer
    # --------------------------------------------------------

    customer = db.customers.find_one({

        "$or": [

            {
                "email": email_or_phone.lower()
            },

            {
                "phone": email_or_phone
            }

        ]

    })


    # --------------------------------------------------------
    # Customer doesn't exist
    # --------------------------------------------------------

    if not customer:

        return {
            "success": False,
            "message": "Invalid email/phone or password"
        }


    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    if customer.get("status") != "active":

        return {
            "success": False,
            "message": "Customer account is inactive"
        }


    # --------------------------------------------------------
    # Get stored password hash
    # --------------------------------------------------------

    stored_password_hash = customer.get("password_hash")


    if not stored_password_hash:

        return {
            "success": False,
            "message": "Account authentication data is missing"
        }


    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    try:

        password_valid = verify_password(
            password,
            stored_password_hash
        )

    except Exception:

        password_valid = False


    # --------------------------------------------------------
    # Invalid password
    # --------------------------------------------------------

    if not password_valid:

        return {
            "success": False,
            "message": "Invalid email/phone or password"
        }


    # --------------------------------------------------------
    # Login successful
    # --------------------------------------------------------

    return {

        "success": True,

        "message": "Login successful",

        "customer": {

            "id": customer["_id"],

            "name": customer["name"],

            "email": customer["email"],

            "phone": customer["phone"],

            "membership_id": customer.get("membership_id")

        }

    }


# ============================================================
# SET LOGIN SESSION
# ============================================================

def set_current_customer(session, customer):
    """
    Store the logged-in customer inside the application session.
    """

    session["customer_id"] = customer["id"]

    session["logged_in"] = True


# ============================================================
# GET CURRENT CUSTOMER
# ============================================================

def get_current_customer(session):
    """
    Get the currently logged-in customer.

    Returns customer information if logged in.
    Returns None if nobody is logged in.
    """

    # --------------------------------------------------------
    # Get customer ID from session
    # --------------------------------------------------------

    customer_id = session.get("customer_id")


    if not customer_id:

        return None


    # --------------------------------------------------------
    # Find customer in MongoDB
    # --------------------------------------------------------

    customer = db.customers.find_one({

        "_id": customer_id

    })


    # --------------------------------------------------------
    # Customer doesn't exist
    # --------------------------------------------------------

    if not customer:

        return None


    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    if customer.get("status") != "active":

        return None


    # --------------------------------------------------------
    # Return customer information
    # --------------------------------------------------------

    return {

        "id": customer["_id"],

        "name": customer["name"],

        "email": customer["email"],

        "phone": customer["phone"],

        "membership_id": customer.get("membership_id")

    }


# ============================================================
# LOGOUT CUSTOMER
# ============================================================

def logout_customer(session):
    """
    Remove the customer login session.
    """

    session.clear()

    return {

        "success": True,

        "message": "Logged out successfully"

    }