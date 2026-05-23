from passlib.context import CryptContext
import jwt
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Use argon2 instead of bcrypt (more reliable on Windows)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


# 🔐 Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 🔐 Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 🔑 Create JWT token
def create_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = datetime.datetime.utcnow() + datetime.timedelta(
        hours=ACCESS_TOKEN_EXPIRE_HOURS
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)