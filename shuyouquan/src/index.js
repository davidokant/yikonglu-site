// 一孔书院·书友圈 雏形（Cloudflare Worker + D1，服务端渲染，零依赖）
// 结构参考 MIT 开源 cf-bbs Nexus、企鹅窝；代码自写。
// 第一版：网名＋密码注册（不要邮箱）、邀请码进会员组、按书分区、帖子回复、两位原创角色账号、Cron 定时发帖、章页直达 /c/1.16。
// 不做：私信、图片上传、邮件通知。

const SITE = "一孔书院 · 书友圈";
const DAY = 864e5;
const now = () => Date.now();
const PIAN = ["xue-er", "wei-zheng", "ba-yi", "li-ren", "gong-ye-chang", "yong-ye", "shu-er", "tai-bo", "zi-han", "xiang-dang", "xian-jin", "yan-yuan", "zi-lu", "xian-wen", "wei-ling-gong", "ji-shi", "yang-huo", "wei-zi", "zi-zhang", "yao-yue"]; // 论语二十篇网址
const chUrl = (c) => { const [a, n] = c.split("."); return `https://yikonglu.com/lunyu/${PIAN[+a - 1]}/${n}.html`; };

// ---------- 小工具 ----------
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
function fmtBody(s) { // 纯文本：转义、自动链接、保留换行
  return esc(s).replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" rel="nofollow noopener" target="_blank">$1</a>').replace(/\n/g, "<br>");
}
function fmtTime(t) {
  if (!t) return "";
  const d = new Date(t + 8 * 3600e3), p = (n) => String(n).padStart(2, "0");
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
}
const rand = (n = 16) => [...crypto.getRandomValues(new Uint8Array(n))].map((b) => b.toString(16).padStart(2, "0")).join("");
const code6 = () => { const A = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; return [...crypto.getRandomValues(new Uint8Array(8))].map((b) => A[b % A.length]).join(""); };

async function hashPw(pw, salt) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: new TextEncoder().encode(salt), iterations: 100000 }, key, 256);
  return [...new Uint8Array(bits)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
function eqConst(a, b) { if (a.length !== b.length) return false; let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i); return r === 0; }

function cookie(req, k) { const m = (req.headers.get("Cookie") || "").match(new RegExp("(?:^|;\\s*)" + k + "=([^;]+)")); return m ? m[1] : null; }
const redirect = (to, headers = {}) => new Response(null, { status: 303, headers: { Location: to, ...headers } });

async function limited(env, key, max, ms) { // 每 key 在 ms 内最多 max 次
  const t = now(), r = await env.DB.prepare("SELECT n, until FROM hits WHERE k=?").bind(key).first();
  if (!r || r.until < t) { await env.DB.prepare("INSERT OR REPLACE INTO hits (k, n, until) VALUES (?, 1, ?)").bind(key, t + ms).run(); return false; }
  if (r.n >= max) return true;
  await env.DB.prepare("UPDATE hits SET n=n+1 WHERE k=?").bind(key).run(); return false;
}

async function currentUser(req, env) {
  const tok = cookie(req, "syq");
  if (!tok) return null;
  return await env.DB.prepare("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?").bind(tok, now()).first();
}
const isMember = (u) => u && (u.role === "member" || u.role === "admin");
const isAdmin = (u) => u && u.role === "admin";

// ---------- 页面外壳 ----------
const CSS = `:root{--bg:#f2f1ea;--paper:#fbfaf5;--fg:#1f2421;--mute:#69716b;--accent:#23503f;--accent2:#8a5a2c;--line:#dcded2;--red:#b03a2e}
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
code{background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:1px 6px}`;

