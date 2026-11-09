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
    go: "接着讀", last: "上次讀到", prog: "已讀 {n} / {t} 章", priv: "一孔錄無需登錄，不取隱私，不打擾。", move: "遷移記錄", mvh: "在這台裝置生成一個專屬鏈接，到另一台手機或電腦的瀏覽器裡打開，讀到哪、讀過哪些章就都帶過去了。不用登錄。", cpy: "複製鏈接", snd: "發給自己…", cls2: "收起", clear: "清除記錄", copied: "鏈接已複製。到另一台裝置的瀏覽器裡貼上打開即可。", imported: "閱讀記錄已導入。", ago: ["剛剛", "{n} 分鐘前", "{n} 小時前", "{n} 天前"], sure: "清除這台裝置上的閱讀記錄？", stk: "已連讀 {n} 天", std: "今天讀一章就接上", plan: "百日計劃 · 第 {d} 天 · 今天讀 {r}"
  } : {
    go: "接着读", last: "上次读到", prog: "已读 {n} / {t} 章", priv: "一孔录无需登录，不取隐私，不打扰。", move: "迁移记录", mvh: "在这台设备生成一个专属链接，到另一台手机或电脑的浏览器里打开，读到哪、读过哪些章就都带过去了。不用登录。", cpy: "复制链接", snd: "发给自己…", cls2: "收起", clear: "清除记录", copied: "链接已复制。到另一台设备的浏览器里粘贴打开即可。", imported: "阅读记录已导入。", ago: ["刚刚", "{n} 分钟前", "{n} 小时前", "{n} 天前"], sure: "清除这台设备上的阅读记录？", stk: "已连读 {n} 天", std: "今天读一章就接上", plan: "百日计划 · 第 {d} 天 · 今天读 {r}"
  }) : (({
    ja: { go: "続きを読む", last: "前回の続き", prog: "{n} / {t} 章 読了", priv: "ログイン不要、個人情報は取らず、邪魔もしません。", move: "記録を移す", mvh: "この端末で専用リンクを作ります。別のスマホやパソコンのブラウザで開けば、どこまで読んだか、どの章を読んだかがそのまま移ります。ログイン不要です。", cpy: "リンクをコピー", snd: "自分に送る…", cls2: "閉じる", clear: "記録を消す", copied: "リンクをコピーしました。別の端末のブラウザに貼り付けて開いてください。", imported: "読書記録を取り込みました。", ago: ["たった今", "{n} 分前", "{n} 時間前", "{n} 日前"], sure: "この端末の読書記録を消しますか？", stk: "{n} 日続けて読書中", std: "今日一章読めば続きます" },
    ko: { go: "이어 읽기", last: "마지막으로 읽은 곳", prog: "{t}장 중 {n}장 읽음", priv: "로그인 없이, 개인정보 없이, 방해 없이.", move: "기록 옮기기", mvh: "이 기기에서 전용 링크를 만듭니다. 다른 휴대폰이나 컴퓨터의 브라우저에서 열면 어디까지, 어느 장을 읽었는지 그대로 옮겨집니다. 로그인은 필요 없습니다.", cpy: "링크 복사", snd: "나에게 보내기…", cls2: "닫기", clear: "기록 지우기", copied: "링크를 복사했습니다. 다른 기기의 브라우저에 붙여 넣어 여세요.", imported: "읽기 기록을 가져왔습니다.", ago: ["방금", "{n}분 전", "{n}시간 전", "{n}일 전"], sure: "이 기기의 읽기 기록을 지울까요?", stk: "{n}일째 이어 읽는 중", std: "오늘 한 장 읽으면 이어집니다" },
    fr: { go: "Reprendre", last: "Dernière lecture", prog: "{n} chapitres lus sur {t}", priv: "Sans compte, sans données personnelles, sans dérangement.", move: "Transférer", mvh: "Cela crée un lien privé. Ouvrez-le dans le navigateur de votre autre téléphone ou ordinateur : votre progression vous suit. Aucun compte.", cpy: "Copier le lien", snd: "M’envoyer…", cls2: "Fermer", clear: "Effacer", copied: "Lien copié. Ouvrez-le sur votre autre appareil pour y retrouver votre progression.", imported: "Progression importée.", ago: ["à l’instant", "il y a {n} min", "il y a {n} h", "il y a {n} j"], sure: "Effacer la progression sur cet appareil ?", stk: "{n} jours de lecture d’affilée", std: "lisez un chapitre aujourd’hui pour continuer" },
    es: { go: "Seguir leyendo", last: "Última lectura", prog: "{n} de {t} capítulos leídos", priv: "Sin registro, sin datos personales, sin molestias.", move: "Llevar progreso", mvh: "Esto crea un enlace privado. Ábrelo en el navegador de tu otro teléfono u ordenador y tu progreso irá contigo. Sin registro.", cpy: "Copiar enlace", snd: "Enviármelo…", cls2: "Cerrar", clear: "Borrar", copied: "Enlace copiado. Ábrelo en tu otro dispositivo para llevar tu progreso.", imported: "Progreso importado.", ago: ["ahora mismo", "hace {n} min", "hace {n} h", "hace {n} d"], sure: "¿Borrar el progreso de este dispositivo?", stk: "{n} días seguidos leyendo", std: "lee un capítulo hoy para seguir" },
    de: { go: "Weiterlesen", last: "Zuletzt gelesen", prog: "{n} von {t} Kapiteln gelesen", priv: "Keine Anmeldung, keine persönlichen Daten, keine Störungen.", move: "Fortschritt mitnehmen", mvh: "Das erzeugt einen privaten Link. Öffne ihn im Browser deines anderen Handys oder Computers, und dein Fortschritt kommt mit. Keine Anmeldung.", cpy: "Link kopieren", snd: "An mich senden…", cls2: "Schließen", clear: "Löschen", copied: "Link kopiert. Öffne ihn auf deinem anderen Gerät, um den Fortschritt mitzunehmen.", imported: "Lesefortschritt übernommen.", ago: ["gerade eben", "vor {n} Min.", "vor {n} Std.", "vor {n} Tagen"], sure: "Lesefortschritt auf diesem Gerät löschen?", stk: "{n} Tage in Folge gelesen", std: "heute ein Kapitel lesen, dann geht es weiter" },
    vi: { go: "Đọc tiếp", last: "Lần trước đọc đến", prog: "Đã đọc {n} / {t} chương", priv: "Không cần đăng nhập, không lấy dữ liệu cá nhân, không làm phiền.", move: "Chuyển tiến độ", mvh: "Tạo một đường link riêng trên thiết bị này. Mở nó bằng trình duyệt trên điện thoại hoặc máy tính khác, tiến độ đọc sẽ đi theo. Không cần đăng nhập.", cpy: "Sao chép link", snd: "Gửi cho mình…", cls2: "Đóng", clear: "Xóa", copied: "Đã sao chép link. Mở nó trên thiết bị khác để mang tiến độ theo.", imported: "Đã nhập tiến độ đọc.", ago: ["vừa xong", "{n} phút trước", "{n} giờ trước", "{n} ngày trước"], sure: "Xóa tiến độ đọc trên thiết bị này?", stk: "Đã đọc liền {n} ngày", std: "đọc một chương hôm nay để nối tiếp" },
    id: { go: "Lanjut membaca", last: "Terakhir dibaca", prog: "{n} dari {t} bab dibaca", priv: "Tanpa login, tanpa data pribadi, tanpa gangguan.", move: "Pindahkan progres", mvh: "Ini membuat tautan pribadi. Buka di peramban ponsel atau komputer lain, dan progres bacaan ikut pindah. Tanpa login.", cpy: "Salin tautan", snd: "Kirim ke diri sendiri…", cls2: "Tutup", clear: "Hapus", copied: "Tautan disalin. Buka di perangkat lain untuk membawa progres Anda.", imported: "Progres bacaan diimpor.", ago: ["baru saja", "{n} mnt lalu", "{n} jam lalu", "{n} hari lalu"], sure: "Hapus progres bacaan di perangkat ini?", stk: "{n} hari berturut-turut membaca", std: "baca satu bab hari ini agar tersambung" },
    ru: { go: "Читать дальше", last: "Последнее прочитанное", prog: "Прочитано глав: {n} из {t}", priv: "Без входа, без личных данных, без навязчивости.", move: "Перенести прогресс", mvh: "Будет создана личная ссылка. Откройте её в браузере на другом телефоне или компьютере — прогресс перенесётся. Вход не нужен.", cpy: "Скопировать ссылку", snd: "Отправить себе…", cls2: "Закрыть", clear: "Очистить", copied: "Ссылка скопирована. Откройте её на другом устройстве, чтобы перенести прогресс.", imported: "Прогресс чтения перенесён.", ago: ["только что", "{n} мин назад", "{n} ч назад", "{n} дн. назад"], sure: "Очистить прогресс чтения на этом устройстве?", stk: "Читаете {n} дн. подряд", std: "прочтите главу сегодня, чтобы не прерывать" }
  })[lang.slice(0, 2)] || {
    go: "Continue reading", last: "Last read", prog: "{n} of {t} chapters read", priv: "No sign-in, no personal data, no interruptions.", move: "Move progress", mvh: "This makes a private link. Open it in a browser on your other phone or computer and your progress comes along. No sign-in.", cpy: "Copy link", snd: "Send to myself…", cls2: "Close", clear: "Clear", copied: "Link copied. Open it on your other device to bring your progress along.", imported: "Reading progress imported.", ago: ["just now", "{n} min ago", "{n} h ago", "{n} d ago"], sure: "Clear reading progress on this device?", stk: "{n}-day reading streak", std: "read a chapter today to keep it going"
  });
  function load() { try { return JSON.parse(localStorage.getItem(K) || "null") || { b: {} } } catch (e) { return null } }
  function save(s) { try { localStorage.setItem(K, JSON.stringify(s)); return true } catch (e) { return false } }
  function dstr(t) { return t.getFullYear() + "-" + ("0" + (t.getMonth() + 1)).slice(-2) + "-" + ("0" + t.getDate()).slice(-2) }
  // 连读天数（11-09 主人定）：读过一章就算这天读了；断一天不归零（隔一天接着读，连读照算），连断两天才重新数
  function streak(ds) {
    var set = {}; (ds || []).forEach(function (d) { set[d] = 1 });
    var t = new Date(), today = !!set[dstr(t)], n = 0, miss = 0;
    if (!today) t.setDate(t.getDate() - 1); // 今天还没读不算断
    for (var i = 0; i < 2000; i++) { if (set[dstr(t)]) { n++; miss = 0 } else if (++miss >= 2) break; t.setDate(t.getDate() - 1) }
    return { n: n, today: today };
  }
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
    + ".xdmvp{margin-top:10px;padding:10px 12px;background:var(--bg,#f2f1ea);border-radius:8px;font-size:14px}.xdmvp p{margin:0 0 8px}.xdmvp button{margin:0 8px 0 0;padding:5px 14px;border-radius:99px;border:1px solid #23503f;background:#23503f;color:#fff;font:inherit;cursor:pointer}.xdmvp .xdb2,.xdmvp .xdb3{background:transparent;color:#23503f}"
    + ".xdstk{margin-top:8px;font-size:14px;color:#23503f}.xdstk span{color:var(--mute,#777)}.xdplan{display:block;margin-top:6px;font-size:14px;color:#8a5a2c;text-decoration:none}.xdplan[hidden]{display:none}.xdprog{height:6px;background:var(--line,#dcded2);border-radius:99px;overflow:hidden;margin-top:8px}.xdprog i{display:block;height:100%;background:#8a5a2c}"
    + ".xdseen::after{content:'✓';margin-left:6px;color:#8a5a2c;font-weight:700}.xdtoast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#1f2421;color:#fff;padding:10px 16px;border-radius:10px;font-size:14px;z-index:99;max-width:90vw}"
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
      (j.d || []).forEach(function (d) { S.d = S.d || []; if (S.d.indexOf(d) < 0) S.d.push(d) }); if (j.plan && !S.plan) S.plan = j.plan; if (S.d) S.d.sort();
      save(S); history.replaceState(null, "", location.pathname + location.search); style(); toast(T.imported);
    } catch (e) { }
  }
  function moveUrl() {
    var s = btoa(unescape(encodeURIComponent(JSON.stringify({ b: S.b, d: S.d || [], plan: S.plan })))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    return location.origin + "/" + (pre ? pre + "/" : "") + "#xd=" + s;
  }
  function movePanel(host) { // 先说明，再让人选复制或发送（手机直接弹系统分享会让人看不懂）
    var old = host.querySelector(".xdmvp"); if (old) { old.remove(); return }
    var u = moveUrl(), p = document.createElement("div"); p.className = "xdmvp";
    p.innerHTML = "<p>" + T.mvh + '</p><div><button type="button" class="xdb1">' + T.cpy + "</button>" + (navigator.share ? '<button type="button" class="xdb2">' + T.snd + "</button>" : "") + '<button type="button" class="xdb3">' + T.cls2 + "</button></div>";
    p.querySelector(".xdb1").onclick = function () {
      if (navigator.clipboard) navigator.clipboard.writeText(u).then(function () { toast(T.copied) }, function () { prompt("", u) }); else prompt("", u);
    };
    var b2 = p.querySelector(".xdb2"); if (b2) b2.onclick = function () { navigator.share({ title: "一孔录 · " + T.move, url: u }).catch(function () { }) };
    p.querySelector(".xdb3").onclick = function () { p.remove() };
    host.appendChild(p);
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
      S.b[book] = bs; var td = dstr(new Date()); S.d = S.d || []; if (S.d.indexOf(td) < 0) { S.d.push(td); if (S.d.length > 800) S.d = S.d.slice(-800) } save(S);
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
    var n = (bs.seen || []).length, t = TOTAL[bk] || 0, L = bs.last, name = BOOKN[bk] ? BOOKN[bk][HANT || /^(ja|ko)/.test(lang) ? 1 : ZH ? 0 : 2] : bk;
    var d = document.createElement("div"); d.className = "xdbar";
    d.innerHTML = '<a class="xdgo" href="' + L.p + (bs._y > 0.05 ? "#xd-y" : "") + '"><span>' + T.last + "：" + name + " · " + esc(L.no) + "<br><b>" + esc(L.ti) + '</b></span><span class="xdarr">' + T.go + " →</span></a>"
      + (t ? '<div class="xdprog" title="' + fmt(T.prog, { n: n, t: t }) + '"><i style="width:' + Math.min(100, n / t * 100).toFixed(1) + '%"></i></div>' : "")
      + (function () { var k = streak(S.d); return k.n >= 2 ? '<div class="xdstk"><b>' + fmt(T.stk, { n: k.n }) + "</b>" + (k.today ? "" : "<span> · " + T.std + "</span>") + "</div>" : "" })()
      + '<a class="xdplan" hidden></a>'
      + '<div class="xdmeta"><span>' + ago(L.ts) + (t ? " · " + fmt(T.prog, { n: n, t: t }) : "") + '</span><button type="button" class="xdmv">' + T.move + '</button><button type="button" class="xdcl">' + T.clear + "</button><span>" + T.priv + "</span></div>";
    d.querySelector(".xdmv").onclick = function () { movePanel(d) };
    d.querySelector(".xdcl").onclick = function () { if (confirm(T.sure)) { delete S.b[bk]; save(S); d.remove(); [].forEach.call(document.querySelectorAll(".xdseen"), function (a) { a.classList.remove("xdseen") }) } };
    if (how === "after") where.parentNode.insertBefore(d, where.nextSibling); else where.insertBefore(d, where.firstChild);
    if (bk === "lunyu" && S.plan && S.plan.id === "bairi" && T.plan && window.fetch) fetch("/data/bairi.json").then(function (r) { return r.json() }).then(function (J) {
      var seen = bs.seen || [], d = 0; for (var i = 0; i < J.d.length; i++) if (!J.d[i].every(function (c) { return seen.indexOf(c) >= 0 })) { d = i + 1; break }
      if (!d) return; var nx = J.d[d - 1].filter(function (c) { return seen.indexOf(c) < 0 })[0], pp = nx.split(".");
      var a = document.querySelector(".xdbar .xdplan"); if (!a) return;
      a.href = "/" + (pre ? pre + "/" : "") + "lunyu/" + PIAN[+pp[0] - 1] + "/" + pp[1] + ".html"; a.textContent = fmt(T.plan, { d: d, r: (HANT && J.rt ? J.rt : J.r)[d - 1] }) + " →"; a.hidden = false;
    }).catch(function () { });
  }
  function esc(s) { return String(s || "").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] }) }
  if (document.body.classList.contains("pg-home")) {
    var hero = document.querySelector("section.hero"), lastBk = null, lt = 0;
    for (var b2 in S.b) if (S.b[b2].last && S.b[b2].last.ts > lt) { lt = S.b[b2].last.ts; lastBk = b2 }
    var intro = document.querySelector("main.home section.intro");
    if (lastBk && intro) bar(lastBk, intro, "first"); // 放进首页同一栏，和下面“今天有人读了”、搜索框左右对齐
    else if (hero && lastBk) {
      bar(lastBk, hero, "after");
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
