#!/usr/bin/env python3
"""一孔录 yikonglu.com 静态站生成器。
输入：读法札记/*.md（只取“片里的读法”，丢“书里可走处”“观众疑问”和待核内容）、
      yuanwen.json（章号→原文）、episodes.json（集名→章号与平台 ID，只列已公开的集）、assets/（横幅、印章）。
用法：python3 tools/build.py <读法札记目录> docs
"""
import json, re, sys, html, os, shutil, datetime

DOMAIN = "https://yikonglu.com"
HERE = os.path.dirname(os.path.abspath(__file__))
PIAN = {"1": ("学而", "xue-er", "学而第一", 16), "2": ("为政", "wei-zheng", "为政第二", 24),
        "3": ("八佾", "ba-yi", "八佾第三", 26), "4": ("里仁", "li-ren", "里仁第四", 26)}
FIELDS = [("常见读法", "常见的理解", "常"), ("字眼", "注里的关键字", "注"), ("诸家", "诸家怎么说", "家"),
          ("片里落点", "一孔录这样读", "读")]
SOURCE = "朱熹《论语集注》（《四部备要》本）"
TAGLINE = "逐字读经典原文"

def esc(s): return html.escape(s, quote=True)

def clean(text):
    """去掉待核与书稿内容。"""
    text = re.sub(r"（[^（）]*(待核|书里)[^（）]*）", "", text)
    parts = [p for p in re.split(r"(?<=[，；])", text) if "待核" not in p]
    text = "".join(parts).strip()
    text = text.replace("照今：", "放到今天：").replace("片里", "这里")
    text = re.sub(r"【[^】]*】", "", text)
    return text.rstrip("；，").strip()

def parse_zhaji(path):
    out, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"^### \S+ (\d+\.\d+) (.+)$", line)
        if m:
            cur = {"no": m.group(1), "title": m.group(2).strip(), "fields": {}, "tags": []}
            out[cur["no"]] = cur
            continue
        if not cur: continue
        if line.startswith("集："):
            t = re.search(r"标签：(.*)$", line)
            if t: cur["tags"] = [x.lstrip("#") for x in t.group(1).split() if x.startswith("#")]
            continue
        m = re.match(r"^- ([^：]+)：(.*)$", line)
        if m and m.group(1) in {f[0] for f in FIELDS}:
            v = clean(m.group(2))
            if v and not v.startswith("这里只取"): cur["fields"][m.group(1)] = v
    return out

def quotes(s):
    """把“引文”包成 <q>，方便上色。"""
    return re.sub(r"“([^”]+)”", r'<span class="q">“\1”</span>', esc(s).replace("&quot;", '"'))

HEAD_FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;900&display=swap" rel="stylesheet">'

CSSV = __import__("hashlib").md5(open(os.path.join(HERE, "style.css"), "rb").read()).hexdigest()[:8]

def page(title, desc, canonical, body, jsonld=None, cls=""):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/seal-180.png">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="一孔录">
<meta property="og:image" content="{DOMAIN}/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
{HEAD_FONTS}
<link rel="stylesheet" href="/style.css?v={CSSV}">
{ld}
</head>
<body class="{cls}">
<header class="top"><div class="wrap">
<a href="/" class="brand"><img src="/assets/seal-180.png" alt="" width="30" height="30">一孔录</a>
<nav><a href="/lunyu/">论语</a><a href="/about.html">关于</a></nav>
</div></header>
{body}
<footer><div class="wrap">
<div class="fbrand"><img src="/assets/seal-180.png" alt="" width="36" height="36"><div><b>一孔录</b><span>{TAGLINE}</span></div></div>
<p>引文据{SOURCE}。发现错误请告诉我们，勘误公开。</p>
<p class="where">YouTube · B站 · 视频号 · 公众号 · 播客：搜「一孔录」</p>
</div></footer>
</body>
</html>
"""

def main(zdir, outdir):
    yw = json.load(open(os.path.join(HERE, "yuanwen.json"), encoding="utf-8"))
    eps = json.load(open(os.path.join(HERE, "episodes.json"), encoding="utf-8"))
    notes = {}
    for f in sorted(os.listdir(zdir)):
        if f.endswith(".md") and f not in ("说明.md", "主题线.md"):
            notes.update(parse_zhaji(os.path.join(zdir, f)))
    ch2ep = {c: (name, e) for name, e in eps.items() for c in e["chapters"]}
    key = lambda c: tuple(map(int, c.split(".")))
    pub = [c for c in sorted(ch2ep, key=key) if c in notes and c in yw]
    for c in sorted(ch2ep, key=key):
        if c not in pub: print("跳过（缺札记或原文）", c)
    today = datetime.date.today().isoformat()
    urls = []
    if os.path.isdir(outdir):
        for x in os.listdir(outdir):
            p = os.path.join(outdir, x)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(outdir, exist_ok=True)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(outdir, "assets"))

    def write(rel, text):
        p = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(p) or outdir, exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)

    def rel_of(c):
        p, n = c.split(".")
        return f"lunyu/{PIAN[p][1]}/{n}.html"

    by_pian = {}
    for c in pub:
        by_pian.setdefault(c.split(".")[0], []).append(c)

    for i, c in enumerate(pub):
        n = notes[c]
        pnum, cnum = c.split(".")
        pname, slug, pfull, _ = PIAN[pnum]
        epname, ep = ch2ep[c]
        rel = rel_of(c); url = f"{DOMAIN}/{rel}"
        name = f"《论语·{pname}》{c} {n['title']}"
        desc = f"{yw[c][:60]}……原文、朱熹注的关键字、诸家说法与一孔录的读法。"
        secs = "".join(
            f'<section class="sec sec-{mark}"><h2><i>{mark}</i>{lab}</h2><p>{quotes(n["fields"][k])}</p></section>'
            for k, lab, mark in FIELDS if k in n["fields"])
        prev_c = pub[i-1] if i > 0 else None
        next_c = pub[i+1] if i+1 < len(pub) else None
        def card(cc, lab, cls):
            if not cc: return '<span></span>'
            return f'<a class="pncard {cls}" href="/{rel_of(cc)}"><small>{lab}</small><b>{cc}　{esc(notes[cc]["title"])}</b></a>'
        side = "".join(
            f'<li{" class=cur" if cc == c else ""}><a href="/{rel_of(cc)}"><em>{cc.split(".")[1]}</em>{esc(notes[cc]["title"])}</a></li>'
            for cc in by_pian[pnum])
        yt = ep["youtube"]
        body = f"""<div class="chhead"><div class="wrap">
