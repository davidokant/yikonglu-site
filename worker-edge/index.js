// 一孔录 yikonglu.com 前置 Worker（11-16）：页面原样转给 GitHub Pages，只数机器来读（硅基）。
// 认得出名字的爬虫和智器抓取（不跑脚本的也算）按 User-Agent 记，每取一个页面记一次，经服务绑定 LIVE 发 /bot {k}；不存 IP、不记人。
// 只数页面类请求（无扩展名、.html、.txt、.xml、.json 里的 llms/robots/sitemap 等），css/js/图片不数。出错一律原样放行。
const BOTS = [["gptbot","gptbot"],["chatgpt-user","chatgpt"],["oai-searchbot","oaisearch"],["claudebot","claudebot"],["claude-user","claude"],["claude-searchbot","claudesearch"],["anthropic-ai","anthropic"],
  ["perplexitybot","perplexity"],["perplexity-user","perplexity"],["bytespider","bytespider"],["googlebot","googlebot"],["google-extended","googleext"],["google-inspectiontool","googlebot"],["googleother","googleother"],
  ["bingbot","bingbot"],["baiduspider","baiduspider"],["yandex","yandex"],["applebot","applebot"],["amazonbot","amazonbot"],["meta-externalagent","meta"],["facebookexternalhit","facebook"],["ccbot","ccbot"],
  ["petalbot","petalbot"],["duckduckbot","duckduckbot"],["sogou","sogou"],["360spider","so360"],["yisouspider","yisou"],["semrushbot","semrush"],["ahrefsbot","ahrefs"],["mj12bot","mj12"],["dotbot","dotbot"],
  ["diffbot","diffbot"],["cohere-ai","cohere"],["youbot","youbot"],["mistralai-user","mistral"],["deepseekbot","deepseek"],["kimi","kimi"],["timpibot","timpi"],["imagesiftbot","imagesift"],["bot","otherbot"],["spider","otherbot"],["crawl","otherbot"]];
const VER = "2611262354";  // 推 main 后改成新值再部署，旧边缘缓存全部作废
const VERIFY = { "www.yikonglu.com": "shenma-site-verification:a5e7bb02c2a161c7fe33c178f0f96ed5_1795511830", "yikonglu.com": "shenma-site-verification:f005659bf9e0a2c96251cd7da2796949_1795513544" };
export default {
  async fetch(req, env, ctx) {
    ctx.passThroughOnException();
    // 11-24 神马站长登记的是 www.yikonglu.com，而 www 由 GitHub Pages 301 到裸域，验证跟不过去：站长验证文件直接给 200（主人点卡）；11-24 裸域站点经 GitHub Pages 也验不过，裸域同样由 Worker 直接给
    try { const v = new URL(req.url); if (v.pathname === "/shenma-site-verification.txt" && VERIFY[v.hostname]) return new Response(VERIFY[v.hostname], { headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-cache" } }); } catch (e) {}
    try {
      const u = new URL(req.url), ua = (req.headers.get("user-agent") || "").toLowerCase();
      if (req.method === "GET" && ua && /(^|\/)[^.\/]*$|\.(html|txt|xml)$|\/data\/[^\/]+\.json$/.test(u.pathname)) {
        const hit = BOTS.find(b => ua.includes(b[0]));
        if (hit && env.LIVE) ctx.waitUntil(env.LIVE.fetch("https://live/bot", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ k: hit[1] }) }).catch(() => {}));
      }
    } catch (e) {}
    // 11-24 主人点卡：边缘缓存。正常页面在 Cloudflare 存一天、首页与 /data/ 存 10 分钟（影响力数字自动更新）、404 存 1 分钟。
    // 令牌没有清缓存权限，所以用 Cache API 自管：缓存键带 VER，每次推 main 后把 VER 改成新值重新部署 Worker，旧缓存就全部作废。浏览器拿到的缓存头照原样。
    if (req.method === "GET") {
      try {
        const u = new URL(req.url), p = u.pathname;
        const ok = s => s === 200 || s === 301 || s === 302 || s === 404;
        const ttl = (/^\/([a-z]{2}(-[a-z]+)?\/)?(index\.html)?$/.test(p) || p.startsWith("/data/")) ? 600 : 86400;
        const key = new Request("https://" + u.hostname + "/__edge/" + VER + p + u.search);
        const cache = caches.default;
        const hit = await cache.match(key);
        if (hit) { const h = new Response(hit.body, hit); h.headers.set("Cache-Control", h.headers.get("X-Orig-CC") || "max-age=600"); h.headers.delete("X-Orig-CC"); h.headers.set("X-Edge", "hit"); return h; }
        const r = await fetch(req);
        if (ok(r.status)) {
          const c = new Response(r.clone().body, r);
          c.headers.set("X-Orig-CC", r.headers.get("Cache-Control") || "max-age=600");
          c.headers.set("Cache-Control", "public, max-age=" + (r.status === 404 ? 60 : ttl));
          c.headers.delete("Set-Cookie");
          ctx.waitUntil(cache.put(key, c));
        }
        return r;
      } catch (e) {}
    }
    return fetch(req);
  }
};
