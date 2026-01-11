 # admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bson import ObjectId

from config import is_admin
from database import (
    submit_pending_content,
    get_all_movies,
    delete_movie,
)

# ---------- /admin ----------

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admins only")
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Movie", callback_data="admin:add")],
        [InlineKeyboardButton("🗑 Delete Movie", callback_data="admin:delete")]
    ])

    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ---------- ADD MOVIE ----------

async def addanime_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admins only")
        return

    raw = update.message.text.replace("/addanime", "").strip()
    if "|" not in raw:
        await update.message.reply_text(
            "❌ Format:\n/addanime Title | S1=link , S2=link"
        )
        return

    title, seasons_raw = raw.split("|", 1)
    seasons = []

    for part in seasons_raw.split(","):
        if "=" not in part:
            continue
        key, link = part.split("=", 1)
        num = int(key.strip().replace("S", ""))
        seasons.append({
            "season": num,
            "button_text": f"Season {num}",
            "redirect": link.strip()
        })

    doc = submit_pending_content(title.strip(), seasons, update.effective_user.id)
    if not doc:
        await update.message.reply_text("❌ Movie already exists")
        return

    await update.message.reply_text("✅ Movie added successfully")

# ---------- DELETE FLOW ----------

async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    if not is_admin(q.from_user.id):
        await q.answer("Admins only")
        return

    if data == "admin:delete":
        movies = get_all_movies()
        if not movies:
            await q.edit_message_text("No movies available")
            return

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(m["title"], callback_data=f"delete:{m['_id']}")]
            for m in movies
        ])

        await q.edit_message_text(
            "🗑 Select movie to delete:",
            reply_markup=kb
        )

    elif data.startswith("delete:"):
        movie_id = data.split(":")[1]
        delete_movie(movie_id)
        await q.edit_message_text("✅ Movie deleted")