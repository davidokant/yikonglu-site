/* 《论语》星图。498 章排成一圈玉璧，人物、同一个问题、场合、别的书是圈里圈外的星。
   数据 /data/xingtu-<语种>.json 由 tools/xingtu.py 出；进入视口才取数据、才开动画；减少动态效果时停成静态。不依赖外部库。 */
(function () {
  const root = document.getElementById('xt'); if (!root || !window.IntersectionObserver || !HTMLCanvasElement.prototype.getContext) return;
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const el = (tag, attrs, ...kids) => { const e = document.createElement(tag); for (const k in attrs || {}) { const v = attrs[k]; if (v == null || v === false) continue; if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v; else if (k === 'html') e.innerHTML = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v); } for (const k of kids.flat()) if (k != null) e.append(k); return e; };
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)), lerp = (a, b, t) => a + (b - a) * t, ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let started = false;
  const io = new IntersectionObserver(es => { if (started || !es.some(e => e.isIntersecting)) return; started = true; io.disconnect();
    fetch(root.dataset.src).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(go).catch(() => { const c = $('.card', root); if (c) c.innerHTML = root.dataset.err ? '<p>' + root.dataset.err + '</p>' : '<p>星图没取到，<a href="' + root.dataset.p + 'lunyu/guanxi/">去看同问异答与人物</a>。</p>'; });
  }, { rootMargin: '200px 0px' });
  io.observe(root);
  const whenVisible = (node, on, off, th) => { const o = new IntersectionObserver(es => es.forEach(e => e.isIntersecting ? on() : off && off()), { threshold: th }); o.observe(node); };
  function go(st) {
    const cv = $('canvas', root), ctx = cv.getContext('2d'), card = $('.card', root), hud = $('.hud', root);
    const NC = st.ch.length;
    const N = st.ch.map((c, i) => ({ k: 'c', i, id: c[0], x: c[1], y: c[2], z: c[3], d: c[4], tk: c[5], row: { t: c[6], x: c[7], u: c[8], n: c[9], o: c[10] } }));
    st.nodes.forEach((n, j) => N.push(Object.assign({ i: NC + j, id: n.n }, n)));
    const adj = N.map(() => []);
    st.edges.forEach(([a, b, t, note]) => { adj[a].push({ j: b, t, note }); adj[b].push({ j: a, t, note }); });
    // c 讲过的章，u 没讲的章，h 本书互见，q 同问异答，p 人物，o 场合，b 别的书
    const COL = { c: '170,235,208', u: '120,164,148', h: '150,232,198', q: '236,190,120', p: '214,178,112', o: '240,160,148', b: '160,184,244' };
    // 11-21 英日版：界面文字随数据 st.ui 来，没有就用中文
    const U = Object.assign({ lun: '论语 ', links: '连着 {n} 处', pick: '点一颗星', stat: '全书 {total} 条关系：本书互见 {h}，同问异答 {q}，人物 {p}，场合 {o}，别的书 {b}，异文 {y}，读法之争 {z}。', done: '已讲', todo: '未讲', nl: ' · 年历第 {n} 课', y: '异文', z: '读法之争', only: '这一章在关系表里只有年历一条。', open: '打开这一章 →', occ: '看这个场合的用句 →', more: '……共 {n} 处，这里列前 60。', nf: '没找到', nfh: '试试章号（如 12.1）、原文里的几个字（如 克己复礼），或人名（如 子路）。', K: { p: '人物', q: '同一个问题', o: '场合', b: '别的书' }, NAME: { h: '本书互见', q: '同问异答', p: '人物', o: '场合', b: '别的书' }, lang: 'zh-Hans', sep: '　', tk: 1 }, st.ui || {});
    const NAME = U.NAME, lc = s => String(s || '').toLowerCase();
    const show = { h: false, q: false, p: false, o: false, b: false }; // 11-22 主人：按钮都不默认点亮
    const sprite = rgb => {
      const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.14, `rgba(${rgb},.95)`); gr.addColorStop(.34, `rgba(${rgb},.3)`); gr.addColorStop(1, `rgba(${rgb},0)`);
      g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return c;
    };
    const spr = {}; Object.keys(COL).forEach(k => spr[k] = sprite(COL[k]));
    const TD = (() => { const d = new Date(Date.now() + 288e5); return (st.nl || {})[(d.getUTCMonth() + 1) + '-' + d.getUTCDate()]; })(), HI = N.findIndex(n => n.id === TD), HOME = HI >= 0 ? HI : N.findIndex(n => n.id === '12.1'), RO = st.R * 1.42, P = {};
    let W = 0, H = 0, DPR = 1, yaw = .5, yawHome = .5, swayT = 0, pitch = 1, zoom = 1, focus = -1, hover = -1, visible = false, running = false, drag = null, yawAnim = null, lastT = 0, clock = 0, intro = RM ? 1 : 0, touched = false, fset = null;
    const resize = () => { DPR = Math.min(devicePixelRatio || 1, 2); W = cv.clientWidth; H = cv.clientHeight; cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR); };
    const defPitch = () => W < 640 ? .64 : .86;
    // 每一帧先定镜头：让最外圈的“别的书”转到哪儿都在画面里；宽屏给右边的卡片让出位置
    const setup = () => {
      const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch), D = 1700;
      const wide = getComputedStyle(card).position === 'absolute', cardW = wide ? card.offsetWidth + 16 : 0, top = hud.offsetHeight + 24, bot = wide ? 34 : 14, availW = W - cardW;
      const front = RO * cp * D / (D - RO * sp), back = RO * cp * D / (D + RO * sp);
      const base = Math.min(availW / 2 / (RO + (wide ? 44 : 26)), (H - top - bot) / (front + back)) * zoom;
      Object.assign(P, { cy, sy, cp, sp, D, base, cx: availW / 2, oy: top + (H - top - bot - (front + back) * base) / 2 + back * base });
    };
    const pp = (x0, y0, z0) => { const x = x0 * P.cy - y0 * P.sy, y = x0 * P.sy + y0 * P.cy, y2 = y * P.cp - z0 * P.sp, z2 = y * P.sp + z0 * P.cp, s = P.D / (P.D - z2); return [P.cx + x * s * P.base, P.oy + y2 * s * P.base, s, z2]; };
    const vis = n => n.k === 'c' || show[n.k] || (n.k === 'p' && n.d >= 15) || (fset && fset.has(n.i));
    const hubR = n => (n.k === 'p' ? clamp(1.7 + Math.sqrt(n.d) * 1.02, 2.6, 8.5) : clamp(3.4 + Math.sqrt(n.d) * .5, 4.6, 9)) * (.72 + n.ss * .36) * clamp(P.base / .72, .72, 1.1);
    const order = N.map((_, i) => i), FONT = '"Noto Serif SC","Songti SC",serif';
    const pill = (text, x, y, color) => {
      ctx.font = `600 13px ${FONT}`; const w = ctx.measureText(text).width + 16, px = clamp(x - w / 2, 6, W - w - 6), py = Math.max(6, y - 26);
      ctx.fillStyle = 'rgba(9,14,12,.88)'; ctx.strokeStyle = 'rgba(160,220,196,.45)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.roundRect(px, py, w, 22, 11); ctx.fill(); ctx.stroke();
      ctx.fillStyle = color || '#F2F1EA'; ctx.textAlign = 'left'; ctx.fillText(text, px + 8, py + 15.5); ctx.textAlign = 'center';
    };
    const draw = () => {
      setup();
      for (const n of N) { const q = pp(n.x, n.y, n.z); n.sx = q[0]; n.sy = q[1]; n.ss = q[2]; n.dp = q[3]; }
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
      const g = ctx.createRadialGradient(P.cx, P.oy, 10, P.cx, P.oy, Math.max(W, H) * .78);
      g.addColorStop(0, '#183128'); g.addColorStop(.5, '#0E1915'); g.addColorStop(1, '#080D0B'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      // 玉璧的环带
      const ring = r => { for (let k = 0; k <= 96; k++) { const a = k / 96 * 6.2832, q = pp(r * Math.cos(a), r * Math.sin(a), 0); k ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); } ctx.closePath(); };
      const bandA = clamp(intro / .35);
      for (const w of [58, 44, 32, 20, 10]) { ctx.beginPath(); ring(st.R + w); ring(st.R - w); ctx.fillStyle = `rgba(120,205,172,${.016 * bandA})`; ctx.fill('evenodd'); } // 11-22 光带边缘渐淡
      // 11-22 主人：去掉两圈轨道线，只留淡光带，像银河
      const eA = clamp((intro - .7) / .3), hA = clamp((intro - .55) / .3), sk = clamp(P.base / .72, .6, 1.15), small = W < 640;
      // 连线
      const ctrl = (a, b) => [P.cx + ((a.sx + b.sx) / 2 - P.cx) * .25, P.oy + ((a.sy + b.sy) / 2 - P.oy) * .25];
      const line = (a, b, t, alpha, wd) => {
        ctx.strokeStyle = `rgba(${COL[t]},${alpha})`; ctx.lineWidth = wd; ctx.beginPath(); ctx.moveTo(a.sx, a.sy);
        if (t === 'h') { const c = ctrl(a, b); ctx.quadraticCurveTo(c[0], c[1], b.sx, b.sy); } else ctx.lineTo(b.sx, b.sy);
        ctx.stroke();
      };
      ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      if (eA > 0) {
        if (focus < 0) { for (const [a, b, t] of st.edges) if (show[t]) line(N[a], N[b], t, (t === 'p' ? .11 : t === 'b' ? .1 : t === 'o' ? .2 : .4) * eA, 1); }
        else {
          for (const [a, b, t] of st.edges) if (show[t] && a !== focus && b !== focus) line(N[a], N[b], t, (t === 'p' || t === 'b' ? .035 : .11) * eA, 1);
          const many = adj[focus].length > 30;
          for (const e of adj[focus]) { if (!many) line(N[focus], N[e.j], e.t, .2, 5); line(N[focus], N[e.j], e.t, many ? .55 : .9, many ? 1 : 1.4); }
          if (!RM) adj[focus].forEach((e, k) => {   // 沿线走的光点
            const a = N[focus], b = N[e.j], u = (clock / 1800 + k * .37) % 1, v = 1 - u; let x, y;
            if (e.t === 'h') { const c = ctrl(a, b); x = v * v * a.sx + 2 * v * u * c[0] + u * u * b.sx; y = v * v * a.sy + 2 * v * u * c[1] + u * u * b.sy; } else { x = lerp(a.sx, b.sx, u); y = lerp(a.sy, b.sy, u); }
            ctx.globalAlpha = Math.sin(Math.PI * u) * .9; ctx.drawImage(spr[e.t], x - 7, y - 7, 14, 14);
          });
          ctx.globalAlpha = 1;
        }
      }
      // 章：一颗一颗的星，叠着发光
      for (let i = 0; i < NC; i++) {
        const n = N[i], ap = clamp((intro * 1.18 - i / NC) / .06); if (ap <= 0) continue;
        const near = clamp((n.dp + 330) / 660), inF = fset && fset.has(i), dim = fset && !inF ? .5 : 1;
        const r = (1.5 + Math.min(n.d, 12) * .22) * (.5 + n.ss * .62) * (inF ? 1.4 : 1) * sk, R = r * (n.tk ? 3.7 : 3) * (1 + (1 - ap) * 2.4 * sk);
        n.r = r; ctx.globalAlpha = (n.tk ? .55 + .45 * near : .3 + .38 * near) * dim * ap;
        ctx.drawImage(spr[n.tk ? 'c' : 'u'], n.sx - R, n.sy - R, 2 * R, 2 * R);
      }
      // 人物、问题、场合、别的书
      order.sort((a, b) => N[a].dp - N[b].dp);
      const labels = [];
      if (hA > 0) for (const i of order) {
        const n = N[i]; if (n.k === 'c' || !vis(n)) continue;
        const near = clamp((n.dp + 330) / 660), r = hubR(n), c = COL[n.k], inF = fset && fset.has(i), a = (.55 + .45 * near) * hA * (fset && !inF ? .4 : 1), gl = n.k === 'p' ? 2.5 : 3.1; n.r = r;
        ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a * (n.k === 'p' ? .55 : .75); ctx.drawImage(spr[n.k], n.sx - r * gl, n.sy - r * gl, r * gl * 2, r * gl * 2);
        ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = a; ctx.fillStyle = `rgb(${c})`; ctx.beginPath();
        if (n.k === 'q') { ctx.moveTo(n.sx, n.sy - r * 1.25); ctx.lineTo(n.sx + r * 1.25, n.sy); ctx.lineTo(n.sx, n.sy + r * 1.25); ctx.lineTo(n.sx - r * 1.25, n.sy); ctx.closePath(); ctx.fill(); }
        else if (n.k === 'b') { ctx.roundRect(n.sx - r, n.sy - r, 2 * r, 2 * r, 2); ctx.fill(); }
        else if (n.k === 'o') { ctx.arc(n.sx, n.sy, r * .95, 0, 6.2832); ctx.strokeStyle = `rgb(${c})`; ctx.lineWidth = Math.max(1.6, r * .42); ctx.stroke(); }
        else { ctx.arc(n.sx, n.sy, r * .8, 0, 6.2832); ctx.fill(); }
        if (fset ? (inF || (!small && n.k === 'p' && n.d >= 15)) : (n.k !== 'p' || n.d >= (show.p ? (small ? 15 : 4) : (small ? 30 : 15)))) labels.push([n.n, n.sx, n.sy - r - 6, `rgba(${c},${Math.min(1, a + .3)})`, small ? 11 : n.k === 'p' ? 12 : 13]);
      }
      ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1; ctx.textAlign = 'center';
      // 篇名绕在环外
      ctx.font = `${W < 640 ? 11 : 12.5}px ${FONT}`;
      st.pian.forEach(p => { const q = pp((st.R + 72) * Math.cos(p.mid), (st.R + 72) * Math.sin(p.mid), 0); ctx.fillStyle = `rgba(200,218,208,${(.3 + .6 * clamp((q[3] + 330) / 660)) * bandA})`; ctx.fillText(p.name, q[0], q[1] + 4); });
      for (const [t, x, y, col, size] of labels) { ctx.font = `${size}px ${FONT}`; ctx.fillStyle = col; ctx.fillText(t, x, y); }
      // 焦点连着的章，标上章号
      if (focus >= 0 && adj[focus].length <= 48) { ctx.font = `11px ${FONT}`; ctx.fillStyle = 'rgba(190,240,220,.92)'; const f = N[focus]; for (const e of adj[focus]) { const m = N[e.j]; if (m.k === 'c' && Math.hypot(m.sx - f.sx, m.sy - f.sy) > 36) ctx.fillText(m.id, m.sx, m.sy - m.r - 5); } }
      if (focus >= 0) {
        const n = N[focus], rr = (n.r || 4) + 6 + (RM ? 0 : 1.6 * Math.sin(clock / 320));
        ctx.strokeStyle = 'rgba(242,241,234,.95)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(n.sx, n.sy, rr, 0, 6.2832); ctx.stroke();
        if (n.k === 'c') pill(U.lun + n.id + U.sep + (n.row.t || ''), n.sx, n.sy - rr - 4);
      }
      if (hover >= 0 && hover !== focus) {
        const n = N[hover]; ctx.strokeStyle = 'rgba(242,241,234,.8)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(n.sx, n.sy, (n.r || 4) + 5, 0, 6.2832); ctx.stroke();
        pill(n.k === 'c' ? U.lun + n.id + U.sep + (n.row.t || '') : n.n + U.sep + U.links.replace('{n}', adj[hover].length), n.sx, n.sy - (n.r || 4) - 8, n.k === 'c' ? '#F2F1EA' : `rgb(${COL[n.k]})`);
      }
    };
    const frame = ts => {
      if (!visible) { running = false; return; }
      const dt = Math.min(50, ts - lastT || 16); lastT = ts; clock += dt;
      if (intro < 1) { intro = Math.min(1, intro + dt / 2600); if (intro >= 1 && focus < 0 && !touched) setFocus(HOME, true); }
      if (yawAnim) { yawAnim.t += dt / 1000; yaw = yawAnim.a + yawAnim.d * ease(clamp(yawAnim.t)); if (yawAnim.t >= 1) { yawAnim = null; yawHome = yaw; swayT = 0; } }
      else if (!drag && !RM && hover < 0) { if (focus < 0) { yaw += dt * .00009; yawHome = yaw; } else { swayT += dt; yaw = yawHome + .16 * Math.sin(swayT / 3600); } }
      draw(); requestAnimationFrame(frame);
    };
    const kick = () => { if (visible && !running) { running = true; lastT = 0; requestAnimationFrame(frame); } };
    const pick = (x, y, rad) => { let best = -1, bd = rad * rad; for (const n of N) { if (!vis(n)) continue; const dx = n.sx - x, dy = n.sy - y, dd = dx * dx + dy * dy - (n.k === 'c' ? 0 : 30); if (dd < bd) { bd = dd; best = n.i; } } return best; };
    const turnTo = n => { const target = Math.PI / 2 - Math.atan2(n.y, n.x); let dlt = (target - yaw) % 6.2832; if (dlt > Math.PI) dlt -= 6.2832; if (dlt < -Math.PI) dlt += 6.2832; yawAnim = { a: yaw, d: dlt, t: 0 }; };
    const chLink = n => el('button', { class: 'lk', type: 'button', text: U.lun + n.id + ' ' + (n.row.t || ''), onclick: () => setFocus(n.i, true) });
    const cut = (s, n) => s.length > n ? s.slice(0, n) + '…' : s;
    const setFocus = (i, turn) => {
      focus = i; fset = i >= 0 ? new Set(adj[i].map(e => e.j).concat(i)) : null; card.textContent = '';
      if (i < 0) { card.append(el('h4', { text: U.pick }), el('p', { text: U.stat.replace('{total}', st.total).replace('{h}', st.stats['互见']).replace('{q}', st.stats['同问异答']).replace('{p}', st.stats['人物']).replace('{o}', st.stats['场合']).replace('{b}', st.stats['书外互见']).replace('{y}', st.stats['异文']).replace('{z}', st.stats['争议']) })); yawHome = yaw; return; }
      const n = N[i]; if (turn && (n.x || n.y)) turnTo(n); else { yawHome = yaw; swayT = 0; }
      if (n.k === 'c') {
        const r = n.row, fl = st.flags[n.id] || [];
        card.append(el('h4', { html: `${esc(U.lun)}${esc(n.id)} · ${esc(r.t || '')}<small>${U.tk ? (n.tk ? U.done : U.todo) : ''}${r.n ? U.nl.replace('{n}', r.n) : ''}</small>` }));
        card.append(el('p', { lang: U.lang, text: r.x.length > (U.xn || 86) ? r.x.slice(0, U.xn || 86) + '……' : r.x }));
        const ul = el('ul');
        adj[i].forEach(e => { const m = N[e.j], li = el('li'); li.append(el('i', { class: e.t, text: NAME[e.t] })); li.append(m.k === 'c' ? chLink(m) : el('button', { class: 'lk', type: 'button', text: m.n, onclick: () => setFocus(m.i, true) })); if (e.note && e.t !== 'h') li.append('　' + cut(e.note, U.cn || 60)); ul.append(li); });
        fl.forEach(([k, note]) => { const li = el('li'); li.append(el('i', { text: k === 'y' ? U.y : U.z }), cut(note, U.cn || 64)); ul.append(li); });
        if (!ul.children.length) ul.append(el('li', { text: U.only }));
        card.append(ul);
        if (r.u) card.append(el('p', {}, el('a', { class: 'go', href: r.u, text: U.open })));
      } else {
        const kind = U.K[n.k];
        card.append(el('h4', { html: `${esc(n.n)}<small>${kind}${n.role ? ' · ' + esc(n.role) : ''} · ${U.links.replace('{n}', adj[i].length)}</small>` }));
        if (n.u) card.append(el('p', {}, el('a', { class: 'go', href: root.dataset.p.replace(/\/$/, '') + n.u, text: U.occ })));
        const ul = el('ul'); adj[i].slice(0, 60).forEach(e => { const li = el('li'); li.append(chLink(N[e.j])); if (e.note) li.append('　' + cut(e.note, U.cn2 || 48)); ul.append(li); });
        if (adj[i].length > 60) ul.append(el('li', { text: U.more.replace('{n}', adj[i].length) }));
        card.append(ul);
      }
      card.scrollTop = 0;
    };
    // 交互
    cv.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, yaw, pitch, moved: 0, touch: e.pointerType === 'touch' }; try { cv.setPointerCapture(e.pointerId); } catch (_) { } yawAnim = null; });
    cv.addEventListener('pointermove', e => {
      const r = cv.getBoundingClientRect();
      if (drag) { const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy)); yaw = drag.yaw + dx * .006; if (!drag.touch) pitch = clamp(drag.pitch + dy * .004, .5, 1.3); }
      else if (e.pointerType !== 'touch') { hover = intro < 1 ? -1 : pick(e.clientX - r.left, e.clientY - r.top, 13); cv.style.cursor = hover >= 0 ? 'pointer' : 'grab'; }
    });
    const up = e => {
      if (!drag) return; const r = cv.getBoundingClientRect(), d = drag; drag = null; yawHome = yaw; swayT = 0;
      if (d.moved < 6) { touched = true; intro = 1; const hit = pick(e.clientX - r.left, e.clientY - r.top, d.touch ? 24 : 15); if (hit >= 0 && hit === focus && N[hit].k === 'c' && N[hit].row.u) { location.href = N[hit].row.u; return; } setFocus(hit, false); }
    };
    cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', () => { drag = null; yawHome = yaw; swayT = 0; }); cv.addEventListener('pointerleave', () => hover = -1);
    $$('[data-f]', hud).forEach(b => b.addEventListener('click', () => { const k = b.dataset.f; show[k] = !show[k]; b.setAttribute('aria-pressed', show[k]); }));
    $('.rand', hud).addEventListener('click', () => { touched = true; intro = 1; const pool = N.filter(n => n.k === 'c' && n.d > 1 && n.i !== focus); setFocus(pool[Math.floor(Math.random() * pool.length)].i, true); });
    $('.reset', hud).addEventListener('click', () => { touched = true; intro = 1; setFocus(-1); zoom = 1; pitch = defPitch(); });
    const q = $('input', hud);
    const find = () => {
      const v = q.value.trim(); if (!v) return; touched = true; intro = 1;
      const w = lc(v), hit = N.find(n => n.k === 'c' && n.id === v) || N.find(n => n.k !== 'c' && (lc(n.n) === w || lc(n.full) === w)) || N.find(n => n.k === 'c' && (lc(n.row.x).includes(w) || (n.row.o || '').includes(v))) || N.find(n => n.k !== 'c' && (lc(n.n).includes(w) || (n.o || '').includes(v))) || N.find(n => n.k === 'c' && lc(n.row.t).includes(w));
      if (hit) setFocus(hit.i, true); else { setFocus(-1); card.textContent = ''; card.append(el('h4', { text: U.nf }), el('p', { text: U.nfh })); }
    };
    q.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); find(); } });
    resize(); pitch = defPitch(); setFocus(RM ? HOME : -1, false);
    if (RM) yaw = yawHome = Math.PI / 2 - Math.atan2(N[HOME].y, N[HOME].x);
    addEventListener('resize', () => { const w = W; resize(); if (w !== W) pitch = defPitch(); if (!running) draw(); });
    whenVisible(root, () => { visible = true; kick(); }, () => visible = false, .05);
    root.classList.add('on');
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { if (!running) draw(); });
    draw();
  }
})();
