from app.models.user_model import UserModel
from app.config.db import trips_collection, users_collection
# Assuming trip_planner graph can be imported here
from trip_planner.graph import graph
from langchain_core.messages import HumanMessage
from trip_planner.agents.llm_config import get_llm
from trip_planner.tools.activities import destination_activities
import datetime
import asyncio


UNWANTED_PLACE_KEYWORDS = {
    "school",
    "bank",
    "atm",
    "college",
    "university",
    "post office",
    "hotel",
    "bar",
}


def _filter_places(places):
    filtered = []
    for place in places:
        if not isinstance(place, dict):
            continue
        name = str(place.get("name", "")).strip()
        if not name:
            continue
        lowered = name.lower()
        if any(keyword in lowered for keyword in UNWANTED_PLACE_KEYWORDS):
            continue
        filtered.append(place)
    return filtered


def _top_places_for_prompt(places, limit=7):
    top = []
    for place in places[:limit]:
        top.append({
            "name": place.get("name"),
            "type": place.get("type"),
            "rating": place.get("rating"),
            "price": place.get("price"),
        })
    return top

async def plan_new_trip(user_id: str, origin: str, destination: str, start_date: str, end_date: str, budget_limit: int, user_preferences: str = ""):
    # Set up initial state matches your PlannerState
    initial_state = {
        "messages": [HumanMessage(content=f"Plan a trip from {origin} to {destination}. User preferences: {user_preferences or 'None'}")],
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "budget_limit": budget_limit,
        "user_preferences": user_preferences,
        "weather_data": None,
        "transport_data": None,
        "activities_data": None,
        "budget_insights": "",
        "final_itinerary": "",
        "next": ""
    }
    
    # Invoke the LangGraph graph
    # Using .ainvoke or .invoke depending on your graph setup
    result = await graph.ainvoke(initial_state)
    
    final_itinerary = result.get("final_itinerary", "Trip planned successfully!")
    
    # Save the trip to the database
    trip_data = {
        "user_id": user_id,
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "budget_limit": budget_limit,
        "user_preferences": user_preferences,
        "weather_data": result.get("weather_data"),
        "transport_data": result.get("transport_data"),
        "activities_data": result.get("activities_data"),
        "budget_insights": result.get("budget_insights"),
        "final_itinerary": final_itinerary,
        "created_at": datetime.datetime.utcnow()
    }
    
    inserted_trip = trips_collection.insert_one(trip_data)
    
    from bson import ObjectId
    # Also link this trip to the user's document
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"trip_ids": str(inserted_trip.inserted_id)}}
    )
    
    # Convert MongoDB ObjectId to string for JSON serialization
    trip_data["_id"] = str(inserted_trip.inserted_id)
    
    return trip_data

async def get_user_trips(user_id: str):
    # Fetch all trips for the specific user
    trips = list(trips_collection.find({"user_id": user_id}).sort("created_at", -1))
    
    # Iterate and convert _id to string
    for trip in trips:
        trip["_id"] = str(trip["_id"])
        
    return trips


async def compare_destinations(
    origin: str,
    destination_one: str,
    destination_two: str,
    start_date: str,
    end_date: str,
    user_prompt: str,
):
    activities_one_raw, activities_two_raw = await asyncio.gather(
        asyncio.to_thread(destination_activities.invoke, {"city": destination_one}),
        asyncio.to_thread(destination_activities.invoke, {"city": destination_two}),
    )

    places_one = _filter_places((activities_one_raw or {}).get("data", []))
    places_two = _filter_places((activities_two_raw or {}).get("data", []))

    top_places_one = _top_places_for_prompt(places_one, limit=7)
    top_places_two = _top_places_for_prompt(places_two, limit=7)

    if len(top_places_one) < 3 or len(top_places_two) < 3:
        return {
            "origin": origin,
            "start_date": start_date,
            "end_date": end_date,
            "user_prompt": user_prompt,
            "destination_one": {
                "destination": destination_one,
                "weather_data": None,
                "transport_data": None,
                "activities_data": {
                    "status": "success",
                    "data": top_places_one,
                    "message": "Top curated places for destination A",
                },
                "summary": {"curated_places_count": len(top_places_one)},
            },
            "destination_two": {
                "destination": destination_two,
                "weather_data": None,
                "transport_data": None,
                "activities_data": {
                    "status": "success",
                    "data": top_places_two,
                    "message": "Top curated places for destination B",
                },
                "summary": {"curated_places_count": len(top_places_two)},
            },
            "comparison": "Could not find enough relevant attractions for one or both destinations. Try different destinations.",
        }

    llm = get_llm()
    comparison_prompt = (
        "You are a travel comparison expert.\n"
        "Compare the two destinations based on the provided places data and user preferences.\n"
        "Return clean markdown with these exact sections:\n"
        "1) Trip Inputs\n"
        "2) Destination A Snapshot\n"
        "3) Destination B Snapshot\n"
        "4) Side-by-Side Comparison Table\n"
        "5) Best Choice Based on User Preferences\n"
        "6) Trade-offs and Risks\n"
        "7) Final Recommendation\n"
        "In Final Recommendation, include a single winner and short reason.\n"
        "\n"
        f"Trip origin: {origin}\n"
        f"Destination A: {destination_one}\n"
        f"Destination B: {destination_two}\n"
        f"Start date: {start_date}\n"
        f"End date: {end_date}\n"
        f"User preferences: {user_prompt}\n\n"
        "Destination A top places (curated):\n"
        f"{top_places_one}\n\n"
        "Destination B top places (curated):\n"
        f"{top_places_two}\n"
    )

    try:
        comparison = llm.invoke([HumanMessage(content=comparison_prompt)]).content
    except Exception:
        comparison = (
            "## Trip Inputs\n"
            f"- Origin: {origin}\n"
            f"- Destination A: {destination_one}\n"
            f"- Destination B: {destination_two}\n"
            f"- Dates: {start_date} to {end_date}\n"
            f"- Preferences: {user_prompt}\n\n"
            "## Destination A Snapshot\n"
            f"- {destination_one} appears suitable for travelers with these preferences.\n\n"
            "## Destination B Snapshot\n"
            f"- {destination_two} also appears suitable depending on budget, weather, and activities.\n\n"
            "## Side-by-Side Comparison Table\n"
            "| Metric | Destination A | Destination B |\n"
            "|---|---|---|\n"
            "| Overall fit | Good | Good |\n\n"
            "## Best Choice Based on User Preferences\n"
            "Both destinations are viable. Final choice depends on your strongest preference.\n\n"
            "## Trade-offs and Risks\n"
            "Without live tool data, pricing/weather/activity details may vary in reality.\n\n"
            "## Final Recommendation\n"
            "Retry later if LLM is unavailable to get a richer recommendation."
        )

    return {
        "origin": origin,
        "start_date": start_date,
        "end_date": end_date,
        "user_prompt": user_prompt,
        "destination_one": {
            "destination": destination_one,
            "weather_data": None,
            "transport_data": None,
            "activities_data": {
                "status": "success",
                "data": top_places_one,
                "message": "Top curated places for destination A",
            },
            "summary": {
                "curated_places_count": len(top_places_one),
            },
        },
        "destination_two": {
            "destination": destination_two,
            "weather_data": None,
            "transport_data": None,
            "activities_data": {
                "status": "success",
                "data": top_places_two,
                "message": "Top curated places for destination B",
            },
            "summary": {
                "curated_places_count": len(top_places_two),
            },
        },
        "comparison": comparison,
    }
