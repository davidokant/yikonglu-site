// 一孔录 内部报表导出（11-16 主人准）：每小时把计数服务的 /bot /ai /stats /hj 原样存进 KV，供盘点从 Cloudflare API 读；不对外。
export default {
  async scheduled(ev, env, ctx) { ctx.waitUntil(dump(env)); },
  async fetch(req, env) { return new Response("", { status: 404 }); }
};
async function dump(env) {
  for (const p of ["bot", "ai", "stats", "hj"]) {
    try { const r = await env.LIVE.fetch("https://live/" + p); await env.KV.put(p, await r.text()); } catch (e) { await env.KV.put(p + "_err", String(e)); }
  }
  await env.KV.put("at", new Date().toISOString());
}
