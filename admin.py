  #admin.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, BadRequest
from config import is_admin
from database import get_all_user_ids, add_title
from rate_limit import is_allowed

def admin_panel():
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("➕ Add Title", callback_data="admin_add_title")],
    ]
    return InlineKeyboardMarkup(keyboard)

def handle_broadcast(update, context):
    uid = update.effective_user.id

    if not is_admin(uid):
        return

    if not is_allowed(uid, "admin"):
        update.message.reply_text("⏳ Slow down")
        return

    if not context.args:
        update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    sent = 0

    for user_id in get_all_user_ids():
        try:
            context.bot.send_message(user_id, message)
            sent += 1
        except (Forbidden, BadRequest):
            pass

    update.message.reply_text(f"✅ Broadcast sent to {sent} users")

def handle_add_title(update, context):
    uid = update.effective_user.id

    if not is_admin(uid):
        return

    if not context.args:
        update.message.reply_text("Usage: /addtitle <name>")
        return

    title = " ".join(context.args)
    add_title(title)
    update.message.reply_text(f"🎬 Added: {title}")