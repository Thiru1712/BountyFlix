 #admin.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
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

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    if not is_allowed(uid, "admin"):
        await update.message.reply_text("⏳ Slow down")
        return
    if not context.args:
        await update.message.reply_text("/broadcast <message>")
        return

    message = " ".join(context.args)
    sent = 0

    for user_id in get_all_user_ids():
        try:
            await context.bot.send_message(user_id, message)
            sent += 1
        except (Forbidden, BadRequest):
            pass

    await update.message.reply_text(f"✅ Sent to {sent} users")

async def handle_add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    if not is_allowed(uid, "admin"):
        return
    if not context.args:
        await update.message.reply_text("/addtitle <name>")
        return

    title = " ".join(context.args)
    add_title(title)
    await update.message.reply_text(f"🎬 Added: {title}")