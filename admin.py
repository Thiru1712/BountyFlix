 # admin.py

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import ContextTypes
from bson import ObjectId
from datetime import datetime

from config import OWNER_ID
from database import (
    submit_pending_content,
    approve_content,
    submit_pending_broadcast,
    get_pending_broadcast,
    approve_broadcast,
    users_col,
)

# ======================================================
# ADD ANIME / MOVIE (SUBMIT → PREVIEW → APPROVE)
# ======================================================

async def addanime_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage:
    /addanime Title | S1=link1 , S2=link2
    """
    if update.effective_user.id != OWNER_ID:
        return

    raw = update.message.text.replace("/addanime", "").strip()
    if "|" not in raw:
        await update.message.reply_text(
            "❌ Invalid format\n\n"
            "Use:\n"
            "/addanime Title | S1=link1 , S2=link2"
        )
        return

    try:
        title_part, seasons_part = raw.split("|", 1)
        title = title_part.strip()

        seasons = []
        for s in seasons_part.split(","):
            if "=" not in s:
                continue
            key, link = s.split("=", 1)
            season_num = int(
                key.strip()
                .replace("S", "")
                .replace("Season", "")
            )
            seasons.append({
                "season": season_num,
                "button_text": f"Season {season_num}",
                "redirect": link.strip()
            })

        if not seasons:
            raise ValueError

    except Exception:
        await update.message.reply_text("❌ Failed to parse seasons")
        return

    doc = submit_pending_content(
        title=title,
        description="",
        seasons=seasons,
        submitted_by=update.effective_user.id
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve:{doc['_id']}"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"reject:{doc['_id']}"
            )
        ]
    ])

    preview = (
        f"📝 <b>ANIME PREVIEW</b>\n\n"
        f"🎬 <b>{title}</b>\n"
        f"Available Seasons: "
        f"{', '.join([str(s['season']) for s in seasons])}"
    )

    await update.message.reply_text(
        preview,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ======================================================
# APPROVE / REJECT ANIME
# ======================================================

async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != OWNER_ID:
        return

    try:
        pending_id = ObjectId(query.data.split(":")[1])
    except Exception:
        await query.answer("Invalid ID")
        return

    ok = approve_content(pending_id, query.from_user.id)

    if ok:
        await query.edit_message_text("✅ Approved & now live 🎉")
    else:
        await query.edit_message_text("❌ Approval failed")


async def reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != OWNER_ID:
        return

    await query.edit_message_text("❌ Submission cancelled")

# ======================================================
# BROADCAST (SUBMIT → PREVIEW → APPROVE)
# ======================================================

async def broadcast_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage:
    /broadcast Title | Body | Button Text | Link
    """
    if update.effective_user.id != OWNER_ID:
        return

    raw = update.message.text.replace("/broadcast", "").strip()
    if "|" not in raw:
        await update.message.reply_text(
            "❌ Invalid format\n\n"
            "Use:\n"
            "/broadcast Title | Body | Button Text | Link"
        )
        return

    try:
        title, body, button_text, link = [x.strip() for x in raw.split("|", 3)]
    except ValueError:
        await update.message.reply_text("❌ Invalid broadcast format")
        return

    bid = submit_pending_broadcast(
        title=title,
        body=body,
        button_text=button_text,
        redirect=link,
        submitted_by=update.effective_user.id
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Send Broadcast",
                callback_data=f"approve_broadcast:{bid}"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"reject_broadcast:{bid}"
            )
        ]
    ])

    preview = (
        f"📢 <b>{title}</b>\n\n"
        f"{body}\n\n"
        "👇 Action below"
    )

    await update.message.reply_text(
        preview,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ======================================================
# APPROVE / REJECT BROADCAST
# ======================================================

async def approve_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != OWNER_ID:
        return

    try:
        bid = ObjectId(query.data.split(":")[1])
    except Exception:
        await query.answer("Invalid ID")
        return

    data = get_pending_broadcast(bid)
    if not data:
        await query.edit_message_text("❌ Broadcast not found")
        return

    approve_broadcast(bid)

    sent = 0
    for u in users_col.find({}, {"user_id": 1}):
        try:
            await context.bot.send_message(
                chat_id=u["user_id"],
                text=f"📢 <b>{data['title']}</b>\n\n{data['body']}",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            data["button_text"],
                            url=data["redirect"]
                        )
                    ]
                ]),
                parse_mode="HTML"
            )
            sent += 1
        except Exception:
            pass

    await query.edit_message_text(f"✅ Broadcast sent to {sent} users")


async def reject_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != OWNER_ID:
        return

    await query.edit_message_text("❌ Broadcast cancelled")