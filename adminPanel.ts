  //adminpanel.ts

import { BOT_TOKEN } from "./config.ts";
import { sendLog } from "./logging.ts";
import { sendOrUpdateIndex } from "./index.ts";

export async function sendAdminPanel(chatId: number) {
  const keyboard = {
    inline_keyboard: [
      [{ text: "📌 Send / Update Index", callback_data: "admin_send_index" }],
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
      text: "🛠️ <b>BountyFlix Admin Panel</b>",
      parse_mode: "HTML",
      reply_markup: keyboard
    })
  });

  await sendLog(`🛠️ Admin panel opened by ${chatId}`);
}

export async function handleAdminCallback(data: string) {
  if (data === "admin_send_index") {
    await sendOrUpdateIndex();
    await sendLog("📌 Index message sent/updated");
  }
}