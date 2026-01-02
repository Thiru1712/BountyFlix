export default {
  fetch(_req: Request): Response {
    return new Response("BountyFlix is live ✅", {
      headers: { "content-type": "text/plain" },
    });
  },
};