const BOT_TOKEN = Deno.env.get("BOT_TOKEN")!;
const API = `https://api.telegram.org/bot${BOT_TOKEN}`;

async function sendMessage(chatId: number, text: string) {
  await fetch(`${API}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text }),
  });
}

export default {
  async fetch(req: Request): Promise<Response> {
    if (req.method !== "POST") {
      return new Response("OK");
    }

    const update = await req.json();

    if (update.message?.text) {
      const chatId = update.message.chat.id;
      await sendMessage(chatId, "👋 Hello from BountyFlix Bot!");
    }

    return new Response("OK");
  },
};