from fastapi import APIRouter
from app.controllers import user_controller
from app.models.user_model import UserCreate, UserLogin

router = APIRouter()

@router.post("/signup")
def signup(user: UserCreate):
    return user_controller.register_user(user)

@router.post("/login")
def login(user: UserLogin):
    return user_controller.login_user(user)

@router.post("/logout")
def logout():
    return user_controller.logout_user()
