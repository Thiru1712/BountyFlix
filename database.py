  # database.py

import os
import sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "telegram_bot"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ MongoDB connected")
except Exception as e:
    print("❌ MongoDB failed:", e)
    sys.exit(1)

db = client[DB_NAME]

users_col = db["users"]
approved_content_col = db["approved_content"]
pending_content_col = db["pending_content"]
pending_broadcasts_col = db["pending_broadcasts"]
stats_col = db["stats"]
menu_state_col = db["menu_state"]

approved_content_col.create_index([("letter", ASCENDING)])
approved_content_col.create_index([("slug", ASCENDING)], unique=True)

# ---------------- SLUG ----------------

def normalize_slug(text: str) -> str:
    return text.strip().lower().replace(" ", "_").replace("-", "_")

# ---------------- CONTENT ----------------

def get_letters_available():
    return sorted(approved_content_col.distinct("letter"))

def get_titles_by_letter(letter):
    return list(
        approved_content_col.find(
            {"letter": letter.upper()},
            {"_id": 0, "title": 1, "slug": 1}
        ).sort("title", ASCENDING)
    )

def get_content_by_slug(slug):
    return approved_content_col.find_one({"slug": slug})

def submit_pending_content(title, description, seasons, submitted_by):
    doc = {
        "type": "anime",
        "title": title,
        "slug": normalize_slug(title),
        "letter": title[0].upper(),
        "description": description,
        "seasons": seasons,
        "submitted_by": submitted_by,
        "submitted_at": datetime.utcnow(),
        "status": "pending"
    }
    pending_content_col.insert_one(doc)
    return doc

def approve_content(pending_id, approved_by):
    doc = pending_content_col.find_one({"_id": pending_id})
    if not doc:
        return False

    doc.pop("_id")
    doc.pop("status")

    doc["approved_by"] = approved_by
    doc["approved_at"] = datetime.utcnow()

    approved_content_col.insert_one(doc)
    pending_content_col.delete_one({"_id": pending_id})
    return True

# ---------------- BROADCAST ----------------

def submit_pending_broadcast(title, body, button_text, redirect, submitted_by):
    doc = {
        "title": title,
        "body": body,
        "button_text": button_text,
        "redirect": redirect,
        "submitted_by": submitted_by,
        "submitted_at": datetime.utcnow(),
        "status": "pending"
    }
    return pending_broadcasts_col.insert_one(doc).inserted_id

def get_pending_broadcast(broadcast_id):
    return pending_broadcasts_col.find_one({"_id": broadcast_id})

def approve_broadcast(broadcast_id):
    pending_broadcasts_col.delete_one({"_id": broadcast_id})

# ---------------- ANALYTICS ----------------

def inc_stat(field):
    stats_col.update_one(
        {"_id": "global"},
        {"$inc": {field: 1}, "$set": {"updated": datetime.utcnow()}},
        upsert=True
    )

def get_stats():
    return stats_col.find_one({"_id": "global"})

# ---------------- PIN STATE ----------------

def get_pinned_menu():
    return menu_state_col.find_one({"_id": "alphabet_menu"})

def save_pinned_menu(message_id):
    menu_state_col.update_one(
        {"_id": "alphabet_menu"},
        {"$set": {"message_id": message_id}},
        upsert=True
    )