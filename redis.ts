  // redis.ts

import { Redis } from "https://deno.land/x/upstash_redis@v1.20.0/mod.ts";

/**
 * Environment variables
 * These MUST be set on Railway
 */
const url = Deno.env.get("UPSTASH_REDIS_REST_URL");
const token = Deno.env.get("UPSTASH_REDIS_REST_TOKEN");

if (!url || !token) {
  throw new Error(
    "❌ Missing UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN",
  );
}

/**
 * Hard validation to prevent crashes like:
 * TypeError: Invalid URL
 */
if (!url.startsWith("https://") || !url.includes(".upstash.io")) {
  throw new Error(
    `❌ Invalid UPSTASH_REDIS_REST_URL: ${url}
Expected format: https://xxxx.upstash.io`,
  );
}

/**
 * Single Redis instance
 * (DO NOT create Redis inside handlers)
 */
export const redis = new Redis({
  url,
  token,
});