<p class="crumb"><a href="/lunyu/">论语</a> › <a href="/lunyu/{slug}/">{pfull}</a></p>
<h1><span class="no">{pname} · 第 {cnum} 章</span>{esc(n['title'])}</h1>
</div></div>
<main class="wrap chapter">
<article>
<figure class="yuanwen"><blockquote>{esc(yw[c])}</blockquote><figcaption>原文与注据{SOURCE}</figcaption></figure>
{secs}
<section class="video"><h2><i>看</i>看这一章的视频</h2>
<div class="vid"><iframe loading="lazy" src="https://www.youtube-nocookie.com/embed/{yt}" title="{esc(epname)}" allowfullscreen></iframe></div>
<p class="vlinks">这一章在一孔录《{epname}》里讲：<a href="https://www.youtube.com/watch?v={yt}">YouTube</a><a href="https://www.bilibili.com/video/{ep['bilibili']}">B站</a></p></section>
<p class="tags">{''.join(f'<span>#{esc(t)}</span>' for t in n['tags'])}</p>
<nav class="pn">{card(prev_c,'上一章','prev')}{card(next_c,'下一章','next')}</nav>
</article>
<aside><h3>{pfull}</h3><ol>{side}</ol></aside>
</main>"""
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": name,
              "inLanguage": "zh-Hans", "url": url, "dateModified": today, "image": f"{DOMAIN}/assets/og.jpg",
              "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN},
              "publisher": {"@type": "Organization", "name": "一孔录", "url": DOMAIN,
                            "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/assets/seal-180.png"}},
              "about": {"@type": "Book", "name": "论语"},
              "isBasedOn": {"@type": "Book", "name": "论语集注", "author": {"@type": "Person", "name": "朱熹"}},
              "video": {"@type": "VideoObject", "name": f"一孔录《{epname}》",
                        "description": f"一孔录讲读《论语·{pname}》，含本章。",
                        "embedUrl": f"https://www.youtube.com/embed/{yt}",
                        "url": f"https://www.youtube.com/watch?v={yt}",
                        "thumbnailUrl": f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg"}}
        write(rel, page(f"{name}｜原文与读法｜一孔录", desc, url, body, ld, "pg-chapter"))
        urls.append(url)

    def toc(cs):
        return '<ol class="toc">' + "".join(
            f'<li><a href="/{rel_of(c)}"><em>{c}</em><b>{esc(notes[c]["title"])}</b>'
            f'<span>{esc(notes[c]["fields"].get("片里落点", "").split("；")[0])}</span></a></li>' for c in cs) + "</ol>"

    def pcard(p):
        pname, slug, pfull, total = PIAN[p]
        done = len(by_pian[p]); pct = round(done * 100 / total)
        return (f'<a class="pcard" href="/lunyu/{slug}/"><b>{pname}</b><small>{pfull}</small>'
                f'<span class="bar"><i style="width:{pct}%"></i></span><em>已讲 {done} / {total} 章</em></a>')

    toc_all = ""
    for p in sorted(by_pian, key=int):
        pname, slug, pfull, total = PIAN[p]
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="/lunyu/">论语</a></p>
<h1><span class="no">《论语》第 {p} 篇 · 已讲 {len(by_pian[p])} / {total} 章</span>{pfull}</h1></div></div>
<main class="wrap narrow"><p class="lead">每章有原文、注里的关键字、诸家说法和一孔录的读法，附视频。</p>{toc(by_pian[p])}</main>'''
        write(f"lunyu/{slug}/index.html", page(f"《论语·{pname}》逐章原文与读法｜一孔录", f"《论语·{pname}》逐章原文、朱熹注与一孔录的读法。", f"{DOMAIN}/lunyu/{slug}/", body))
        urls.append(f"{DOMAIN}/lunyu/{slug}/")
        toc_all += f'<h2 class="ph"><a href="/lunyu/{slug}/">{pfull}</a></h2>{toc(by_pian[p])}'
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">二十篇 · 持续更新</span>论语</h1></div></div>
<main class="wrap narrow"><p class="lead">按篇按章排。底本：{SOURCE}。</p>
<div class="pcards">{"".join(pcard(p) for p in sorted(by_pian, key=int))}</div>{toc_all}</main>'''
    write("lunyu/index.html", page("《论语》逐章原文与读法｜一孔录", "《论语》逐章原文、朱熹注、诸家说法与一孔录的读法，附讲解视频。", f"{DOMAIN}/lunyu/", body))
    urls.append(f"{DOMAIN}/lunyu/")

    recent = pub[-6:][::-1]
    home = f'''<section class="banner">
<picture><source media="(max-width:700px)" srcset="/assets/banner-1000.jpg"><img src="/assets/banner.jpg" alt="一孔录群像：一张长桌边围坐读书的人物" width="3072" height="1024" style="width:100%;height:auto;max-height:420px;object-fit:cover"></picture>
</section>
<main class="home">
<section class="intro wrap narrow">
<h1>一孔录<small>{TAGLINE}</small></h1>
<p>一孔录逐章讲读中国经典，现在读的是《论语》。每一章从原文和注家原页读起，再落到一个今天的处境里。默认你没读过原书，也不用看过前几期。</p>
<p class="cta"><a class="btn" href="/{rel_of(pub[0])}">从第一章读起</a><a class="btn ghost" href="/lunyu/">看全部目录</a></p>
</section>
<section class="pillars wrap">
<div><i>原</i><b>原文上屏</b><p>原文和注都从古刻本原页取，写明底本，句句可核。</p></div>
<div><i>注</i><b>诸家并读</b><p>先讲朱熹在哪个字停、诸家怎么分，再讲我们怎么读。</p></div>
<div><i>今</i><b>放到今天</b><p>一句原文落到一个具体的人、一个今天的处境上。</p></div>
</section>
<section class="wrap narrow"><h2 class="ph">正在读：《论语》</h2><div class="pcards">{"".join(pcard(p) for p in sorted(by_pian, key=int))}</div></section>
<section class="wrap narrow"><h2 class="ph">最近讲到</h2>{toc(recent)}</section>
</main>'''
    write("index.html", page(f"一孔录｜{TAGLINE}", "一孔录逐章讲读《论语》等中国经典：原文、注家原页、诸家说法与一孔录的读法，附讲解视频。", f"{DOMAIN}/", home,
          {"@context": "https://schema.org", "@type": "Organization", "name": "一孔录", "url": DOMAIN,
           "logo": f"{DOMAIN}/assets/seal-180.png"}, "pg-home"))
    urls.insert(0, f"{DOMAIN}/")
    about = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{TAGLINE}</span>关于一孔录</h1></div></div>
<main class="wrap narrow prose">
<p>一孔录是一个逐章讲读中国经典的频道，用讲书动画和几位固定的人物，把一句原文落到具体的人和处境上。默认你没读过原书，也不用看过前几期。</p>
<h2>我们的承诺</h2>
<ul><li>原文和注家的话都从古刻本原页取，页面写明底本。</li><li>先讲注家怎么说，再讲我们怎么读；我们自己的看法明说是一孔录的读法，不冒充古人。</li><li>核不到出处的话不放。发现错误请告诉我们，勘误公开。</li></ul>
<h2>在哪里看</h2><p>YouTube、B站、视频号「一孔录」，播客「一孔录｜在故事里读经典」（Spotify、Apple 播客、小宇宙、喜马拉雅），公众号「一孔录」。</p>
</main>'''
    write("about.html", page("关于一孔录", "一孔录是什么、怎么读经典、在哪里看。", f"{DOMAIN}/about.html", about))
    urls.append(f"{DOMAIN}/about.html")

    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    llms = [f"# 一孔录\n\n> 逐章讲读中国经典（现为《论语》）。每章含原文、朱熹《论语集注》里的关键字、诸家说法与一孔录的读法，附讲解视频。底本：{SOURCE}。引用请注明“一孔录”。\n\n## 论语\n"]
    for c in pub:
        llms.append(f"- [{c} {notes[c]['title']}]({DOMAIN}/{rel_of(c)}): {notes[c]['fields'].get('片里落点', '')}\n")
    write("llms.txt", "".join(llms))
    write("CNAME", "yikonglu.com\n")
    write(".nojekyll", "")
    shutil.copy(os.path.join(HERE, "style.css"), os.path.join(outdir, "style.css"))
    print(f"生成 {len(urls)} 页 → {outdir}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
