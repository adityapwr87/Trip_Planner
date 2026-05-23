from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class TripModel(BaseModel):
    user_id: str
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_limit: int
    user_preferences: Optional[str] = None
    weather_data: Optional[Any] = None
    transport_data: Optional[Any] = None
    activities_data: Optional[Any] = None
    budget_insights: Optional[str] = None
    final_itinerary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TripCreate(BaseModel):
    user_id: str
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_limit: int
    user_preferences: Optional[str] = None