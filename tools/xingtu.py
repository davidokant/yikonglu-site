"""《论语》星图（11-15 主人定：首页招牌，；11-15 晚主人：关系图页撤掉星图栏，改名“同问异答与人物”）。
498 章排成一圈玉璧，人物、同一个问题、场合、别的书是圈里圈外的星。数据＝tools/lunyu_guanxi.json，做法照炫技演示 prep.py 的“星图”一段。
页面：xt_html() 出画布和控件；脚本 /assets/xingtu.js 进入视口才取 <语种前缀>/data/xingtu.json、才开动画；减少动态效果时停成静态。只简繁。"""
import json, os, math, hashlib, collections, html

HERE = os.path.dirname(os.path.abspath(__file__))
JS_FILE = os.path.join(HERE, "assets", "xingtu.js")
esc = html.escape
R = 300.0


def _h01(s, salt=""): return int(hashlib.md5((s + salt).encode()).hexdigest()[:8], 16) / 0xffffffff


XI = {l: json.load(open(os.path.join(HERE, "i18n", f"xt-{l}.json"), encoding="utf-8")) for l in ("en", "ja") if os.path.exists(os.path.join(HERE, "i18n", f"xt-{l}.json"))}


def langs(): return list(XI)


def data(G, PIAN, pub, href, title_of, tx, X, code=None, gxtr=None, ztx=None):
    """G＝guanxi.load()；PIAN＝{"1": ("学而第一", ...)}；pub＝讲过的章；X＝lunyu_extra.load()（年历课号、场合名）。
    11-21 英日版：code＝en/ja，gxtr＝guanxi.TR[code]（人名、同问异答、关系注），XI[code]（界面、场合）；ztx(c)＝中文原文（供中文检索）。"""
    if not G: return None
    gx = G["raw"]
    F = XI.get(code) if code else None; T = gxtr or {}; TX = T.get("X") or {}; TP = T.get("p") or {}; TW = {w["id"]: w for w in T.get("W") or []}
    def xo(r, k="note"): return ((TX.get(str(r.get("_i"))) or {}).get(k)) or ""
    cc = lambda s: s.split(":", 1)[1]
    rels = [r for r in gx["rels"] if ":" in r["a"]]
    pk = sorted(PIAN, key=int)
    order = sorted({cc(r["a"]) for r in rels if r["type"] == "年历"}, key=lambda c: tuple(int(x) for x in c.split(".")))
    idx = {c: n for n, c in enumerate(order)}
    pian = [{"name": PIAN[p][0].split("第")[0], "n": sum(1 for c in order if c.split(".")[0] == p)} for p in pk]
    GA = math.pi * (3 - math.sqrt(5)); tot = len(order); acc = 0
    GAP = 0.012 * 2 * math.pi; span_total = 2 * math.pi - len(pian) * GAP
    pos = []
    for p in pian:
        n = p["n"]; span = span_total * n / tot
        for j in range(n):
            th = acc + span * (j + 0.5) / n - math.pi / 2
            ph = j * GA; rr = 30 * math.sqrt(((j * 7) % 11 + 1) / 11)
            r = R + rr * math.cos(ph); z = rr * math.sin(ph)
            pos.append([round(r * math.cos(th), 1), round(r * math.sin(th), 1), round(z, 1)])
        p["mid"] = round(acc + span / 2 - math.pi / 2, 4); acc += span + GAP

    def centroid(cids):
        xs = [pos[idx[c]][0] for c in cids if c in idx]; ys = [pos[idx[c]][1] for c in cids if c in idx]
        return (sum(xs) / len(xs), sum(ys) / len(ys)) if xs else (0, 0)

    def cang(cids, name):
        cx, cy = centroid(cids)
        return math.atan2(cy, cx) if abs(cx) + abs(cy) > 8 else _h01(name) * 6.283

    def spread(items, need):  # 挤在一起的沿圆周推开
        n = len(items)
        for _ in range(4000):
            items.sort(key=lambda t: t[0]); moved = False
            for k in range(n):
                a, b = items[k], items[(k + 1) % n]
                gap = b[0] - a[0] + (2 * math.pi if k == n - 1 else 0); want = (need(a[1]) + need(b[1])) / 2
                if gap < want - 1e-6:
                    d = (want - gap) / 2; a[0] -= d; b[0] += d; moved = True
            if not moved: break
        return items

    nodes, edges, deg, flags = [], [], [0] * tot, collections.defaultdict(list)
    for r in rels:
        a = cc(r["a"])
        if a not in idx: continue
        if r["type"] == "互见" and r.get("b", "").startswith("lunyu:") and cc(r["b"]) in idx:
            b = cc(r["b"]); edges.append([idx[a], idx[b], "h", r.get("note", "")]); deg[idx[a]] += 1; deg[idx[b]] += 1
        elif r["type"] == "异文": flags[a].append(["y", (xo(r) if F else "") or r.get("note", "")])
        elif r["type"] == "争议": flags[a].append(["z", ((xo(r, "pick") or xo(r)) if F else "") or r.get("pick", "") or r.get("note", "")])
    ring_big, ring_mid = [], []
    for p in gx["groups"]["renwu"]:
        cids = [cc(c) for c in p["chs"] if cc(c) in idx]
        if not cids: continue
        name = p.get("common") or p["name"]
        ni = len(nodes); nd = {"k": "p", "n": name, "full": p["name"], "role": p.get("role", ""), "x": 0, "y": 0, "z": 0, "d": len(cids)}
        if F:
            tp = TP.get(p["name"]) or {}
            nd.update(n=tp.get("common") or tp.get("name") or name, full=tp.get("name") or p["name"], role=tp.get("role", ""), o=name)
        if len(cids) == 1:
            px, py, _ = pos[idx[cids[0]]]; nd.update(x=round(px * 0.87, 1), y=round(py * 0.87, 1), z=round((_h01(name) - 0.5) * 40, 1))
        else:
            (ring_big if len(cids) >= 15 else ring_mid).append([cang(cids, name), ni])
        nodes.append(nd)
        for c in cids: edges.append([idx[c], tot + ni, "p", ""]); deg[idx[c]] += 1
    for ring, rad, need in ((ring_big, 150, lambda ni: 0.6), (ring_mid, 222, lambda ni: 0.2 if nodes[ni]["d"] >= 4 else 0.075)):
        for ang, ni in spread(ring, need):
            nodes[ni].update(x=round(rad * math.cos(ang), 1), y=round(rad * math.sin(ang), 1), z=round((_h01(nodes[ni]["n"], "z") - 0.5) * 36, 1))
    qs = []
    for g in gx["groups"]["wenda"]:
        cids = [cc(i["c"]) for i in g["items"] if cc(i["c"]) in idx]
        tw = TW.get(g.get("id")) or {}; tits = tw.get("items") or []
        ni = len(nodes); nodes.append({"k": "q", "n": (tw.get("q") if F else "") or g["q"], "x": 0, "y": 0, "z": 105, "d": len(cids), **({"o": g["q"]} if F else {})}); qs.append([cang(cids, g["q"]), ni])
        for k_, it in enumerate(g["items"]):
            c = cc(it["c"]); ti = tits[k_] if k_ < len(tits) else {}
            nt = F["wd"].replace("{who}", ti.get("who") or it["who"]).replace("{a}", ti.get("a") or it["a"]) if F else f"{it['who']}问，答：{it['a']}"
            if c in idx: edges.append([idx[c], tot + ni, "q", nt]); deg[idx[c]] += 1
    for ang, ni in spread(qs, lambda ni: 0.8): nodes[ni].update(x=round(66 * math.cos(ang), 1), y=round(66 * math.sin(ang), 1))
    oname = {p["slug"]: p["name"] for p in (X or {}).get("ch") or []}
    og = collections.defaultdict(list)
    for r in rels:
        if r["type"] == "场合" and cc(r["a"]) in idx: og[r["group"]].append(r)
    os_ = []
    for gk, rs in og.items():
        cids = [cc(r["a"]) for r in rs]
        if F: nodes.append({"k": "o", "n": F["occ"].get(gk, gk), "u": "", "x": 0, "y": 0, "z": -100, "d": len(cids), "o": oname.get(gk, gk)})
        else: nodes.append({"k": "o", "n": oname.get(gk, gk), "u": f"/changhe/{gk}.html" if gk in oname else "", "x": 0, "y": 0, "z": -100, "d": len(cids)})
        ni = len(nodes) - 1; os_.append([cang(cids, gk), ni])
        for r in rs:
            nt = f"{F['kind'].get(r.get('kind', ''), r.get('kind', ''))}{F.get('colon', ': ')}{F['ch'].get(str(r.get('_i')), '')}" if F else f"{r.get('kind', '')}：{r.get('txt') or r.get('note', '')}"
            edges.append([idx[cc(r["a"])], tot + ni, "o", nt]); deg[idx[cc(r["a"])]] += 1
    for ang, ni in spread(os_, lambda ni: 0.5): nodes[ni].update(x=round(112 * math.cos(ang), 1), y=round(112 * math.sin(ang), 1))
    bg = collections.defaultdict(list)
    for r in rels:
        if r["type"] == "书外互见" and cc(r["a"]) in idx: bg[r.get("book", "别的书")].append(r)
    for bi, bk in enumerate(sorted(bg, key=lambda k: -len(bg[k]))):
        rs = bg[bk]; cids = [cc(r["a"]) for r in rs]
        x, y = centroid(cids); ang = math.atan2(y, x) if (x or y) else bi
        if len(rs) > 40: ang = [2.2, 0.6][bi % 2]  # 两本大书（道德经、三字经）放在环外固定位置
        bn = (next((xo(r, "book") for r in rs if xo(r, "book")), "") if F else "") or bk
        ni = len(nodes); nodes.append({"k": "b", "n": bn, "x": round(1.42 * R * math.cos(ang), 1), "y": round(1.42 * R * math.sin(ang), 1), "z": round((_h01(bk) - 0.5) * 80, 1), "d": len(rs), **({"o": bk} if F else {})})
        for r in rs:
            if F: nt = f"{F['bk'].get(r.get('kind'), r.get('kind', ''))}{F.get('colon', ': ')}{xo(r) or r.get('txt') or r.get('note', '')}"
            else: nt = f"{ {'相通': '一孔录对读'}.get(r.get('kind'), r.get('kind', ''))}：{r.get('txt') or r.get('note', '')}"
            edges.append([idx[cc(r["a"])], tot + ni, "b", nt]); deg[idx[cc(r["a"])]] += 1
    nlc = (X or {}).get("nlc") or {}
    def row(c):
        t = tx(c) or ""
        lim = 240 if F else 86
        return [title_of(c), t if len(t) <= lim else t[:lim].rstrip() + ("…" if F else "……"), href(c), (nlc.get(c) or [0])[0]] + ([ztx(c) if ztx else ""] if F else [])
    st = gx.get("stats", {})
    if F:
        if code == "en": pn = [f"Book {i + 1}" for i in range(len(pian))]
        else: _cv = __import__("opencc").OpenCC("s2t").convert; _jp = __import__("opencc").OpenCC("t2jp").convert; pn = [_jp(_cv(p["name"])) for p in pian]
        for p, n_ in zip(pian, pn): p["name"] = n_
    out = {"pian": [{"name": p["name"], "mid": p["mid"]} for p in pian], "R": R,
            "ch": [[c, *pos[i], deg[i], 1 if c in pub else 0, *row(c)] for i, c in enumerate(order)],
            "flags": flags, "nodes": nodes, "edges": edges, "stats": st, "total": sum(v for k, v in st.items() if k != "年历"),
            "nl": {r["md"]: r["c"] for r in (X or {}).get("nl") or []}}
    if F: out["ui"] = F["ui"]
    return out  # 11-16 默认点亮当天“今日《论语》”那一章（北京时间，按年历）


