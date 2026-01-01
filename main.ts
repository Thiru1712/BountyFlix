// main.ts
import { serve } from "https://deno.land/std@0.203.0/http/server.ts";

// -------------------------
// Environment Variables
// -------------------------
const BOT_TOKEN = Deno.env.get("BOT_TOKEN")!;
const TG_API = `https://api.telegram.org/bot${BOT_TOKEN}`;

const REDIS_URL = Deno.env.get("REDIS_URL")!;
const REDIS_TOKEN = Deno.env.get("REDIS_TOKEN")!;

const MONGO_ENDPOINT = Deno.env.get("MONGO_ENDPOINT")!;
const MONGO_API_KEY = Deno.env.get("MONGO_API_KEY")!;

const ADMIN_IDS = Deno.env.get("ADMIN_IDS")!.split(",").map(id => parseInt(id));

// -------------------------
// Redis Helpers (Upstash)
// -------------------------
async function redisGet(key: string): Promise<string | null> {
  const res = await fetch(`${REDIS_URL}/get/${key}`, {
    headers: { "Authorization": `Bearer ${REDIS_TOKEN}` }
  });
  const data = await res.json();
  return data.result || null;
}

async function redisSet(key: string, value: string, ttl = 60) {
  await fetch(`${REDIS_URL}/set/${key}`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${REDIS_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ value, ex: ttl })
  });
}

async function redisIncr(key: string) {
  await fetch(`${REDIS_URL}/incr/${key}`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${REDIS_TOKEN}` }
  });
}

// -------------------------
// MongoDB Data API Helpers
// -------------------------
async function mongoFindOne(collection: string, filter: object) {
  const res = await fetch(`${MONGO_ENDPOINT}/action/findOne`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": MONGO_API_KEY
    },
    body: JSON.stringify({
      dataSource: "Cluster0",
      database: "bot",
      collection,
      filter
    })
  });
  const data = await res.json();
  return data.document || null;
}

async function mongoUpdateOne(collection: string, filter: object, update: object) {
  await fetch(`${MONGO_ENDPOINT}/action/updateOne`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": MONGO_API_KEY
    },
    body: JSON.stringify({
      dataSource: "Cluster0",
      database: "bot",
      collection,
      filter,
      update: { "$set": update },
      upsert: true
    })
  });
}

// -------------------------
// Telegram Helpers
// -------------------------
async function sendMessage(chat_id: number, text: string) {
  await fetch(`${TG_API}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id, text })
  });
}

// -------------------------
// Admin Check
// -------------------------
async function isAdmin(user_id: number): Promise<boolean> {
  if (ADMIN_IDS.includes(user_id)) return true;
  const admin = await mongoFindOne("admins", { user_id });
  return admin !== null;
}

// -------------------------
// Add / Update User
// -------------------------
async function addUser(user_id: number, username: string) {
  await mongoUpdateOne("users", { user_id }, { username });
}

// -------------------------
// Stats
// -------------------------
const START_TIME = Date.now();

async function updateStats(user_id: number) {
  await redisIncr("total_msgs");
  await redisIncr("msgs_today");
  await redisSet(`active:${user_id}`, "1", 86400);
}

async function getStats() {
  const total = parseInt((await redisGet("total_msgs")) || "0");
  const today = parseInt((await redisGet("msgs_today")) || "0");

  // Count active users
  const r = await fetch(`${REDIS_URL}/keys/active:*`, {
    headers: { "Authorization": `Bearer ${REDIS_TOKEN}` }
  });
  const data = await r.json();
  const active_users = data.result?.length || 0;

  const uptime = Math.floor((Date.now() - START_TIME) / 1000);
  return { total, today, active_users, uptime };
}

// -------------------------
// HTTP Server (Webhook + Dashboard)
// -------------------------
serve(async (req) => {
  const url = new URL(req.url);
  const pathname = url.pathname;

  // Dashboard
  if (pathname === "/dashboard") {
    const stats = await getStats();
    return new Response(
      `<h1>Bot Dashboard</h1>
      <p>Active Users (24h): ${stats.active_users}</p>
      <p>Messages Today: ${stats.today}</p>
      <p>Total Messages: ${stats.total}</p>
      <p>Uptime (s): ${stats.uptime}</p>`,
      { headers: { "Content-Type": "text/html" } }
    );
  }

  // Webhook
  if (req.method === "POST") {
    const update = await req.json();
    if (!update.message) return new Response("ok");

    const msg = update.message;
    const chat_id = msg.chat.id;
    const user_id = msg.from.id;
    const username = msg.from.username || "";
    const text = msg.text || "";

    // Add user + update stats
    await addUser(user_id, username);
    await updateStats(user_id);

    // ---------------- Admin Commands ----------------
    if (text.startsWith("/stats") && await isAdmin(user_id)) {
      const stats = await getStats();
      await sendMessage(chat_id,
        `📊 Bot Stats\n` +
        `👥 Active (24h): ${stats.active_users}\n` +
        `💬 Messages today: ${stats.today}\n` +
        `💬 Total messages: ${stats.total}\n` +
        `⏱ Uptime: ${stats.uptime}s`
      );
      return new Response("ok");
    }

    if (text.startsWith("/addadmin") && await isAdmin(user_id)) {
      const parts = text.split(" ");
      if (parts.length === 2) {
        const new_id = parseInt(parts[1]);
        await mongoUpdateOne("admins", { user_id: new_id }, { user_id: new_id });
        await sendMessage(chat_id, `✅ Admin ${new_id} added`);
      } else {
        await sendMessage(chat_id, "❌ Usage: /addadmin <user_id>");
      }
      return new Response("ok");
    }

    // ---------------- Normal Reply ----------------
    await sendMessage(chat_id, "🚀 Bot online & fast!");
    return new Response("ok");
  }

  return new Response("Not Found", { status: 404 });
});
