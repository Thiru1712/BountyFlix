import { BOT_TOKEN, INDEX_CHANNEL_ID } from "./config.ts";
import { saveIndexMessageId, getIndexMessageId } from "./redis.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

function azKeyboard() {
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
  return { inline_keyboard: rows };
}

export async function sendOrUpdateIndex() {
  const text = `🎬 <b>BountyFlix Index</b>\n\nBrowse anime & movies by letter.\n━━━━━━━━━━━━━━━`;
  const existingId = await getIndexMessageId();

  if (existingId) {
    try {
      await fetch(`${API}/editMessageText`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          chat_id: INDEX_CHANNEL_ID,
          message_id: existingId,
          text,
          parse_mode: "HTML",
          reply_markup: azKeyboard(),
        }),
      });
      return existingId;
    } catch {}
  }

  // Send new message
  const res = await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: INDEX_CHANNEL_ID,
      text,
      parse_mode: "HTML",
      reply_markup: azKeyboard(),
    }),
  });

  const data = await res.json();
  const messageId = data.result.message_id;
  await saveIndexMessageId(messageId);

  return messageId;
}

export async function pinMessage(messageId: number) {
  await fetch(`${API}/pinChatMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: INDEX_CHANNEL_ID,
      message_id: messageId,
      disable_notification: true,
    }),
  });
}