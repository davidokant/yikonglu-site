"""“故事”栏（演义层）：片中原创人物、十三经岛导览、“跟着一个人读”路线。

只在 数据/网站素材/_故事/人物.csv 存在时生成；只出简繁两语。
硬线：
- 只写已播：出场表、路线里没上网的章自动不出；
- 章节页只在页脚回链一句，分歧表、一孔按、白话里不出现人物名；
- 不进 /data/ 开放数据、不进站内检索；搜索元数据用 CreativeWork（genre 虚构）。

资料文件（都在 _故事/ 下，UTF-8 CSV）：
- 人物.csv：id,名,一句关系,简介,立绘,头像       （立绘、头像是 _故事/立绘/ 下的文件名，可空）
- 出场.csv：集号,章号,人物,句,本章片中         （人物写 id 或名，多人用、隔开；句＝该段落点的原文句；本章片中＝章节页页脚那一句）
- 书区.csv：区名,书名,篇目,x,y,状态            （x、y 是热点在地图上的百分比；状态：在讲／已讲／未讲）
- 地图.png（可选，有文字层的全图）
- 路线.csv：人物,题目,导语,章号,起句,说明      （题目、导语只在该人第一行填；起句用来对号，未讲章显示起句；说明可空）
"""
import csv, os, re, html, json

def esc(s): return html.escape(s or "", quote=True)

NOTICE = "片中人物与岛屿为本站原创，不是史料。"

def rows(p):
    return [r for r in csv.DictReader(open(p, encoding="utf-8-sig"))] if os.path.exists(p) else []

def load(gdir, pub):
    """读资料；没有人物表返回 None（整栏不生成）。"""
    pf = os.path.join(gdir, "人物.csv")
    if not os.path.exists(pf): return None
    ppl = [{k: (v or "").strip() for k, v in r.items()} for r in rows(pf) if (r.get("id") or "").strip()]
    by = {}
    for p in ppl: by[p["id"]] = p; by[p["名"]] = p
    pubset = set(pub)
    appear = []  # 只留已上网的章
    for r in rows(os.path.join(gdir, "出场.csv")):
        c = (r.get("章号") or "").strip()
        if c not in pubset: continue
        who = [by[w.strip()]["id"] for w in re.split(r"[、,，/ ]+", r.get("人物") or "") if w.strip() in by]
        appear.append({"ep": (r.get("集号") or "").strip(), "c": c, "who": who, "ju": (r.get("句") or "").strip(), "line": (r.get("本章片中") or "").strip()})
    routes, cur = {}, None
    for r in rows(os.path.join(gdir, "路线.csv")):
        w = (r.get("人物") or "").strip()
        if w in by: cur = by[w]["id"]
        if not cur: continue
        rt = routes.setdefault(cur, {"title": "", "intro": "", "items": []})
        if (r.get("题目") or "").strip(): rt["title"] = r["题目"].strip()
        if (r.get("导语") or "").strip(): rt["intro"] = r["导语"].strip()
        if (r.get("章号") or "").strip(): rt["items"].append(((r["章号"]).strip(), (r.get("说明") or "").strip(), (r.get("起句") or "").strip()))
    zones = [{k: (v or "").strip() for k, v in r.items()} for r in rows(os.path.join(gdir, "书区.csv"))]
    imgdir = os.path.join(gdir, "立绘")
    return {"ppl": ppl, "by": by, "appear": appear, "routes": routes, "zones": zones, "dir": gdir,
            "imgdir": imgdir if os.path.isdir(imgdir) else None, "map": os.path.join(gdir, "地图.png") if os.path.exists(os.path.join(gdir, "地图.png")) else None}

def copy_images(G, outdir):
    """立绘缩到长边 900、头像 400、地图 2000，放 /gushi/img/（不随语种复制）。"""
    from PIL import Image
    od = os.path.join(outdir, "gushi", "img"); os.makedirs(od, exist_ok=True)
    def put(src, name, edge):
        im = Image.open(src); im.thumbnail((edge, edge)); im.save(os.path.join(od, name), optimize=True)
        return f"/gushi/img/{name}"
    for p in G["ppl"]:
        for k, edge in (("立绘", 900), ("头像", 400)):
            f = p.get(k)
            if f and G["imgdir"] and os.path.exists(os.path.join(G["imgdir"], f)):
                p["_" + k] = put(os.path.join(G["imgdir"], f), f"{p['id']}-{'full' if k == '立绘' else 'head'}.png", edge)
    if G["map"]: G["_map"] = put(G["map"], "map.png", 2000)

