 # main.py

import os
import time
import asyncio
import threading
from flask import Flask, jsonify

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import BOT_TOKEN, is_admin
from callbacks import main_menu, movies_menu
from admin import handle_broadcast, handle_add_title, admin_panel
from rate_limit import is_allowed

# ---------------- HEALTH SERVER ----------------
app = Flask(__name__)
START_TIME = time.time()
LAST_HEARTBEAT = time.time()

@app.route("/")
def home():
    return "BountyFlix alive 🟢"

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "uptime": int(time.time() - START_TIME),
        "heartbeat": int(time.time() - LAST_HEARTBEAT),
    }), 200


def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# ---------------- BOT HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_allowed(uid, "command"):
        return

    await update.message.reply_text(
        "🎬 Welcome to BountyFlix",
        reply_markup=main_menu()
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_allowed(uid, "admin"):
        return

    if not is_admin(uid):
        await update.message.reply_text("❌ Admin only")
        return

    await update.message.reply_text(
        "👑 Admin Panel",
        reply_markup=admin_panel()
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id

    if not is_allowed(uid, "callback"):
        await query.answer("⏳ Slow down")
        return

    await query.answer()

    if query.data == "movies":
        await query.edit_message_text(
            "🎬 Available Movies:",
            reply_markup=movies_menu()
        )

    elif query.data == "back":
        await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=main_menu()
        )


# ---------------- BOT RUNNER ----------------
async def bot_main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("broadcast", handle_broadcast))
    application.add_handler(CommandHandler("addtitle", handle_add_title))
    application.add_handler(CallbackQueryHandler(callback_handler))

    print("🤖 Telegram bot started")
    await application.run_polling()


def start_bot():
    global LAST_HEARTBEAT
    while True:
        try:
            asyncio.run(bot_main())
        except Exception as e:
            print("❌ Bot crashed, restarting:", e)
            time.sleep(5)


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    start_bot()