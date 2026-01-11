 # config.py

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "telegram_bot"

ADMINS = [
        6778132055,
]

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS