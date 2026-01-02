import { serve } from "https://deno.land/std@0.203.0/http/server.ts";

const PORT = Number(Deno.env.get("PORT") || 8000);

console.log(`Listening on http://localhost:${PORT}`);

serve(
  () => new Response("BountyFlix is live ✅"),
  { port: PORT }
);