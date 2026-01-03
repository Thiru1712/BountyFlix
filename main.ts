  // main.ts

import { BOT_TOKEN, ADMIN_IDS } from "./config.ts";
import { handleCallback } from "./callbacks.ts";
import { sendAdminPanel } from "./adminPanel.ts";
import { sendAnimeAnnouncement } from "./announcements.ts";
import { handleNewUser, broadcastMessage } from "./users.ts";
import { addTitle, addSeason } from "./titles.ts";
import { sendOrUpdateIndex } from "./index.ts";
import { sendLog, LogType } from "./logging.ts";
import { getUsers } from "./redis.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

// ==============================
// TEMP ADMIN STATES
// ==============================
const pendingTitle: Record<number, string> = {};
const pendingSeason: Record<number, string> = {};
const pendingLetter: Record<number, string> = {};

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("OK");

  const update = await req.json();

  // ==============================
  // MESSAGE HANDLER
  // ==============================
  if (update.message) {
    const chatId = update.message.chat.id;
    const userId = update.message.from.id;
    const text: string | undefined = update.message.text;

    // ---------- HEALTH ----------
    if (text === "/health") {
      await sendMessage(chatId, "✅ Bot is healthy");
      return new Response("OK");
    }

    // ---------- STATS ----------
    if (text === "/stats") {
      if (!ADMIN_IDS.has(userId)) return new Response("OK");

      const users = await getUsers();
      await sendMessage(
        chatId,
        `📊 <b>Bot Stats</b>\n\n👥 Users: ${users.length}`,
        true
      );
      return new Response("OK");
    }

    // ---------- ADMIN ONLY ----------
    if (!ADMIN_IDS.has(userId)) return new Response("OK");

    // SAVE TITLE NAME
    if (pendingLetter[userId] && text) {
      const letter = pendingLetter[userId];
      delete pendingLetter[userId];

      await addTitle(letter, text);
      await sendOrUpdateIndex();

      await sendMessage(
        chatId,
        `✅ Title saved\n<b>${text}</b> under <b>${letter}</b>`,
        true
      );

      await sendLog(LogType.ADMIN, `🎬 Title added: ${text}`);
      return new Response("OK");
    }

    // SAVE SEASON NAME
    if (pendingSeason[userId] && text) {
      const title = pendingSeason[userId];
      delete pendingSeason[userId];

      await addSeason(title, text);

      await sendMessage(
        chatId,
        `✅ Season saved\n<b>${text}</b> for <b>${title}</b>`,
        true
      );

      await sendLog(LogType.ADMIN, `🎞️ Season added: ${title} → ${text}`);
      return new Response("OK");
    }

    // ---------- COMMANDS ----------
    if (text === "/adminpanel") {
      await sendAdminPanel(chatId);
    }

    if (text?.startsWith("/adduser")) {
      const id = Number(text.split(" ")[1]);
      await handleNewUser(id);
    }

    if (text?.startsWith("/broadcast")) {
      const msg = text.replace("/broadcast", "").trim();
      await broadcastMessage(msg);
    }

    if (text?.startsWith("/announceanime")) {
      const [title, season, link] = text
        .replace("/announceanime", "")
        .split("|")
        .map((s) => s.trim());

      await sendAnimeAnnouncement(title, season, link);
    }

    if (text === "/refreshindex") {
      await sendOrUpdateIndex();
      await sendLog(LogType.ADMIN, "📌 Index refreshed");
    }
  }

  // ==============================
  // CALLBACK HANDLER
  // ==============================
  if (update.callback_query) {
    const cb = update.callback_query;
    const data = cb.data;
    const userId = cb.from.id;
    const chatId = cb.message.chat.id;

    // Admin wants to add title
    if (data.startsWith("add_title_letter:")) {
      const letter = data.split(":")[1];
      pendingLetter[userId] = letter;

      await sendMessage(
        chatId,
        `✏️ Send title name starting with <b>${letter}</b>`,
        true
      );
      return new Response("OK");
    }

    // Admin wants to add season
    if (data.startsWith("add_season:")) {
      const title = data.split(":")[1];
      pendingSeason[userId] = title;

      await sendMessage(
        chatId,
        `✏️ Send season name for <b>${title}</b>`,
        true
      );
      return new Response("OK");
    }

    await handleCallback(cb);
  }

  return new Response("OK");
});

// ==============================
// SEND MESSAGE HELPER
// ==============================
async function sendMessage(
  chatId: number,
  text: string,
  html = false
) {
  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: html ? "HTML" : undefined,
    }),
  });
}