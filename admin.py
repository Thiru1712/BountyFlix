 # admin.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from bson import ObjectId
from config import OWNER_ID
from database import (
    submit_pending_content,
    approve_content,
    submit_pending_broadcast,
    get_pending_broadcast,
    approve_broadcast,
    users_col,
)

# ---------------- ADD ANIME ----------------

async def addanime_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    raw = update.message.text.replace("/addanime", "").strip()
    if "|" not in raw:
        await update.message.reply_text("❌ Format: /addanime Title | S1=link , S2=link")
        return

    title, seasons_raw = raw.split("|", 1)
    title = title.strip()
    seasons = []

    for part in seasons_raw.split(","):
        if "=" not in part:
            continue
        key, link = part.split("=", 1)
        num = int(key.strip().replace("S", "").replace("Season", ""))
        seasons.append({
            "season": num,
            "button_text": f"Season {num}",
            "redirect": link.strip()
        })

    doc = submit_pending_content(title, "", seasons, update.effective_user.id)

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{doc['_id']}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"reject:{doc['_id']}")
        ]
    ])

    await update.message.reply_text(
        f"📝 <b>Preview</b>\n\n🎬 <b>{title}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != OWNER_ID:
        return
    approve_content(ObjectId(q.data.split(":")[1]), OWNER_ID)
    await q.edit_message_text("✅ Approved & live")

async def reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("❌ Cancelled")

# ---------------- BROADCAST ----------------

async def broadcast_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    raw = update.message.text.replace("/broadcast", "").strip()
    title, body, btn, link = [x.strip() for x in raw.split("|", 3)]

    bid = submit_pending_broadcast(title, body, btn, link, OWNER_ID)

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Send", callback_data=f"approve_broadcast:{bid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"reject_broadcast:{bid}")
        ]
    ])

    await update.message.reply_text(
        f"📢 <b>{title}</b>\n\n{body}",
        reply_markup=kb,
        parse_mode="HTML"
    )

async def approve_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    bid = ObjectId(q.data.split(":")[1])
    data = get_pending_broadcast(bid)
    approve_broadcast(bid)

    for u in users_col.find({}, {"user_id": 1}):
        try:
            await context.bot.send_message(
                u["user_id"],
                f"📢 <b>{data['title']}</b>\n\n{data['body']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(data["button_text"], url=data["redirect"])]
                ]),
                parse_mode="HTML"
            )
        except:
            pass

    await q.edit_message_text("✅ Broadcast sent")

async def reject_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("❌ Broadcast cancelled")