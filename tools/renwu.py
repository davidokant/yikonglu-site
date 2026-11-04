"""论语真实人物页（志层）：每人一页，列全书出场章。

数据：数据/网站素材/_人物/*.csv（Codex 交），列：
  id,人名,字/别称,身份,与孔子关系,章号,该章所述,出处
- 一人多行，每行一章；人名、字/别称、身份、与孔子关系、出处只需在该人第一行填。
- id 用拼音小写作网址（如 zilu、zigong）；没填就按出场先后编 r1、r2……（繁体页由简体整页转换，网址不能用汉字）。
- 章号按本站分章（篇.章）。已上网的章链到章节页，没上网的标“未讲”。
没有任何 CSV 时整栏不出。先只出简繁两语。
"""
import csv, glob, os, re, html

def esc(s): return html.escape(s or "", quote=True)
KEY = lambda c: tuple(int(x) for x in c.split(".")) if re.match(r"^\d+\.\d+$", c) else (999, 999)

def load(rdir):
    files = sorted(glob.glob(os.path.join(rdir, "*.csv")))
    if not files: return None
    ppl, order = {}, []
    for f in files:
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
            name = r.get("人名")
            if not name: continue
            p = ppl.get(name)
            if not p:
                p = ppl[name] = {"name": name, "id": "", "alias": "", "role": "", "rel": "", "src": "", "apps": []}
                order.append(name)
            for k, col in (("id", "id"), ("alias", "字/别称"), ("role", "身份"), ("rel", "与孔子关系"), ("src", "出处")):
                if r.get(col) and not p[k]: p[k] = r[col]
            if r.get("章号"): p["apps"].append((r["章号"], r.get("该章所述", "")))
    used = set()
    for i, n in enumerate(order, 1):
        p = ppl[n]; sid = re.sub(r"[^a-z0-9-]", "", p["id"].lower()) or f"r{i}"
        while sid in used: sid += "x"
        used.add(sid); p["id"] = sid
        p["apps"].sort(key=lambda a: KEY(a[0]))
    return [ppl[n] for n in order]

def chapter_people(R, c):
    return [p for p in (R or []) if any(a[0] == c for a in p["apps"])]

def chip_line(R, c, P):
    ps = chapter_people(R, c)
    if not ps: return ""
    return '<p class="rwchips">本章人物：' + "".join(f'<a href="{P}renwu/{p["id"]}.html">{esc(p["name"])}</a>' for p in ps) + "</p>"

def build(L, D, R, write, page, P, rel_of, title_of, DOMAIN):
    urls = []; pub = set(D["pub"]); yw = D["yw"]
    U = lambda rel: f"{DOMAIN}/{L.prefix}{rel}"
    head = lambda h, sub, crumb="": f'<div class="chhead"><div class="wrap">{crumb}<h1><span class="no">{esc(sub)}</span>{esc(h)}</h1></div></div>'
    crumb = f'<p class="crumb"><a href="{P}renwu/">《论语》人物</a></p>'
    cards = ""
    for p in sorted(R, key=lambda p: -len(p["apps"])):
        n_pub = sum(1 for a in p["apps"] if a[0] in pub)
        items = ""
        for c, say in p["apps"]:
            if c in pub:
                items += f'<li><a href="{P}{rel_of(c)}"><em>{c}</em><b>{esc(title_of(c))}</b></a>' + (f'<p class="zy" lang="zh-Hans">{esc(yw[c])}</p>' if c in yw else "") + (f'<p class="zd">{esc(say)}</p>' if say else "") + "</li>"
            else:
                items += f'<li><span class="gsnot"><em>{c}</em><b>未讲</b></span>' + (f'<p class="zd">{esc(say)}</p>' if say else "") + "</li>"
        meta = "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in (("字、别称", p["alias"]), ("身份", p["role"]), ("与孔子", p["rel"]), ("出处", p["src"])) if v)
        rel = f"renwu/{p['id']}.html"
        body = head(p["name"], f"出场 {len(p['apps'])} 章，已讲 {n_pub} 章", crumb) + f'''
<main class="wrap narrow"><dl class="rwmeta">{meta}</dl><h2 class="ph">出场各章</h2><ol class="ztl">{items}</ol>
<p class="note">按本站分章排列。已讲的章链到章节页，带原文、注家原页与读法；未讲的章等全书原文上线后补链接。</p></main>'''
        ld = {"@context": "https://schema.org", "@type": "Person", "name": p["name"], "alternateName": [x for x in re.split(r"[、，,]", p["alias"]) if x] or None,
              "description": p["role"] or None, "url": U(rel), "subjectOf": {"@type": "Book", "name": "论语"}}
        ld = {k: v for k, v in ld.items() if v}
        write(rel, page(L, f"{p['name']}：《论语》里的出场各章｜一孔录", f"{p['name']}（{p['alias']}）{p['role']}，《论语》出场 {len(p['apps'])} 章。"[:110], rel, body, ld)); urls.append(U(rel))
        cards += f'<a class="rwcard" href="{P}{rel}"><b>{esc(p["name"])}</b><small>{esc(p["alias"])}</small><span>{len(p["apps"])} 章</span></a>'
    body = head("《论语》人物", "书里出场的真实人物，每人一页列出全部出场章") + f'''
<main class="wrap narrow"><p class="lead">孔子、弟子、国君、大夫与隐者，按出场章数排列。点进去看他在哪几章出现、说了什么、做了什么。</p><div class="rwcards">{cards}</div></main>'''
    write("renwu/index.html", page(L, "《论语》人物：出场各章索引｜一孔录", "《论语》里出场的真实人物，每人一页，列出全部出场章，链到原文与注家原页。", "renwu/", body)); urls.append(U("renwu/"))
    return urls
