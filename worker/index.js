// 一孔录网站在线人数与累计读者数（Cloudflare Worker + 一个 Durable Object）
// POST /hit  {id, first}  页面每 60 秒发一次心跳；first=true 表示这台设备第一次来，累计数加一
// GET  /stats            返回 {online, total, k}；k＝来过的国家/地区数（只记 Cloudflare 给的两位国家码，不存 IP）
// POST /hit 带 c（章号）时记一次阅读：按天计数（7 天滚动）＋最近读过的章
// POST /copy {c, s}      某句被复制/分享一次（7 天滚动）
// GET  /top              {recent:[c…], heat:{c:n}, top:[[c#sN, n]…]}
// POST /intent {join:true} 一孔书院“我想第一批加入”加一（同一浏览器只点一次，页面本地记）；POST /intent {want:[…]} 各项“最想要”加一
// GET  /intent          {n}（满 20 才给数，否则 n:null）；GET /intent/stats {n, want, days} 全部计数（不含任何个人信息）
// POST /done  {c}         某章“读完了”加一（同一设备只点一次，由页面本地记）；GET /done?c=1.1 返回 {today, total}
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
    const fh = new Headers(req.headers); fh.set("X-Yk-Cc", String((req.cf && req.cf.country) || "")); // 只传国家码
    const r = await stub.fetch(new Request(req, { headers: fh }));
    const h = new Headers(r.headers); for (const [k, v] of Object.entries(cors(req))) h.set(k, v);
    h.set("Cache-Control", "no-store");
    return new Response(r.body, { status: r.status, headers: h });
  },
};

export class Live {
  constructor(state) { this.state = state; this.seen = new Map(); this.total = null; this.cc = null; }
  async getCc() { if (this.cc === null) this.cc = new Set((await this.state.storage.get("cc")) || []); return this.cc; }
  async getTotal() { if (this.total === null) this.total = (await this.state.storage.get("total")) || 0; return this.total; }
  online() { const n = Date.now(); for (const [k, t] of this.seen) if (n - t > WINDOW) this.seen.delete(k); return this.seen.size; }
  day() { return new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10); }
  async roll(key) { // 7 天滚动的 {day:{k:n}}
    const o = (await this.state.storage.get(key)) || {}; const keep = new Set();
    for (let i = 0; i < 7; i++) keep.add(new Date(Date.now() + 8 * 3600e3 - i * 864e5).toISOString().slice(0, 10));
    for (const d of Object.keys(o)) if (!keep.has(d)) delete o[d];
    return o;
  }
  async fetch(req) {
    const url = new URL(req.url);
    const OKC = /^[0-9]{1,2}\.[0-9]{1,2}$/;
    if (req.method === "POST" && url.pathname === "/hit") {
      let b = {}; try { b = await req.json(); } catch (e) {}
      const id = String(b.id || "").slice(0, 40);
      if (id) this.seen.set(id, Date.now());
      const cc = (req.headers.get("X-Yk-Cc") || "").toUpperCase(), S = await this.getCc();
      if (/^[A-Z]{2}$/.test(cc) && cc !== "XX" && cc !== "T1" && !S.has(cc)) { S.add(cc); await this.state.storage.put("cc", [...S]); }
      if (b.first === true) { this.total = (await this.getTotal()) + 1; await this.state.storage.put("total", this.total); }
      const c = String(b.c || "");
      if (OKC.test(c)) {
        const d = this.day(), R = await this.roll("reads"); R[d] = R[d] || {}; R[d][c] = (R[d][c] || 0) + 1;
        let rc = (await this.state.storage.get("recent")) || []; rc = [{ c, d }].concat(rc.filter(x => x.c !== c)).slice(0, 8);
        await this.state.storage.put({ reads: R, recent: rc });
      }
    } else if (req.method === "POST" && url.pathname === "/copy") {
      let b = {}; try { b = await req.json(); } catch (e) {}
      const c = String(b.c || ""), sId = String(b.s || "");
      if (OKC.test(c) && /^s[0-9]{1,2}$/.test(sId)) {
        const d = this.day(), C = await this.roll("copies"), k = c + "#" + sId; C[d] = C[d] || {}; C[d][k] = (C[d][k] || 0) + 1;
        await this.state.storage.put("copies", C);
      }
      return Response.json({ ok: true });
    } else if (req.method === "GET" && url.pathname === "/reads") { // 某章今天被读了几次
      const c = url.searchParams.get("c") || "", R = await this.roll("reads");
      return Response.json({ today: (OKC.test(c) && R[this.day()] && R[this.day()][c]) || 0 });
    } else if (req.method === "GET" && url.pathname === "/top") {
      const R = await this.roll("reads"), C = await this.roll("copies"), heat = {}, cp = {}, d0 = this.day();
      for (const d in R) for (const c in R[d]) heat[c] = (heat[c] || 0) + R[d][c];
      for (const d in C) for (const k in C[d]) cp[k] = (cp[k] || 0) + C[d][k];
      const top = Object.entries(cp).sort((a, b) => b[1] - a[1]).slice(0, 3);
      const recent = ((await this.state.storage.get("recent")) || []).filter(x => x.d === d0).map(x => x.c).slice(0, 5);
      return Response.json({ recent, heat, top });
    } else if (url.pathname === "/intent" || url.pathname === "/intent/stats") {
      const WANT = ["shiyong", "shuhou", "shuyou", "gongdu", "wenda", "gongju", "zhencang"];
      let I = (await this.state.storage.get("intent")) || { n: 0, want: {}, days: {} };
      if (req.method === "POST" && url.pathname === "/intent") {
        let b = {}; try { b = await req.json(); } catch (e) {}
        if (b.join === true) { I.n++; const d = this.day(); I.days[d] = (I.days[d] || 0) + 1; }
        if (Array.isArray(b.want)) for (const w of new Set(b.want.map(String))) if (WANT.includes(w)) I.want[w] = (I.want[w] || 0) + 1;
        await this.state.storage.put("intent", I);
      }
      if (url.pathname === "/intent/stats") return Response.json(I);
      return Response.json({ n: I.n >= 20 ? I.n : null });
    } else if (url.pathname === "/done") {
      let c = url.searchParams.get("c") || "";
      if (req.method === "POST") { try { c = String((await req.json()).c || ""); } catch (e) {} }
      if (!/^[a-z0-9.\-]{1,24}$/.test(c)) return new Response("bad", { status: 400 });
      const day = new Date(Date.now() + 8 * 3600e3).toISOString().slice(0, 10); // 北京日期
      const kt = "d:" + c, kd = "dd:" + day + ":" + c;
      let [t, d] = [(await this.state.storage.get(kt)) || 0, (await this.state.storage.get(kd)) || 0];
      if (req.method === "POST") { t++; d++; await this.state.storage.put({ [kt]: t, [kd]: d }); }
      return Response.json({ today: d, total: t });
    } else if (!(req.method === "GET" && url.pathname === "/stats")) return new Response("not found", { status: 404 });
    return Response.json({ online: Math.max(1, this.online()), total: await this.getTotal(), k: (await this.getCc()).size });
  }
}
