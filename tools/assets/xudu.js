/* 一孔录 · 接着读（不登录）：阅读记录只存在这台设备的浏览器里（localStorage yk_xd）。
   章页：记下最近读到的章、读过哪些章、读到页面哪里。
   首页头图下、书页和篇页顶部：有记录才出“接着读”条（第一次来的人看不到）。
   篇页、书页里读过的章打勾；条里有本书进度。
   换设备：生成一个带记录的链接，在另一台设备打开即导入（记录在链接里，不经服务器）。 */
(function () {
  var PIAN = ["xue-er", "wei-zheng", "ba-yi", "li-ren", "gong-ye-chang", "yong-ye", "shu-er", "tai-bo", "zi-han", "xiang-dang", "xian-jin", "yan-yuan", "zi-lu", "xian-wen", "wei-ling-gong", "ji-shi", "yang-huo", "wei-zi", "zi-zhang", "yao-yue"];
  var K = "yk_xd", TOTAL = { lunyu: 498 }, BOOKN = { lunyu: ["论语", "論語", "Analects"] };
  var lang = document.documentElement.lang || "", HANT = /Hant/.test(lang), ZH = /^zh/.test(lang);
  var T = ZH ? (HANT ? {
    go: "接着讀", last: "上次讀到", prog: "已讀 {n} / {t} 章", priv: "一孔錄採用免登錄技術，免隱私，不打擾。", move: "帶到別的裝置", clear: "清除記錄", copied: "鏈接已複製：在另一台裝置打開，記錄就帶過去了。", imported: "閱讀記錄已導入。", ago: ["剛剛", "{n} 分鐘前", "{n} 小時前", "{n} 天前"], sure: "清除這台裝置上的閱讀記錄？"
  } : {
    go: "接着读", last: "上次读到", prog: "已读 {n} / {t} 章", priv: "一孔录采用免登录技术，免隐私，不打扰。", move: "带到别的设备", clear: "清除记录", copied: "链接已复制：在另一台设备打开，记录就带过去了。", imported: "阅读记录已导入。", ago: ["刚刚", "{n} 分钟前", "{n} 小时前", "{n} 天前"], sure: "清除这台设备上的阅读记录？"
  }) : {
    go: "Continue reading", last: "Last read", prog: "{n} of {t} chapters read", priv: "No sign-in, no personal data, no interruptions.", move: "Move to another device", clear: "Clear", copied: "Link copied. Open it on your other device to bring your progress along.", imported: "Reading progress imported.", ago: ["just now", "{n} min ago", "{n} h ago", "{n} d ago"], sure: "Clear reading progress on this device?"
  };
  function load() { try { return JSON.parse(localStorage.getItem(K) || "null") || { b: {} } } catch (e) { return null } }
  function save(s) { try { localStorage.setItem(K, JSON.stringify(s)); return true } catch (e) { return false } }
  var S = load(); if (!S) return; S.b = S.b || {};
  var pre = (location.pathname.match(/^\/(zh-hant|en|ja|ko|fr|es|de|vi|id|ru)\//) || ["", ""])[1];
  var rest = location.pathname.slice(pre ? pre.length + 1 : 0).replace(/^\//, "");
  var book = rest.split("/")[0];
  function fmt(s, o) { return s.replace(/\{(\w)\}/g, function (_, k) { return o[k] }) }
  function ago(ts) { var m = (Date.now() - ts) / 6e4; return m < 2 ? T.ago[0] : m < 60 ? fmt(T.ago[1], { n: Math.round(m) }) : m < 1440 ? fmt(T.ago[2], { n: Math.round(m / 60) }) : fmt(T.ago[3], { n: Math.round(m / 1440) }) }
  function toast(msg) { var d = document.createElement("div"); d.className = "xdtoast"; d.textContent = msg; document.body.appendChild(d); setTimeout(function () { d.remove() }, 3500) }
  var css = ".xdbar{background:var(--paper,#fbfaf5);border:1px solid var(--line,#dcded2);border-left:4px solid #8a5a2c;border-radius:10px;padding:12px 14px;margin:14px auto;max-width:860px;font-size:15px;line-height:1.6}"
    + ".xdbar .xdgo{display:flex;align-items:center;gap:10px;color:inherit;text-decoration:none}.xdbar .xdgo b{color:#23503f;font-size:17px}.xdbar .xdgo .xdarr{margin-left:auto;background:#23503f;color:#fff;border-radius:99px;padding:3px 14px;white-space:nowrap;font-size:14px}"
    + ".xdbar .xdmeta{color:var(--mute,#69716b);font-size:13px;margin-top:6px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center}.xdbar .xdmeta button{background:none;border:0;padding:0;color:#23503f;font:inherit;cursor:pointer;text-decoration:underline}"
    + ".xdprog{height:6px;background:var(--line,#dcded2);border-radius:99px;overflow:hidden;margin-top:8px}.xdprog i{display:block;height:100%;background:#8a5a2c}"
    + ".xdseen::after{content:'✓';margin-left:6px;color:#8a5a2c;font-weight:700}.xdtoast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#1f2421;color:#fff;padding:10px 16px;border-radius:10px;font-size:14px;z-index:99;max-width:90vw}"
    + ".xdpill{display:table;margin:12px auto 4px;background:rgba(251,250,245,.94);color:#23503f;border-radius:99px;padding:7px 16px;font-size:15px;font-weight:700;text-decoration:none;max-width:92%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;box-shadow:0 2px 10px rgba(0,0,0,.25)}"
    + "@media (prefers-color-scheme:dark){.xdbar .xdgo b{color:#83bba0}.xdbar .xdgo .xdarr{background:#2d6a53}}";
  function style() { if (document.getElementById("xdcss")) return; var st = document.createElement("style"); st.id = "xdcss"; st.textContent = css; document.head.appendChild(st) }

  // 换设备：#xd=<base64url(JSON)>
  var m = location.hash.match(/[#&]xd=([A-Za-z0-9_-]+)/);
  if (m) {
    try {
      var j = JSON.parse(decodeURIComponent(escape(atob(m[1].replace(/-/g, "+").replace(/_/g, "/")))));
      for (var bk in j.b || {}) {
        var a = S.b[bk] || { seen: [] }, x = j.b[bk];
        a.seen = (a.seen || []).concat((x.seen || []).filter(function (c) { return (a.seen || []).indexOf(c) < 0 }));
        if (x.last && (!a.last || x.last.ts > a.last.ts)) a.last = x.last;
        S.b[bk] = a;
      }
      save(S); history.replaceState(null, "", location.pathname + location.search); style(); toast(T.imported);
    } catch (e) { }
  }
  function moveLink() {
    var s = btoa(unescape(encodeURIComponent(JSON.stringify({ b: S.b })))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    var u = location.origin + "/" + (pre ? pre + "/" : "") + "#xd=" + s;
    var done = function () { toast(T.copied) };
    if (navigator.share && /Mobi/.test(navigator.userAgent)) navigator.share({ title: "一孔录", url: u }).catch(function () { });
    else if (navigator.clipboard) navigator.clipboard.writeText(u).then(done, function () { prompt("", u) });
    else prompt("", u);
  }

  // 章页：记录
  var dataEl = document.querySelector(".shdata");
  if (document.body.classList.contains("pg-chapter") && dataEl && TOTAL[book]) {
    try {
      var D = JSON.parse(dataEl.textContent), h1 = document.querySelector("h1 .no");
      var bs = S.b[book] || { seen: [] };
      if (bs.seen.indexOf(D.c) < 0) bs.seen.push(D.c);
      var y0 = location.hash === "#xd-y" && bs.last && bs.last.c === D.c ? bs._y : 0;
      bs.last = { p: location.pathname, c: D.c, ti: D.ti || "", no: h1 ? h1.textContent.split(" · ").slice(0, 2).join(" · ") : D.c, ts: Date.now() }; bs._y = y0 || 0;
      S.b[book] = bs; save(S);
      if (y0) { history.replaceState(null, "", location.pathname); addEventListener("load", function () { scrollTo(0, y0 * document.documentElement.scrollHeight) }) }
      var tick = 0;
      addEventListener("scroll", function () {
        if (tick) return; tick = setTimeout(function () {
          tick = 0; var r = scrollY / Math.max(1, document.documentElement.scrollHeight);
          var s2 = load(); if (s2 && s2.b[book] && s2.b[book].last && s2.b[book].last.c === D.c) { s2.b[book]._y = r; save(s2) }
        }, 800)
      }, { passive: true });
    } catch (e) { }
    return;
  }

  // 首页、书页、篇页：接着读条
  function bar(bk, where, how) {
    var bs = S.b[bk]; if (!bs || !bs.last) return;
    style();
    var n = (bs.seen || []).length, t = TOTAL[bk] || 0, L = bs.last, name = BOOKN[bk] ? BOOKN[bk][HANT ? 1 : ZH ? 0 : 2] : bk;
    var d = document.createElement("div"); d.className = "xdbar";
    d.innerHTML = '<a class="xdgo" href="' + L.p + (bs._y > 0.05 ? "#xd-y" : "") + '"><span>' + T.last + "：" + name + " · " + esc(L.no) + "<br><b>" + esc(L.ti) + '</b></span><span class="xdarr">' + T.go + " →</span></a>"
      + (t ? '<div class="xdprog" title="' + fmt(T.prog, { n: n, t: t }) + '"><i style="width:' + Math.min(100, n / t * 100).toFixed(1) + '%"></i></div>' : "")
      + '<div class="xdmeta"><span>' + ago(L.ts) + (t ? " · " + fmt(T.prog, { n: n, t: t }) : "") + '</span><button type="button" class="xdmv">' + T.move + '</button><button type="button" class="xdcl">' + T.clear + "</button><span>" + T.priv + "</span></div>";
    d.querySelector(".xdmv").onclick = moveLink;
    d.querySelector(".xdcl").onclick = function () { if (confirm(T.sure)) { delete S.b[bk]; save(S); d.remove(); [].forEach.call(document.querySelectorAll(".xdseen"), function (a) { a.classList.remove("xdseen") }) } };
    if (how === "after") where.parentNode.insertBefore(d, where.nextSibling); else where.insertBefore(d, where.firstChild);
  }
  function esc(s) { return String(s || "").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] }) }
  if (document.body.classList.contains("pg-home")) {
    var hero = document.querySelector("section.hero"), lastBk = null, lt = 0;
    for (var b2 in S.b) if (S.b[b2].last && S.b[b2].last.ts > lt) { lt = S.b[b2].last.ts; lastBk = b2 }
    if (hero && lastBk) {
      bar(lastBk, hero, "after");
      var ct = hero.querySelector("p.cta"), L2 = S.b[lastBk].last; // 头图里再放一颗小按钮，手机第一屏就看得见
      if (ct && L2) { var a2 = document.createElement("a"); a2.className = "xdpill"; a2.href = L2.p + (S.b[lastBk]._y > 0.05 ? "#xd-y" : ""); a2.innerHTML = T.go + "：" + esc(L2.no) + " " + esc(L2.ti) + " →"; ct.parentNode.insertBefore(a2, ct) }
    }
    return;
  }
  if (TOTAL[book] && S.b[book]) {
    var main = document.querySelector("main"); if (main) bar(book, main, "first");
    var seen = S.b[book].seen || [];
    [].forEach.call(document.querySelectorAll('main a[href*="/' + book + '/"]'), function (a) {
      if (a.closest(".xdbar")) return;
      var mm = a.getAttribute("href").match(new RegExp("/" + book + "/([a-z-]+)/(\\d+)\\.html$"));
      if (!mm) return;
      var pianIdx = PIAN.indexOf(mm[1]); if (pianIdx < 0) return;
      if (seen.indexOf((pianIdx + 1) + "." + mm[2]) >= 0) a.classList.add("xdseen");
    });
  }
})();
