 # callbacks.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import (
    get_letters_available,
    get_titles_by_letter,
    get_content_by_slug,
)

# ------------------ ALPHABET MENU ------------------

def alphabet_menu():
    letters = get_letters_available()
    keyboard = []

    row = []
    for letter in letters:
        row.append(
            InlineKeyboardButton(letter, callback_data=f"letter:{letter}")
        )
        if len(row) == 5:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


# ------------------ TITLES BY LETTER ------------------

def titles_menu(letter: str):
    titles = get_titles_by_letter(letter)
    keyboard = []

    for t in titles:
        keyboard.append([
            InlineKeyboardButton(
                t["title"],
                callback_data=f"anime:{t['slug']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="back:alphabet")
    ])

    return InlineKeyboardMarkup(keyboard)


# ------------------ SEASONS MENU ------------------

def seasons_menu(slug: str):
    content = get_content_by_slug(slug)
    keyboard = []

    if not content:
        return InlineKeyboardMarkup([])

    seasons = content.get("seasons", [])

    row = []
    for s in seasons:
        row.append(
            InlineKeyboardButton(
                s.get("button_text", f"Season {s['season']}"),
                callback_data=f"season:{slug}:{s['season']}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data=f"back:titles:{content['letter']}")
    ])

    return InlineKeyboardMarkup(keyboard)


# ------------------ DOWNLOAD BUTTON ------------------

def download_menu(slug: str, season: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬇ Download Now",
                callback_data=f"redirect:{slug}:{season}"
            )
        ],
        [
            InlineKeyboardButton("⬅ Back", callback_data=f"back:seasons:{slug}")
        ]
    ])

# ---------------- ADMIN APPROVAL CALLBACKS ----------------

def admin_approval_handler(data: str):
    if data.startswith("approve:"):
        return "approve"
    if data.startswith("reject:"):
        return "reject"
    return None