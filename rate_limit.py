 #rate_limit.py

import time
from collections import defaultdict

CALLS = defaultdict(list)

LIMITS = {
    "command": (5, 10),
    "callback": (8, 10),
    "admin": (10, 60),
}

def is_allowed(user_id: int, action: str) -> bool:
    now = time.time()
    max_calls, window = LIMITS[action]
    key = (user_id, action)

    CALLS[key] = [t for t in CALLS[key] if t > now - window]

    if len(CALLS[key]) >= max_calls:
        return False

    CALLS[key].append(now)
    return True