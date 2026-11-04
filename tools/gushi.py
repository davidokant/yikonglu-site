"""“故事”栏（演义层）：片中原创人物、十三经岛导览、“跟着一个人读”路线。

只在 数据/网站素材/_故事/人物.csv 存在时生成；只出简繁两语。
硬线（11-04 主人定，见 评审/2026-11-03-网站功能扩展/设定集进网站-形式与度-v1.md）：
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

def build(L, D, G, write, page, P, rel_of, title_of, split_ju, DOMAIN):
    urls = []; yw, pub = D["yw"], set(D["pub"])
    head = lambda crumb, h, sub: f'<div class="chhead gs"><div class="wrap"><p class="gsnote">{NOTICE}</p>{crumb}<h1><span class="no">{esc(sub)}</span>{esc(h)}</h1></div></div>'
    crumb = f'<p class="crumb"><a href="{P}gushi/">故事</a></p>'
    def cl(c, extra=""):
        return f'<a href="{P}{rel_of(c)}{extra}"><em>{c}</em><b>{esc(title_of(c))}</b></a>'
    def U(rel): return f"{DOMAIN}/{L.prefix}{rel}"
    # 人物页
    cards = ""
    for p in G["ppl"]:
        mine = [a for a in G["appear"] if p["id"] in a["who"]]
        items = "".join(f'<li>{cl(a["c"], ju_anchor(yw[a["c"]], a["ju"], split_ju))}' + (f'<p class="zy" lang="zh-Hans">{esc(a["ju"])}</p>' if a["ju"] else "") + "</li>" for a in mine)
        img = f'<img class="gsimg" src="{p["_立绘"]}" alt="{esc(p["名"])}立绘" loading="lazy">' if p.get("_立绘") else ""
        rt = G["routes"].get(p["id"])
        rlink = f'<p class="gsroute">跟着{esc(p["名"])}读：<a href="{P}gushi/lu-{p["id"]}.html">{esc(rt["title"] or "路线")}</a></p>' if rt and rt["items"] else ""
        body = head(crumb, p["名"], p.get("一句关系") or "片中人物") + f'''
<main class="wrap narrow gsmain"><div class="gsperson">{img}<div><p>{esc(p.get("简介"))}</p>{rlink}</div></div>
<h2 class="ph">出场章句</h2>{"<ol class=ztl>" + items + "</ol>" if items else "<p class=empty>已播各集里还没有。</p>"}</main>'''
        rel = f"gushi/{p['id']}.html"
        write(rel, page(L, f"{p['名']}｜片中人物｜一孔录·故事", (p.get("简介") or "")[:100], rel, body, ld(p["名"], U(rel), p.get("简介", ""), [p["名"]]), "pg-gushi", og_img=(p.get("_立绘") or "").lstrip("/") or None)); urls.append(U(rel))
        av = f'<img src="{p.get("_头像") or p.get("_立绘")}" alt="" loading="lazy">' if (p.get("_头像") or p.get("_立绘")) else f'<span class="gsav">{esc(p["名"][:1])}</span>'
        cards += f'<a class="gscard" href="{P}{rel}">{av}<b>{esc(p["名"])}</b><small>{esc(p.get("一句关系"))}</small></a>'
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
        body = head(crumb, rt["title"] or f"跟着{p['名']}读", f"跟着{p['名']}读") + f'''
<main class="wrap narrow gsmain">{f'<p class="lead gsvoice">{esc(rt["intro"])}<span>——{esc(p["名"])}</span></p>' if rt["intro"] else ""}<p class="note">下面是原文与章节页链接；人物只在这一句导语里出现，读法以章节页为准。</p><ol class="ztl">{items}</ol></main>'''
        write(rel, page(L, f"跟着{p['名']}读：{rt['title']}｜一孔录·故事", (rt["intro"] or rt["title"])[:100], rel, body, ld(f"跟着{p['名']}读", U(rel), rt["intro"], [p["名"]]), "pg-gushi")); urls.append(U(rel))
        rlist += f'<li><a href="{P}{rel}"><b>跟着{esc(p["名"])}读</b>：{esc(rt["title"])}</a></li>'
    # 十三经岛导览
    if G["zones"] or G.get("_map"):
        spots = "".join(f'<a class="spot{" now" if z.get("状态") == "在讲" else ""}" style="left:{esc(z["x"])}%;top:{esc(z["y"])}%" href="#z{i}" title="{esc(z["区名"])}"></a>' for i, z in enumerate(G["zones"]) if z.get("x") and z.get("y"))
        mp = f'<div class="gsmap"><img src="{G["_map"]}" alt="十三经岛地图">{spots}</div>' if G.get("_map") else ""
        trs = "".join(f'<tr id="z{i}"{" class=now" if z.get("状态") == "在讲" else ""}><td>{esc(z["区名"])}</td><td>{esc(z["书名"])}</td><td>{esc(z.get("篇目"))}</td><td>{"<b>现在讲到</b>" if z.get("状态") == "在讲" else esc(z.get("状态"))}</td></tr>' for i, z in enumerate(G["zones"]))
        body = head(crumb, "十三经岛", "片中的书区地图") + f'''
<main class="wrap narrow gsmain"><p class="lead">片里把每部经典画成一座岛或一片山。这张图是片中的虚构地图，不是历史地理。</p>{mp}
<table class="gstab"><thead><tr><th>书区</th><th>书</th><th>篇目</th><th>进度</th></tr></thead><tbody>{trs}</tbody></table></main>'''
        write("gushi/dao.html", page(L, "十三经岛｜一孔录·故事", "一孔录片中的书区地图：每部经典一座岛，标着现在讲到哪里。", "gushi/dao.html", body, ld("十三经岛", U("gushi/dao.html"), "一孔录片中的虚构书区地图"), "pg-gushi", og_img=(G.get("_map") or "").lstrip("/") or None)); urls.append(U("gushi/dao.html"))
    # 栏目首页
    body = head("", "故事", "片中的人和岛") + f'''
<main class="wrap narrow gsmain"><p class="lead">一孔录的视频里有六位原创人物陪着读书，住在一张虚构的书区地图上。这一栏介绍他们，只写已经播出的内容；原文、注家和读法都在<a href="{P}lunyu/">章节页</a>，这里不讲。</p>
<h2 class="ph">片中人物</h2><div class="gscards">{cards}</div>
{f'<h2 class="ph">跟着一个人读</h2><ul class="gsroutes">{rlist}</ul>' if rlist else ""}
{f'<h2 class="ph">地图</h2><p><a href="{P}gushi/dao.html">十三经岛导览</a>：每部经典在片中是哪座岛，现在讲到哪里。</p>' if (G["zones"] or G.get("_map")) else ""}</main>'''
    write("gushi/index.html", page(L, "故事：片中人物与十三经岛｜一孔录", "一孔录视频里的原创人物与书区地图，只写已播内容。", "gushi/", body, ld("一孔录·故事", U("gushi/"), "一孔录视频里的原创人物与书区地图", [p["名"] for p in G["ppl"]]), "pg-gushi")); urls.append(U("gushi/"))
    return urls
