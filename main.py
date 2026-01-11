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

# ---------------- HEALTH SERVER ----------------

app = Flask(__name__)
START_TIME = time.time()

@app.route("/")
def home():
    return "BountyFlix alive 🟢"

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "uptime": int(time.time() - START_TIME)
    })

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# ---------------- AUTO PIN ----------------

async def pin_alphabet_menu(app_bot):
    old = get_pinned_menu()
    if old:
        try:
            await app_bot.bot.delete_message(CHANNEL_ID, old["message_id"])
        except BadRequest:
            pass

    msg = await app_bot.bot.send_message(
        CHANNEL_ID,
        "🎬 <b>Welcome to AnimeExplorers</b>\n\nBrowse A–Z 👇",
        reply_markup=alphabet_menu(),
        parse_mode="HTML"
    )

    await app_bot.bot.pin_chat_message(
        CHANNEL_ID,
        msg.message_id,
        disable_notification=True
    )

    save_pinned_menu(msg.message_id)

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id, "command"):
        return

    await update.message.reply_text(
        "🎬 <b>Browse Anime & Movies</b>",
        reply_markup=alphabet_menu(),
        parse_mode="HTML"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(
        "🛠 Admin Commands\n\n"
        "/start\n"
        "/addanime\n"
        "/broadcast\n"
        "/stats\n"
        "/help"
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    s = get_stats() or {}
    await update.message.reply_text(
        f"📊 Stats\n\n"
        f"Alphabet: {s.get('alphabet_clicks', 0)}\n"
        f"Anime: {s.get('anime_clicks', 0)}\n"
        f"Season: {s.get('season_clicks', 0)}\n"
        f"Download: {s.get('download_clicks', 0)}"
    )

# ---------------- CALLBACK HANDLER ----------------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data

    if not is_allowed(uid, "callback"):
        await q.answer("⏳ Slow down")
        return

    await q.answer()

    # ADMIN
    if data.startswith("approve:"):
        await approve_callback(update, context); return
    if data.startswith("reject:"):
        await reject_callback(update, context); return
    if data.startswith("approve_broadcast:"):
        await approve_broadcast_callback(update, context); return
    if data.startswith("reject_broadcast:"):
        await reject_broadcast_callback(update, context); return

    # BACK
    if data == "back:alphabet":
        await q.edit_message_text(
            "🎬 <b>Browse Anime & Movies</b>",
            reply_markup=alphabet_menu(),
            parse_mode="HTML"
        )
        return

    if data.startswith("back:titles:"):
        letter = data.split(":")[2]
        await q.edit_message_text(
            f"🔤 <b>{letter}</b>",
            reply_markup=titles_menu(letter),
            parse_mode="HTML"
        )
        return

    if data.startswith("back:seasons:"):
        slug = data.split(":")[2]
        content = get_content_by_slug(slug)
        await q.edit_message_text(
            f"🎬 <b>{content['title']}</b>",
            reply_markup=seasons_menu(slug),
            parse_mode="HTML"
        )
        return

    # FLOW
    if data.startswith("letter:"):
        inc_stat("alphabet_clicks")
        l = data.split(":")[1]
        await q.edit_message_text(
            f"🔤 <b>{l}</b>",
            reply_markup=titles_menu(l),
            parse_mode="HTML"
        )

    elif data.startswith("anime:"):
        inc_stat("anime_clicks")
        slug = data.split(":")[1]
        c = get_content_by_slug(slug)
        await q.edit_message_text(
            f"🎬 <b>{c['title']}</b>",
            reply_markup=seasons_menu(slug),
            parse_mode="HTML"
        )

    elif data.startswith("season:"):
        inc_stat("season_clicks")
        _, slug, s = data.split(":")
        await q.edit_message_text(
            "Select download 👇",
            reply_markup=download_menu(slug, int(s)),
            parse_mode="HTML"
        )

    elif data.startswith("redirect:"):
        inc_stat("download_clicks")
        _, slug, s = data.split(":")
        c = get_content_by_slug(slug)
        for ss in c["seasons"]:
            if ss["season"] == int(s):
                await context.bot.send_message(uid, ss["redirect"])

# ---------------- RUNNER ----------------

async def bot_main():
    app_bot = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_cmd))
    app_bot.add_handler(CommandHandler("stats", stats_cmd))
    app_bot.add_handler(CommandHandler("addanime", addanime_submit))
    app_bot.add_handler(CommandHandler("broadcast", broadcast_submit))
    app_bot.add_handler(CallbackQueryHandler(callback_handler))

    await pin_alphabet_menu(app_bot)
    await app_bot.run_polling()

def start_bot():
    while True:
        try:
            asyncio.run(bot_main())
        except Exception as e:
            print("CRASH:", e)
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    start_bot()