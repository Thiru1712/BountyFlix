import { serve } from "https://deno.land/std@0.203.0/http/server.ts";

serve(() => {
  return new Response("BountyFlix is live ✅");
});