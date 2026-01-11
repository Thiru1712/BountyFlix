#main.py

from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
)
from telegram.error import BadRequest
from flask import Flask, jsonify
import threading, time

from config import BOT_TOKEN, is_admin
from callbacks import main_menu, movies_menu
from admin import admin_panel, handle_broadcast, handle_add_title
from rate_limit import is_allowed

# ------------------ HEALTH ------------------
app = Flask(__name__)
START_TIME = time.time()
LAST_HEARTBEAT = time.time()
BOT_OK = True

@app.route("/")
def home():
    return "BountyFlix alive 🟢"

@app.route("/health")
def health():
    return jsonify({
        "status": "ok" if BOT_OK else "error",
        "uptime": int(time.time() - START_TIME),
        "heartbeat": int(time.time() - LAST_HEARTBEAT)
    }), 200

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ------------------ BOT ------------------
def start(update, context):
    uid = update.effective_user.id
    if not is_allowed(uid, "command"):
        return
    update.message.reply_text("🎬 Welcome to BountyFlix", reply_markup=main_menu())

def admin(update, context):
    uid = update.effective_user.id
    if not is_allowed(uid, "admin"):
        return
    if not is_admin(uid):
        update.message.reply_text("❌ Admin only")
        return
    update.message.reply_text("👑 Admin Panel", reply_markup=admin_panel())

def callback_handler(update, context):
    query = update.callback_query
    uid = query.from_user.id

    if not is_allowed(uid, "callback"):
        query.answer("⏳ Slow down")
        return

    query.answer()

    if query.data == "movies":
        query.edit_message_text("🎬 Available Movies:", reply_markup=movies_menu())

    elif query.data == "back":
        query.edit_message_text("🏠 Main Menu", reply_markup=main_menu())

def run_bot():
    global BOT_OK, LAST_HEARTBEAT

    while True:
        try:
            BOT_OK = True
            updater = Updater(BOT_TOKEN, use_context=True)
            dp = updater.dispatcher

            dp.add_handler(CommandHandler("start", start))
            dp.add_handler(CommandHandler("admin", admin))
            dp.add_handler(CommandHandler("broadcast", handle_broadcast))
            dp.add_handler(CommandHandler("addtitle", handle_add_title))
            dp.add_handler(CallbackQueryHandler(callback_handler))

            updater.start_polling()

            while True:
                LAST_HEARTBEAT = time.time()
                time.sleep(10)

        except Exception as e:
            BOT_OK = False
            print("Bot crashed, restarting:", e)
            time.sleep(5)

# ------------------ ENTRY ------------------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()