def ju_anchor(text, ju, split_ju):
    """原文句 → #sN 锚点（按句切与章节页一致）。"""
    if not ju: return ""
    key = re.sub(r"[，。？！；：、“”‘’「」\s]", "", ju)
    for i, s in enumerate(split_ju(text), 1):
        if key and key[:6] in re.sub(r"[，。？！；：、“”‘’「」\s]", "", s): return f"#s{i}"
    return ""

def footer_line(G, c, P):
    """章节页页脚回链一句（仅简繁）。"""
    if not G: return ""
    lines = [a for a in G["appear"] if a["c"] == c and a["line"]]
    if not lines: return ""
    a = lines[0]; pid = a["who"][0] if a["who"] else None
    link = f'<a href="{P}gushi/{pid}.html">人物页</a>' if pid else f'<a href="{P}gushi/">故事</a>'
    return f'<p class="gsback">本章片中：{esc(a["line"])} → {link}</p>'

def ld(name, url, desc, chars=None):
    d = {"@context": "https://schema.org", "@type": "CreativeWork", "genre": "fiction", "name": name, "url": url, "description": desc,
         "isPartOf": {"@type": "CreativeWork", "name": "一孔录·故事", "genre": "fiction"},
         "creator": {"@type": "Organization", "name": "一孔录", "url": "https://yikonglu.com"}}
    if chars: d["character"] = [{"@type": "Person", "name": n, "description": "一孔录原创虚构人物"} for n in chars]
    return d

def fields_of(intro):
    """“家境：……。本事：……。”这种简介拆成字段表；拆不开就整段当简介。"""
    out = []
    for seg in re.split(r"(?<=。)(?=[一-鿿]{2,4}：)", intro or ""):
        m = re.match(r"^([一-鿿]{2,4})：(.+)$", seg.strip())
        if m: out.append((m.group(1), m.group(2).rstrip("。")))
        elif seg.strip(): out.append(("", seg.strip()))
    return out

def ep_label(ep):
    m = re.match(r"^论语-\d+-(.+)$", ep or "")
    return f"《论语》{m.group(1)}" if m else ""

