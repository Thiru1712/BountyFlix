 # admin.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database import submit_pending_content, approve_content, normalize_slug
from config import OWNER_ID

# ---------------- ADD ANIME ----------------

async def addanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(
        "🎬 <b>Add Anime</b>\n\n"
        "Usage:\n"
        "<code>/addanime Title | Season1=link1 , Season2=link2</code>\n\n"
        "Example:\n"
        "<code>/addanime Attack on Titan | S1=https://t.me/filebot/1 , S2=https://t.me/filebot/2</code>",
        parse_mode="HTML"
    )


async def addanime_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    text = update.message.text.replace("/addanime", "").strip()
    if "|" not in text:
        await update.message.reply_text("❌ Invalid format")
        return

    title_part, seasons_part = text.split("|", 1)
    title = title_part.strip()

    seasons = []
    for s in seasons_part.split(","):
        if "=" not in s:
            continue
        name, link = s.split("=", 1)
        season_num = int(name.strip().replace("S", "").replace("Season", ""))
        seasons.append({
            "season": season_num,
            "button_text": f"Season {season_num}",
            "redirect": link.strip()
        })

    doc = submit_pending_content(
        title=title,
        description="",
        seasons=seasons,
        submitted_by=update.effective_user.id
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{doc['_id']}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"reject:{doc['_id']}")
        ]
    ])

    await update.message.reply_text(
        f"📝 <b>Preview</b>\n\n"
        f"🎬 <b>{title}</b>\n"
        f"Available seasons: {', '.join([str(s['season']) for s in seasons])}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ---------------- APPROVAL ----------------

async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        return

    pending_id = query.data.split(":")[1]
    approve_content(pending_id, query.from_user.id)

    await query.edit_message_text("✅ Approved & now live 🎉")


async def reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        return

    await query.edit_message_text("❌ Submission cancelled")