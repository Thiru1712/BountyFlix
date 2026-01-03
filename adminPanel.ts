  // adminpanel.ts

import { BOT_TOKEN } from "./config.ts";
import { sendLog, LogType } from "./logging.ts";
import { sendOrUpdateIndex } from "./index.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

// ========================
// SEND ADMIN PANEL
// ========================
export async function sendAdminPanel(chatId: number) {
  const keyboard = {
    inline_keyboard: [
      [{ text: "📌 Send / Update Index", callback_data: "admin_send_index" }],
      [
        { text: "🎬 Manage Titles", callback_data: "admin_titles" },
        { text: "📺 Manage Seasons", callback_data: "admin_seasons" }
      ],
      [
        { text: "👥 Manage Users", callback_data: "admin_users" },
        { text: "📢 Broadcast", callback_data: "admin_broadcast" }
      ]
    ]
  };

  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: "🛠️ <b>BountyFlix Admin Panel</b>",
      parse_mode: "HTML",
      reply_markup: keyboard
    })
  });

  await sendLog(LogType.ADMIN, `Admin panel opened by ${chatId}`);
}

// ========================
// HANDLE ADMIN CALLBACKS
// ========================
export async function handleAdminCallback(data: string, chatId: number) {
  if (data === "admin_send_index") {
    await sendOrUpdateIndex();
    await sendLog(LogType.ADMIN, "📌 Index sent / updated");
    return;
  }

  if (data === "admin_broadcast") {
    await fetch(`${API}/sendMessage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text: "📢 Use:\n/broadcast Your message here"
      })
    });
    return;
  }

  if (data === "admin_users") {
    await fetch(`${API}/sendMessage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text: "👥 Users are auto-added when they interact with the bot."
      })
    });
    return;
  }

  if (data === "admin_seasons") {
    await fetch(`${API}/sendMessage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text: "📺 To add seasons:\nUse Manage Titles → select title → add season"
      })
    });
    return;
  }
}