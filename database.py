 # database.py

from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# SHARED collection with old bot
users_col = db["users"]

# BountyFlix collections
admins_col = db["bountyflix_admins"]
logs_col = db["bountyflix_logs"]

def get_all_user_ids():
    ids = []
    for u in users_col.find({}):
        if "user_id" in u:
            ids.append(u["user_id"])
        elif "user id" in u:  # typo-safe
            ids.append(u["user id"])
    return list(set(ids))  # remove duplicates