function page(title, body, u) {
  const nav = u
    ? `<span class="mute">${esc(u.name)}${u.role === "guest" ? "（未入会）" : ""}</span>${u.role === "guest" ? '<a href="/invite">用邀请码入会</a>' : ""}${isAdmin(u) ? '<a href="/admin">管理</a>' : ""}<form method="post" action="/logout" style="display:inline"><button class="btn ghost" style="margin:0;padding:0 12px">退出</button></form>`
    : `<a href="/login">登录</a><a href="/register">注册</a>`;
  return new Response(`<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>${esc(title)}｜${SITE}</title><style>${CSS}</style></head><body>
<header><div class="w"><a class="brand" href="/">${SITE}</a><nav>${nav}</nav></div></header><main class="w">${body}</main>
<footer>一孔录 · 书友圈不公开，只给书院书友。上官有理、孔照今是一孔录原创角色，由智器主持；读法以“一孔按”为准。<br><a href="https://yikonglu.com/shuyuan.html">一孔书院</a> · 别贴真名、手机号、单位。</footer></body></html>`,
    { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Frame-Options": "DENY", "Referrer-Policy": "same-origin" } });
}
const notFound = (u) => { const r = page("找不到", `<h1>找不到这一页</h1><p><a href="/">回书友圈</a></p>`, u); return new Response(r.body, { status: 404, headers: r.headers }); };
function avatar(u) {
  return u.avatar ? `<img class="av" src="${esc(u.avatar)}" alt="">` : `<span class="av">${esc((u.name || "?").slice(0, 1))}</span>`;
}
const whoTag = (u) => (u.tag ? `<span class="tag">${esc(u.tag)}</span>` : u.role === "admin" ? '<span class="tag">一孔录</span>' : "");

// ---------- 页面 ----------
async function home(env, u) {
  const { results: boards } = await env.DB.prepare(
    "SELECT b.*, (SELECT COUNT(*) FROM threads t WHERE t.board_id=b.id) n, (SELECT MAX(last_at) FROM threads t WHERE t.board_id=b.id) last FROM boards b ORDER BY sort").all();
  const li = boards.map((b) => `<li><a class="t" href="/b/${b.slug}">${esc(b.name)}</a>${b.members_only ? '<span class="lock">会员</span>' : ""}<span class="mute" style="flex-basis:100%">${esc(b.descr)}</span><span class="m">${b.n} 帖${b.last ? " · " + fmtTime(b.last) : ""}</span></li>`).join("");
  const hello = !u
    ? `<div class="box">书友圈只给一孔书院的书友。先<a href="/register">注册</a>（只要网名和密码），再用入会邀请码进会员区。“门口”谁都能看。</div>`
    : u.role === "guest" ? `<div class="box">你已注册，还没入会。拿到邀请码后，<a href="/invite">在这里入会</a>。</div>` : "";
  return page("首页", `<h1>${SITE}</h1><p class="mute">把读同一部书、口味相近的人聚在一起：读到哪聊到哪，有人接话，有人较真。</p>${hello}<ul class="list">${li}</ul>`, u);
}

async function board(env, u, slug) {
  const b = await env.DB.prepare("SELECT * FROM boards WHERE slug=?").bind(slug).first();
  if (!b) return notFound(u);
  if (b.members_only && !isMember(u)) return page(b.name, `<h1>${esc(b.name)}</h1><div class="box">这一区只给书院会员。${u ? '<a href="/invite">用邀请码入会</a>' : '<a href="/login">登录</a>或<a href="/register">注册</a>'}。</div>`, u);
  const { results } = await env.DB.prepare(
    "SELECT t.*, u.name uname FROM threads t JOIN users u ON u.id=t.user_id WHERE board_id=? ORDER BY pinned DESC, last_at DESC LIMIT 100").bind(b.id).all();
  const li = results.map((t) => `<li>${t.pinned ? '<span class="pin">置顶</span>' : ""}${t.answered ? '<span class="ans">已答</span>' : ""}<a class="t" href="/t/${t.id}">${esc(t.title)}</a><span class="m">${esc(t.uname)} · ${t.replies} 回 · ${fmtTime(t.last_at)}</span></li>`).join("") || '<li class="mute">还没有帖子。</li>';
  const can = u && (isMember(u) || !b.members_only);
  return page(b.name, `<p class="mute"><a href="/">书友圈</a> ›</p><h1>${esc(b.name)}</h1><p class="mute">${esc(b.descr)}</p>${can ? `<a class="btn" href="/new?b=${b.slug}">发帖</a>` : ""}<ul class="list">${li}</ul>`, u);
}

async function thread(env, u, id, msg = "") {
  const t = await env.DB.prepare("SELECT t.*, b.slug, b.name bname, b.members_only FROM threads t JOIN boards b ON b.id=t.board_id WHERE t.id=?").bind(id).first();
  if (!t) return notFound(u);
  if (t.members_only && !isMember(u)) return page(t.bname, `<h1>${esc(t.bname)}</h1><div class="box">这一帖在会员区。${u ? '<a href="/invite">用邀请码入会</a>' : '<a href="/login">登录</a>'}。</div>`, u);
  const { results } = await env.DB.prepare("SELECT p.*, u.name, u.role, u.avatar, u.tag FROM posts p JOIN users u ON u.id=p.user_id WHERE thread_id=? ORDER BY p.id").bind(id).all();
  const ps = results.map((p, i) => `<div class="post" id="p${p.id}">${avatar(p)}<div><div><span class="who">${esc(p.name)}</span>${whoTag(p)} <span class="mute">${i ? "#" + i + " · " : ""}${fmtTime(p.created)}</span></div><div class="body">${fmtBody(p.body)}</div></div></div>`).join("");
  const adm = isAdmin(u) ? `<form method="post" action="/t/${id}/flag" class="mute" style="margin-top:6px"><button name="f" value="pinned" class="btn ghost" style="padding:2px 12px">${t.pinned ? "取消置顶" : "置顶"}</button> <button name="f" value="answered" class="btn ghost" style="padding:2px 12px">${t.answered ? "取消已答" : "标已答"}</button></form>` : "";
  const canReply = u && (isMember(u) || !t.members_only);
  const asSel = isAdmin(u) ? await asSelect(env, u) : "";
  const form = canReply ? `<form method="post" action="/t/${id}/reply" class="box"><label>回复</label><textarea name="body" required maxlength="8000"></textarea>${asSel}<button>发出</button></form>` : u ? "" : `<p class="mute"><a href="/login">登录</a>后可回复。</p>`;
  return page(t.title, `<p class="mute"><a href="/">书友圈</a> › <a href="/b/${t.slug}">${esc(t.bname)}</a>${t.chapter ? ` · <a href="${chUrl(t.chapter)}">论语 ${esc(t.chapter)} 原文</a>` : ""}</p><h1>${t.answered ? '<span class="ans">已答</span> ' : ""}${esc(t.title)}</h1>${adm}${msg}${ps}${form}`, u);
}

async function asSelect(env, u) { // 管理员可用角色账号发
  const { results } = await env.DB.prepare("SELECT id, name FROM users WHERE role='char' ORDER BY id").all();
  return `<label>以谁的身份发</label><select name="as"><option value="">${esc(u.name)}（自己）</option>${results.map((c) => `<option value="${c.id}">${esc(c.name)}（原创角色）</option>`).join("")}</select>`;
}
async function resolveAs(env, u, as) {
  if (!as || !isAdmin(u)) return u.id;
  const c = await env.DB.prepare("SELECT id FROM users WHERE id=? AND role='char'").bind(+as).first();
  return c ? c.id : u.id;
}

function authForm(kind, err = "", name = "") {
  const reg = kind === "register";
  return `<h1>${reg ? "注册" : "登录"}</h1>${err ? `<p class="err">${esc(err)}</p>` : ""}<form method="post" class="box">
<label>网名（2—16 字，别用真名）</label><input type="text" name="name" value="${esc(name)}" required minlength="2" maxlength="16" autocomplete="username">
<label>密码（至少 8 位）</label><input type="password" name="pw" required minlength="8" autocomplete="${reg ? "new-password" : "current-password"}">
${reg ? '<label>入会邀请码（有就填，没有可以先空着）</label><input type="text" name="code" autocomplete="off"><input class="hp" name="website" tabindex="-1" autocomplete="off">' : ""}
<button>${reg ? "注册" : "登录"}</button></form>
<p class="mute">${reg ? '不要邮箱、不要手机号。忘了密码，找上官有理要一个重置码，在<a href="/reset">这里</a>改。' : '还没有账号？<a href="/register">注册</a>。忘了密码？<a href="/reset">用重置码改</a>。'}</p>`;
}

async function startSession(env, uid) {
  const tok = rand(24);
  await env.DB.prepare("INSERT INTO sessions (token, user_id, expires) VALUES (?, ?, ?)").bind(tok, uid, now() + 60 * DAY).run();
  return `syq=${tok}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${60 * 86400}`;
}

async function useInvite(env, uid, code, kinds) {
  code = String(code || "").trim().toUpperCase();
  if (!code) return null;
  if (env.ADMIN_CODE && kinds.includes("admin") && code === String(env.ADMIN_CODE).toUpperCase()) { // 首位管理员：部署时 --var ADMIN_CODE:… 给一次性码，已有管理员就失效
    const a = await env.DB.prepare("SELECT 1 FROM users WHERE role='admin'").first();
    return a ? null : { kind: "admin" };
  }
  const inv = await env.DB.prepare("SELECT * FROM invites WHERE code=? AND used_by IS NULL").bind(code).first();
  if (!inv || !kinds.includes(inv.kind)) return null;
  const r = await env.DB.prepare("UPDATE invites SET used_by=?, used_at=? WHERE code=? AND used_by IS NULL").bind(uid, now(), code).run();
  return r.meta.changes ? inv : null;
}

// ---------- 定时帖 ----------
async function runScheduled(env) {
  const { results } = await env.DB.prepare("SELECT * FROM scheduled WHERE done=0 AND run_at<=? ORDER BY run_at LIMIT 20").bind(now()).all();
  for (const s of results) {
    const t = now();
    if (s.thread_id) {
      await env.DB.prepare("INSERT INTO posts (thread_id, user_id, body, created) VALUES (?, ?, ?, ?)").bind(s.thread_id, s.as_user, s.body, t).run();
      await env.DB.prepare("UPDATE threads SET replies=replies+1, last_at=? WHERE id=?").bind(t, s.thread_id).run();
    } else {
      const b = await env.DB.prepare("SELECT id FROM boards WHERE slug=?").bind(s.board_slug).first();
      if (b) await newThread(env, b.id, s.as_user, s.title || "（无题）", s.body, null);
    }
    await env.DB.prepare("UPDATE scheduled SET done=1 WHERE id=?").bind(s.id).run();
  }
  await env.DB.prepare("DELETE FROM sessions WHERE expires<?").bind(now()).run();
  await env.DB.prepare("DELETE FROM hits WHERE until<?").bind(now()).run();
}
async function newThread(env, boardId, uid, title, body, chapter) {
  const t = now();
  const r = await env.DB.prepare("INSERT INTO threads (board_id, user_id, title, chapter, created, last_at) VALUES (?, ?, ?, ?, ?, ?)").bind(boardId, uid, title, chapter, t, t).run();
  const id = r.meta.last_row_id;
  await env.DB.prepare("INSERT INTO posts (thread_id, user_id, body, created) VALUES (?, ?, ?, ?)").bind(id, uid, body, t).run();
  return id;
}

// ---------- 管理 ----------
async function admin(env, u, msg = "") {
  const { results: inv } = await env.DB.prepare("SELECT i.*, u.name uname FROM invites i LEFT JOIN users u ON u.id=i.used_by ORDER BY created DESC LIMIT 30").all();
  const { results: sch } = await env.DB.prepare("SELECT s.*, u.name FROM scheduled s JOIN users u ON u.id=s.as_user WHERE done=0 ORDER BY run_at LIMIT 30").all();
  const { results: boards } = await env.DB.prepare("SELECT slug, name FROM boards ORDER BY sort").all();
  const { results: chars } = await env.DB.prepare("SELECT id, name FROM users WHERE role='char' ORDER BY id").all();
  const n = await env.DB.prepare("SELECT SUM(role='member') m, SUM(role='guest') g FROM users").first();
  const invRows = inv.map((i) => `<li><code>${esc(i.code)}</code> ${i.kind === "member" ? "入会" : i.kind === "admin" ? "管理" : "重置"}${i.for_name ? " · 给 " + esc(i.for_name) : ""}${i.note ? " · " + esc(i.note) : ""}<span class="m">${i.used_by ? "已用：" + esc(i.uname) : "未用"}</span></li>`).join("");
  const schRows = sch.map((s) => `<li>${fmtTime(s.run_at)} · ${esc(s.name)} · ${s.thread_id ? "回帖 #" + s.thread_id : esc(s.board_slug) + "：" + esc(s.title)}<span class="m">${esc(String(s.body).slice(0, 30))}…</span></li>`).join("") || '<li class="mute">没有待发的。</li>';
  return page("管理", `<h1>管理</h1>${msg}<p class="mute">会员 ${n.m || 0} 人，已注册未入会 ${n.g || 0} 人。</p>
<h2>发邀请码</h2><form method="post" action="/admin/invite" class="box"><label>种类</label><select name="kind"><option value="member">入会（付费后发给书友）</option><option value="reset">重置密码（必须填网名）</option></select>
<label>给谁（网名，可空）</label><input type="text" name="for_name"><label>备注（可空，如“知识星球 11-09”）</label><input type="text" name="note"><label>一次发几个</label><input type="text" name="n" value="1"><button>生成</button></form>
<ul class="list">${invRows}</ul>
<h2>角色定时帖</h2><form method="post" action="/admin/schedule" class="box"><label>角色</label><select name="as">${chars.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("")}</select>
<label>发到哪个区（开新帖）</label><select name="board">${boards.map((b) => `<option value="${b.slug}">${esc(b.name)}</option>`).join("")}</select>
<label>或回复到帖子编号（填了就不开新帖）</label><input type="text" name="thread"><label>标题（开新帖时用）</label><input type="text" name="title" maxlength="80">
<label>正文</label><textarea name="body" required></textarea><label>什么时候发（北京时间）</label><input type="datetime-local" name="at" required><button>排上</button></form>
<ul class="list">${schRows}</ul>`, u);
}

// ---------- 路由 ----------
const App = {
  async fetch(req, env) {
    const url = new URL(req.url), path = url.pathname, M = req.method;
    if (M === "POST") { // 跨站提交一律拒
      const o = req.headers.get("Origin");
      if (o && o !== url.origin) return new Response("bad origin", { status: 403 });
    }
    const u = await currentUser(req, env);
    const ip = req.headers.get("CF-Connecting-IP") || "x";
    const form = M === "POST" ? await req.formData() : null;
    const f = (k) => String(form?.get(k) ?? "").trim();

    if (path === "/" && M === "GET") return home(env, u);
    let m;
    if ((m = path.match(/^\/b\/([a-z0-9-]+)$/)) && M === "GET") return board(env, u, m[1]);
    if ((m = path.match(/^\/t\/(\d+)$/)) && M === "GET") return thread(env, u, +m[1]);
    if ((m = path.match(/^\/c\/(\d{1,2}\.\d{1,2})$/)) && M === "GET" && +m[1].split(".")[0] <= 20) { // 章页直达：有讨论帖就跳过去，没有就在共读区发起
      const t = await env.DB.prepare("SELECT id FROM threads WHERE chapter=? ORDER BY id LIMIT 1").bind(m[1]).first();
      return redirect(t ? `/t/${t.id}` : `/new?b=lunyu&c=${m[1]}`);
    }

    if (path === "/register") {
      if (M === "GET") return page("注册", authForm("register"), u);
      if (f("website")) return redirect("/");
      if (await limited(env, "reg:" + ip, 5, DAY)) return page("注册", authForm("register", "今天注册次数太多，明天再来。"), u);
      const name = f("name"), pw = String(form.get("pw") || "");
      if (name.length < 2 || name.length > 16 || /[<>\s]/.test(name)) return page("注册", authForm("register", "网名要 2—16 个字，不能有空格。", name), u);
      if (pw.length < 8) return page("注册", authForm("register", "密码至少 8 位。", name), u);
      if (await env.DB.prepare("SELECT 1 FROM users WHERE lower(name)=lower(?)").bind(name).first()) return page("注册", authForm("register", "这个网名有人用了，换一个。", name), u);
      const salt = rand(16), h = await hashPw(pw, salt);
      const r = await env.DB.prepare("INSERT INTO users (name, pw, salt, role, created) VALUES (?, ?, ?, 'guest', ?)").bind(name, h, salt, now()).run();
      const uid = r.meta.last_row_id, inv = await useInvite(env, uid, f("code"), ["member", "admin"]);
      if (inv) await env.DB.prepare("UPDATE users SET role=? WHERE id=?").bind(inv.kind === "admin" ? "admin" : "member", uid).run();
      return redirect("/", { "Set-Cookie": await startSession(env, uid) });
    }
    if (path === "/login") {
      if (M === "GET") return page("登录", authForm("login"), u);
      if (await limited(env, "login:" + ip, 20, 3600e3)) return page("登录", authForm("login", "试太多次了，一小时后再来。"), u);
      const name = f("name"), pw = String(form.get("pw") || "");
      const x = await env.DB.prepare("SELECT * FROM users WHERE lower(name)=lower(?) AND pw IS NOT NULL").bind(name).first();
      if (!x || !eqConst(await hashPw(pw, x.salt), x.pw)) return page("登录", authForm("login", "网名或密码不对。", name), u);
      return redirect("/", { "Set-Cookie": await startSession(env, x.id) });
    }
    if (path === "/logout" && M === "POST") {
      const tok = cookie(req, "syq"); if (tok) await env.DB.prepare("DELETE FROM sessions WHERE token=?").bind(tok).run();
      return redirect("/", { "Set-Cookie": "syq=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax" });
    }
    if (path === "/reset") {
      const fm = (e = "") => `<h1>用重置码改密码</h1>${e}<form method="post" class="box"><label>网名</label><input type="text" name="name" required><label>重置码（找上官有理要）</label><input type="text" name="code" required><label>新密码（至少 8 位）</label><input type="password" name="pw" required minlength="8"><button>改密码</button></form>`;
      if (M === "GET") return page("重置密码", fm(), u);
      if (await limited(env, "reset:" + ip, 10, 3600e3)) return page("重置密码", fm('<p class="err">试太多次了。</p>'), u);
      const name = f("name"), pw = String(form.get("pw") || ""), code = f("code").toUpperCase();
      const x = await env.DB.prepare("SELECT * FROM users WHERE lower(name)=lower(?) AND pw IS NOT NULL").bind(name).first();
      const inv = x && (await env.DB.prepare("SELECT * FROM invites WHERE code=? AND kind='reset' AND used_by IS NULL AND lower(for_name)=lower(?)").bind(code, name).first());
      if (!inv || pw.length < 8) return page("重置密码", fm('<p class="err">网名、重置码对不上，或密码太短。</p>'), u);
      await useInvite(env, x.id, code, ["reset"]);
      const salt = rand(16);
      await env.DB.prepare("UPDATE users SET pw=?, salt=? WHERE id=?").bind(await hashPw(pw, salt), salt, x.id).run();
      await env.DB.prepare("DELETE FROM sessions WHERE user_id=?").bind(x.id).run();
      return redirect("/login");
    }

    if (!u) return M === "GET" ? notFound(u) : redirect("/login");

    if (path === "/invite") {
      const fm = (e = "") => `<h1>用邀请码入会</h1>${e}<form method="post" class="box"><label>邀请码</label><input type="text" name="code" required><button>入会</button></form><p class="mute">邀请码在付费后由上官有理发给你，一个码只能用一次。</p>`;
      if (M === "GET") return page("入会", fm(), u);
      if (await limited(env, "inv:" + u.id, 10, 3600e3)) return page("入会", fm('<p class="err">试太多次了。</p>'), u);
      const inv = await useInvite(env, u.id, f("code"), ["member", "admin"]);
      if (!inv) return page("入会", fm('<p class="err">这个码不对，或已经用过。</p>'), u);
      if (u.role !== "admin") await env.DB.prepare("UPDATE users SET role=? WHERE id=?").bind(inv.kind === "admin" ? "admin" : "member", u.id).run();
      return redirect("/");
    }
    if (path === "/new") {
      const slug = url.searchParams.get("b") || f("b"), b = await env.DB.prepare("SELECT * FROM boards WHERE slug=?").bind(slug).first();
      if (!b) return notFound(u);
      if (b.members_only && !isMember(u)) return redirect("/invite");
      const ch = (url.searchParams.get("c") || f("c")).match(/^\d{1,2}\.\d{1,2}$/)?.[0] || "";
      if (M === "GET") return page("发帖", `<p class="mute"><a href="/b/${b.slug}">${esc(b.name)}</a> ›</p><h1>发帖</h1><form method="post" class="box"><input type="hidden" name="b" value="${b.slug}"><input type="hidden" name="c" value="${ch}">
<label>标题</label><input type="text" name="title" required maxlength="80" value="${ch ? "论语 " + ch : ""}"><label>正文</label><textarea name="body" required maxlength="8000"></textarea>${isAdmin(u) ? await asSelect(env, u) : ""}<button>发出</button></form>`, u);
      if (await limited(env, "post:" + u.id, 30, 3600e3)) return page("发帖", `<p class="err">发得太快了，歇一会儿。</p>`, u);
      const title = f("title").slice(0, 80), body = f("body").slice(0, 8000);
      if (!title || !body) return redirect(`/new?b=${b.slug}`);
      const id = await newThread(env, b.id, await resolveAs(env, u, f("as")), title, body, ch || null);
      return redirect(`/t/${id}`);
    }
    if ((m = path.match(/^\/t\/(\d+)\/reply$/)) && M === "POST") {
      const t = await env.DB.prepare("SELECT t.id, b.members_only FROM threads t JOIN boards b ON b.id=t.board_id WHERE t.id=?").bind(+m[1]).first();
      if (!t) return notFound(u);
      if (t.members_only && !isMember(u)) return redirect("/invite");
      if (await limited(env, "post:" + u.id, 30, 3600e3)) return thread(env, u, t.id, '<p class="err">发得太快了，歇一会儿。</p>');
      const body = f("body").slice(0, 8000);
      if (body) {
        const ts = now();
        await env.DB.prepare("INSERT INTO posts (thread_id, user_id, body, created) VALUES (?, ?, ?, ?)").bind(t.id, await resolveAs(env, u, f("as")), body, ts).run();
        await env.DB.prepare("UPDATE threads SET replies=replies+1, last_at=? WHERE id=?").bind(ts, t.id).run();
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
        if (kind === "reset" && !f("for_name")) return admin(env, u, '<p class="err">重置码必须填网名。</p>');
        for (let i = 0; i < n; i++) await env.DB.prepare("INSERT INTO invites (code, kind, for_name, note, created) VALUES (?, ?, ?, ?, ?)").bind(code6(), kind, f("for_name") || null, f("note") || null, now()).run();
        return admin(env, u, `<p class="ok">生成了 ${n} 个。</p>`);
      }
      if (path === "/admin/schedule" && M === "POST") {
        const at = Date.parse(f("at") + ":00+08:00"), tid = parseInt(f("thread")) || null;
        if (!at || !f("body")) return admin(env, u, '<p class="err">时间和正文都要填。</p>');
        await env.DB.prepare("INSERT INTO scheduled (as_user, board_slug, thread_id, title, body, run_at) VALUES (?, ?, ?, ?, ?, ?)").bind(+f("as"), f("board"), tid, f("title") || null, f("body"), at).run();
        return admin(env, u, '<p class="ok">排上了，到点自动发（每 10 分钟查一次）。</p>');
      }
    }
    return notFound(u);
  },
};

// ---------- 存储：一个 SQLite Durable Object（不用 D1，现有 API 令牌就能部署）----------
import SCHEMA from "../schema.sql";
class Stmt {
  constructor(sql, q) { this.sql = sql; this.q = q; this.a = []; }
  bind(...a) { this.a = a; return this; }
  first() { const r = this.sql.exec(this.q, ...this.a).toArray(); return r[0] || null; }
  all() { return { results: this.sql.exec(this.q, ...this.a).toArray() }; }
  run() {
    const c = this.sql.exec(this.q, ...this.a); c.toArray();
    return { meta: { changes: c.rowsWritten, last_row_id: this.sql.exec("SELECT last_insert_rowid() AS id").one().id } };
  }
}
export class Syq {
  constructor(state, env) {
    const sql = state.storage.sql;
    for (const q of SCHEMA.split(/;\s*\n/).map((x) => x.replace(/^\s*--.*$/gm, "").trim()).filter(Boolean)) sql.exec(q);
    this.env = { ...env, DB: { prepare: (q) => new Stmt(sql, q) } };
  }
  async fetch(req) {
    if (new URL(req.url).pathname === "/__cron") { await runScheduled(this.env); return new Response("ok"); }
    return App.fetch(req, this.env);
  }
}
const hub = (env) => env.SYQ.get(env.SYQ.idFromName("main"));
export default {
  async fetch(req, env) {
    if (new URL(req.url).pathname === "/__cron") return new Response("not found", { status: 404 });
    return hub(env).fetch(req);
  },
  async scheduled(_ev, env) { await hub(env).fetch("https://internal/__cron"); },
};
