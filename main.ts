import { BOT_TOKEN, ADMIN_IDS, INDEX_CHANNEL_ID } from "./config.ts";
import { sendAdminPanel, setDownloadUrlPrompt } from "./adminPanel.ts";
import { handleCallback } from "./callbacks.ts";
import { sendAnimeAnnouncement } from "./announcements.ts";
import { handleNewUser, broadcastMessage } from "./users.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

// Send main A–Z inline keyboard
async function sendIndexMenu() {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const rows = [];
  for (let i = 0; i < alphabet.length; i += 4) {
    rows.push(alphabet.slice(i, i + 4).map(l => ({ text: l, callback_data: `letter:${l}` })));
  }

  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: INDEX_CHANNEL_ID,
      text: "Choose a letter 👇",
      reply_markup: { inline_keyboard: rows }
    })
  });
}

sendIndexMenu();

while (true) {
  try {
    const updatesRes = await fetch(`${API}/getUpdates?timeout=30`);
    const data = await updatesRes.json();
    const updates = data.result || [];

    for (const update of updates) {
      if (update.message) {
        const chatId = update.message.chat.id;
        const userId = update.message.from.id;
        const text = update.message.text;

        if (!ADMIN_IDS.has(userId)) continue;

        if (text?.startsWith("/adminpanel")) {
          await sendAdminPanel(chatId);
        }

        if (text?.startsWith("/adduser")) {
          const newUserId = Number(text.split(" ")[1]);
          await handleNewUser(newUserId);
        }

        if (text?.startsWith("/broadcast")) {
          const message = text.replace("/broadcast", "").trim();
          await broadcastMessage(message);
        }

        if (text?.startsWith("/announceanime")) {
          const parts = text.replace("/announceanime", "").trim().split("|");
          const title = parts[0].trim();
          const season = parts[1].trim();
          const link = parts[2].trim();
          await sendAnimeAnnouncement(title, season, link);
        }

        if (text?.startsWith("/setdownload")) {
          const parts = text.replace("/setdownload", "").trim().split("|");
          const title = parts[0].trim();
          const season = parts[1].trim();
          const url = parts[2].trim();
          await setDownloadUrlPrompt(userId, title, season, url);
        }
      }

      if (update.callback_query) {
        await handleCallback(update.callback_query);
      }
    }
  } catch (err) {
    console.error(err);
    await new Promise(r => setTimeout(r, 5000));
  }
}