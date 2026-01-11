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
from telegram.error import BadRequest

from callbacks import (
    alphabet_menu,
    titles_menu,
    seasons_menu,
    download_menu,
)
from admin import (
    addanime_submit,
    approve_callback,
    reject_callback,
    broadcast_submit,
    approve_broadcast_callback,
    reject_broadcast_callback,
)
from database import (
    get_content_by_slug,
    inc_stat,
    get_stats,
    get_pinned_menu,
    save_pinned_menu,
)
from rate_limit import is_allowed
from config import OWNER_ID, CHANNEL_ID

# ======================================================
# HEALTH SERVER
# ======================================================

app = Flask(__name__)
START_TIME = time.time()

@app.route("/")
def home():
    return "BountyFlix alive 🟢"

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
    }), 200


def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ======================================================
# AUTO-PIN ALPHABET MENU
# ======================================================

async def pin_alphabet_menu(application):
    try:
        old = get_pinned_menu()
        if old:
            try:
                await application.bot.unpin_chat_message(
                    chat_id=CHANNEL_ID,
                    message_id=old["message_id"]
                )
                await application.bot.delete_message(
                    chat_id=CHANNEL_ID,
                    message_id=old["message_id"]
                )
            except BadRequest:
                pass

        msg = await application.bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                "🎬 <b>Welcome to AnimeExplorers</b>\n\n"
                "Browse anime & movies alphabetically 👇"
            ),
            reply_markup=alphabet_menu(),
            parse_mode="HTML"
        )

        await application.bot.pin_chat_message(
            chat_id=CHANNEL_ID,
            message_id=msg.message_id,
            disable_notification=True
        )

        save_pinned_menu(msg.message_id)
        print("📌 Alphabet menu pinned")

    except Exception as e:
        print("❌ Failed to pin alphabet menu:", e)

# ======================================================
# COMMANDS
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_allowed(uid, "command"):
        return

    await update.message.reply_text(
        "🎬 <b>Browse Anime & Movies</b>\n\nSelect a letter 👇",
        reply_markup=alphabet_menu(),
        parse_mode="HTML"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    text = (
        "🛠 <b>BountyFlix Admin Help</b>\n\n"
        "🔹 /start\nShow A–Z menu\n\n"
        "🔹 /addanime\nAdd anime/movie (approval required)\n"
        "<code>/addanime Title | S1=link , S2=link</code>\n\n"
        "🔹 /broadcast\nSend embed broadcast (approval required)\n"
        "<code>/broadcast Title | Message | Button | Link</code>\n\n"
        "🔹 /stats\nView analytics & bot health\n\n"
        "🔹 /help\nShow this help\n\n"
        "⚠️ Nothing goes live without approval."
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    stats = get_stats() or {}
    uptime = int(time.time() - START_TIME)

    text = (
        "📊 <b>BountyFlix Analytics</b>\n\n"
        f"🔤 Alphabet clicks: {stats.get('alphabet_clicks', 0)}\n"
        f"🎬 Anime clicks: {stats.get('anime_clicks', 0)}\n"
        f"📺 Season clicks: {stats.get('season_clicks', 0)}\n"
        f"⬇ Download clicks: {stats.get('download_clicks', 0)}\n\n"
        "<b>Health</b>\n"
        f"⏱ Uptime: {uptime} seconds\n"
        "🟢 Status: Running"
    )

    await update.message.reply_text(text, parse_mode="HTML")

# ======================================================
# CALLBACK HANDLER
# ======================================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data

    if not is_allowed(uid, "callback"):
        await query.answer("⏳ Slow down")
        return

    await query.answer()

    # ---------- ADMIN ----------
    if data.startswith("approve:"):
        await approve_callback(update, context)
        return

    if data.startswith("reject:"):
        await reject_callback(update, context)
        return

    if data.startswith("approve_broadcast:"):
        await approve_broadcast_callback(update, context)
        return

    if data.startswith("reject_broadcast:"):
        await reject_broadcast_callback(update, context)
        return

    # ---------- USER FLOW ----------
    if data.startswith("letter:"):
        inc_stat("alphabet_clicks")
        letter = data.split(":")[1]
        await query.edit_message_text(
            f"🔤 <b>Titles starting with {letter}</b>",
            reply_markup=titles_menu(letter),
            parse_mode="HTML"
        )

    elif data.startswith("anime:"):
        inc_stat("anime_clicks")
        slug = data.split(":")[1]
        content = get_content_by_slug(slug)

        await query.edit_message_text(
            f"🎬 <b>{content['title']}</b>\n\nSelect a season 👇",
            reply_markup=seasons_menu(slug),
            parse_mode="HTML"
        )

    elif data.startswith("season:"):
        inc_stat("season_clicks")
        _, slug, season = data.split(":")
        season = int(season)
        content = get_content_by_slug(slug)

        await query.edit_message_text(
            f"🎬 <b>{content['title']}</b>\nSeason {season}\n\n"
            "Click below to download 👇",
            reply_markup=download_menu(slug, season),
            parse_mode="HTML"
        )

    elif data.startswith("redirect:"):
        inc_stat("download_clicks")
        _, slug, season = data.split(":")
        season = int(season)
        content = get_content_by_slug(slug)

        for s in content["seasons"]:
            if s["season"] == season:
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text=s["redirect"]
                )
                return

# ======================================================
# BOT RUNNER
# ======================================================

async def bot_main():
    application = (
        ApplicationBuilder()
        .token(os.getenv("TOKEN"))
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("addanime", addanime_submit))
    application.add_handler(CommandHandler("broadcast", broadcast_submit))
    application.add_handler(CallbackQueryHandler(callback_handler))

    print("🤖 BountyFlix bot started")

    # Auto-pin alphabet menu on startup
    await pin_alphabet_menu(application)

    await application.run_polling()


def start_bot():
    while True:
        try:
            asyncio.run(bot_main())
        except Exception as e:
            print("❌ Bot crashed, restarting in 5s:", e)
            time.sleep(5)

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    start_bot()