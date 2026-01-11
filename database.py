  # database.py

import os
import sys
from pymongo import MongoClient, ASCENDING
from datetime import datetime

# ------------------ SAFE MONGO CONNECTION ------------------

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "telegram_bot"

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )
    client.admin.command("ping")
    print("✅ MongoDB connected")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    sys.exit(1)

db = client[DB_NAME]

# ------------------ COLLECTIONS ------------------

# already exists (from files bot)
users_col = db["users"]

# new collections
approved_content_col = db["approved_content"]
pending_content_col = db["pending_content"]
pending_broadcasts_col = db["pending_broadcasts"]

# ------------------ INDEXES (VERY IMPORTANT) ------------------
# These make queries fast and avoid future lag

approved_content_col.create_index([("letter", ASCENDING)])
approved_content_col.create_index([("slug", ASCENDING)], unique=True)

pending_content_col.create_index([("status", ASCENDING)])
pending_broadcasts_col.create_index([("status", ASCENDING)])

# ------------------ HELPERS ------------------

def normalize_slug(text: str) -> str:
    """
    Convert title to safe lowercase slug.
    Example: 'Attack on Titan' -> 'attack_on_titan'
    """
    return (
        text.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

# ------------------ READ FUNCTIONS (USER FLOW) ------------------

def get_letters_available():
    """
    Returns list of letters that actually have content.
    Example: ['A', 'B', 'C']
    """
    return sorted(
        approved_content_col.distinct("letter")
    )


def get_titles_by_letter(letter: str):
    """
    Get all approved anime/movies starting with a letter.
    """
    return list(
        approved_content_col.find(
            {"letter": letter.upper()},
            {"_id": 0, "title": 1, "slug": 1}
        ).sort("title", ASCENDING)
    )


def get_content_by_slug(slug: str):
    """
    Get full anime/movie data by slug.
    """
    return approved_content_col.find_one(
        {"slug": slug}
    )


def get_seasons_by_slug(slug: str):
    """
    Get seasons list for an anime/movie.
    """
    content = get_content_by_slug(slug)
    if not content:
        return []
    return content.get("seasons", [])


# ------------------ WRITE FUNCTIONS (ADMIN FLOW) ------------------

def submit_pending_content(
    title: str,
    description: str,
    seasons: list,
    submitted_by: int
):
    """
    Store anime/movie in pending_content for approval.
    """
    slug = normalize_slug(title)
    letter = title[0].upper()

    doc = {
        "type": "anime",
        "title": title,
        "slug": slug,
        "letter": letter,
        "description": description,
        "seasons": seasons,
        "submitted_by": submitted_by,
        "submitted_at": datetime.utcnow(),
        "status": "pending"
    }

    pending_content_col.insert_one(doc)
    return doc


def approve_content(pending_id, approved_by: int):
    """
    Move content from pending_content -> approved_content.
    """
    pending = pending_content_col.find_one({"_id": pending_id})
    if not pending:
        return False

    pending.pop("_id")
    pending.pop("status")

    pending["approved_by"] = approved_by
    pending["approved_at"] = datetime.utcnow()

    approved_content_col.insert_one(pending)
    pending_content_col.delete_one({"_id": pending_id})

    return True