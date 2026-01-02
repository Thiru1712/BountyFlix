  // adminTitles.ts

import { BOT_TOKEN } from "./config.ts";
import { saveTitle } from "./titles.ts";
import { sendLog } from "./logging.ts";
import { sendOrUpdateIndex } from "./index.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

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
      text: "🔤 Select starting letter",
      reply_markup: { inline_keyboard: rows },
    }),
  });
}

export async function askTitleName(chatId: number, letter: string) {
  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: `✏️ Send the title name starting with "${letter}"`,
    }),
  });
}

export async function saveAdminTitle(
  chatId: number,
  letter: string,
  title: string
) {
  await saveTitle(letter, title);
  await sendOrUpdateIndex();

  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: `✅ Saved\n<b>${title}</b> under <b>${letter}</b>`,
      parse_mode: "HTML",
    }),
  });

  await sendLog(`🎬 Title added: ${title} (${letter})`);
}