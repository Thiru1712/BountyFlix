  #admin.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest

from config import is_admin
from database import get_all_user_ids, add_title
from rate_limit import is_allowed


# ---------------- ADMIN PANEL UI ----------------
def admin_panel():
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("➕ Add Title", callback_data="admin_add_title")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------------- BROADCAST COMMAND ----------------
async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # admin check
    if not is_admin(uid):
        return

    # rate limit
    if not is_allowed(uid, "admin"):
        await update.message.reply_text("⏳ Slow down, admin.")
        return

    # message check
    if not context.args:
        await update.message.reply_text(
            "📢 Usage:\n/broadcast <message>"
        )
        return

    message = " ".join(context.args)
    sent = 0
    failed = 0

    # send to all users from shared collection
    for user_id in get_all_user_ids():
        try:
            await context.bot.send_message(user_id, message)
            sent += 1
        except (Forbidden, BadRequest):
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast finished\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )


# ---------------- ADD TITLE COMMAND ----------------
async def handle_add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # admin check
    if not is_admin(uid):
        return

    # rate limit
    if not is_allowed(uid, "admin"):
        await update.message.reply_text("⏳ Slow down.")
        return

    # args check
    if not context.args:
        await update.message.reply_text(
            "➕ Usage:\n/addtitle <movie name>"
        )
        return

    title = " ".join(context.args)

    add_title(title)

    await update.message.reply_text(
        f"🎬 Title added successfully:\n<b>{title}</b>",
        parse_mode="HTML"
    )