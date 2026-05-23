import sys
import os

# Ensure root directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user_routes, trip_routes
from app.routes.explore_routes import explore_router

# This file acts exactly as app.js and server.js combined in the MERN stack context
app = FastAPI(title="Trip Planner Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Register Routes (Similar to app.use('/api/users', userRoutes) in Express)
app.include_router(user_routes.router, prefix="/api/users", tags=["Users"])
app.include_router(trip_routes.router, prefix="/api/trips", tags=["Trips"])
app.include_router(explore_router, prefix="/api/explore", tags=["Explore"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Trip Planner API. MERN-style architecture in Python!"}

# To run the server (equivalent to node server.js):
# uvicorn main:app --reload
