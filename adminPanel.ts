  // adminpanel.ts

import { BOT_TOKEN } from "./config.ts";
import { sendLog } from "./logging.ts";

export async function sendAdminPanel(chatId: number) {
  const keyboard = {
    inline_keyboard: [
      [
        { text: "Manage Titles", callback_data: "admin_titles" },
        { text: "Manage Seasons", callback_data: "admin_seasons" }
      ],
      [
        { text: "Manage Users", callback_data: "admin_users" },
        { text: "Broadcast", callback_data: "admin_broadcast" }
      ]
    ]
  };

  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: "🛠️ BountyFlix Admin Panel",
      reply_markup: keyboard
    })
  });

  await sendLog(`🛠️ Admin panel sent to ${chatId}`);
}

export async function setDownloadUrlPrompt(chatId: number, title: string, season: string, url: string) {
  const inlineKeyboard = {
    inline_keyboard: [
      [
        { text: "✅ Confirm", callback_data: `confirm_download:${title}:${season}:${url}` },
        { text: "❌ Cancel", callback_data: `cancel_download` }
      ]
    ]
  };

  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id,
      text: `⚠️ Confirm download link\n\nTitle: ${title}\nSeason: ${season}\nLink: ${url}`,
      reply_markup: inlineKeyboard
    })
  });
}