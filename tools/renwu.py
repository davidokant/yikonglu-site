"""经典里的真实人物页（志层）：每人一页，按书列出场章。索引页按书分段，计数以人为单位，章数只在各书段内说。

数据：数据/网站素材/_人物/*.csv，列：
  id,人名,字/别称,身份,与孔子关系,章号,该章所述,出处[,书]
- “书”列可省，省了算《论语》；同一人出现在几本书里，各书各填几行。
- 一人多行，每行一章；人名、字/别称、身份、与孔子关系、出处只需在该人第一行填。
- id 用拼音小写作网址（如 zilu、zigong）；没填就按出场先后编 r1、r2……（繁体页由简体整页转换，网址不能用汉字）。
- 章号按本站分章（篇.章）。已上网的章链到章节页，没上网的标“未讲”。
没有任何 CSV 时整栏不出。先只出简繁两语。
"""
import csv, glob, os, re, html
try:
    from pypinyin import lazy_pinyin  # 人名转拼音作网址；没装就退到 r1、r2……
except ImportError: lazy_pinyin = None
HAN = lambda t: re.sub(r"[^\u4e00-\u9fff]", "", t or "")
PY_FIX = {"曾": "zeng", "参": "shen", "适": "kuo", "单": "shan", "乐": "yue"}  # 人名里的姓氏读法与常用读法不同者
def pinyin_id(n):
    if not lazy_pinyin: return ""
    out = []
    for ch in n:
        out.append(PY_FIX[ch] if ch in PY_FIX and n not in ("参", "乐") else "".join(lazy_pinyin(ch)))
    return re.sub(r"[^a-z0-9]", "", "".join(out))

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
                p = ppl[name] = {"name": name, "id": "", "alias": "", "role": "", "rel": "", "src": "", "apps": [], "books": []}
                order.append(name)
            for k, col in (("id", "id"), ("alias", "字/别称"), ("role", "身份"), ("rel", "与孔子关系"), ("src", "出处")):
                if r.get(col) and not p[k]: p[k] = r[col]
            bk = r.get("书") or "论语"
            if bk not in p["books"]: p["books"].append(bk)
            if r.get("章号"): p["apps"].append((r["章号"], r.get("该章所述", "")))
    used = set()
    for i, n in enumerate(order, 1):
        p = ppl[n]; sid = re.sub(r"[^a-z0-9-]", "", p["id"].lower()) or pinyin_id(n) or f"r{i}"
        if re.match(r"^《论语集注》\d", p["src"]): p["src"] = "《论语》本章经文；身份据朱注（四部备要本《四书集注》）"
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
    urls = []; pub = set(D["pub"]); yw = dict(D["yw"]); qw = D.get("qw") or {}
    for c, q in qw.items(): yw.setdefault(c, q["text"])  # 未讲章也有原文（全书上网后各章都有页）
    U = lambda rel: f"{DOMAIN}/{L.prefix}{rel}"
    head = lambda h, sub, crumb="": f'<div class="chhead"><div class="wrap">{crumb}<h1><span class="no">{esc(sub)}</span>{esc(h)}</h1></div></div>'
    crumb = f'<p class="crumb"><a href="{P}renwu/">人物</a></p>'
    cards = ""; card_of = {}
    for p in sorted(R, key=lambda p: -len(p["apps"])):
        n_pub = sum(1 for a in p["apps"] if a[0] in pub)
        items = ""
        for c, say in p["apps"]:
            if say and c in yw and HAN(say) == HAN(yw[c]): say = ""  # “该章所述”就是本章经文时不重复
            if c in pub or c in qw:
                tag = "" if c in pub else '<i class="wjtag">未讲</i>'
                items += f'<li><a href="{P}{rel_of(c)}"><em>{c}</em><b>{esc(title_of(c))}</b>{tag}</a>' + (f'<p class="zy" lang="zh-Hans">{esc(yw[c])}</p>' if c in yw else "") + (f'<p class="zd">{esc(say)}</p>' if say else "") + "</li>"
            else:
                items += f'<li><span class="gsnot"><em>{c}</em><b>未讲</b></span>' + (f'<p class="zd">{esc(say)}</p>' if say else "") + "</li>"
        meta = "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in (("字、别称", p["alias"]), ("身份", p["role"]), ("与孔子", p["rel"]), ("出处", p["src"])) if v)
        rel = f"renwu/{p['id']}.html"
        bk = "、".join(f"《{b}》" for b in p["books"])
        body = head(p["name"], f"{bk}出场 {len(p['apps'])} 章，已讲 {n_pub} 章", crumb) + f'''
<main class="wrap narrow"><dl class="rwmeta">{meta}</dl><h2 class="ph">{bk}出场各章</h2><ol class="ztl">{items}</ol>
<p class="note">按本站分章排列。已讲的章带读法与注家原页；标“未讲”的章只有原文与各家注。</p></main>'''
        ld = {"@context": "https://schema.org", "@type": "Person", "name": p["name"], "alternateName": [x for x in re.split(r"[、，,]", p["alias"]) if x] or None,
              "description": p["role"] or None, "url": U(rel), "subjectOf": {"@type": "Book", "name": "论语"}}
        ld = {k: v for k, v in ld.items() if v}
        write(rel, page(L, f"{p['name']}：《论语》里的出场各章｜一孔录", f"{p['name']}（{p['alias']}）{p['role']}，《论语》出场 {len(p['apps'])} 章。"[:110], rel, body, ld)); urls.append(U(rel))
        card_of[p["id"]] = f'<a class="rwcard" href="{P}{rel}"><b>{esc(p["name"])}</b><small>{esc(p["alias"])}</small><span>{len(p["apps"])} 章</span></a>'
    def grp(p):
        rel, role, n = p["rel"], p["role"], p["name"]
        if rel in ("本人", "父", "子", "女", "侄女", "兄") or (n.startswith("孔子之") and not n.endswith("友")) or n.startswith("孔子兄"): return 0
        if "弟子" in role or "弟子" in rel: return 1
        if "历史人物" in rel or "引述" in rel or "历史人物" in role: return 3
        return 2
    GN = ["孔子与家人", "弟子", "当时的人：国君、大夫与问者", "书里提到的古人"]
    groups = {}
    for p in sorted(R, key=lambda p: -len(p["apps"])): groups.setdefault(grp(p), []).append(p)
    cards = f'<h2 class="ph">《论语》<small>{len(R)} 人</small></h2><p class="note">孔子、弟子、国君、大夫与隐者，分四组，组内按出场章数排列。</p>' + "".join(f'<h3 class="ph">{GN[g]}<small>{len(groups[g])} 人</small></h3><div class="rwcards">' + "".join(card_of[p["id"]] for p in groups[g]) + "</div>" for g in sorted(groups))
    body = head("人物", "经典里出场的真实人物，每人一页列出出场各章") + f'''
<main class="wrap narrow"><p class="lead">按书分段。点进去看他在哪几章出现、说了什么、做了什么。</p>{cards}</main>'''
    write("renwu/index.html", page(L, "人物：经典里出场的真实人物｜一孔录", "一孔录所讲经典里出场的真实人物，每人一页，按书列出出场各章，链到原文与注家原页。", "renwu/", body)); urls.append(U("renwu/"))
    return urls
