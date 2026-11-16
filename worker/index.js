// 一孔录网站在线人数与累计读者数（Cloudflare Worker + 一个 Durable Object）
// POST /hit  {id, first}  页面每 60 秒发一次心跳；first=true 表示这台设备第一次来，累计数加一
// 11-15：/hit、/stats 另给 today＝今天（北京时间）来过的设备数，老读者回来也算（前台宽口径，主人：宁可偏多）
// GET  /stats            返回 {online, total, k}；k＝来过的国家/地区数（只记 Cloudflare 给的两位国家码，不存 IP）
// POST /hit 带 c（章号）时记一次阅读：按天计数（7 天滚动）＋最近读过的章
// POST /copy {c, s}      某句被复制/分享一次（7 天滚动）
// GET  /top              {recent:[c…], rn:今天读过的章数, heat:{c:n}, top:[[c#sN, n]…]}
// POST /intent {join:true} 一孔书院“我想第一批加入”加一（同一浏览器只点一次，页面本地记）；POST /intent {want:[…]} 各项“最想要”加一
// GET  /intent          {n}（满 20 才给数，否则 n:null）；GET /intent/stats {n, want, days} 全部计数（不含任何个人信息）
// POST /wk {a:n} 或 {l:n}  匿名周读：这台设备本周（北京时间周一起）第 n 天读书（a 各书、l 只算《论语》），每周每个 n 只发一次；不带任何编号
// GET  /wk               {周一日期: {a:{n:台数}, l:{n:台数}}}，留 12 周；北极星＝本周 a[4]（读满四天的台数）
// POST /mirror {h, p, y}  11-16 防抄：页面在 yikonglu.com 以外的域名打开时（整站镜像）由页面发一次；只记域名、路径、页面出处编号，不记访客
// GET  /mirror           {域名: {n, first, last, paths:[…最多 20]}}，最多留 200 个域名
// POST /ai {k, p}         11-16 智器来访：从智器回答里点进来（来路或 utm_source 是智器），k＝哪家，p＝落地页；GET /ai 返回 {days:{日:{k:n}}, pages:{页:n}}，留 120 天
// POST /hj {f, c}         11-16 他书章页“《论语》互见”点击：f＝从哪章（ddj.N／szj.N），c＝点去的论语章；GET /hj 返回 {日:{"f>c":n}}，留 120 天
// POST /bot {k}          11-16 硅基儒者：机器来读一次加一（页面里认出是机器在跑脚本时发 k＝哪家；连接器每回答一次发 k＝mcp）；/hit、/stats 的 bots＝有用的硅基（USEFUL）；GET /bot 返回 {useful, all, days:{日:{k:n}}}（留 120 天）
// POST /done  {c}         某章“读完了”加一（同一设备只点一次，由页面本地记）；GET /done?c=1.1 返回 {today, total}
const ORIGINS = ["https://yikonglu.com", "https://www.yikonglu.com", "http://localhost:8767"];
const WINDOW = 90 * 1000;
// 11-16 主人定：累计 N＝碳基＋有用的硅基。有用＝搜索引擎爬虫、智器爬虫与连接器；SEO 工具、采集器、扫漏洞的、认不出名字的不算（后台照记）
const USEFUL = new Set(["googlebot","googleext","googleother","bingbot","baiduspider","yandex","applebot","duckduckbot","sogou","so360","yisou","petalbot",
  "gptbot","chatgpt","oaisearch","claudebot","claude","claudesearch","anthropic","perplexity","bytespider","amazonbot","meta","ccbot","cohere","youbot","mistral","deepseek","kimi","mcp"]); // 90 秒内有心跳算在线

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
  async getBots() { // 前台只算“有用的硅基”（搜索引擎、智器爬虫、连接器）；全部机器另记在 bt 与 btd
    if (this.bots === undefined) { let u = await this.state.storage.get("btu"); if (u === undefined) { u = 0; const O = (await this.state.storage.get("btd")) || {}; for (const d of Object.values(O)) for (const [k, n] of Object.entries(d)) if (USEFUL.has(k)) u += n; await this.state.storage.put("btu", u); } this.bots = u; }
    return this.bots; }
  async getTotal() { if (this.total === null) this.total = (await this.state.storage.get("total")) || 0; return this.total; }
  async markDay(id) { // 今天来过的设备：只记随机编号，过了北京时间零点就清
    const d = this.day(); if (!this.dv || this.dv.d !== d) { const o = await this.state.storage.get("dv"); this.dv = o && o.d === d ? { d, ids: new Set(o.ids) } : { d, ids: new Set() }; }
    if (this.dv.ids.has(id) || this.dv.ids.size >= 50000) return; this.dv.ids.add(id); await this.state.storage.put("dv", { d, ids: [...this.dv.ids] });
  }
  async todayN() { const d = this.day(); if (!this.dv || this.dv.d !== d) { const o = await this.state.storage.get("dv"); this.dv = o && o.d === d ? { d, ids: new Set(o.ids) } : { d, ids: new Set() }; } return this.dv.ids.size; }
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
      if (id) await this.markDay(id);
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
    } else if (url.pathname === "/wk") { // 11-14 主人定北极星：每周读满四天的人数
      const W = (await this.state.storage.get("week")) || {};
      if (req.method === "POST") {
        let b = {}; try { b = await req.json(); } catch (e) {}
        const now = new Date(Date.now() + 8 * 3600e3), mon = new Date(now.getTime() - ((now.getUTCDay() + 6) % 7) * 864e5).toISOString().slice(0, 10);
        const w = W[mon] = W[mon] || { a: {}, l: {} };
        for (const k of ["a", "l"]) { const n = Number(b[k]); if (Number.isInteger(n) && n >= 1 && n <= 7) w[k][n] = (w[k][n] || 0) + 1; }
        for (const k of Object.keys(W).sort().slice(0, -12)) delete W[k];
        await this.state.storage.put("week", W);
        return Response.json({ ok: true });
      }
      return Response.json(W);
    } else if (url.pathname === "/bot") {
      const d = this.day(), cut = new Date(Date.now() + 8 * 3600e3 - 120 * 864e5).toISOString().slice(0, 10);
      const O = (await this.state.storage.get("btd")) || {}; for (const x of Object.keys(O)) if (x < cut) delete O[x];
      if (req.method === "POST") {
        let b = {}; try { b = JSON.parse(await req.text()); } catch (e) {}
        const k = String(b.k || ""); if (!/^[a-z0-9]{2,16}$/.test(k)) return Response.json({ ok: false });
        const u = await this.getBots(); O[d] = O[d] || {}; O[d][k] = (O[d][k] || 0) + 1;
        const all = ((await this.state.storage.get("bt")) || 0) + 1, put = { bt: all, btd: O };
        if (USEFUL.has(k)) { this.bots = u + 1; put.btu = this.bots; }
        await this.state.storage.put(put);
        return Response.json({ ok: true });
      }
      return Response.json({ useful: await this.getBots(), all: (await this.state.storage.get("bt")) || 0, days: O });
    } else if (url.pathname === "/ai" || url.pathname === "/hj") {
      const key = url.pathname.slice(1), d = this.day();
      const keep = o => { const cut = new Date(Date.now() + 8 * 3600e3 - 120 * 864e5).toISOString().slice(0, 10); for (const x of Object.keys(o)) if (x < cut) delete o[x]; return o; };
      if (req.method === "POST") {
        let b = {}; try { b = JSON.parse(await req.text()); } catch (e) {}
        let k = "";
        if (key === "ai") { k = String(b.k || ""); if (!/^[a-z]{2,12}$/.test(k)) return Response.json({ ok: false }); }
        else { const f = String(b.f || ""), c = String(b.c || ""); if (!/^(ddj|szj)\.[0-9]{1,2}$/.test(f) || !/^([0-9]{1,2}\.[0-9]{1,2}|book)$/.test(c)) return Response.json({ ok: false }); k = f + ">" + c; }
        const O = keep((await this.state.storage.get(key)) || {}); O[d] = O[d] || {}; O[d][k] = (O[d][k] || 0) + 1;
        const put = { [key]: O };
        if (key === "ai") { const p = String(b.p || "").slice(0, 120); if (/^\/[a-z0-9\/._-]*$/i.test(p)) { const P = (await this.state.storage.get("aip")) || {}; if (P[p] || Object.keys(P).length < 2000) { P[p] = (P[p] || 0) + 1; put.aip = P; } } }
        await this.state.storage.put(put);
        return Response.json({ ok: true });
      }
      const O = keep((await this.state.storage.get(key)) || {});
      return Response.json(key === "ai" ? { days: O, pages: (await this.state.storage.get("aip")) || {} } : O);
    } else if (url.pathname === "/mirror") {
      if (req.method === "POST") {
        let b = {}; try { b = JSON.parse(await req.text()); } catch (e) {}
        const host = String(b.h || "").toLowerCase().slice(0, 100), p = String(b.p || "").slice(0, 200), y = String(b.y || "").slice(0, 40);
        if (!host || /(^|\.)yikonglu\.com$/.test(host) || !/^[a-z0-9.-]+$/.test(host)) return Response.json({ ok: false });
        const M = (await this.state.storage.get("mirror")) || {}, d = this.day();
        if (!M[host] && Object.keys(M).length >= 200) return Response.json({ ok: false });
        const m = M[host] || { n: 0, first: d, paths: [] }; m.n++; m.last = d;
        const k = p + (y ? " " + y : ""); if (!m.paths.includes(k) && m.paths.length < 20) m.paths.push(k);
        M[host] = m; await this.state.storage.put("mirror", M);
        return Response.json({ ok: true });
      }
      return Response.json((await this.state.storage.get("mirror")) || {});
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
    return Response.json({ online: Math.max(1, this.online()), total: await this.getTotal(), bots: await this.getBots(), today: Math.max(1, await this.todayN()) });
  }
}
