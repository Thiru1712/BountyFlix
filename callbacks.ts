import { BOT_TOKEN, INDEX_CHANNEL_ID } from "./config.ts";
import { getTitles, getSeasons, getDownloadLink } from "./titles.ts";

export async function handleCallback(callback: any) {
  const data = callback.data;
  const messageId = callback.message.message_id;

  // A–Z letter selected
  if (data.startsWith("letter:")) {
    const letter = data.split(":")[1];
    const titles = await getTitles(letter);

    const buttons = titles.map(title => [{ text: title, callback_data: `title:${title}` }]);
    buttons.push([{ text: "⬅️ Back", callback_data: "main_menu" }]);

    await editMessage(INDEX_CHANNEL_ID, messageId, `Titles starting with ${letter}:`, buttons);
  }

  // Title selected → show seasons
  else if (data.startsWith("title:")) {
    const title = data.split(":")[1];
    const seasons = await getSeasons(title);

    const buttons = seasons.map(season => [{ text: season, callback_data: `season:${title}:${season}` }]);
    buttons.push([{ text: "⬅️ Back", callback_data: "letter_menu" }]);

    await editMessage(INDEX_CHANNEL_ID, messageId, `${title} - Choose Season:`, buttons);
  }

  // Season selected → show download button
  else if (data.startsWith("season:")) {
    const [_, title, season] = data.split(":");
    const link = await getDownloadLink(title, season);

    const buttons = [[{ text: "✅ Download Now", url: link }]];
    buttons.push([{ text: "⬅️ Back", callback_data: `title:${title}` }]);

    await editMessage(INDEX_CHANNEL_ID, messageId, `${title} - ${season}`, buttons);
  }

  // Back to main menu
  else if (data === "main_menu") {
    // Rebuild main A–Z menu
    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    const rows = [];
    for (let i = 0; i < alphabet.length; i += 4) {
      rows.push(alphabet.slice(i, i + 4).map(l => ({ text: l, callback_data: `letter:${l}` })));
    }
    await editMessage(INDEX_CHANNEL_ID, messageId, "Choose a letter 👇", rows);
  }
}

async function editMessage(chatId: string, messageId: number, text: string, inlineKeyboard: any) {
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/editMessageText`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: messageId,
      text,
      reply_markup: { inline_keyboard: inlineKeyboard },
      parse_mode: "HTML"
    })
  });
}