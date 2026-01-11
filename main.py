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

from callbacks import (
    alphabet_menu,
    titles_menu,
    seasons_menu,
    download_menu,
)
from database import get_content_by_slug
from rate_limit import is_allowed

# -------------------- HEALTH SERVER --------------------

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
        "uptime_seconds": int(time.time() - START_TIME),
        "heartbeat_seconds_ago": int(time.time() - LAST_HEARTBEAT)
    }), 200


def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# -------------------- COMMANDS --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not is_allowed(uid, "command"):
        return

    await update.message.reply_text(
        "🎬 <b>Browse Anime & Movies</b>\n\nSelect a letter to begin 👇",
        reply_markup=alphabet_menu(),
        parse_mode="HTML"
    )

# -------------------- CALLBACK HANDLER --------------------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_HEARTBEAT

    query = update.callback_query
    uid = query.from_user.id

    if not is_allowed(uid, "callback"):
        await query.answer("⏳ Slow down")
        return

    await query.answer()
    LAST_HEARTBEAT = time.time()

    data = query.data

    # -------- LETTER --------
    if data.startswith("letter:"):
        letter = data.split(":")[1]

        await query.edit_message_text(
            f"🔤 <b>Titles starting with {letter}</b>",
            reply_markup=titles_menu(letter),
            parse_mode="HTML"
        )

    # -------- ANIME --------
    elif data.startswith("anime:"):
        slug = data.split(":")[1]
        content = get_content_by_slug(slug)

        if not content:
            await query.edit_message_text("❌ Content not found")
            return

        await query.edit_message_text(
            f"🎬 <b>{content['title']}</b>\n\nSelect a season 👇",
            reply_markup=seasons_menu(slug),
            parse_mode="HTML"
        )

    # -------- SEASON --------
    elif data.startswith("season:"):
        _, slug, season = data.split(":")
        season = int(season)
        content = get_content_by_slug(slug)

        await query.edit_message_text(
            f"🎬 <b>{content['title']}</b>\nSeason {season}\n\nClick below to download 👇",
            reply_markup=download_menu(slug, season),
            parse_mode="HTML"
        )

    # -------- REDIRECT --------
    elif data.startswith("redirect:"):
        _, slug, season = data.split(":")
        season = int(season)
        content = get_content_by_slug(slug)

        for s in content.get("seasons", []):
            if s["season"] == season:
                await query.answer("Opening download…", show_alert=False)
                await query.message.reply_text(
                    "⬇ Download here:",
                    reply_markup=None
                )
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text=s["redirect"]
                )
                return

        await query.answer("❌ Link not found")

    # -------- BACK HANDLERS --------
    elif data == "back:alphabet":
        await query.edit_message_text(
            "🎬 <b>Browse Anime & Movies</b>\n\nSelect a letter to begin 👇",
            reply_markup=alphabet_menu(),
            parse_mode="HTML"
        )

    elif data.startswith("back:titles:"):
        letter = data.split(":")[2]
        await query.edit_message_text(
            f"🔤 <b>Titles starting with {letter}</b>",
            reply_markup=titles_menu(letter),
            parse_mode="HTML"
        )

    elif data.startswith("back:seasons:"):
        slug = data.split(":")[2]
        content = get_content_by_slug(slug)

        await query.edit_message_text(
            f"🎬 <b>{content['title']}</b>\n\nSelect a season 👇",
            reply_markup=seasons_menu(slug),
            parse_mode="HTML"
        )

# -------------------- BOT RUNNER --------------------

async def bot_main():
    application = (
        ApplicationBuilder()
        .token(os.getenv("TOKEN"))
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(callback_handler))

    print("🤖 BountyFlix bot started")
    await application.run_polling()

def start_bot():
    while True:
        try:
            asyncio.run(bot_main())
        except Exception as e:
            print("❌ Bot crashed, restarting in 5s:", e)
            time.sleep(5)

# -------------------- ENTRY --------------------

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    start_bot()