DVER = __import__("time").strftime("%y%m%d%H%M")  # 数据版本＝建站时刻（主页先于 data() 写出，只能按建站算），页面 data-src 带 ?v=，免得旧缓存里的数据（如没有 nl）顶上来


def write_data(write, d):
    """写到 <语种前缀>/data/xingtu.json；繁体站经 write 自带的转换。"""
    if d: write("data/xingtu.json", json.dumps(d, ensure_ascii=False, separators=(",", ":")))


def js_ver():
    return hashlib.md5(open(JS_FILE, "rb").read()).hexdigest()[:8] if os.path.exists(JS_FILE) else "0"


def xt_html(L, P, home=False):
    """画布＋控件。home=True 时带标题行和“去关系图”链接。11-21 英日版文字取 XI[code]["page"]。"""
    F = (XI.get(L.code) or {}).get("page")
    if F: return xt_html_f(F, P, home)
    hd = (f'<div class="xthead"><h2 class="ph">《论语》星图</h2></div>' if home else "")
    return (f'<section class="xtsec{" xthome" if home else ""}">{hd}<div class="xt" id="xt" data-src="{P}data/xingtu.json?v={DVER}" data-p="{P}">'
            '<canvas aria-label="《论语》关系星图：可拖动旋转，点星看这一章连着哪几章"></canvas>'
            '<div class="hud"><input type="search" placeholder="章号、字句或人名" aria-label="在星图里找">'
            '<button type="button" data-f="h" aria-pressed="true">本书互见</button><button type="button" data-f="q" aria-pressed="true">同问异答</button>'
            '<button type="button" data-f="p" aria-pressed="false">人物</button><button type="button" data-f="o" aria-pressed="false">场合</button>'
            '<button type="button" data-f="b" aria-pressed="false">别的书</button><button type="button" class="rand">随便点一章</button><button type="button" class="reset">复位</button></div>'
            '<p class="legend">拖动旋转；手机上左右划。再点一次选中的星，打开那一章。</p>'
            '<div class="card" aria-live="polite"><h4>《论语》星图</h4><p>滑到这里，星图就会亮起来。</p></div></div>'
            f'<noscript><p class="note"><a href="{P}lunyu/guanxi/">看《论语》同问异答与人物</a></p></noscript></section>'
            f'<script src="/assets/xingtu.js?v={js_ver()}" defer></script>')


