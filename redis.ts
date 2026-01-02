import { REDIS_URL, REDIS_TOKEN } from "./config.ts";
import { connect } from "https://deno.land/x/upstash_redis@v1.35.0/mod.ts";

export const redis = await connect({
  url: REDIS_URL,
  token: REDIS_TOKEN
});

// Users
export async function addUser(userId: number) {
  await redis.sadd("users", userId.toString());
}
export async function getUsers(): Promise<string[]> {
  return await redis.smembers("users") || [];
}

// Titles
export async function saveTitle(letter: string, title: string) {
  await redis.sadd(`letters:${letter}`, title);
}
export async function getTitles(letter: string): Promise<string[]> {
  return await redis.smembers(`letters:${letter}`) || [];
}

// Seasons
export async function saveSeason(title: string, season: string) {
  await redis.sadd(`title:${title}`, season);
}
export async function getSeasons(title: string): Promise<string[]> {
  return await redis.smembers(`title:${title}`) || [];
}

// Download links
export async function setDownloadLink(title: string, season: string, url: string) {
  await redis.set(`season:${title}:${season}`, url);
}
export async function getDownloadLink(title: string, season: string): Promise<string | null> {
  return await redis.get(`season:${title}:${season}`);
}