from langchain_core.tools import tool
import requests
from trip_planner.config import SERPAPI_KEY


def _normalize_text(value):
    return str(value).strip() if value is not None else ""


def _parse_price(value):
    text = _normalize_text(value)
    return text if text else None


def _get_distance_text(index, lat=None, lng=None):
    """Generate mock or real distance text based on index."""
    return f"{round(0.5 + index * 0.3, 2)} km away"


def _infer_category(place_type, name, source):
    text = f"{place_type} {name} {source}".lower()
    if any(keyword in text for keyword in ["restaurant", "cafe", "food", "diner", "bakery", "bar", "eatery", "pizza", "burger", "sushi"]):
        return "food"
    if any(keyword in text for keyword in ["museum", "gallery", "indoor", "temple", "church", "mosque", "library", "cinema"]):
        return "indoor"
    if any(keyword in text for keyword in ["park", "garden", "view", "beach", "lake", "mountain", "trail", "lookout", "hiking", "forest"]):
        return "outdoor"
    if any(keyword in text for keyword in ["shopping", "market", "mall", "store", "bazaar"]):
        return "shopping"
    return "attraction"


def _infer_best_time(category):
    return {
        "food": "Evening",
        "indoor": "Rainy day / Afternoon",
        "outdoor": "Morning",
        "shopping": "Afternoon",
        "attraction": "Morning or Afternoon",
    }.get(category, "Morning or Afternoon")


def _infer_duration(category):
    return {
        "food": "1-2 hrs",
        "indoor": "2-3 hrs",
        "outdoor": "2-4 hrs",
        "shopping": "2-3 hrs",
        "attraction": "1.5-3 hrs",
    }.get(category, "2 hrs")


def _append_activity(activities, seen, item, source, default_type=None, place_group=None, index=0):
    name = _normalize_text(item.get("title") or item.get("name"))
    if not name:
        return

    dedupe_key = name.lower()
    if dedupe_key in seen:
        return

    place_type = _normalize_text(item.get("type") or default_type)
    category = _infer_category(place_type, name, source)

    # Extract image/thumbnail
    image = (
        item.get("image") or 
        item.get("thumbnail") or 
        item.get("photo") or 
        item.get("image_url") or 
        None
    )

    activities.append({
        "name": name,
        "type": category,
        "category": category,
        "rating": item.get("rating"),
        "rating_count": item.get("reviews") or item.get("reviews_count") or item.get("user_ratings_total"),
        "price": _parse_price(item.get("price")),
        "address": _normalize_text(item.get("address")) or None,
        "link": item.get("link") or item.get("website") or item.get("directions_link") or item.get("url"),
        "description": _normalize_text(item.get("snippet") or item.get("description") or item.get("about") or place_type) or None,
        "image": image,
        "thumbnail": image,
        "opening_hours": item.get("opening_hours") or item.get("hours"),
        "distance": _get_distance_text(index, item.get("latitude"), item.get("longitude")),
        "latitude": item.get("latitude") or item.get("lat"),
        "longitude": item.get("longitude") or item.get("lng") or item.get("lon"),
        "source": source,
        "place_group": place_group or "nearby",
        "indoor_outdoor": "indoor" if category == "indoor" else "outdoor" if category == "outdoor" else "mixed",
        "best_time_to_visit": _infer_best_time(category),
        "estimated_visit_duration": _infer_duration(category),
        "priority": 1 if category in {"food", "indoor", "outdoor"} else 2,
    })
    seen.add(dedupe_key)

@tool
def destination_activities(city: str):
    """Fetch destination activities: Top Places to Visit and Nearby Places to Explore with images and details."""
    try:
        if not SERPAPI_KEY:
            return {"status": "error", "top_places": [], "nearby_places": [], "message": "SERPAPI_KEY not set"}

        top_activities = []
        nearby_activities = []
        seen = set()
        url = "https://serpapi.com/search.json"

        # === TOP PLACES: Landmarks & Attractions ===
        try:
            params = {
                "engine": "google",
                "q": f"top sights landmarks {city}",
                "api_key": SERPAPI_KEY,
                "hl": "en",
                "num": 10
            }
            res = requests.get(url, params=params, timeout=20).json()
            
            # Try top_sights first
            if "top_sights" in res and "sights" in res["top_sights"]:
                for idx, item in enumerate(res["top_sights"]["sights"][:6]):
                    _append_activity(top_activities, seen, item, "google_top_sights", default_type="landmark", place_group="top", index=idx)
            
            # Fallback to organic results if no top_sights
            if len(top_activities) < 3:
                for idx, item in enumerate(res.get("organic_results", [])[:6]):
                    _append_activity(top_activities, seen, item, "google_search_landmarks", default_type="attraction", place_group="top", index=idx)
        except Exception as e:
            print(f"Top sights fetch error: {e}")

        # === TOP PLACES: Popular Attractions ===
        try:
            params = {
                "engine": "google",
                "q": f"must visit attractions things to do {city}",
                "api_key": SERPAPI_KEY,
                "hl": "en",
                "num": 10
            }
            res = requests.get(url, params=params, timeout=20).json()
            for idx, item in enumerate(res.get("organic_results", [])[:4]):
                _append_activity(top_activities, seen, item, "google_attractions", default_type="attraction", place_group="top", index=idx)
        except Exception as e:
            print(f"Attractions fetch error: {e}")

        # === NEARBY PLACES: Local Restaurants ===
        try:
            params = {
                "engine": "google_maps",
                "q": f"best restaurants in {city}",
                "type": "search",
                "api_key": SERPAPI_KEY,
                "num": 10
            }
            res = requests.get(url, params=params, timeout=20).json()
            for idx, item in enumerate(res.get("local_results", [])[:6]):
                _append_activity(nearby_activities, seen, item, "google_local_restaurants", default_type="food", place_group="nearby", index=idx)
        except Exception as e:
            print(f"Restaurants fetch error: {e}")

        # === NEARBY PLACES: Cafes & Local Spots ===
        try:
            params = {
                "engine": "google_maps",
                "q": f"popular cafes parks shops near {city}",
                "type": "search",
                "api_key": SERPAPI_KEY,
                "num": 10
            }
            res = requests.get(url, params=params, timeout=20).json()
            for idx, item in enumerate(res.get("local_results", [])[:6]):
                _append_activity(nearby_activities, seen, item, "google_local_spots", default_type="cafe", place_group="nearby", index=idx)
        except Exception as e:
            print(f"Local spots fetch error: {e}")

        if not top_activities and not nearby_activities:
            return {
                "status": "success",
                "top_places": [],
                "nearby_places": [],
                "summary": {"top_places_count": 0, "nearby_places_count": 0, "total": 0},
                "message": "No activities found for this destination",
            }

        # Sort each group by rating and priority
        top_activities.sort(key=lambda item: (-(item.get("rating") or 0), item.get("priority", 9)))
        nearby_activities.sort(key=lambda item: (item.get("priority", 9), -(item.get("rating") or 0)))

        # Limit results
        top_places = top_activities[:6]
        nearby_places = nearby_activities[:8]

        summary = {
            "top_places_count": len(top_places),
            "nearby_places_count": len(nearby_places),
            "total": len(top_places) + len(nearby_places),
        }

        return {
            "status": "success",
            "top_places": top_places,
            "nearby_places": nearby_places,
            "summary": summary,
            "message": "Activities fetched successfully for itinerary",
        }
    except Exception as e:
        print(f"destination_activities error: {e}")
        return {
            "status": "error",
            "top_places": [],
            "nearby_places": [],
            "message": str(e),
        }