def xt_html_f(F, P, home):
    hd = (f'<div class="xthead"><h2 class="ph">{esc(F["h2"])}</h2></div>' if home else "")
    b = lambda f, k, on: f'<button type="button" data-f="{f}" aria-pressed="{"true" if on else "false"}">{esc(F[k])}</button>'
    return (f'<section class="xtsec{" xthome" if home else ""}">{hd}<div class="xt" id="xt" data-src="{P}data/xingtu.json?v={DVER}" data-p="{P}" data-err="{esc(F["err"])}">'
            f'<canvas aria-label="{esc(F["aria"])}"></canvas>'
            f'<div class="hud"><input type="search" placeholder="{esc(F["ph"])}" aria-label="{esc(F["pharia"])}">'
            + b("h", "f_h", 1) + b("q", "f_q", 1) + b("p", "f_p", 0) + b("o", "f_o", 0) + b("b", "f_b", 0)
            + f'<button type="button" class="rand">{esc(F["rand"])}</button><button type="button" class="reset">{esc(F["reset"])}</button></div>'
            f'<p class="legend">{esc(F["legend"])}</p>'
            f'<div class="card" aria-live="polite"><h4>{esc(F["c_h"])}</h4><p>{esc(F["c_p"])}</p></div></div></section>'
            f'<script src="/assets/xingtu.js?v={js_ver()}" defer></script>')
