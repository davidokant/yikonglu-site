// 一孔录网站在线人数与累计读者数（Cloudflare Worker + 一个 Durable Object）
// POST /hit  {id, first}  页面每 60 秒发一次心跳；first=true 表示这台设备第一次来，累计数加一
// GET  /stats            返回 {online, total}
const ORIGINS = ["https://yikonglu.com", "https://www.yikonglu.com", "http://localhost:8767"];
const WINDOW = 90 * 1000; // 90 秒内有心跳算在线

function cors(req) {
  const o = req.headers.get("Origin") || "";
  return { "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0], "Access-Control-Allow-Methods": "GET,POST,OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" };
}

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(req) });
    const stub = env.LIVE.get(env.LIVE.idFromName("site"));
    const r = await stub.fetch(req);
    const h = new Headers(r.headers); for (const [k, v] of Object.entries(cors(req))) h.set(k, v);
    h.set("Cache-Control", "no-store");
    return new Response(r.body, { status: r.status, headers: h });
  },
};

export class Live {
  constructor(state) { this.state = state; this.seen = new Map(); this.total = null; }
  async getTotal() { if (this.total === null) this.total = (await this.state.storage.get("total")) || 0; return this.total; }
  online() { const n = Date.now(); for (const [k, t] of this.seen) if (n - t > WINDOW) this.seen.delete(k); return this.seen.size; }
  async fetch(req) {
    const url = new URL(req.url);
    if (req.method === "POST" && url.pathname === "/hit") {
      let b = {}; try { b = await req.json(); } catch (e) {}
      const id = String(b.id || "").slice(0, 40);
      if (id) this.seen.set(id, Date.now());
      if (b.first === true) { this.total = (await this.getTotal()) + 1; await this.state.storage.put("total", this.total); }
    } else if (!(req.method === "GET" && url.pathname === "/stats")) return new Response("not found", { status: 404 });
    return Response.json({ online: Math.max(1, this.online()), total: await this.getTotal() });
  }
}
