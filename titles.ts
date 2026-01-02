  //titles.ts

import { redis } from "./redis.ts";

// Save title by letter
export async function saveTitle(letter: string, title: string) {
  await redis.sadd(`letters:${letter}`, title);
}

// Get titles by letter
export async function getTitles(letter: string): Promise<string[]> {
  return await redis.smembers(`letters:${letter}`) || [];
}

// Save season
export async function saveSeason(title: string, season: string) {
  await redis.sadd(`title:${title}`, season);
}

// Get seasons for title
export async function getSeasons(title: string): Promise<string[]> {
  return await redis.smembers(`title:${title}`) || [];
}

// Set download link for season
export async function setDownloadLink(title: string, season: string, url: string) {
  await redis.set(`season:${title}:${season}`, url);
}

// Get download link
export async function getDownloadLink(title: string, season: string): Promise<string | null> {
  return await redis.get(`season:${title}:${season}`);
}