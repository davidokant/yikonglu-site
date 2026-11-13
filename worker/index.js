// 一孔录网站在线人数与累计读者数（Cloudflare Worker + 一个 Durable Object）
// POST /hit  {id, first}  页面每 60 秒发一次心跳；first=true 表示这台设备第一次来，累计数加一
// GET  /stats            返回 {online, total, k}；k＝来过的国家/地区数（只记 Cloudflare 给的两位国家码，不存 IP）
// POST /hit 带 c（章号）时记一次阅读：按天计数（7 天滚动）＋最近读过的章
// POST /copy {c, s}      某句被复制/分享一次（7 天滚动）
// GET  /top              {recent:[c…], rn:今天读过的章数, heat:{c:n}, top:[[c#sN, n]…]}
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
    const r = await stub.fetch(req); // 11-09 主人：不再统计国家和地区
    const h = new Headers(r.headers); for (const [k, v] of Object.entries(cors(req))) h.set(k, v);
    h.set("Cache-Control", "no-store");
    return new Response(r.body, { status: r.status, headers: h });
  },
};

export class Live {
  constructor(state) { this.state = state; this.seen = new Map(); this.total = null; }
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
    const OKC = /^[0-9]{1,2}\.[0-9]{1,2}$/, OKB = /^(ddj|szj)\.[0-9]{1,2}$/;
    if (req.method === "POST" && url.pathname === "/hit") {
      let b = {}; try { b = await req.json(); } catch (e) {}
      const id = String(b.id || "").slice(0, 40);
      if (id) this.seen.set(id, Date.now());
      if (b.first === true) { this.total = (await this.getTotal()) + 1; await this.state.storage.put("total", this.total); }
      const c = String(b.c || "");
      if (OKC.test(c) || OKB.test(c)) { // 11-13：道德经 ddj.N、三字经 szj.N 也记
        const d = this.day(), R = await this.roll("reads"); R[d] = R[d] || {}; R[d][c] = (R[d][c] || 0) + 1;
        let rc = (await this.state.storage.get("recent")) || []; rc = [{ c, d }].concat(rc.filter(x => x.c !== c)).slice(0, 200); // 11-12 主人：多记一些，原来只留 8 条
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
      return Response.json({ today: ((OKC.test(c) || OKB.test(c)) && R[this.day()] && R[this.day()][c]) || 0 });
    } else if (req.method === "GET" && url.pathname === "/top") {
      const R = await this.roll("reads"), C = await this.roll("copies"), heat = {}, cp = {}, d0 = this.day();
      for (const d in R) for (const c in R[d]) heat[c] = (heat[c] || 0) + R[d][c];
      for (const d in C) for (const k in C[d]) cp[k] = (cp[k] || 0) + C[d][k];
      const top = Object.entries(cp).sort((a, b) => b[1] - a[1]).slice(0, 3);
      const today = R[d0] || {}, rn = Object.keys(today).length; // 今天有人读过的章数
      // 11-13：先按最近读的顺序，再补今天读过但已被挤出最近记录的章（按读的次数），列表和章数对得上
      const rc0 = ((await this.state.storage.get("recent")) || []).filter(x => x.d === d0 && today[x.c]).map(x => x.c);
      const recent = rc0.concat(Object.keys(today).filter(c => !rc0.includes(c)).sort((a, b) => today[b] - today[a])).slice(0, 40);
      return Response.json({ recent, rn, heat, top });
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
    return Response.json({ online: Math.max(1, this.online()), total: await this.getTotal() });
  }
}
