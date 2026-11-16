// 一孔录 yikonglu.com 前置 Worker（11-16）：页面原样转给 GitHub Pages，只数机器来读（硅基）。
// 认得出名字的爬虫和智器抓取（不跑脚本的也算）按 User-Agent 记，每取一个页面记一次，经服务绑定 LIVE 发 /bot {k}；不存 IP、不记人。
// 只数页面类请求（无扩展名、.html、.txt、.xml、.json 里的 llms/robots/sitemap 等），css/js/图片不数。出错一律原样放行。
const BOTS = [["gptbot","gptbot"],["chatgpt-user","chatgpt"],["oai-searchbot","oaisearch"],["claudebot","claudebot"],["claude-user","claude"],["claude-searchbot","claudesearch"],["anthropic-ai","anthropic"],
  ["perplexitybot","perplexity"],["perplexity-user","perplexity"],["bytespider","bytespider"],["googlebot","googlebot"],["google-extended","googleext"],["google-inspectiontool","googlebot"],["googleother","googleother"],
  ["bingbot","bingbot"],["baiduspider","baiduspider"],["yandex","yandex"],["applebot","applebot"],["amazonbot","amazonbot"],["meta-externalagent","meta"],["facebookexternalhit","facebook"],["ccbot","ccbot"],
  ["petalbot","petalbot"],["duckduckbot","duckduckbot"],["sogou","sogou"],["360spider","so360"],["yisouspider","yisou"],["semrushbot","semrush"],["ahrefsbot","ahrefs"],["mj12bot","mj12"],["dotbot","dotbot"],
  ["diffbot","diffbot"],["cohere-ai","cohere"],["youbot","youbot"],["mistralai-user","mistral"],["deepseekbot","deepseek"],["kimi","kimi"],["timpibot","timpi"],["imagesiftbot","imagesift"],["bot","otherbot"],["spider","otherbot"],["crawl","otherbot"]];
export default {
  async fetch(req, env, ctx) {
    ctx.passThroughOnException();
    try {
      const u = new URL(req.url), ua = (req.headers.get("user-agent") || "").toLowerCase();
      if (req.method === "GET" && ua && /(^|\/)[^.\/]*$|\.(html|txt|xml)$|\/data\/[^\/]+\.json$/.test(u.pathname)) {
        const hit = BOTS.find(b => ua.includes(b[0]));
        if (hit && env.LIVE) ctx.waitUntil(env.LIVE.fetch("https://live/bot", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ k: hit[1] }) }).catch(() => {}));
      }
    } catch (e) {}
    return fetch(req);
  }
};
