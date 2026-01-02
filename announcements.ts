  // announcements.ts

import { BOT_TOKEN, ANNOUNCE_CHANNEL_ID } from "./config.ts";
import { sendLog } from "./logging.ts";

export async function sendAnimeAnnouncement(title: string, season: string, downloadUrl: string) {
  const text = `🎬 <b>New Anime Added!</b>\n\nTitle: ${title}\nSeason: ${season}`;
  
  const inlineKeyboard = {
    inline_keyboard: [[
      { text: "✅ Download Now", url: downloadUrl },
      { text: "📂 Open Index", callback_data: "open_index" }
    ]]
  };
  
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: ANNOUNCE_CHANNEL_ID,
      text,
      parse_mode: "HTML",
      reply_markup: inlineKeyboard
    })
  });

  await sendLog(`📝 Admin announced: ${title} Season ${season}`);
}