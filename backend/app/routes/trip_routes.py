from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.controllers import trip_controller
from app.middeleware.auth_middleware import verify_token

router = APIRouter()

class TripRequest(BaseModel):
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_limit: int
    user_preferences: str = ""


class CompareDestinationsRequest(BaseModel):
    origin: str
    destination_one: str
    destination_two: str
    start_date: str
    end_date: str
    user_prompt: str

@router.post("/plan")
async def plan_trip(trip_req: TripRequest, current_user: dict = Depends(verify_token)):
    # Pass user info extracted from token (e.g. current_user['user_id'])
    return await trip_controller.plan_new_trip(
        user_id=current_user["user_id"],
        origin=trip_req.origin,
        destination=trip_req.destination,
        start_date=trip_req.start_date,
        end_date=trip_req.end_date,
        budget_limit=trip_req.budget_limit,
        user_preferences=trip_req.user_preferences,
    )

@router.get("/")
async def get_trips(current_user: dict = Depends(verify_token)):
    return await trip_controller.get_user_trips(user_id=current_user["user_id"])


@router.post("/compare")
async def compare_destinations(compare_req: CompareDestinationsRequest, current_user: dict = Depends(verify_token)):
    return await trip_controller.compare_destinations(
        origin=compare_req.origin,
        destination_one=compare_req.destination_one,
        destination_two=compare_req.destination_two,
        start_date=compare_req.start_date,
        end_date=compare_req.end_date,
        user_prompt=compare_req.user_prompt,
    )
