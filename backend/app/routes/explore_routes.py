from fastapi import APIRouter, HTTPException
from typing import Optional
from serpapi import GoogleSearch
import os
import httpx

explore_router = APIRouter()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

@explore_router.get("/places")
async def get_places(location: str):
    try:
        params = {
            "engine": "google",
            "q": f"top sights in {location}",
            "api_key": SERPAPI_KEY,
            "hl": "en",
            "gl": "in"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        places = []
        
        if "top_sights" in results and "sights" in results["top_sights"]:
            for index, sight in enumerate(results["top_sights"]["sights"]):
                places.append({
                    "id": index,
                    "title": sight.get("title", ""),
                    "description": sight.get("description", ""),
                    "image": sight.get("thumbnail", "https://via.placeholder.com/300x400?text=No+Image"),
                    "rating": sight.get("rating", ""),
                    "distance": f"{round(1 + index * 0.5, 2)} km away" # Mock distance since it's hard to get exact from general search
                })
        elif "local_results" in results:
             for index, local in enumerate(results["local_results"]):
                # Sometimes images are deep in local_results
                thumbnail = local.get("thumbnail", "https://via.placeholder.com/300x400?text=No+Image")
                places.append({
                    "id": index,
                    "title": local.get("title", ""),
                    "description": local.get("type", ""),
                    "image": thumbnail,
                    "rating": local.get("rating", ""),
                    "distance": f"{round(1 + index * 0.5, 2)} km away"
                })
        
        # If no image found or list empty, fallback
        if not places:
            places = [
                {
                    "id": 1,
                    "title": f"Explore {location}",
                    "description": "Discover local attractions",
                    "image": "https://via.placeholder.com/300x400?text=Explore+More",
                    "distance": "Nearby"
                }
            ]

        return {"status": "success", "location": location, "places": places}
        
    except Exception as e:
        print(f"Places Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
