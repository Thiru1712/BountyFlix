// callbacks.ts

import { BOT_TOKEN, INDEX_CHANNEL_ID } from "./config.ts";
import {
  getTitles,
  getSeasons,
  getDownloadLink,
  setDownloadLink,
} from "./titles.ts";
import { sendLog } from "./logging.ts";
import { showLetterPicker, askTitleName } from "./adminTitles.ts";
import { handleAdminCallback } from "./adminPanel.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

export async function handleCallback(callback: any) {
  const data = callback.data;
  const chatId = callback.message.chat.id;
  const messageId = callback.message.message_id;

  // ===== ADMIN =====
  if (data.startsWith("admin_")) {
    await handleAdminCallback(data);
    return;
  }

  if (data === "admin_titles") {
    await showLetterPicker(chatId);
    return;
  }

  if (data.startsWith("add_title_letter:")) {
    const letter = data.split(":")[1];
    await askTitleName(chatId, letter);
    await sendLog(`🛠️ Admin adding title under ${letter}`);
    return;
  }

  // ===== INDEX FLOW =====
  if (data.startsWith("letter:")) {
    const letter = data.split(":")[1];
    const titles = await getTitles(letter);

    const buttons = titles.map((t) => [
      { text: t, callback_data: `title:${t}` },
    ]);

    buttons.push([{ text: "⬅ Back", callback_data: "main_menu" }]);

    await editMessage(
      INDEX_CHANNEL_ID,
      messageId,
      `Titles starting with <b>${letter}</b>:`,
      buttons
    );
  }

  else if (data.startsWith("title:")) {
    const title = data.split(":")[1];
    const seasons = await getSeasons(title);

    const buttons = seasons.map((s) => [
      { text: s, callback_data: `season:${title}:${s}` },
    ]);

    buttons.push([{ text: "⬅ Back", callback_data: "main_menu" }]);

    await editMessage(
      INDEX_CHANNEL_ID,
      messageId,
      `<b>${title}</b> — Select season`,
      buttons
    );
  }

  else if (data.startsWith("season:")) {
    const [, title, season] = data.split(":");
    const link = await getDownloadLink(title, season);

    await editMessage(
      INDEX_CHANNEL_ID,
      messageId,
      `<b>${title}</b>\n${season}`,
      [[{ text: "⬇ Download", url: link }]]
    );
  }
}

async function editMessage(
  chatId: number,
  messageId: number,
  text: string,
  inlineKeyboard: any[]
) {
  await fetch(`${API}/editMessageText`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: messageId,
      text,
      parse_mode: "HTML",
      reply_markup: { inline_keyboard: inlineKeyboard },
    }),
  });
}