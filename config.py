 # config.py

# ======================================================
# BOT OWNERSHIP & ACCESS CONTROL
# ======================================================

OWNER_ID = 6778132055

ADMINS = [
    OWNER_ID
]

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# ======================================================
# CHANNEL CONFIGURATION
# ======================================================

CHANNEL_ID = -1002522385560

# ======================================================
# FEATURE TOGGLES
# ======================================================

ENABLE_ANALYTICS = True
ENABLE_AUTO_PIN = True
ENABLE_RATE_LIMIT = True