// supabase/functions/submit-price/index.ts
// Edge Function : récupère l'IP réelle du client (non falsifiable),
// la hash, puis appelle la RPC submit_price côté Postgres.
//
// Déploiement :
//   supabase functions deploy submit-price --no-verify-jwt
//
// Le client appelle CETTE fonction, jamais submit_price directement.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY  = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const IP_SALT      = Deno.env.get("IP_SALT") ?? "retro-toolbox-salt";

async function hashIp(ip: string): Promise<string> {
  const data = new TextEncoder().encode(IP_SALT + "|" + ip);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  // IP réelle, injectée par l'infra Supabase — le client ne peut pas la falsifier
  const ip =
    req.headers.get("x-forwarded-for")?.split(",")[0].trim() ??
    req.headers.get("x-real-ip") ??
    "0.0.0.0";
  const ipHash = await hashIp(ip);

  let body: { uuid?: string; server?: string; item_id?: number; price?: number };
  try {
    body = await req.json();
  } catch {
    return Response.json({ ok: false, error: "bad_json" }, { status: 400 });
  }

  const { uuid, server, item_id, price } = body;
  if (!uuid || !server || !item_id || !price) {
    return Response.json({ ok: false, error: "missing_fields" }, { status: 400 });
  }

  const supabase = createClient(SUPABASE_URL, SERVICE_KEY);
  const { data, error } = await supabase.rpc("submit_price", {
    p_uuid: uuid,
    p_ip_hash: ipHash,
    p_server: server,
    p_item_id: item_id,
    p_price: price,
  });

  if (error) {
    return Response.json({ ok: false, error: error.message }, { status: 500 });
  }
  return Response.json(data);
});
