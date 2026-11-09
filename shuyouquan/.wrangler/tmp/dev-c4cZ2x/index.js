var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/index.js
import SCHEMA from "./513037278a568141902383fe760236cef69040ba-schema.sql";
var SITE = "\u4E00\u5B54\u4E66\u9662 \xB7 \u4E66\u53CB\u5708";
var DAY = 864e5;
var now = /* @__PURE__ */ __name(() => Date.now(), "now");
var PIAN = ["xue-er", "wei-zheng", "ba-yi", "li-ren", "gong-ye-chang", "yong-ye", "shu-er", "tai-bo", "zi-han", "xiang-dang", "xian-jin", "yan-yuan", "zi-lu", "xian-wen", "wei-ling-gong", "ji-shi", "yang-huo", "wei-zi", "zi-zhang", "yao-yue"];
var chUrl = /* @__PURE__ */ __name((c) => {
  const [a, n] = c.split(".");
  return `https://yikonglu.com/lunyu/${PIAN[+a - 1]}/${n}.html`;
}, "chUrl");
var IDENT = { shusheng: ["\u4E66\u751F", "\u4E66"], youxia: ["\u6E38\u4FA0", "\u4FA0"], shanglv: ["\u5546\u65C5", "\u5546"], yizhe: ["\u533B\u8005", "\u533B"], jiangren: ["\u5320\u4EBA", "\u5320"], fangwai: ["\u65B9\u5916", "\u65B9"] };
var AV_BASE = "https://img.yikonglu.com/shuyuan/av/";
var RANKS = [[150, "\u8BB2\u53CB"], [60, "\u658B\u957F"], [20, "\u751F\u5458"], [5, "\u5B66\u7AE5"], [0, "\u521D\u5165\u9662"]];
var rankOf = /* @__PURE__ */ __name((n) => RANKS.find(([k]) => (n || 0) >= k)[1], "rankOf");
var HAS_AV = false;
var esc = /* @__PURE__ */ __name((s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]), "esc");
function fmtBody(s) {
  return esc(s).replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" rel="nofollow noopener" target="_blank">$1</a>').replace(/\n/g, "<br>");
}
__name(fmtBody, "fmtBody");
function fmtTime(t) {
  if (!t) return "";
  const d = new Date(t + 8 * 36e5), p = /* @__PURE__ */ __name((n) => String(n).padStart(2, "0"), "p");
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
}
__name(fmtTime, "fmtTime");
var rand = /* @__PURE__ */ __name((n = 16) => [...crypto.getRandomValues(new Uint8Array(n))].map((b) => b.toString(16).padStart(2, "0")).join(""), "rand");
var code6 = /* @__PURE__ */ __name(() => {
  const A = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  return [...crypto.getRandomValues(new Uint8Array(8))].map((b) => A[b % A.length]).join("");
}, "code6");
async function hashPw(pw, salt) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: new TextEncoder().encode(salt), iterations: 1e5 }, key, 256);
  return [...new Uint8Array(bits)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
__name(hashPw, "hashPw");
function eqConst(a, b) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}
__name(eqConst, "eqConst");
function cookie(req, k) {
  const m = (req.headers.get("Cookie") || "").match(new RegExp("(?:^|;\\s*)" + k + "=([^;]+)"));
  return m ? m[1] : null;
}
__name(cookie, "cookie");
var redirect = /* @__PURE__ */ __name((to, headers = {}) => new Response(null, { status: 303, headers: { Location: to, ...headers } }), "redirect");
async function limited(env, key, max, ms) {
  const t = now(), r = await env.DB.prepare("SELECT n, until FROM hits WHERE k=?").bind(key).first();
  if (!r || r.until < t) {
    await env.DB.prepare("INSERT OR REPLACE INTO hits (k, n, until) VALUES (?, 1, ?)").bind(key, t + ms).run();
    return false;
  }
  if (r.n >= max) return true;
  await env.DB.prepare("UPDATE hits SET n=n+1 WHERE k=?").bind(key).run();
  return false;
}
__name(limited, "limited");
async function currentUser(req, env) {
  const tok = cookie(req, "syq");
  if (!tok) return null;
  return await env.DB.prepare("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?").bind(tok, now()).first();
}
__name(currentUser, "currentUser");
var isMember = /* @__PURE__ */ __name((u) => u && (u.role === "member" || u.role === "admin"), "isMember");
var isAdmin = /* @__PURE__ */ __name((u) => u && u.role === "admin", "isAdmin");
var CSS = `:root{--bg:#f2f1ea;--paper:#fbfaf5;--fg:#1f2421;--mute:#69716b;--accent:#23503f;--accent2:#8a5a2c;--line:#dcded2;--red:#b03a2e}
@media (prefers-color-scheme:dark){:root{--bg:#111513;--paper:#19201c;--fg:#e5e8e1;--mute:#9aa49d;--accent:#83bba0;--accent2:#d4a373;--line:#28312c;--red:#e07a6e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.75 "Noto Serif SC","Songti SC",serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header{background:var(--paper);border-bottom:1px solid var(--line)}header .w{display:flex;align-items:center;gap:12px;padding:10px 16px}
header .brand{font-weight:700;color:var(--fg);font-size:18px}header nav{margin-left:auto;display:flex;gap:14px;font-size:15px;flex-wrap:wrap}
.w{max-width:820px;margin:0 auto;padding:0 16px}main.w{padding-top:18px;padding-bottom:60px}
h1{font-size:24px;margin:6px 0 4px}h2{font-size:19px;margin:22px 0 8px}.mute{color:var(--mute);font-size:14px}
.box{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.list{list-style:none;padding:0;margin:0}.list li{padding:12px 4px;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.list li .t{font-weight:700;font-size:17px}.list li .m{margin-left:auto;color:var(--mute);font-size:13px;white-space:nowrap}
.lock{color:var(--mute);font-size:13px;border:1px solid var(--line);border-radius:99px;padding:0 8px}
.pin{color:var(--accent2);font-size:13px}.ans{color:#fff;background:var(--accent);font-size:12px;border-radius:4px;padding:0 6px}
.post{display:flex;gap:12px;padding:14px 0;border-bottom:1px solid var(--line)}.post .av{width:44px;height:44px;border-radius:50%;flex:none;background:var(--line);object-fit:cover;display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--accent)}
.post .who{font-weight:700}.post .tag{font-size:12px;color:var(--accent2);border:1px solid var(--accent2);border-radius:4px;padding:0 5px;margin-left:6px;font-weight:400}.post .body{margin-top:4px;word-break:break-word}
form label{display:block;margin:10px 0 4px;font-size:15px}input[type=text],input[type=password],input[type=datetime-local],textarea,select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg);font:inherit}
textarea{min-height:140px}button,.btn{display:inline-block;margin-top:12px;padding:8px 20px;border:0;border-radius:99px;background:var(--accent);color:#fff;font:inherit;cursor:pointer}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}.err{color:var(--red)}.ok{color:var(--accent)}
.hp{position:absolute;left:-9999px}footer{color:var(--mute);font-size:13px;text-align:center;padding:30px 16px}

.maphero{position:relative;border-radius:12px;overflow:hidden;margin:4px 0 14px;background:#16201b}.maphero img{display:block;width:100%;height:190px;object-fit:cover;opacity:.7}.maphero div{position:absolute;left:0;right:0;bottom:0;padding:14px 16px;background:linear-gradient(transparent,rgba(0,0,0,.85));color:#fff}.maphero h1{margin:0;color:#fff}.maphero p{margin:2px 0 0;font-size:14px;opacity:.92}
.post .rank{font-size:12px;color:var(--mute);margin-left:6px}.post .tag.men{color:var(--accent);border-color:var(--accent)}
.av.id-shusheng{background:#dfe8e2;color:#23503f}.av.id-youxia{background:#efe2d6;color:#8a5a2c}.av.id-shanglv{background:#efe9d4;color:#7a6420}.av.id-yizhe{background:#dcebe8;color:#2c6a60}.av.id-jiangren{background:#e6e1dc;color:#5c4a3a}.av.id-fangwai{background:#e7e3ee;color:#5a4a7a}
.idpick{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.idpick label{display:flex;align-items:center;gap:6px;margin:0;border:1px solid var(--line);border-radius:10px;padding:6px 8px;cursor:pointer;font-size:15px}.idpick .av{width:30px;height:30px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:14px}.idpick input{position:absolute;opacity:0;width:0;height:0}.idpick label{position:relative;white-space:nowrap;justify-content:center}.idpick label:has(input:checked){border-color:var(--accent);box-shadow:0 0 0 2px var(--accent) inset;font-weight:700}
code{background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:1px 6px}`;
function page(title, body, u) {
  const nav = u ? `<span class="mute">${esc(u.name)}${u.role === "guest" ? "\uFF08\u672A\u5165\u4F1A\uFF09" : ""}</span>${u.role === "guest" ? '<a href="/invite">\u7528\u9080\u8BF7\u7801\u5165\u4F1A</a>' : ""}${isAdmin(u) ? '<a href="/admin">\u7BA1\u7406</a>' : ""}<form method="post" action="/logout" style="display:inline"><button class="btn ghost" style="margin:0;padding:0 12px">\u9000\u51FA</button></form>` : `<a href="/login">\u767B\u5F55</a><a href="/register">\u6CE8\u518C</a>`;
  return new Response(
    `<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>${esc(title)}\uFF5C${SITE}</title><style>${CSS}</style></head><body>
<header><div class="w"><a class="brand" href="/">${SITE}</a><nav>${nav}</nav></div></header><main class="w">${body}</main>
<footer>\u4E00\u5B54\u5F55 \xB7 \u4E66\u53CB\u5708\u4E0D\u516C\u5F00\uFF0C\u53EA\u7ED9\u4E66\u9662\u4E66\u53CB\u3002\u4E0A\u5B98\u6709\u7406\u3001\u5B54\u7167\u4ECA\u662F\u4E00\u5B54\u5F55\u539F\u521B\u89D2\u8272\uFF0C\u7531\u667A\u5668\u4E3B\u6301\uFF1B\u8BFB\u6CD5\u4EE5\u201C\u4E00\u5B54\u6309\u201D\u4E3A\u51C6\u3002<br><a href="https://yikonglu.com/shuyuan.html">\u4E00\u5B54\u4E66\u9662</a> \xB7 \u522B\u8D34\u771F\u540D\u3001\u624B\u673A\u53F7\u3001\u5355\u4F4D\u3002</footer></body></html>`,
    { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Frame-Options": "DENY", "Referrer-Policy": "same-origin" } }
  );
}
__name(page, "page");
var notFound = /* @__PURE__ */ __name((u) => {
  const r = page("\u627E\u4E0D\u5230", `<h1>\u627E\u4E0D\u5230\u8FD9\u4E00\u9875</h1><p><a href="/">\u56DE\u4E66\u53CB\u5708</a></p>`, u);
  return new Response(r.body, { status: 404, headers: r.headers });
}, "notFound");
function avatar(u) {
  if (u.avatar) return `<img class="av" src="${esc(u.avatar)}" alt="">`;
  const id = IDENT[u.ident];
  if (id && HAS_AV) return `<img class="av" src="${AV_BASE}${u.ident}.png" alt="${id[0]}">`;
  return `<span class="av id-${esc(u.ident || "none")}">${esc(id ? id[1] : (u.name || "?").slice(0, 1))}</span>`;
}
__name(avatar, "avatar");
function whoTag(u) {
  if (u.tag) return `<span class="tag">${esc(u.tag)}</span>`;
  if (u.role === "admin") return '<span class="tag">\u4E00\u5B54\u5F55</span>';
  const id = IDENT[u.ident];
  return `<span class="rank">${id ? id[0] + " \xB7 " : ""}${rankOf(u.posts)}</span>${u.role === "member" ? '<span class="tag men">\u4E66\u9662\u95E8\u4EBA</span>' : ""}`;
}
__name(whoTag, "whoTag");
async function home(env, u) {
  const { results: boards } = await env.DB.prepare(
    "SELECT b.*, (SELECT COUNT(*) FROM threads t WHERE t.board_id=b.id) n, (SELECT MAX(last_at) FROM threads t WHERE t.board_id=b.id) last FROM boards b ORDER BY sort"
  ).all();
  const li = boards.map((b) => `<li><a class="t" href="/b/${b.slug}">${esc(b.name)}</a>${b.members_only ? '<span class="lock">\u4F1A\u5458</span>' : ""}<span class="mute" style="flex-basis:100%">${esc(b.descr)}</span><span class="m">${b.n} \u5E16${b.last ? " \xB7 " + fmtTime(b.last) : ""}</span></li>`).join("");
  const hello = !u ? `<div class="box">\u4E66\u53CB\u5708\u53EA\u7ED9\u4E00\u5B54\u4E66\u9662\u7684\u4E66\u53CB\u3002\u5148<a href="/register">\u6CE8\u518C</a>\uFF08\u53EA\u8981\u7F51\u540D\u548C\u5BC6\u7801\uFF09\uFF0C\u518D\u7528\u5165\u4F1A\u9080\u8BF7\u7801\u8FDB\u4F1A\u5458\u533A\u3002\u201C\u5C71\u95E8\u201D\u8C01\u90FD\u80FD\u770B\u3002</div>` : u.role === "guest" ? `<div class="box">\u4F60\u5DF2\u6CE8\u518C\uFF0C\u8FD8\u6CA1\u5165\u4F1A\u3002\u62FF\u5230\u9080\u8BF7\u7801\u540E\uFF0C<a href="/invite">\u5728\u8FD9\u91CC\u5165\u4F1A</a>\u3002</div>` : "";
  return page("\u9996\u9875", `<div class="maphero"><img src="https://img.yikonglu.com/gushi/img/ditu/world-%E7%AE%80.jpg" alt=""><div><h1>\u4E00\u5B54\u4E66\u9662</h1><p>\u628A\u8BFB\u540C\u4E00\u90E8\u4E66\u3001\u53E3\u5473\u76F8\u8FD1\u7684\u4EBA\u805A\u5728\u4E00\u8D77\uFF1A\u8BFB\u5230\u54EA\u804A\u5230\u54EA\uFF0C\u6709\u4EBA\u63A5\u8BDD\uFF0C\u6709\u4EBA\u8F83\u771F\u3002</p></div></div>${hello}<h2>\u9662\u843D</h2><ul class="list">${li}</ul>${u ? `<p class="mute">\u4F60\u7684\u5B66\u7C4D\uFF1A${IDENT[u.ident] ? IDENT[u.ident][0] + " \xB7 " : ""}${rankOf(u.posts)}\u3002\u591A\u53D1\u8A00\u3001\u591A\u53C2\u52A0\u5171\u8BFB\uFF0C\u5B66\u7C4D\u4F1A\u5347\uFF1A\u521D\u5165\u9662 \u2192 \u5B66\u7AE5 \u2192 \u751F\u5458 \u2192 \u658B\u957F \u2192 \u8BB2\u53CB\u3002</p>` : ""}`, u);
}
__name(home, "home");
async function board(env, u, slug) {
  const b = await env.DB.prepare("SELECT * FROM boards WHERE slug=?").bind(slug).first();
  if (!b) return notFound(u);
  if (b.members_only && !isMember(u)) return page(b.name, `<h1>${esc(b.name)}</h1><div class="box">\u8FD9\u4E00\u533A\u53EA\u7ED9\u4E66\u9662\u4F1A\u5458\u3002${u ? '<a href="/invite">\u7528\u9080\u8BF7\u7801\u5165\u4F1A</a>' : '<a href="/login">\u767B\u5F55</a>\u6216<a href="/register">\u6CE8\u518C</a>'}\u3002</div>`, u);
  const { results } = await env.DB.prepare(
    "SELECT t.*, u.name uname FROM threads t JOIN users u ON u.id=t.user_id WHERE board_id=? ORDER BY pinned DESC, last_at DESC LIMIT 100"
  ).bind(b.id).all();
  const li = results.map((t) => `<li>${t.pinned ? '<span class="pin">\u7F6E\u9876</span>' : ""}${t.answered ? '<span class="ans">\u5DF2\u7B54</span>' : ""}<a class="t" href="/t/${t.id}">${esc(t.title)}</a><span class="m">${esc(t.uname)} \xB7 ${t.replies} \u56DE \xB7 ${fmtTime(t.last_at)}</span></li>`).join("") || '<li class="mute">\u8FD8\u6CA1\u6709\u5E16\u5B50\u3002</li>';
  const can = u && (isMember(u) || !b.members_only);
  return page(b.name, `<p class="mute"><a href="/">\u4E66\u53CB\u5708</a> \u203A</p><h1>${esc(b.name)}</h1><p class="mute">${esc(b.descr)}</p>${can ? `<a class="btn" href="/new?b=${b.slug}">\u53D1\u5E16</a>` : ""}<ul class="list">${li}</ul>`, u);
}
__name(board, "board");
async function thread(env, u, id, msg = "") {
  const t = await env.DB.prepare("SELECT t.*, b.slug, b.name bname, b.members_only FROM threads t JOIN boards b ON b.id=t.board_id WHERE t.id=?").bind(id).first();
  if (!t) return notFound(u);
  if (t.members_only && !isMember(u)) return page(t.bname, `<h1>${esc(t.bname)}</h1><div class="box">\u8FD9\u4E00\u5E16\u5728\u4F1A\u5458\u533A\u3002${u ? '<a href="/invite">\u7528\u9080\u8BF7\u7801\u5165\u4F1A</a>' : '<a href="/login">\u767B\u5F55</a>'}\u3002</div>`, u);
  const { results } = await env.DB.prepare("SELECT p.*, u.name, u.role, u.avatar, u.tag, u.ident, u.posts FROM posts p JOIN users u ON u.id=p.user_id WHERE thread_id=? ORDER BY p.id").bind(id).all();
  const ps = results.map((p, i) => `<div class="post" id="p${p.id}">${avatar(p)}<div><div><span class="who">${esc(p.name)}</span>${whoTag(p)} <span class="mute">${i ? "#" + i + " \xB7 " : ""}${fmtTime(p.created)}</span></div><div class="body">${fmtBody(p.body)}</div></div></div>`).join("");
  const adm = isAdmin(u) ? `<form method="post" action="/t/${id}/flag" class="mute" style="margin-top:6px"><button name="f" value="pinned" class="btn ghost" style="padding:2px 12px">${t.pinned ? "\u53D6\u6D88\u7F6E\u9876" : "\u7F6E\u9876"}</button> <button name="f" value="answered" class="btn ghost" style="padding:2px 12px">${t.answered ? "\u53D6\u6D88\u5DF2\u7B54" : "\u6807\u5DF2\u7B54"}</button></form>` : "";
  const canReply = u && (isMember(u) || !t.members_only);
  const asSel = isAdmin(u) ? await asSelect(env, u) : "";
  const form = canReply ? `<form method="post" action="/t/${id}/reply" class="box"><label>\u56DE\u590D</label><textarea name="body" required maxlength="8000"></textarea>${asSel}<button>\u53D1\u51FA</button></form>` : u ? "" : `<p class="mute"><a href="/login">\u767B\u5F55</a>\u540E\u53EF\u56DE\u590D\u3002</p>`;
  return page(t.title, `<p class="mute"><a href="/">\u4E66\u53CB\u5708</a> \u203A <a href="/b/${t.slug}">${esc(t.bname)}</a>${t.chapter ? ` \xB7 <a href="${chUrl(t.chapter)}">\u8BBA\u8BED ${esc(t.chapter)} \u539F\u6587</a>` : ""}</p><h1>${t.answered ? '<span class="ans">\u5DF2\u7B54</span> ' : ""}${esc(t.title)}</h1>${adm}${msg}${ps}${form}`, u);
}
__name(thread, "thread");
async function asSelect(env, u) {
  const { results } = await env.DB.prepare("SELECT id, name FROM users WHERE role='char' ORDER BY id").all();
  return `<label>\u4EE5\u8C01\u7684\u8EAB\u4EFD\u53D1</label><select name="as"><option value="">${esc(u.name)}\uFF08\u81EA\u5DF1\uFF09</option>${results.map((c) => `<option value="${c.id}">${esc(c.name)}\uFF08\u539F\u521B\u89D2\u8272\uFF09</option>`).join("")}</select>`;
}
__name(asSelect, "asSelect");
async function resolveAs(env, u, as) {
  if (!as || !isAdmin(u)) return u.id;
  const c = await env.DB.prepare("SELECT id FROM users WHERE id=? AND role='char'").bind(+as).first();
  return c ? c.id : u.id;
}
__name(resolveAs, "resolveAs");
function authForm(kind, err = "", name = "") {
  const reg = kind === "register";
  return `<h1>${reg ? "\u6CE8\u518C" : "\u767B\u5F55"}</h1>${err ? `<p class="err">${esc(err)}</p>` : ""}<form method="post" class="box">
<label>\u7F51\u540D\uFF082\u201416 \u5B57\uFF0C\u522B\u7528\u771F\u540D\uFF09</label><input type="text" name="name" value="${esc(name)}" required minlength="2" maxlength="16" autocomplete="username">
<label>\u5BC6\u7801\uFF08\u81F3\u5C11 8 \u4F4D\uFF09</label><input type="password" name="pw" required minlength="8" autocomplete="${reg ? "new-password" : "current-password"}">
${reg ? `<label>\u4F60\u5728\u4E66\u9662\u91CC\u662F\u4EC0\u4E48\u8EAB\u4EFD\uFF08\u51B3\u5B9A\u5934\u50CF\uFF09</label><div class="idpick">${Object.entries(IDENT).map(([k, v], i) => `<label><input type="radio" name="ident" value="${k}"${i ? "" : " checked"}><span class="av id-${k}">${v[1]}</span>${v[0]}</label>`).join("")}</div>` : ""}
${reg ? '<label>\u5165\u4F1A\u9080\u8BF7\u7801\uFF08\u6709\u5C31\u586B\uFF0C\u6CA1\u6709\u53EF\u4EE5\u5148\u7A7A\u7740\uFF09</label><input type="text" name="code" autocomplete="off"><input class="hp" name="website" tabindex="-1" autocomplete="off">' : ""}
<button>${reg ? "\u6CE8\u518C" : "\u767B\u5F55"}</button></form>
<p class="mute">${reg ? '\u4E0D\u8981\u90AE\u7BB1\u3001\u4E0D\u8981\u624B\u673A\u53F7\u3002\u5FD8\u4E86\u5BC6\u7801\uFF0C\u627E\u4E0A\u5B98\u6709\u7406\u8981\u4E00\u4E2A\u91CD\u7F6E\u7801\uFF0C\u5728<a href="/reset">\u8FD9\u91CC</a>\u6539\u3002' : '\u8FD8\u6CA1\u6709\u8D26\u53F7\uFF1F<a href="/register">\u6CE8\u518C</a>\u3002\u5FD8\u4E86\u5BC6\u7801\uFF1F<a href="/reset">\u7528\u91CD\u7F6E\u7801\u6539</a>\u3002'}</p>`;
}
__name(authForm, "authForm");
async function startSession(env, uid) {
  const tok = rand(24);
  await env.DB.prepare("INSERT INTO sessions (token, user_id, expires) VALUES (?, ?, ?)").bind(tok, uid, now() + 60 * DAY).run();
  return `syq=${tok}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${60 * 86400}`;
}
__name(startSession, "startSession");
async function useInvite(env, uid, code, kinds) {
  code = String(code || "").trim().toUpperCase();
  if (!code) return null;
  if (env.ADMIN_CODE && kinds.includes("admin") && code === String(env.ADMIN_CODE).toUpperCase()) {
    const a = await env.DB.prepare("SELECT 1 FROM users WHERE role='admin'").first();
    return a ? null : { kind: "admin" };
  }
  const inv = await env.DB.prepare("SELECT * FROM invites WHERE code=? AND used_by IS NULL").bind(code).first();
  if (!inv || !kinds.includes(inv.kind)) return null;
  const r = await env.DB.prepare("UPDATE invites SET used_by=?, used_at=? WHERE code=? AND used_by IS NULL").bind(uid, now(), code).run();
  return r.meta.changes ? inv : null;
}
__name(useInvite, "useInvite");
async function runScheduled(env) {
  const { results } = await env.DB.prepare("SELECT * FROM scheduled WHERE done=0 AND run_at<=? ORDER BY run_at LIMIT 20").bind(now()).all();
  for (const s of results) {
    const t = now();
    if (s.thread_id) {
      await env.DB.prepare("INSERT INTO posts (thread_id, user_id, body, created) VALUES (?, ?, ?, ?)").bind(s.thread_id, s.as_user, s.body, t).run();
      await env.DB.prepare("UPDATE threads SET replies=replies+1, last_at=? WHERE id=?").bind(t, s.thread_id).run();
    } else {
      const b = await env.DB.prepare("SELECT id FROM boards WHERE slug=?").bind(s.board_slug).first();
      if (b) await newThread(env, b.id, s.as_user, s.title || "\uFF08\u65E0\u9898\uFF09", s.body, null);
    }
    await env.DB.prepare("UPDATE scheduled SET done=1 WHERE id=?").bind(s.id).run();
  }
  await env.DB.prepare("DELETE FROM sessions WHERE expires<?").bind(now()).run();
  await env.DB.prepare("DELETE FROM hits WHERE until<?").bind(now()).run();
}
__name(runScheduled, "runScheduled");
async function newThread(env, boardId, uid, title, body, chapter) {
  const t = now();
  const r = await env.DB.prepare("INSERT INTO threads (board_id, user_id, title, chapter, created, last_at) VALUES (?, ?, ?, ?, ?, ?)").bind(boardId, uid, title, chapter, t, t).run();
  const id = r.meta.last_row_id;
  await env.DB.prepare("INSERT INTO posts (thread_id, user_id, body, created) VALUES (?, ?, ?, ?)").bind(id, uid, body, t).run();
  await env.DB.prepare("UPDATE users SET posts=posts+1 WHERE id=?").bind(uid).run();
  return id;
}
__name(newThread, "newThread");
async function admin(env, u, msg = "") {
  const { results: inv } = await env.DB.prepare("SELECT i.*, u.name uname FROM invites i LEFT JOIN users u ON u.id=i.used_by ORDER BY created DESC LIMIT 30").all();
  const { results: sch } = await env.DB.prepare("SELECT s.*, u.name FROM scheduled s JOIN users u ON u.id=s.as_user WHERE done=0 ORDER BY run_at LIMIT 30").all();
  const { results: boards } = await env.DB.prepare("SELECT slug, name FROM boards ORDER BY sort").all();
  const { results: chars } = await env.DB.prepare("SELECT id, name FROM users WHERE role='char' ORDER BY id").all();
  const n = await env.DB.prepare("SELECT SUM(role='member') m, SUM(role='guest') g FROM users").first();
  const invRows = inv.map((i) => `<li><code>${esc(i.code)}</code> ${i.kind === "member" ? "\u5165\u4F1A" : i.kind === "admin" ? "\u7BA1\u7406" : "\u91CD\u7F6E"}${i.for_name ? " \xB7 \u7ED9 " + esc(i.for_name) : ""}${i.note ? " \xB7 " + esc(i.note) : ""}<span class="m">${i.used_by ? "\u5DF2\u7528\uFF1A" + esc(i.uname) : "\u672A\u7528"}</span></li>`).join("");
  const schRows = sch.map((s) => `<li>${fmtTime(s.run_at)} \xB7 ${esc(s.name)} \xB7 ${s.thread_id ? "\u56DE\u5E16 #" + s.thread_id : esc(s.board_slug) + "\uFF1A" + esc(s.title)}<span class="m">${esc(String(s.body).slice(0, 30))}\u2026</span></li>`).join("") || '<li class="mute">\u6CA1\u6709\u5F85\u53D1\u7684\u3002</li>';
  return page("\u7BA1\u7406", `<h1>\u7BA1\u7406</h1>${msg}<p class="mute">\u4F1A\u5458 ${n.m || 0} \u4EBA\uFF0C\u5DF2\u6CE8\u518C\u672A\u5165\u4F1A ${n.g || 0} \u4EBA\u3002</p>
<h2>\u53D1\u9080\u8BF7\u7801</h2><form method="post" action="/admin/invite" class="box"><label>\u79CD\u7C7B</label><select name="kind"><option value="member">\u5165\u4F1A\uFF08\u4ED8\u8D39\u540E\u53D1\u7ED9\u4E66\u53CB\uFF09</option><option value="reset">\u91CD\u7F6E\u5BC6\u7801\uFF08\u5FC5\u987B\u586B\u7F51\u540D\uFF09</option></select>
<label>\u7ED9\u8C01\uFF08\u7F51\u540D\uFF0C\u53EF\u7A7A\uFF09</label><input type="text" name="for_name"><label>\u5907\u6CE8\uFF08\u53EF\u7A7A\uFF0C\u5982\u201C\u77E5\u8BC6\u661F\u7403 11-09\u201D\uFF09</label><input type="text" name="note"><label>\u4E00\u6B21\u53D1\u51E0\u4E2A</label><input type="text" name="n" value="1"><button>\u751F\u6210</button></form>
<ul class="list">${invRows}</ul>
<h2>\u89D2\u8272\u5B9A\u65F6\u5E16</h2><form method="post" action="/admin/schedule" class="box"><label>\u89D2\u8272</label><select name="as">${chars.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("")}</select>
<label>\u53D1\u5230\u54EA\u4E2A\u533A\uFF08\u5F00\u65B0\u5E16\uFF09</label><select name="board">${boards.map((b) => `<option value="${b.slug}">${esc(b.name)}</option>`).join("")}</select>
<label>\u6216\u56DE\u590D\u5230\u5E16\u5B50\u7F16\u53F7\uFF08\u586B\u4E86\u5C31\u4E0D\u5F00\u65B0\u5E16\uFF09</label><input type="text" name="thread"><label>\u6807\u9898\uFF08\u5F00\u65B0\u5E16\u65F6\u7528\uFF09</label><input type="text" name="title" maxlength="80">
<label>\u6B63\u6587</label><textarea name="body" required></textarea><label>\u4EC0\u4E48\u65F6\u5019\u53D1\uFF08\u5317\u4EAC\u65F6\u95F4\uFF09</label><input type="datetime-local" name="at" required><button>\u6392\u4E0A</button></form>
<ul class="list">${schRows}</ul>`, u);
}
__name(admin, "admin");
var App = {
  async fetch(req, env) {
    const url = new URL(req.url), path = url.pathname, M = req.method;
    if (M === "POST") {
      const o = req.headers.get("Origin");
      if (o && o !== url.origin) return new Response("bad origin", { status: 403 });
    }
    const u = await currentUser(req, env);
    const ip = req.headers.get("CF-Connecting-IP") || "x";
    const form = M === "POST" ? await req.formData() : null;
    const f = /* @__PURE__ */ __name((k) => String(form?.get(k) ?? "").trim(), "f");
    if (path === "/" && M === "GET") return home(env, u);
    let m;
    if ((m = path.match(/^\/b\/([a-z0-9-]+)$/)) && M === "GET") return board(env, u, m[1]);
    if ((m = path.match(/^\/t\/(\d+)$/)) && M === "GET") return thread(env, u, +m[1]);
    if ((m = path.match(/^\/c\/(\d{1,2}\.\d{1,2})$/)) && M === "GET" && +m[1].split(".")[0] <= 20) {
      const t = await env.DB.prepare("SELECT id FROM threads WHERE chapter=? ORDER BY id LIMIT 1").bind(m[1]).first();
      return redirect(t ? `/t/${t.id}` : `/new?b=lunyu&c=${m[1]}`);
    }
    if (path === "/register") {
      if (M === "GET") return page("\u6CE8\u518C", authForm("register"), u);
      if (f("website")) return redirect("/");
      if (await limited(env, "reg:" + ip, 5, DAY)) return page("\u6CE8\u518C", authForm("register", "\u4ECA\u5929\u6CE8\u518C\u6B21\u6570\u592A\u591A\uFF0C\u660E\u5929\u518D\u6765\u3002"), u);
      const name = f("name"), pw = String(form.get("pw") || "");
      if (name.length < 2 || name.length > 16 || /[<>\s]/.test(name)) return page("\u6CE8\u518C", authForm("register", "\u7F51\u540D\u8981 2\u201416 \u4E2A\u5B57\uFF0C\u4E0D\u80FD\u6709\u7A7A\u683C\u3002", name), u);
      if (pw.length < 8) return page("\u6CE8\u518C", authForm("register", "\u5BC6\u7801\u81F3\u5C11 8 \u4F4D\u3002", name), u);
      if (await env.DB.prepare("SELECT 1 FROM users WHERE lower(name)=lower(?)").bind(name).first()) return page("\u6CE8\u518C", authForm("register", "\u8FD9\u4E2A\u7F51\u540D\u6709\u4EBA\u7528\u4E86\uFF0C\u6362\u4E00\u4E2A\u3002", name), u);
      const salt = rand(16), h = await hashPw(pw, salt);
      const ident = IDENT[f("ident")] ? f("ident") : "shusheng";
      const r = await env.DB.prepare("INSERT INTO users (name, pw, salt, role, ident, created) VALUES (?, ?, ?, 'guest', ?, ?)").bind(name, h, salt, ident, now()).run();
      const uid = r.meta.last_row_id, inv = await useInvite(env, uid, f("code"), ["member", "admin"]);
      if (inv) await env.DB.prepare("UPDATE users SET role=? WHERE id=?").bind(inv.kind === "admin" ? "admin" : "member", uid).run();
      return redirect("/", { "Set-Cookie": await startSession(env, uid) });
    }
    if (path === "/login") {
      if (M === "GET") return page("\u767B\u5F55", authForm("login"), u);
      if (await limited(env, "login:" + ip, 20, 36e5)) return page("\u767B\u5F55", authForm("login", "\u8BD5\u592A\u591A\u6B21\u4E86\uFF0C\u4E00\u5C0F\u65F6\u540E\u518D\u6765\u3002"), u);
      const name = f("name"), pw = String(form.get("pw") || "");
      const x = await env.DB.prepare("SELECT * FROM users WHERE lower(name)=lower(?) AND pw IS NOT NULL").bind(name).first();
      if (!x || !eqConst(await hashPw(pw, x.salt), x.pw)) return page("\u767B\u5F55", authForm("login", "\u7F51\u540D\u6216\u5BC6\u7801\u4E0D\u5BF9\u3002", name), u);
      return redirect("/", { "Set-Cookie": await startSession(env, x.id) });
    }
    if (path === "/logout" && M === "POST") {
      const tok = cookie(req, "syq");
      if (tok) await env.DB.prepare("DELETE FROM sessions WHERE token=?").bind(tok).run();
      return redirect("/", { "Set-Cookie": "syq=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" });
    }
    if (path === "/reset") {
      const fm = /* @__PURE__ */ __name((e = "") => `<h1>\u7528\u91CD\u7F6E\u7801\u6539\u5BC6\u7801</h1>${e}<form method="post" class="box"><label>\u7F51\u540D</label><input type="text" name="name" required><label>\u91CD\u7F6E\u7801\uFF08\u627E\u4E0A\u5B98\u6709\u7406\u8981\uFF09</label><input type="text" name="code" required><label>\u65B0\u5BC6\u7801\uFF08\u81F3\u5C11 8 \u4F4D\uFF09</label><input type="password" name="pw" required minlength="8"><button>\u6539\u5BC6\u7801</button></form>`, "fm");
      if (M === "GET") return page("\u91CD\u7F6E\u5BC6\u7801", fm(), u);
      if (await limited(env, "reset:" + ip, 10, 36e5)) return page("\u91CD\u7F6E\u5BC6\u7801", fm('<p class="err">\u8BD5\u592A\u591A\u6B21\u4E86\u3002</p>'), u);
      const name = f("name"), pw = String(form.get("pw") || ""), code = f("code").toUpperCase();
      const x = await env.DB.prepare("SELECT * FROM users WHERE lower(name)=lower(?) AND pw IS NOT NULL").bind(name).first();
      const inv = x && await env.DB.prepare("SELECT * FROM invites WHERE code=? AND kind='reset' AND used_by IS NULL AND lower(for_name)=lower(?)").bind(code, name).first();
      if (!inv || pw.length < 8) return page("\u91CD\u7F6E\u5BC6\u7801", fm('<p class="err">\u7F51\u540D\u3001\u91CD\u7F6E\u7801\u5BF9\u4E0D\u4E0A\uFF0C\u6216\u5BC6\u7801\u592A\u77ED\u3002</p>'), u);
      await useInvite(env, x.id, code, ["reset"]);
      const salt = rand(16);
      await env.DB.prepare("UPDATE users SET pw=?, salt=? WHERE id=?").bind(await hashPw(pw, salt), salt, x.id).run();
      await env.DB.prepare("DELETE FROM sessions WHERE user_id=?").bind(x.id).run();
      return redirect("/login");
    }
    if (!u) return M === "GET" ? notFound(u) : redirect("/login");
    if (path === "/invite") {
      const fm = /* @__PURE__ */ __name((e = "") => `<h1>\u7528\u9080\u8BF7\u7801\u5165\u4F1A</h1>${e}<form method="post" class="box"><label>\u9080\u8BF7\u7801</label><input type="text" name="code" required><button>\u5165\u4F1A</button></form><p class="mute">\u9080\u8BF7\u7801\u5728\u4ED8\u8D39\u540E\u7531\u4E0A\u5B98\u6709\u7406\u53D1\u7ED9\u4F60\uFF0C\u4E00\u4E2A\u7801\u53EA\u80FD\u7528\u4E00\u6B21\u3002</p>`, "fm");
      if (M === "GET") return page("\u5165\u4F1A", fm(), u);
      if (await limited(env, "inv:" + u.id, 10, 36e5)) return page("\u5165\u4F1A", fm('<p class="err">\u8BD5\u592A\u591A\u6B21\u4E86\u3002</p>'), u);
      const inv = await useInvite(env, u.id, f("code"), ["member", "admin"]);
      if (!inv) return page("\u5165\u4F1A", fm('<p class="err">\u8FD9\u4E2A\u7801\u4E0D\u5BF9\uFF0C\u6216\u5DF2\u7ECF\u7528\u8FC7\u3002</p>'), u);
      if (u.role !== "admin") await env.DB.prepare("UPDATE users SET role=? WHERE id=?").bind(inv.kind === "admin" ? "admin" : "member", u.id).run();
      return redirect("/");
    }
    if (path === "/new") {
      const slug = url.searchParams.get("b") || f("b"), b = await env.DB.prepare("SELECT * FROM boards WHERE slug=?").bind(slug).first();
      if (!b) return notFound(u);
      if (b.members_only && !isMember(u)) return redirect("/invite");
      const ch = (url.searchParams.get("c") || f("c")).match(/^\d{1,2}\.\d{1,2}$/)?.[0] || "";
      if (M === "GET") return page("\u53D1\u5E16", `<p class="mute"><a href="/b/${b.slug}">${esc(b.name)}</a> \u203A</p><h1>\u53D1\u5E16</h1><form method="post" class="box"><input type="hidden" name="b" value="${b.slug}"><input type="hidden" name="c" value="${ch}">
<label>\u6807\u9898</label><input type="text" name="title" required maxlength="80" value="${ch ? "\u8BBA\u8BED " + ch : ""}"><label>\u6B63\u6587</label><textarea name="body" required maxlength="8000"></textarea>${isAdmin(u) ? await asSelect(env, u) : ""}<button>\u53D1\u51FA</button></form>`, u);
      if (await limited(env, "post:" + u.id, 30, 36e5)) return page("\u53D1\u5E16", `<p class="err">\u53D1\u5F97\u592A\u5FEB\u4E86\uFF0C\u6B47\u4E00\u4F1A\u513F\u3002</p>`, u);
      const title = f("title").slice(0, 80), body = f("body").slice(0, 8e3);
      if (!title || !body) return redirect(`/new?b=${b.slug}`);
      const id = await newThread(env, b.id, await resolveAs(env, u, f("as")), title, body, ch || null);
      return redirect(`/t/${id}`);
    }
    if ((m = path.match(/^\/t\/(\d+)\/reply$/)) && M === "POST") {
      const t = await env.DB.prepare("SELECT t.id, b.members_only FROM threads t JOIN boards b ON b.id=t.board_id WHERE t.id=?").bind(+m[1]).first();
      if (!t) return notFound(u);
      if (t.members_only && !isMember(u)) return redirect("/invite");
      if (await limited(env, "post:" + u.id, 30, 36e5)) return thread(env, u, t.id, '<p class="err">\u53D1\u5F97\u592A\u5FEB\u4E86\uFF0C\u6B47\u4E00\u4F1A\u513F\u3002</p>');
      const body = f("body").slice(0, 8e3);
      if (body) {
        const ts = now();
        await env.DB.prepare("INSERT INTO posts (thread_id, user_id, body, created) VALUES (?, ?, ?, ?)").bind(t.id, await resolveAs(env, u, f("as")), body, ts).run();
        await env.DB.prepare("UPDATE threads SET replies=replies+1, last_at=? WHERE id=?").bind(ts, t.id).run();
        await env.DB.prepare("UPDATE users SET posts=posts+1 WHERE id=?").bind(await resolveAs(env, u, f("as"))).run();
      }
      return redirect(`/t/${t.id}#end`);
    }
    if ((m = path.match(/^\/t\/(\d+)\/flag$/)) && M === "POST" && isAdmin(u)) {
      const col = f("f") === "pinned" ? "pinned" : "answered";
      await env.DB.prepare(`UPDATE threads SET ${col}=1-${col} WHERE id=?`).bind(+m[1]).run();
      return redirect(`/t/${m[1]}`);
    }
    if (path.startsWith("/admin")) {
      if (!isAdmin(u)) return notFound(u);
      if (path === "/admin" && M === "GET") return admin(env, u);
      if (path === "/admin/invite" && M === "POST") {
        const kind = f("kind") === "reset" ? "reset" : "member", n = Math.min(50, Math.max(1, parseInt(f("n")) || 1));
        if (kind === "reset" && !f("for_name")) return admin(env, u, '<p class="err">\u91CD\u7F6E\u7801\u5FC5\u987B\u586B\u7F51\u540D\u3002</p>');
        for (let i = 0; i < n; i++) await env.DB.prepare("INSERT INTO invites (code, kind, for_name, note, created) VALUES (?, ?, ?, ?, ?)").bind(code6(), kind, f("for_name") || null, f("note") || null, now()).run();
        return admin(env, u, `<p class="ok">\u751F\u6210\u4E86 ${n} \u4E2A\u3002</p>`);
      }
      if (path === "/admin/schedule" && M === "POST") {
        const at = Date.parse(f("at") + ":00+08:00"), tid = parseInt(f("thread")) || null;
        if (!at || !f("body")) return admin(env, u, '<p class="err">\u65F6\u95F4\u548C\u6B63\u6587\u90FD\u8981\u586B\u3002</p>');
        await env.DB.prepare("INSERT INTO scheduled (as_user, board_slug, thread_id, title, body, run_at) VALUES (?, ?, ?, ?, ?, ?)").bind(+f("as"), f("board"), tid, f("title") || null, f("body"), at).run();
        return admin(env, u, '<p class="ok">\u6392\u4E0A\u4E86\uFF0C\u5230\u70B9\u81EA\u52A8\u53D1\uFF08\u6BCF 10 \u5206\u949F\u67E5\u4E00\u6B21\uFF09\u3002</p>');
      }
    }
    return notFound(u);
  }
};
var Stmt = class {
  static {
    __name(this, "Stmt");
  }
  constructor(sql, q) {
    this.sql = sql;
    this.q = q;
    this.a = [];
  }
  bind(...a) {
    this.a = a;
    return this;
  }
  first() {
    const r = this.sql.exec(this.q, ...this.a).toArray();
    return r[0] || null;
  }
  all() {
    return { results: this.sql.exec(this.q, ...this.a).toArray() };
  }
  run() {
    const c = this.sql.exec(this.q, ...this.a);
    c.toArray();
    return { meta: { changes: c.rowsWritten, last_row_id: this.sql.exec("SELECT last_insert_rowid() AS id").one().id } };
  }
};
var Syq = class {
  static {
    __name(this, "Syq");
  }
  constructor(state, env) {
    const sql = state.storage.sql;
    for (const q of SCHEMA.split(/;\s*\n/).map((x) => x.replace(/^\s*--.*$/gm, "").trim()).filter(Boolean)) sql.exec(q);
    this.env = { ...env, DB: { prepare: /* @__PURE__ */ __name((q) => new Stmt(sql, q), "prepare") } };
  }
  async fetch(req) {
    if (new URL(req.url).pathname === "/__cron") {
      await runScheduled(this.env);
      return new Response("ok");
    }
    return App.fetch(req, this.env);
  }
};
var hub = /* @__PURE__ */ __name((env) => env.SYQ.get(env.SYQ.idFromName("main")), "hub");
var src_default = {
  async fetch(req, env) {
    if (new URL(req.url).pathname === "/__cron") return new Response("not found", { status: 404 });
    return hub(env).fetch(req);
  },
  async scheduled(_ev, env) {
    await hub(env).fetch("https://internal/__cron");
  }
};

// ../../../../tmp/claude-0/syqtest/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../../tmp/claude-0/syqtest/node_modules/wrangler/templates/middleware/middleware-scheduled.ts
var scheduled = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  const url = new URL(request.url);
  if (url.pathname === "/__scheduled") {
    const cron = url.searchParams.get("cron") ?? "";
    await middlewareCtx.dispatch("scheduled", { cron });
    return new Response("Ran scheduled event");
  }
  const resp = await middlewareCtx.next(request, env);
  if (request.headers.get("referer")?.endsWith("/__scheduled") && url.pathname === "/favicon.ico" && resp.status === 500) {
    return new Response(null, { status: 404 });
  }
  return resp;
}, "scheduled");
var middleware_scheduled_default = scheduled;

// ../../../../tmp/claude-0/syqtest/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    const body = JSON.stringify(error);
    const headers = {
      "Content-Type": "application/json",
      "MF-Experimental-Error-Stack": "true"
    };
    const encoded = encodeURIComponent(body);
    if (encoded.length <= 8192) {
      headers["MF-Experimental-Error-Stack-Payload"] = encoded;
    }
    return new Response(body, { status: 500, headers });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-XfEPHX/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_scheduled_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = src_default;

// ../../../../tmp/claude-0/syqtest/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-XfEPHX/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  scheduledTime;
  cron;
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  Syq,
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
//# sourceMappingURL=index.js.map
