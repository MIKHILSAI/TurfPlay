import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "turf_booking")

client = MongoClient(MONGODB_URI)

db = client[MONGODB_DATABASE]

print("MongoDB connected successfully")