import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Standard synchronous MongoDB connection setup
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collections exported directly for easy use in controllers/routes
users_collection = db["users"]
trips_collection = db["trips"]
