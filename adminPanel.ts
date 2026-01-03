  // adminpanel.ts

import { BOT_TOKEN } from "./config.ts";
import { sendMessage } from "./callbacks.ts";
import { sendOrUpdateIndex } from "./index.ts";

/**
 * Send the admin panel menu to a chat
 */
export async function sendAdminPanel(chatId: number) {
  const keyboard = {
    inline_keyboard: [
      [{ text: "📌 Send / Update Index", callback_data: "admin_send_index" }],
      [
        { text: "Manage Titles", callback_data: "admin_titles" },
        { text: "Manage Seasons", callback_data: "admin_seasons" },
      ],
      [
        { text: "Manage Users", callback_data: "admin_users" },
        { text: "Broadcast", callback_data: "admin_broadcast" },
      ],
    ],
  };

  await sendMessage(chatId, "🛠️ <b>BountyFlix Admin Panel</b>", keyboard);
}

/**
 * Handle admin callback from inline keyboard
 */
export async function handleAdminCallback(data: string, chatId?: number) {
  if (data === "admin_send_index") {
    await sendOrUpdateIndex();
    if (chatId) {
      await sendMessage(chatId, "📌 Index message sent/updated");
    }
  }

  // Additional admin callbacks can be handled here
}

/**
 * Placeholder for future download URL prompt
 * Currently safe to import
 */
export async function setDownloadUrlPrompt(
  chatId: number,
  title: string,
  season: string,
  url: string,
) {
  await sendMessage(
    chatId,
    `✅ Download URL saved\n<b>${title}</b> — ${season}\n${url}`,
  );
}