   // main.ts


// main.ts
import { BOT_TOKEN, ADMIN_IDS, INDEX_CHANNEL_ID } from "./config.ts";
import { handleCallback } from "./callbacks.ts";
import { sendAdminPanel, setDownloadUrlPrompt } from "./adminPanel.ts";
import { sendAnimeAnnouncement } from "./announcements.ts";
import { handleNewUser, broadcastMessage } from "./users.ts";
import { addSeason as saveSeason } from "./titles.ts";
import { sendOrUpdateIndex, pinMessage } from "./indexMessage.ts";
import { sendLog, LogType } from "./logging.ts";
import { redis, getIndexMessageId } from "./redis.ts";

const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

// ========================
// TEMP STATES
// ========================

// Admin pending season input: adminId -> title
const pendingSeasonTitle: Record<number, string> = {};

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("OK");

  const update = await req.json();

  // ----------------------
  // Handle messages
  // ----------------------
  if (update.message) {
    const chatId = update.message.chat.id;
    const userId = update.message.from.id;
    const text = update.message.text;

    // Only admins allowed
    if (!ADMIN_IDS.has(userId)) return new Response("OK");

    // ===== STEP 4: Save season for title =====
    if (text && pendingSeasonTitle[userId]) {
      const title = pendingSeasonTitle[userId];
      delete pendingSeasonTitle[userId];

      await saveSeason(title, text);

      await fetch(`${API}/sendMessage`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text: `✅ Season saved\n\n<b>${text}</b>\nfor <b>${title}</b>`,
          parse_mode: "HTML",
        }),
      });

      await sendLog(LogType.ADMIN, `🎞️ Season added: ${title} → ${text}`);
      return new Response("OK");
    }

    // ===== Admin Commands =====
    if (text?.startsWith("/adminpanel")) {
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
        .map((s: string) => s.trim());

      await sendAnimeAnnouncement(title, season, link);
    }

    if (text?.startsWith("/setdownload")) {
      const [title, season, link] = text
        .replace("/setdownload", "")
        .split("|")
        .map((s: string) => s.trim());

      await setDownloadUrlPrompt(chatId, title, season, link);
    }

    // ======================
    // STEP 7: Refresh / Auto-Pin Index
    // ======================
    if (text?.startsWith("/refreshindex")) {
      const msgId = await sendOrUpdateIndex();
      await pinMessage(msgId);
      await sendLog(LogType.ADMIN, "📌 Index refreshed");
    }

    // ======================
    // /stats command
    // ======================
    if (text?.startsWith("/stats")) {
      const usersCount = (await redis.scard("users")) || 0;

      // Count titles and seasons
      let totalTitles = 0;
      let totalSeasons = 0;
      const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
      for (const letter of letters) {
        const titles = await redis.smembers(`letters:${letter}`) || [];
        totalTitles += titles.length;
        for (const title of titles) {
          const seasons = await redis.smembers(`title:${title}`) || [];
          totalSeasons += seasons.length;
        }
      }

      const statsMessage = `
📊 <b>BountyFlixBot Stats</b>
━━━━━━━━━━━━━━━
👤 Users: ${usersCount}
🎬 Titles: ${totalTitles}
📂 Seasons: ${totalSeasons}
🔤 Letters with titles: ${letters.filter(l => (redis.scard(`letters:${l}`) > 0)).length}
`;

      await fetch(`${API}/sendMessage`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          chat_id,
          text: statsMessage,
          parse_mode: "HTML"
        }),
      });

      await sendLog(LogType.ADMIN, `📊 Stats requested by admin ${userId}`);
    }

    // ======================
    // /health command
    // ======================
    if (text?.startsWith("/health")) {
      let redisStatus = "❌ Redis not connected";
      try {
        await redis.ping();
        redisStatus = "✅ Redis OK";
      } catch {}

      const lastIndexId = await getIndexMessageId();

      const healthMessage = `
💻 <b>BountyFlixBot Health</b>
━━━━━━━━━━━━━━━
🤖 Bot: Running
${redisStatus}
📌 Last Index Message ID: ${lastIndexId ?? "N/A"}
`;

      await fetch(`${API}/sendMessage`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          chat_id,
          text: healthMessage,
          parse_mode: "HTML"
        }),
      });

      await sendLog(LogType.ADMIN, `💻 Health check requested by admin ${userId}`);
    }
  }

  // ----------------------
  // Handle inline buttons
  // ----------------------
  if (update.callback_query) {
    const callback = update.callback_query;

    const adminId = callback.from.id;
    const chatId = callback.message.chat.id;

    // STEP 4: Admin clicked a title to add season
    if (callback.data.startsWith("add_season:")) {
      const title = callback.data.split(":")[1];
      pendingSeasonTitle[adminId] = title;

      await fetch(`${API}/sendMessage`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          chat_id,
          text: `✏️ Send season / arc name for\n<b>${title}</b>`,
          parse_mode: "HTML",
        }),
      });

      return new Response("OK");
    }

    // Pass everything else to callback handler
    await handleCallback(callback);
  }

  return new Response("OK");
});