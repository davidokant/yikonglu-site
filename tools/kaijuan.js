/* 11-15 原页开卷与听读同步（主人定的十一项之 7、9）。
   开卷：点一句，原页小窗跟镜头推到那几列，红框一笔画出来，字一个个从原页取下来落进原文。
   听读：按“音”朗读时，读到哪个字哪个字亮，原页小窗跟着走；可慢速。（跟读 11-15 主人撤掉：中间停顿和网速叠在一起容易漏音）
   数据在 figure 里的 .zjkj（tools/zhuju.py kj_data 出）：z 每字原页框，t 每字起止秒（只有对得准的章才有），k 小句。
   减少动态效果时：不飞字、不推镜头动画，直接到位。 */
(function () {
  var F = document.querySelector('.yuanwen.dz'); if (!F) return;
  var J = null; try { J = JSON.parse(F.querySelector('.zjkj').textContent); } catch (e) { }  // 道德经、三字经只有注音、没有开卷数据
  var Q = F.querySelector('blockquote'), PANE = F.querySelector('.yypane'), NS = 'http://www.w3.org/2000/svg';
  var RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var RE = /([㐀-鿿豈-﫿]|[\ud840-\ud87f][\udc00-\udfff])/;
  // 原文里的汉字逐个包起来，好逐字亮、逐字落
  var Z = [];
  Q.querySelectorAll('.ju').forEach(function (s) {
    var w = document.createTreeWalker(s, 4), ns = []; while (w.nextNode()) ns.push(w.currentNode);
    ns.forEach(function (t) {
      var parts = t.nodeValue.split(RE); if (parts.length < 2) return;
      var fr = document.createDocumentFragment();
      parts.forEach(function (x, i) { if (!x) return; if (i % 2) { var e = document.createElement('i'); e.className = 'zc'; e.textContent = x; Z.push(e); fr.appendChild(e); } else fr.appendChild(document.createTextNode(x)); });
      t.parentNode.replaceChild(fr, t);
    });
  });
  // —— 注音（十一项之 5）：“注”按钮在 拼音 → 注音符号 → 不注 之间切；多音字赭色 ——
  (function () {
    var el = F.querySelector('.zjzy'), Y; if (!el) return; try { Y = JSON.parse(el.textContent); } catch (e) { return; }
    if (Y.length !== Z.length) return;
    Z.forEach(function (e, i) { e.dataset.py = Y[i][0]; e.dataset.bp = Y[i][1]; if (Y[i][2]) e.classList.add('zpoly'); });
    var tools = F.querySelector('.dztools'), yb = F.querySelector('.yibtn'); if (!tools) return;
    var b = document.createElement('button'); b.type = 'button'; b.className = 'yibtn zybtn'; b.textContent = '注'; b.title = '在字上标拼音或注音符号'; b.setAttribute('aria-pressed', 'false');
    tools.insertBefore(b, yb ? yb.nextSibling : tools.querySelector('.ldbtn'));
    var M = ['', 'py', 'bp'], LB = ['注', '拼', '注'], k = 0; try { k = +(localStorage.getItem('yk_zy') || 0) % 3; } catch (e) { }
    function set() { F.classList.remove('zy-py', 'zy-bp'); if (M[k]) F.classList.add('zy-' + M[k]); b.textContent = LB[k]; b.setAttribute('aria-pressed', k ? 'true' : 'false'); try { localStorage.setItem('yk_zy', k); } catch (e) { } }
    b.addEventListener('click', function () { k = (k + 1) % 3; set(); }); set();
  })();
  if (!J || !PANE || Z.length !== J.z.length) return;
  var SV = {}; PANE.querySelectorAll('.yyp').forEach(function (a) { var s = a.querySelector('svg'); if (s) SV[a.dataset.p] = s; });
  var R = J.z.map(function (b, i) {
    var s = b && SV[b[0]]; if (!s) return null;
    var r = document.createElementNS(NS, 'rect'); r.setAttribute('class', 'zcb'); r.setAttribute('x', b[1]); r.setAttribute('y', b[2]); r.setAttribute('width', b[3]); r.setAttribute('height', b[4]); r.setAttribute('rx', 4);
    s.appendChild(r); return r;
  });
  var sentOf = Z.map(function (e) { return +e.closest('.ju').dataset.n; });
  var ease = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  // —— 镜头：改 svg 的 viewBox；先把 svg 的高定住，推近拉远版面不跳 ——
  var cam = {};
  function vb(s) { if (!s._vb0) s._vb0 = s.getAttribute('viewBox').split(/\s+/).map(Number); return s._vb0; }
  function setVB(s, v) { s.setAttribute('viewBox', v.map(function (x) { return x.toFixed(1); }).join(' ')); }
  function look(p, box, dur) {
    var s = SV[p]; if (!s) return; var v0 = vb(s), cur = (s.getAttribute('viewBox') || '').split(/\s+/).map(Number);
    if (!s.style.height) { var h = s.getBoundingClientRect().height; if (!h) return; s.style.height = h + 'px'; s.style.width = '100%'; }
    var ar = s.clientWidth / s.clientHeight || v0[2] / v0[3], t;
    if (box) {
      var pad = Math.max(box[2], box[3]) * .18 + 30, w = Math.max(box[2] + 2 * pad, v0[2] * .38), h2 = Math.max(box[3] + 2 * pad, w / ar);
      w = Math.max(w, h2 * ar); h2 = w / ar;
      if (w > v0[2]) { w = v0[2]; h2 = w / ar; } if (h2 > v0[3]) { h2 = v0[3]; w = Math.min(v0[2], h2 * ar); }
      var x = box[0] + box[2] / 2 - w / 2, y = box[1] + box[3] / 2 - h2 / 2;
      x = Math.min(Math.max(x, v0[0]), v0[0] + v0[2] - w); y = Math.min(Math.max(y, v0[1]), v0[1] + v0[3] - h2);
      t = [x, y, w, h2];
    } else t = v0.slice();
    if (cam[p]) cancelAnimationFrame(cam[p]);
    PANE.classList.toggle('kjzoom', !!box || Object.keys(cam).some(function (k) { return k !== p && SV[k]._z; })); s._z = !!box;
    if (RM || !dur) { setVB(s, t); if (!box) s.style.height = ''; return; }
    var t0 = performance.now();
    (function step(now) { var u = ease(Math.min(1, (now - t0) / dur)); setVB(s, cur.map(function (a, i) { return a + (t[i] - a) * u; })); if (u < 1) cam[p] = requestAnimationFrame(step); else { cam[p] = 0; if (!box) s.style.height = ''; } })(t0);
  }
  function bbox(ix) {  // 一组字在各页的外框，取字最多的那页
    var by = {}; ix.forEach(function (i) { var b = J.z[i]; if (!b) return; (by[b[0]] = by[b[0]] || []).push(b); });
    var p = Object.keys(by).sort(function (a, b) { return by[b].length - by[a].length; })[0]; if (!p) return null;
    var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; by[p].forEach(function (b) { x0 = Math.min(x0, b[1]); y0 = Math.min(y0, b[2]); x1 = Math.max(x1, b[1] + b[3]); y1 = Math.max(y1, b[2] + b[4]); });
    return [p, [x0, y0, x1 - x0, y1 - y0]];
  }
  function home(dur) { Object.keys(SV).forEach(function (p) { if (SV[p]._z) look(p, null, dur); }); PANE.classList.remove('kjzoom'); }
  var hb = document.createElement('button'); hb.type = 'button'; hb.className = 'kjhome'; hb.textContent = '整页'; hb.setAttribute('aria-label', '原页回到整页');
  hb.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); home(450); }); PANE.appendChild(hb);
  // —— 开卷：点一句 → 镜头推近 → 红框画出 → 字落进原文 ——
  var flown = {};
  function draw(n) {
    F.querySelectorAll('.yyp .hl[data-s="' + n + '"]').forEach(function (r) {
      var L = 2 * ((+r.getAttribute('width')) + (+r.getAttribute('height')));
      r.style.strokeDasharray = L; r.style.strokeDashoffset = RM ? 0 : L; r.classList.remove('kjdraw'); void r.getBoundingClientRect(); if (!RM) r.classList.add('kjdraw');
    });
  }
  function fly(ix) {
    if (RM || !Element.prototype.animate) return;
    var gap = Math.min(70, 1500 / ix.length), vh = innerHeight;
    ix.forEach(function (i, k) {
      var r = R[i], e = Z[i]; if (!r) return; var s = r.ownerSVGElement, m = r.getScreenCTM(), img = s.querySelector('image'); if (!m || !img) return;
      var b = J.z[i], sc = m.a, x = m.e + b[1] * sc, y = m.f + b[2] * sc, w = b[3] * sc, h = b[4] * sc, to = e.getBoundingClientRect();
      if (y < -h || y > vh || to.top < 0 || to.bottom > vh || w < 2) return;
      var tl = document.createElement('div'); tl.className = 'kjtile';
      tl.style.cssText = 'left:' + x + 'px;top:' + y + 'px;width:' + w + 'px;height:' + h + 'px;background-image:url("' + (img.getAttribute('href') || img.getAttribute('xlink:href')) + '");background-size:' + (+img.getAttribute('width')) * sc + 'px ' + (+img.getAttribute('height')) * sc + 'px;background-position:' + (-b[1] * sc) + 'px ' + (-b[2] * sc) + 'px';
      document.body.appendChild(tl); e.classList.add('kjw');
      var k2 = Math.max(to.width, to.height) / Math.max(w, h), dx = to.left + to.width / 2 - (x + w / 2), dy = to.top + to.height / 2 - (y + h / 2);
      var a = tl.animate([{ transform: 'translate(0,0) scale(1)', opacity: 1 }, { transform: 'translate(' + dx * .5 + 'px,' + (dy * .5 - 28) + 'px) scale(' + (1 + k2) / 2 + ')', opacity: 1, offset: .55 }, { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(' + k2 + ')', opacity: 0 }],
        { duration: 760, delay: 380 + k * gap, easing: 'cubic-bezier(.3,.1,.2,1)', fill: 'both' });
      a.onfinish = a.oncancel = function () { tl.remove(); e.classList.remove('kjw'); };
    });
  }
  // 第一次来的人看不到“点句”这回事：原文下面放一行提示，点过一次就不再出（11-15 主人）
  var TIP = 'yk_kjtip', tip = null, seenTip = false; try { seenTip = localStorage.getItem(TIP) === '1'; } catch (e) { }
  if (!seenTip) { tip = document.createElement('p'); tip.className = 'kjtip'; tip.innerHTML = '<b>点任意一句试试</b>'; Q.parentNode.insertBefore(tip, Q.nextSibling); }
  function tipDone() { if (tip) { tip.remove(); tip = null; } try { localStorage.setItem(TIP, '1'); } catch (e) { } }
  function open(n) {
    tipDone();
    var ix = []; sentOf.forEach(function (s, i) { if (s === n) ix.push(i); }); if (!ix.length) return;
    var bb = bbox(ix); if (!bb) return;
    look(bb[0], bb[1], 520); draw(n);
    if (!flown[n] && !playing()) { flown[n] = 1; setTimeout(function () { fly(ix); }, RM ? 0 : 40); }
  }
  Q.addEventListener('click', function (e) { var s = e.target.closest('.ju'); if (s && !String(getSelection ? getSelection() : '').trim()) open(+s.dataset.n); });
  Q.addEventListener('keydown', function (e) { if (e.key === 'Enter') { var s = e.target.closest('.ju'); if (s) open(+s.dataset.n); } });
  // —— 听读同步 ——
  var B = F.querySelector('.ldbtn'), A = null;
  function playing() { return A && !A.paused; }
  if (!B || !J.t) return;
  var T = J.t, K = J.k || [[0, T.length]], tools = B.parentNode;
  var mk = function (cls, txt, tip) { var b = document.createElement('button'); b.type = 'button'; b.className = 'ldbtn ' + cls; b.textContent = txt; b.title = tip; b.setAttribute('aria-pressed', 'false'); tools.insertBefore(b, B.nextSibling.nextSibling ? B.nextSibling : null); return b; };
  var slowB = mk('kjslow', '慢', '慢一点读（0.8 倍）');
  tools.insertBefore(slowB, B.nextSibling);
  var slow = false, raf = 0, curK = -1, lastI = -2;
  var kOf = []; K.forEach(function (k, j) { for (var i = k[0]; i < k[1]; i++) kOf[i] = j; });
  slowB.addEventListener('click', function () { slow = !slow; slowB.setAttribute('aria-pressed', slow); if (A) A.playbackRate = slow ? .8 : 1; });
  function paint(done, now) {
    var key = done + '/' + now; if (key === lastI) return; lastI = key;
    Z.forEach(function (e, i) { e.classList.toggle('kjd', i < done); e.classList.toggle('kjn', i === now); if (R[i]) { R[i].classList.toggle('on', i < done); R[i].classList.toggle('now', i === now); } });
    var at = now >= 0 ? now : done < T.length ? done : -1;
    if (at >= 0 && kOf[at] !== curK) { curK = kOf[at]; var ix = []; for (var i = K[curK][0]; i < K[curK][1]; i++) ix.push(i); var bb = bbox(ix); if (bb) look(bb[0], bb[1], 480); }
  }
  function clear() { lastI = -2; curK = -1; Z.forEach(function (e) { e.classList.remove('kjd', 'kjn'); }); R.forEach(function (r) { if (r) r.classList.remove('on', 'now'); }); F.classList.remove('kjplay'); }
  function loop() {
    var t = A.currentTime, idx = -1; for (var i = 0; i < T.length; i++) if (t >= T[i][0]) idx = i; else break;
    var inC = idx >= 0 && t <= T[idx][1] + .12; paint(inC ? idx : idx + 1, inC ? idx : -1);
    if (!A.paused) raf = requestAnimationFrame(loop);
  }
  B.addEventListener('ykaudio', function () {
    A = B.ykA; A.playbackRate = slow ? .8 : 1;
    A.addEventListener('play', function () { if (A.currentTime < .05) clear(); A.playbackRate = slow ? .8 : 1; F.classList.add('kjplay'); cancelAnimationFrame(raf); raf = requestAnimationFrame(loop); });
    A.addEventListener('pause', function () { cancelAnimationFrame(raf); });
    A.addEventListener('ended', function () { paint(T.length, -1); setTimeout(function () { clear(); home(600); }, 1600); });
  });
})();
