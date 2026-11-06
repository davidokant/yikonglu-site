/* 一孔录 service worker（build.py 生成时填入版本号）
   页面：先走网络，拿到就更新缓存；没网才用缓存，缓存也没有就给离线页。每周日补页、改页后，联网打开就是新版。
   样式、图片、检索索引：先给缓存再后台更新。字体：缓存优先。 */
const VER = "72f7841d74";
const PREFIXES = ["", "zh-hant/", "en/", "ja/", "ko/", "fr/", "es/", "de/", "vi/", "id/", "ru/"];  // "", "zh-hant/", "en/" ...
const CORE = "yk-core-" + VER, PAGES = "yk-pages", STATIC = "yk-static", FONTS = "yk-fonts";
const MAX_PAGES = 400, MAX_STATIC = 300;

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CORE).then(c => c.addAll(PREFIXES.map(p => "/" + p + "offline.html").concat(["/assets/seal-180.png", "/assets/icon-192.png"]))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("yk-core-") && k !== CORE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

async function trim(name, max) {
  const c = await caches.open(name), ks = await c.keys();
  for (let i = 0; i < ks.length - max; i++) await c.delete(ks[i]);
}
function offlineFor(url) {
  const path = new URL(url).pathname;
  const p = PREFIXES.filter(x => x && path.startsWith("/" + x))[0] || "";
  return caches.match("/" + p + "offline.html");
}

self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {
    if (u.pathname === "/sw.js" || u.pathname.endsWith(".pdf")) return;  // 读本 PDF 不进缓存
    if (r.mode === "navigate" || (r.headers.get("accept") || "").includes("text/html")) {
      // 页面绕过浏览器 HTTP 缓存（GitHub Pages 给 10 分钟），向服务器验一次 ETag，刚部署的新页马上看得到
      e.respondWith(fetch(r.url, { cache: "no-cache", credentials: "same-origin" }).then(res => {
        if (res.ok) { const cp = res.clone(); caches.open(PAGES).then(c => c.put(u.origin + u.pathname, cp)).then(() => trim(PAGES, MAX_PAGES)); }
        return res;
      }).catch(() => caches.match(u.origin + u.pathname, { ignoreSearch: true }).then(m => m || offlineFor(r.url))));
      return;
    }
    if (/\.(css|png|jpg|jpeg|webp|svg|json|xml|txt)$/.test(u.pathname)) {
      e.respondWith(caches.open(STATIC).then(c => c.match(r).then(m => {
        const net = fetch(r).then(res => { if (res.ok) { c.put(r, res.clone()); trim(STATIC, MAX_STATIC); } return res; }).catch(() => m);
        return m || net;
      })));
    }
    return;
  }
  if (u.hostname === "fonts.googleapis.com" || u.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(FONTS).then(c => c.match(r).then(m => m || fetch(r).then(res => { c.put(r, res.clone()); return res; }))));
  }
});
