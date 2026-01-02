   // adminTitles.ts

import { BOT_TOKEN } from "./config.ts";
import { addTitle as saveTitle } from "./titles.ts";
import { sendLog, LogType } from "./logging.ts";
import { sendOrUpdateIndex } from "./indexMessage.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

// Step 3: Show A–Z letter picker for adding titles
export async function showLetterPicker(chatId: number) {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const rows = [];

  for (let i = 0; i < letters.length; i += 6) {
    rows.push(
      letters.slice(i, i + 6).map((l) => ({
        text: l,
        callback_data: `add_title_letter:${l}`,
      }))
    );
  }

  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: "🔤 Select the starting letter for the new title",
      reply_markup: { inline_keyboard: rows },
    }),
  });
}

// Prompt admin to send title name
export async function askTitleName(chatId: number, letter: string) {
  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id,
      text: `✏️ Send the title name starting with "${letter}"`,
    }),
  });
}

// Save title and refresh index
export async function saveAdminTitle(chatId: number, letter: string, title: string) {
  await saveTitle(letter, title);
  await sendOrUpdateIndex();

  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id,
      text: `✅ Saved\n<b>${title}</b> under <b>${letter}</b>`,
      parse_mode: "HTML",
    }),
  });

  await sendLog(LogType.ADMIN, `🎬 Title added: ${title} (${letter})`);
}