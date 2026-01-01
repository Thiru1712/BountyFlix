import json, os, time, requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")
MONGO_API_KEY = os.getenv("MONGO_API_KEY")

START_TIME = time.time()
TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ---------- Redis ----------
def redis(cmd, key="", value=None, ex=None):
    url = f"{REDIS_URL}/{cmd}/{key}"
    headers = {"Authorization": f"Bearer {REDIS_TOKEN}"}
    data = {}
    if value is not None: data["value"] = value
    if ex: data["ex"] = ex
    r = requests.post(url, headers=headers, json=data)
    return r.json().get("result")

# ---------- Mongo ----------
MONGO_ENDPOINT = "https://data.mongodb-api.com/app/data-xxxx/endpoint/data/v1/action"

def mongo(action, payload):
    return requests.post(
        f"{MONGO_ENDPOINT}/{action}",
        headers={
            "Content-Type": "application/json",
            "api-key": MONGO_API_KEY
        },
        json=payload
    ).json()

def is_admin(user_id):
    r = mongo("findOne", {
        "dataSource": "Cluster0",
        "database": "bot",
        "collection": "admins",
        "filter": {"user_id": user_id}
    })
    return r.get("document") is not None

def add_user(user):
    mongo("insertOne", {
        "dataSource": "Cluster0",
        "database": "bot",
        "collection": "users",
        "document": {
            "user_id": user["id"],
            "username": user.get("username"),
            "first_name": user.get("first_name")
        }
    })

# ---------- Telegram ----------
def send(chat_id, text):
    requests.post(f"{TG}/sendMessage", json={"chat_id": chat_id, "text": text})

# ---------- Stats ----------
def update_stats(user_id):
    redis("incr", "total_msgs")
    redis("incr", "msgs_today")
    redis("set", f"active:{user_id}", 1, ex=86400)

def get_stats():
    total = redis("get", "total_msgs") or 0
    today = redis("get", "msgs_today") or 0
    active = redis("keys", "active:*")
    uptime = int(time.time() - START_TIME)
    return total, today, len(active), uptime

# ---------- Webhook ----------
def handler(request):
    path = request.url.split("/")[-1]

    # ---- Dashboard ----
    if path == "dashboard":
        total, today, active, uptime = get_stats()
        return f"""
        <html><body>
        <h1>📊 Bot Dashboard</h1>
        <p>Total messages: {total}</p>
        <p>Messages today: {today}</p>
        <p>Active users (24h): {active}</p>
        <p>Uptime: {uptime}s</p>
        </body></html>
        """

    update = json.loads(request.body)
    if "message" not in update:
        return "ok"

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user = msg["from"]
    text = msg.get("text", "")

    add_user(user)
    update_stats(user["id"])

    # ---- Admin commands ----
    if text.startswith("/stats") and is_admin(user["id"]):
        t, d, a, u = get_stats()
        send(chat_id, f"""
📊 Bot Stats
👥 Active (24h): {a}
💬 Today: {d}
💬 Total: {t}
⏱ Uptime: {u}s
        """)
        return "ok"

    if text.startswith("/addadmin") and is_admin(user["id"]):
        new_id = int(text.split()[1])
        mongo("insertOne", {
            "dataSource": "Cluster0",
            "database": "bot",
            "collection": "admins",
            "document": {"user_id": new_id}
        })
        send(chat_id, "✅ Admin added")
        return "ok"

    # ---- Normal user ----
    send(chat_id, "🚀 Bot online & fast")
    return "ok"
