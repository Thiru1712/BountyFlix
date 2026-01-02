import { BOT_TOKEN, LOG_CHANNEL_ID } from "./config.ts";

export async function sendLog(text: string) {
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: LOG_CHANNEL_ID,
      text,
      parse_mode: "Markdown"
    })
  });
}