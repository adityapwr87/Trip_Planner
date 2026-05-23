from fastapi import HTTPException
from app.models.user_model import UserCreate, UserLogin
from app.config.db import users_collection
from app.utils.auth import hash_password, verify_password, create_token
import datetime


# -------------------------
# 🟢 REGISTER
# -------------------------
def register_user(user: UserCreate):
    # Check existing user
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(user.password)

    user_data = user.model_dump()
    user_data["password"] = hashed_password
    user_data["trip_ids"] = []
    user_data["created_at"] = datetime.datetime.utcnow()

    result = users_collection.insert_one(user_data)

    # Generate token (auto-login)
    token = create_token({
        "user_id": str(result.inserted_id),
        "email": user.email
    })

    return {
        "message": "User registered successfully",
        "token": token,
        "type": "Bearer",
        "user": {
            "id": str(result.inserted_id),
            "username": user.username,
            "email": user.email,
        },
    }


# -------------------------
# 🔵 LOGIN
# -------------------------
def login_user(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Verify password
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = create_token({
        "user_id": str(db_user["_id"]),
        "email": db_user["email"]
    })

    return {
        "message": "Login successful",
        "token": token,
        "type": "Bearer",
        "user": {
            "id": str(db_user["_id"]),
            "username": db_user.get("username"),
            "email": db_user.get("email"),
        },
    }


# -------------------------
# 🔴 LOGOUT
# -------------------------
def logout_user():
    return {"message": "Logged out successfully"}