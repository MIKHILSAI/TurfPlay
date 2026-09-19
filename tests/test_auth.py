from backend.services.auth_service import (
    register_customer,
    login_customer,
    set_current_customer,
    get_current_customer,
    logout_customer
)


# Fake session for testing
session = {}


# ============================================================
# 1. REGISTER
# ============================================================

print("\n==============================")
print("1. REGISTER CUSTOMER")
print("==============================")

register_result = register_customer(
    name="Rahul",
    email="rahul@gmail.com",
    phone="+919876543210",
    password="123456"
)

print(register_result)


# ============================================================
# 2. LOGIN
# ============================================================

print("\n==============================")
print("2. LOGIN CUSTOMER")
print("==============================")

login_result = login_customer(
    email_or_phone="rahul@gmail.com",
    password="123456"
)

print(login_result)


# ============================================================
# 3. SET SESSION
# ============================================================

if login_result["success"]:

    set_current_customer(
        session,
        login_result["customer"]
    )

    print("\nSession:")
    print(session)


# ============================================================
# 4. GET CURRENT CUSTOMER
# ============================================================

print("\n==============================")
print("3. CURRENT CUSTOMER")
print("==============================")

current_customer = get_current_customer(session)

print(current_customer)


# ============================================================
# 5. LOGOUT
# ============================================================

print("\n==============================")
print("4. LOGOUT")
print("==============================")

logout_result = logout_customer(session)

print(logout_result)

print("\nSession after logout:")
print(session)


# ============================================================
# 6. CHECK CURRENT CUSTOMER
# ============================================================

print("\n==============================")
print("5. CURRENT CUSTOMER AFTER LOGOUT")
print("==============================")

current_customer = get_current_customer(session)

print(current_customer)