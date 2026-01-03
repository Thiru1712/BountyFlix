  // redis.ts

import Redis from "npm:ioredis";

// Railway provides REDIS_URL automatically
const REDIS_URL = Deno.env.get("REDIS_URL");

if (!REDIS_URL) {
  console.error("❌ REDIS_URL is not set");
  throw new Error("REDIS_URL missing");
}

export const redis = new Redis(REDIS_URL, {
  maxRetriesPerRequest: 3,
  enableReadyCheck: true,
});

redis.on("connect", () => {
  console.log("✅ Redis connected");
});

redis.on("error", (err) => {
  console.error("❌ Redis error:", err);
});