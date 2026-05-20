from langchain_core.tools import tool
import os
import requests  # <-- Added for OSRM Road API
from dotenv import load_dotenv
from serpapi import GoogleSearch
import datetime
import re

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# ------------------ COMMON ------------------
def compute_score(cost, duration):
    return round(cost * 0.6 + duration * 0.4, 2)

from trip_planner.utils import get_iata_code

# ------------------ HELPER: GEOCODING (For Roads) ------------------
def get_coordinates(city_name):
    """Converts a city name to latitude and longitude using free OpenStreetMap API."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        # Nominatim requires a custom User-Agent to prevent blocking
        headers = {
            'User-Agent': 'CodeKeeperApp/1.0 (adityapwr13@gmail.com)' 
        }
        params = {
            'q': city_name, 
            'format': 'json', 
            'limit': 1
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data:
            # Returns Longitude, Latitude
            return float(data[0]['lon']), float(data[0]['lat'])
    except Exception as e:
        print(f"Geocoding Error for {city_name}: {e}")
    
    return None, None

# ------------------ FLIGHTS (Unchanged) ------------------
def get_flights(origin, destination, date):
    results = []

    # ------------------ DATE CLEANING ------------------
    if date and isinstance(date, str):
        if " " in date:
            date = date.split(" ")[0]
        if "T" in date:
            date = date.split("T")[0]

    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except (ValueError, TypeError):
        date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # ------------------ API CALL ------------------
    try:
        params = {
            "engine": "google_flights",
            "departure_id": get_iata_code(origin),
            "arrival_id": get_iata_code(destination),
            "outbound_date": date,
            "type": "2",  # One-way
            "currency": "INR",
            "hl": "en",
            "api_key": SERPAPI_KEY
        }

        search = GoogleSearch(params)
        data = search.get_dict()

        if "error" in data:
            print(f"SerpApi Error (Flights): {data['error']}")
            return []

        # ------------------ PROCESS TOP FLIGHTS ------------------
        for flight in data.get("best_flights", [])[:6]:  # ✅ limit to 6
            price = flight.get("price", 0)
            total_duration = flight.get("total_duration", 0)
            duration_hours = total_duration / 60 if total_duration else 0

            results.append({
                "mode": "flight",
                "provider": "Google Flights (SerpApi)",

                # Basic Info
                "price": price,
                "duration_hours": round(duration_hours, 2),
                "total_duration_minutes": total_duration,
                "score": compute_score(price, duration_hours),

                # ------------------ FULL STRUCTURED DATA ------------------
                "flights": flight.get("flights", []),           # ✈️ segments
                "layovers": flight.get("layovers", []),         # ⏱ layovers
                "carbon_emissions": flight.get("carbon_emissions", {}),
                "airline_logo": flight.get("airline_logo"),
                "extensions": flight.get("extensions", []),
                "booking_token": flight.get("booking_token"),
                "type": flight.get("type"),

                # ------------------ EXTRA (VERY USEFUL FOR UI) ------------------
                "first_departure": (
                    flight.get("flights", [{}])[0].get("departure_airport")
                    if flight.get("flights") else None
                ),
                "final_arrival": (
                    flight.get("flights", [{}])[-1].get("arrival_airport")
                    if flight.get("flights") else None
                ),
                "airline": (
                    flight.get("flights", [{}])[0].get("airline")
                    if flight.get("flights") else None
                )
            })

    except Exception as e:
        print("Flight Error:", e)
        return []

    return results

# ------------------ TRAINS (Unchanged) ------------------
def get_trains(origin, destination, date):
    results = []
    try:
        params = {
            "engine": "google",
            "q": f"trains from {origin} to {destination} on {date}",
            "api_key": SERPAPI_KEY
        }

        search = GoogleSearch(params)
        data = search.get_dict()

        # Parsing organic results (approximation)
        for idx, res in enumerate(data.get("organic_results", [])[:3]):
            snippet = res.get("snippet", "")
            title = res.get("title") or f"Train option {idx + 1}"

            results.append({
                "mode": "train",
                "duration_hours": 10,  # fallback estimate
                "duration_text": "~10 hrs",
                "estimated_cost": 500,
                "provider": "Google Search (SerpApi)",
                "title": title,
                "route_name": title,
                "info": snippet,
                "source_link": res.get("link"),
                "is_primary": idx == 0,
                "score": compute_score(500, 10)
            })

    except Exception as e:
        print("Train Error:", e)

    return results

# ------------------ ROADS (Updated to Free OSRM) ------------------
def get_road(origin, destination):
    results = []
    
    # 1. Convert origin and destination strings to coordinates
    lon1, lat1 = get_coordinates(origin)
    lon2, lat2 = get_coordinates(destination)
    
    if not (lon1 and lat1 and lon2 and lat2):
        print("Could not resolve coordinates for routing.")
        return results

    try:
        # 2. Call OSRM Public API with alternatives enabled so we can return multiple routes.
        url = (
            f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
            "?overview=full&alternatives=true"
        )

        response = requests.get(url, timeout=12)
        if response.status_code != 200:
            return results

        data = response.json()

        if data.get("code") == "Ok":
            routes = data.get("routes", [])[:4]
            if not routes:
                return results

            road_options = []

            for idx, route in enumerate(routes):
                # Parse distance (OSRM returns meters) -> Convert to km
                distance_km = route.get("distance", 0) / 1000.0

                # Parse duration (OSRM returns seconds) -> Convert to hours
                duration_hours = route.get("duration", 0) / 3600.0

                # Estimate Cost (Assuming 7.5 INR per km)
                estimated_cost = distance_km * 7.5

                road_options.append({
                    "mode": "road",
                    "provider": "OSRM (Free Open Source)",
                    "is_primary": False,

                    # Core Metrics
                    "estimated_cost": round(estimated_cost),
                    "duration_hours": round(duration_hours, 2),
                    "distance_km": round(distance_km, 2),
                    "score": compute_score(estimated_cost, duration_hours),

                    # Frontend Visuals
                    "route_name": f"Route {idx + 1}: {origin} to {destination}",
                    "encoded_polyline": route.get("geometry", "")
                })

            # Mark the fastest route as the primary route for UI emphasis.
            fastest_route = min(
                road_options,
                key=lambda option: option["duration_hours"],
            )
            fastest_route["is_primary"] = True

            results.extend(road_options)

    except Exception as e:
        print(f"Road Search Warning (OSRM skipped): {e}")

    return results

# ------------------ MAIN TOOL ------------------
@tool
def get_transport_options(origin: str, destination: str, date: str):
    """
    Fetch transport options (flight, train, road) using SerpApi and OSRM.
    """

    results = []

    # Flights (SerpApi)
    results.extend(get_flights(origin, destination, date))

    # Trains (SerpApi)
    results.extend(get_trains(origin, destination, date))

    # Road (OSRM - Free)
    results.extend(get_road(origin, destination))

    results.sort(key=lambda x: x["score"])

    return {
        "status": "success",
        "data": results,
        "message": "Transport options fetched successfully"
    }