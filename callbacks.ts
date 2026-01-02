 // callbacks.ts

import { BOT_TOKEN } from "./config.ts";
import { getTitles, getSeasons, getDownloadLink, setDownloadLink } from "./titles.ts";
import { sendLog } from "./logging.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

export async function handleCallback(cb: any) {
  const data = cb.data;
  const chatId = cb.message.chat.id;
  const messageId = cb.message.message_id;

  // LETTER
  if (data.startsWith("letter:")) {
    const letter = data.split(":")[1];
    const titles = await getTitles(letter);

    if (!titles.length) {
      return answer(cb, "❌ No titles found");
    }

    const kb = titles.map(t => [{ text: t, callback_data: `title:${t}` }]);
    kb.push([{ text: "⬅ Back", callback_data: "main_menu" }]);

    await edit(chatId, messageId, `📂 Titles starting with ${letter}`, kb);
  }

  // TITLE → SEASONS
  else if (data.startsWith("title:")) {
    const title = data.split(":")[1];
    const seasons = await getSeasons(title);

    const kb = seasons.map(s => [{ text: s, callback_data: `season:${title}:${s}` }]);
    kb.push([{ text: "⬅ Back", callback_data: `letter:${title[0]}` }]);

    await edit(chatId, messageId, `🎬 ${title}\nChoose season:`, kb);
  }

  // SEASON → DOWNLOAD
  else if (data.startsWith("season:")) {
    const [, title, season] = data.split(":");
    const link = await getDownloadLink(title, season);

    if (!link) {
      return answer(cb, "❌ Download not set yet");
    }

    await edit(chatId, messageId, `${title} – ${season}`, [
      [{ text: "✅ Download Now", url: link }],
      [{ text: "⬅ Back", callback_data: `title:${title}` }],
    ]);
  }

  await answer(cb);
}

async function edit(chatId: number, msgId: number, text: string, kb: any[]) {
  await fetch(`${API}/editMessageText`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: msgId,
      text,
      reply_markup: { inline_keyboard: kb },
    }),
  });
}

async function answer(cb: any, text = "") {
  await fetch(`${API}/answerCallbackQuery`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      callback_query_id: cb.id,
      text,
      show_alert: false,
    }),
  });
}