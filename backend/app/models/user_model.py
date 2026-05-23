from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class UserModel(BaseModel):
    username: str
    email: EmailStr
    password: str
    trip_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
