import { addUser, getUsers } from "./redis.ts";
import { sendLog } from "./logging.ts";

export async function handleNewUser(userId: number) {
  await addUser(userId);
  await sendLog(`👤 New user added: ${userId}`);
}

export async function broadcastMessage(message: string) {
  const users = await getUsers();
  const batchSize = 25;
  
  for (let i = 0; i < users.length; i += batchSize) {
    const batch = users.slice(i, i + batchSize);
    for (const userId of batch) {
      try {
        await fetch(`https://api.telegram.org/bot${Deno.env.get("BOT_TOKEN")}/sendMessage`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ chat_id: userId, text: message })
        });
      } catch (err) {
        console.error("Failed to send to", userId, err);
      }
    }
    await new Promise(r => setTimeout(r, 1000));
  }

  await sendLog(`📢 Broadcast sent to ${users.length} users`);
}