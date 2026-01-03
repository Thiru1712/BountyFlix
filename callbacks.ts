  // callbacks.ts

import { BOT_TOKEN, INDEX_CHANNEL_ID } from "./config.ts";
import {
  getTitles,
  getSeasons,
  getDownloadLink,
} from "./titles.ts";
import { sendLog } from "./logging.ts";
import { showLetterPicker } from "./adminTitles.ts";
import { handleAdminCallback } from "./adminPanel.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

export async function handleCallback(callback: any) {
  const data: string = callback.data;
  const chatId = callback.message.chat.id;
  const messageId = callback.message.message_id;

  // ========================
  // ADMIN CALLBACKS
  // ========================
  if (data.startsWith("admin_")) {
    await handleAdminCallback(data, chatId);
    return;
  }

  if (data === "admin_titles") {
    await showLetterPicker(chatId);
    return;
  }

  // ========================
  // INDEX NAVIGATION
  // ========================
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
      `📂 <b>Titles starting with ${letter}</b>`,
      buttons
    );
    return;
  }

  if (data.startsWith("title:")) {
    const title = data.split(":")[1];
    const seasons = await getSeasons(title);

    const buttons = seasons.map((s) => [
      { text: s, callback_data: `season:${title}:${s}` },
    ]);

    buttons.push([{ text: "⬅ Back", callback_data: "main_menu" }]);

    await editMessage(
      INDEX_CHANNEL_ID,
      messageId,
      `🎬 <b>${title}</b>\nSelect season`,
      buttons
    );
    return;
  }

  if (data.startsWith("season:")) {
    const [, title, season] = data.split(":");
    const link = await getDownloadLink(title, season);

    if (!link) {
      await editMessage(
        INDEX_CHANNEL_ID,
        messageId,
        "❌ Download link not available",
        [[{ text: "⬅ Back", callback_data: "main_menu" }]]
      );
      return;
    }

    await editMessage(
      INDEX_CHANNEL_ID,
      messageId,
      `<b>${title}</b>\n${season}`,
      [[{ text: "⬇ Download", url: link }]]
    );

    await sendLog(`📂 Download clicked: ${title} → ${season}`);
    return;
  }

  if (data === "main_menu") {
    await editMessage(
      INDEX_CHANNEL_ID,
      messageId,
      "🎬 <b>BountyFlix Index</b>\n\nChoose a letter:",
      buildAZKeyboard()
    );
    return;
  }
}

// ========================
// HELPERS
// ========================
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

function buildAZKeyboard() {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const rows = [];

  for (let i = 0; i < letters.length; i += 6) {
    rows.push(
      letters.slice(i, i + 6).map((l) => ({
        text: l,
        callback_data: `letter:${l}`,
      }))
    );
  }

  return rows;
}