def build(L, D, G, write, page, P, rel_of, title_of, split_ju, DOMAIN):
    urls = []; yw, pub = D["yw"], set(D["pub"]); slugs = D.get("book_slugs") or {}; live = D.get("live_books") or set()
    mapimg = G.get("_map")
    def hero(h, sub, extra="", cls="", crumb=True):
        cr = f'<p class="crumb"><a href="{P}gushi/">故事</a></p>' if crumb else ""
        return f'<div class="gshero {cls}"><div class="wrap">{extra}<div class="gshtext"><p class="gsnote">{NOTICE}</p>{cr}<span class="ov">{esc(sub)}</span><h1>{esc(h)}</h1></div></div></div>'
    def cl(c, extra=""):
        return f'<a href="{P}{rel_of(c)}{extra}"><em>{c}</em><b>{esc(title_of(c))}</b></a>'
    def U(rel): return f"{DOMAIN}/{L.prefix}{rel}"
    def av(p, cls="gsav"):
        src = p.get("_头像") or p.get("_立绘")
        return f'<img src="{src}" alt="" loading="lazy">' if src else f'<span class="{cls}">{esc(p["名"][:1])}</span>'
    now_zone = next((z for z in G["zones"] if z.get("状态") == "在讲"), None)
    # 人物页
    cards = ""
    for p in G["ppl"]:
        mine = sorted((a for a in G["appear"] if p["id"] in a["who"]), key=lambda a: tuple(int(x) for x in a["c"].split(".")))
        items = ""
        for a in mine:
            ep = ep_label(a["ep"])
            items += f'<li>{cl(a["c"], ju_anchor(yw[a["c"]], a["ju"], split_ju))}' + (f'<p class="zy" lang="zh-Hans">{esc(a["ju"])}</p>' if a["ju"] else "") + (f'<small class="gsep">{esc(ep)}</small>' if ep else "") + "</li>"
        fl = fields_of(p.get("简介"))
        dl = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' if k else f'<p>{esc(v)}</p>' for k, v in fl)
        rt = G["routes"].get(p["id"])
        rlink = f'<a class="gsbtn" href="{P}gushi/lu-{p["id"]}.html">跟着{esc(p["名"])}读：{esc(rt["title"] or "路线")} ›</a>' if rt and rt["items"] else ""
        fig = f'<div class="gsfig"><img src="{p["_立绘"]}" alt="{esc(p["名"])}" width="400" height="600"></div>' if p.get("_立绘") else ""
        h = (f'<div class="gshero person"><div class="wrap gsp">{fig}<div class="gshtext"><p class="gsnote">{NOTICE}</p><p class="crumb"><a href="{P}gushi/">故事</a></p>'
             f'<span class="ov">{esc(p.get("一句关系") or "片中人物")}</span><h1>{esc(p["名"])}</h1><dl class="gsfields">{dl}</dl>{rlink}</div></div></div>')
        body = h + (f'<main class="wrap narrow gsmain"><h2 class="ph">出场章句<small>已播 {len(mine)} 章</small></h2>'
                    + ("<ol class=ztl>" + items + "</ol>" if items else "<p class=empty>已播各集里还没有。</p>")
                    + '<p class="note">每条链到章节页的那一句；原文、注家和读法都在章节页，这里只引不解。</p></main>')
        rel = f"gushi/{p['id']}.html"
        write(rel, page(L, f"{p['名']}｜片中人物｜一孔录·故事", f"{p['名']}，{p.get('一句关系','')}。一孔录片中人物，出场 {len(mine)} 章。"[:100], rel, body, ld(p["名"], U(rel), p.get("一句关系", ""), [p["名"]]), "pg-gushi", og_img=(p.get("_立绘") or "").lstrip("/") or None)); urls.append(U(rel))
        cards += f'<a class="gscard" href="{P}{rel}">{av(p)}<b>{esc(p["名"])}</b><small>{esc(p.get("一句关系"))}</small><em>出场 {len(mine)} 章</em></a>'
    # 路线页
    rlist = ""
    for pid, rt in G["routes"].items():
        p = G["by"][pid]
        items = ""
        for c, note, qi in rt["items"]:
            k = re.sub(r"[，。？！；：、“”…\s]", "", qi.split("……")[0])[:4]
            if c in pub and k and k not in re.sub(r"[，。？！；：、“”\s]", "", yw[c]): print(f"路线对号不上：{pid} {c} 起句“{qi}”")
            if c in pub:
                items += f'<li>{cl(c)}<p class="zy" lang="zh-Hans">{esc(yw[c])}</p>' + (f'<p class="zd">{esc(note)}</p>' if note else "") + "</li>"
            else:
                items += f'<li><span class="gsnot"><em>{c}</em><b>未讲</b></span>' + (f'<p class="zy" lang="zh-Hans">{esc(qi)}……</p>' if qi else "") + (f'<p class="zd">{esc(note)}</p>' if note else "") + "</li>"
        rel = f"gushi/lu-{pid}.html"
        voice = f'<div class="gsvoice">{av(p)}<p>{esc(rt["intro"])}<span>——{esc(p["名"])}</span></p></div>' if rt["intro"] else ""
        body = hero(rt["title"] or f"跟着{p['名']}读", f"跟着{p['名']}读") + f'<main class="wrap narrow gsmain">{voice}<p class="note">下面是原文与章节页链接；人物只在这一句导语里出现，读法以章节页为准。</p><ol class="ztl">{items}</ol></main>'
        write(rel, page(L, f"跟着{p['名']}读：{rt['title']}｜一孔录·故事", (rt["intro"] or rt["title"])[:100], rel, body, ld(f"跟着{p['名']}读", U(rel), rt["intro"], [p["名"]]), "pg-gushi")); urls.append(U(rel))
        rlist += f'<a class="gsroute" href="{P}{rel}">{av(p)}<div><b>跟着{esc(p["名"])}读<span>{esc(rt["title"])}</span></b><p>{esc(rt["intro"])}</p></div></a>'
    # 十三经岛导览
    if G["zones"] or mapimg:
        def short(z):
            n = z["书名"]; return n[-2:] if n.startswith("春秋") else (n[:2] if len(n) > 3 else n)
        def book_href(z):
            n = z["书名"]; sl = slugs.get(n) or next((v for k, v in slugs.items() if n in k or k in n), "")
            return f"{P}lunyu/" if sl in live else f"{P}shumu/"
        spots = "".join(f'<a class="spot{" now" if z.get("状态") == "在讲" else ""}" style="left:{esc(z["x"])}%;top:{esc(z["y"])}%" href="#z{i}" title="{esc(z["书名"])}" aria-label="{esc(z["书名"])}">{esc(short(z))}</a>' for i, z in enumerate(G["zones"]) if z.get("x") and z.get("y"))
        mp = f'<div class="gsmap"><img src="{mapimg}" alt="十三经岛地图" width="2000" height="1547">{spots}</div>' if mapimg else ""
        zc = ""
        for i, z in enumerate(G["zones"]):
            pm = [x for x in re.split(r"[、，,]", z.get("篇目") or "") if x]
            pt = "、".join(pm[:6]) + (f" 等 {len(pm)} 篇" if len(pm) > 6 else "")
            now = z.get("状态") == "在讲"
            zc += f'<a class="zcard{" now" if now else ""}" id="z{i}" href="{book_href(z)}"><span class="ov">{i + 1:02d} · {esc(z["区名"].split("·")[0])}</span><b>《{esc(z["书名"])}》</b><small>{esc(pt)}</small><em>{"现在讲到这里 ›" if now else "筹备中 · 看书目"}</em></a>'
        body = hero("十三经岛", "片中的书区地图") + f'<main class="wrap gsmain"><p class="lead narrow">片里把每部经典画成一座岛或一片山。这张图是片中的虚构地图，不是历史地理；点岛上的标记或下面的卡片，看那部书的篇目和进度。</p>{mp}<div class="zcards">{zc}</div></main>'
        write("gushi/dao.html", page(L, "十三经岛｜一孔录·故事", "一孔录片中的书区地图：每部经典一座岛，标着现在讲到哪里。", "gushi/dao.html", body, ld("十三经岛", U("gushi/dao.html"), "一孔录片中的虚构书区地图"), "pg-gushi", og_img=(mapimg or "").lstrip("/") or None)); urls.append(U("gushi/dao.html"))
    # 栏目首页
    nowtxt = f"，现在讲到《{esc(now_zone['书名'])}》" if now_zone else ""
    teaser = f'<a class="gsteaser" href="{P}gushi/dao.html"><img src="{mapimg}" alt="" loading="lazy"><div><span class="ov">片中的书区地图</span><b>十三经岛</b><span>每部经典一座岛{nowtxt} ›</span></div></a>' if mapimg else ""
    body = hero("故事", "片中的人和岛", crumb=False, cls="index") + (
        f'<main class="wrap narrow gsmain"><p class="lead">一孔录的视频里有六位原创人物陪着读书，住在一张虚构的书区地图上。这一栏介绍他们，只写已经播出的内容；原文、注家和读法都在<a href="{P}lunyu/">章节页</a>，这里不讲。</p>'
        f'<h2 class="ph">片中人物</h2><div class="gscards">{cards}</div>'
        + (f'<h2 class="ph">跟着一个人读</h2><div class="gsroutes">{rlist}</div>' if rlist else "")
        + (f'<h2 class="ph">地图</h2>{teaser}' if teaser else "") + "</main>")
    write("gushi/index.html", page(L, "故事：片中人物与十三经岛｜一孔录", "一孔录视频里的原创人物与书区地图，只写已播内容。", "gushi/", body, ld("一孔录·故事", U("gushi/"), "一孔录视频里的原创人物与书区地图", [p["名"] for p in G["ppl"]]), "pg-gushi", og_img=(mapimg or "").lstrip("/") or None)); urls.append(U("gushi/"))
    return urls
