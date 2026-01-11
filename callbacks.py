 # callbacks.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_letters_available, get_titles_by_letter, get_content_by_slug

def alphabet_menu():
    letters = get_letters_available()

    if not letters:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("No content yet", callback_data="noop")]
        ])

    keyboard, row = [], []
    for l in letters:
        row.append(InlineKeyboardButton(l, callback_data=f"letter:{l}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

def titles_menu(letter):
    titles = get_titles_by_letter(letter)
    keyboard = []

    for t in titles:
        keyboard.append(
            [InlineKeyboardButton(t["title"], callback_data=f"anime:{t['slug']}")]
        )

    keyboard.append(
        [InlineKeyboardButton("⬅ Back", callback_data="back:alphabet")]
    )
    return InlineKeyboardMarkup(keyboard)

def seasons_menu(slug):
    content = get_content_by_slug(slug)

    if not content:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅ Back", callback_data="back:alphabet")]
        ])

    keyboard, row = [], []
    for s in content.get("seasons", []):
        row.append(
            InlineKeyboardButton(
                s["button_text"],
                callback_data=f"season:{slug}:{s['season']}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(
        [InlineKeyboardButton("⬅ Back", callback_data=f"back:titles:{content['letter']}")]
    )
    return InlineKeyboardMarkup(keyboard)

def download_menu(slug, season):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇ Download Now", callback_data=f"redirect:{slug}:{season}")],
        [InlineKeyboardButton("⬅ Back", callback_data=f"back:seasons:{slug}")]
    ])