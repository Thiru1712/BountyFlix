  // main.ts

import { BOT_TOKEN, ADMIN_IDS } from "./config.ts";
import { handleCallback, sendMessage } from "./callbacks.ts";
import { sendAdminPanel } from "./adminPanel.ts";
import { handleAdminMessage } from "./adminTitles.ts";
import { redis } from "./redis.ts";

type Update = {
  update_id: number;
  message?: any;
  callback_query?: any;
};

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

// ==============================
// POLLING OFFSET
// ==============================
let offset = 0;

// ==============================
// HANDLE TEXT MESSAGES
// ==============================
async function handleMessage(msg: any) {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const text: string | undefined = msg.text;

  // ---------- BASIC COMMANDS ----------
  if (text === "/start") {
    await sendMessage(chatId, "👋 Welcome to BountyFlix!");
    return;
  }

  if (text === "/health") {
    await sendMessage(chatId, "✅ Bot is running\n⚙️ Mode: Polling");
    return;
  }

  if (text === "/stats") {
    if (!ADMIN_IDS.has(userId)) return;

    const users = await redis.scard("users");

    await sendMessage(
      chatId,
      `<b>📊 Bot Stats</b>\n\n👥 Users: ${users}`,
    );
    return;
  }

  // ---------- ADMIN ONLY ----------
  if (!ADMIN_IDS.has(userId)) return;

  if (text === "/adminpanel") {
    await sendAdminPanel(chatId);
    return;
  }

  // ---------- ADMIN TITLE / SEASON FLOW ----------
  if (text) {
    const handled = await handleAdminMessage(chatId, text);
    if (handled) return;
  }
}

// ==============================
// POLLING LOOP
// ==============================
async function poll() {
  try {
    const res = await fetch(
      `${API}/getUpdates?timeout=30&offset=${offset}`,
    );
    const data = await res.json();

    if (!data.ok) return;

    for (const update of data.result as Update[]) {
      offset = update.update_id + 1;

      if (update.message) {
        await handleMessage(update.message);
      }

      if (update.callback_query) {
        await handleCallback(update.callback_query);
      }
    }
  } catch (err) {
    console.error("Polling error:", err);
  }
}

// ==============================
// START BOT
// ==============================
console.log("🤖 BountyFlix bot started (Railway / Polling)");

while (true) {
  await poll();
  await new Promise((r) => setTimeout(r, 2000));
}