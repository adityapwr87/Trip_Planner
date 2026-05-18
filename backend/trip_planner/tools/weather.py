from langchain_core.tools import tool
import requests
from datetime import datetime
from trip_planner.config import WEATHER_API_KEY

@tool
def get_weather(city: str, start_date: str, end_date: str):
    """Fetch day-wise weather forecast for given city and date range."""
    try:
        if not WEATHER_API_KEY:
            return {"status": "error", "data": [], "message": "WEATHER_API_KEY not configured"}

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if end < start:
            return {"status": "error", "data": [], "message": "Invalid date range"}

        days = (end - start).days + 1
        if days > 14:
            return {"status": "error", "data": [], "message": "Max 14 day forecast allowed"}

        url = "https://api.weatherapi.com/v1/forecast.json"
        params = {"key": WEATHER_API_KEY, "q": city, "days": days, "aqi": "no", "alerts": "no"}
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return {"status": "error", "data": [], "message": f"Weather API error {response.status_code}"}

        data = response.json()
        if "forecast" not in data:
            return {"status": "error", "data": [], "message": "No forecast data"}

        result = []
        for day in data["forecast"]["forecastday"]:
            result.append({
                "date": day["date"],
                "max_temp": day["day"]["maxtemp_c"],
                "min_temp": day["day"]["mintemp_c"],
                "climate": day["day"]["condition"]["text"],
                "rain_chance": day["day"]["daily_chance_of_rain"]
            })

        return {"status": "success", "data": result, "location": {"lat": data["location"]["lat"], "lon": data["location"]["lon"]}, "message": "Weather fetched successfully"}
    except Exception as e:
        return {"status": "error", "data": [], "message": f"Weather tool failure: {str(e)}"}
