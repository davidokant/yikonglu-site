#!/usr/bin/env python3
"""一孔录 yikonglu.com 静态站生成器。
输入：读法札记/*.md（只取“片里的读法”，丢“书里可走处”“观众疑问”和待核内容）、
      yuanwen.json（章号→原文）、episodes.json（集名→章号与平台 ID，只列已公开的集）。
输出：out/ 下的静态页、sitemap.xml、robots.txt、llms.txt、CNAME。
用法：python3 tools/build.py <读法札记目录> docs
"""
import json, re, sys, html, os, datetime

DOMAIN = "https://yikonglu.com"
HERE = os.path.dirname(os.path.abspath(__file__))
PIAN = {"1": ("学而", "xue-er", "学而第一"), "2": ("为政", "wei-zheng", "为政第二"),
        "3": ("八佾", "ba-yi", "八佾第三"), "4": ("里仁", "li-ren", "里仁第四")}
FIELDS = [("常见读法", "常见的理解"), ("字眼", "注里的关键字"), ("诸家", "诸家怎么说"),
          ("片里落点", "一孔录这样读")]
SOURCE = "朱熹《论语集注》（《四部备要》本）"

def esc(s): return html.escape(s, quote=True)

def clean(text):
    """去掉待核与书稿内容：括号段含待核/书里 → 删；分号段含待核 → 删。"""
    text = re.sub(r"（[^（）]*(待核|书里)[^（）]*）", "", text)
    parts = [p for p in re.split(r"(?<=[，；])", text) if "待核" not in p]
    text = "".join(parts).strip()
    text = text.replace("照今：", "放到今天：").replace("片里", "这里")
    text = re.sub(r"【[^】]*】", "", text)
    return text.rstrip("；").strip()

def parse_zhaji(path):
    out = {}
    cur = None
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
        if m and m.group(1) in dict(FIELDS):
            v = clean(m.group(2))
            if v and not v.startswith("这里只取"): cur["fields"][m.group(1)] = v
    return out

def page(title, desc, canonical, body, jsonld=None):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="一孔录">
<link rel="stylesheet" href="/style.css">
{ld}
</head>
<body>
<header class="top"><a href="/" class="brand">一孔录</a><nav><a href="/lunyu/">论语</a><a href="/about.html">关于</a></nav></header>
<main>
{body}
</main>
<footer>一孔录 · 在故事里读经典 · 引文据{SOURCE}，有误请告诉我们，勘误公开。<br>
YouTube · B站 · 视频号 · 公众号：「一孔录」</footer>
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
    pub = sorted(ch2ep, key=lambda c: tuple(map(int, c.split("."))))
    today = datetime.date.today().isoformat()
    urls = []
    os.makedirs(outdir, exist_ok=True)

    def write(rel, text):
        p = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)

    by_pian = {}
    for i, c in enumerate(pub):
        n = notes.get(c)
        if not n or c not in yw:
            print("跳过（缺札记或原文）", c); continue
        pnum, cnum = c.split(".")
        pname, slug, pfull = PIAN[pnum]
        epname, ep = ch2ep[c]
        rel = f"lunyu/{slug}/{cnum}.html"
        url = f"{DOMAIN}/{rel}"
        name = f"《论语·{pname}》{c} {n['title']}"
        lead = n["fields"].get("片里落点", "")
        desc = f"{yw[c][:60]}……原文、朱熹注的关键字、诸家说法与一孔录的读法。"
        rows = "".join(f"<h2>{lab}</h2><p>{esc(n['fields'][k])}</p>" for k, lab in FIELDS if k in n["fields"])
        prev_c = pub[i-1] if i > 0 else None
        next_c = pub[i+1] if i+1 < len(pub) else None
        def link(cc, lab):
            if not cc: return "<span></span>"
            pp, nn = cc.split(".")
            return f'<a href="/lunyu/{PIAN[pp][1]}/{nn}.html">{lab}{cc} {esc(notes[cc]["title"])}</a>'
        yt = ep["youtube"]
        body = f"""<article>
<p class="crumb"><a href="/lunyu/">论语</a> › <a href="/lunyu/{slug}/">{pfull}</a> › {c}</p>
<h1>{esc(n['title'])}<small>《论语·{pname}》第 {cnum} 章</small></h1>
<blockquote class="yuanwen">{esc(yw[c])}</blockquote>
<p class="src">原文与注据{SOURCE}。</p>
{rows}
<h2>看这一章的视频</h2>
<p>这一章在一孔录《{epname}》里讲。<a href="https://www.youtube.com/watch?v={yt}">YouTube 观看</a> · <a href="https://www.bilibili.com/video/{ep['bilibili']}">B站观看</a></p>
<div class="vid"><iframe loading="lazy" src="https://www.youtube-nocookie.com/embed/{yt}" title="{esc(epname)}" allowfullscreen></iframe></div>
<p class="tags">{' '.join('#'+esc(t) for t in n['tags'])}</p>
<nav class="pn">{link(prev_c,'← ')}{link(next_c,'→ ')}</nav>
</article>"""
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": name,
              "inLanguage": "zh-Hans", "url": url, "dateModified": today,
              "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN},
              "publisher": {"@type": "Organization", "name": "一孔录", "url": DOMAIN},
              "about": {"@type": "Book", "name": "论语"},
              "isBasedOn": {"@type": "Book", "name": "论语集注", "author": {"@type": "Person", "name": "朱熹"}},
              "video": {"@type": "VideoObject", "name": f"一孔录《{epname}》",
                        "embedUrl": f"https://www.youtube.com/embed/{yt}",
                        "url": f"https://www.youtube.com/watch?v={yt}",
                        "thumbnailUrl": f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg"}}
        write(rel, page(f"{name}｜原文与读法｜一孔录", desc, url, body, ld))
        urls.append(url)
        by_pian.setdefault(pnum, []).append((c, n["title"], rel, lead))

    toc_all = ""
    for pnum, items in sorted(by_pian.items(), key=lambda x: int(x[0])):
        pname, slug, pfull = PIAN[pnum]
        lis = "".join(f'<li><a href="/{rel}"><b>{c}</b> {esc(t)}</a><span>{esc(l)}</span></li>' for c, t, rel, l in items)
        body = f'<h1>{pfull}</h1><p>已讲到的章节，每章有原文、注里的关键字、诸家说法和一孔录的读法，附视频。</p><ol class="toc">{lis}</ol>'
        write(f"lunyu/{slug}/index.html", page(f"《论语·{pname}》逐章原文与读法｜一孔录", f"《论语·{pname}》逐章原文、朱熹注与一孔录的读法。", f"{DOMAIN}/lunyu/{slug}/", body))
        urls.append(f"{DOMAIN}/lunyu/{slug}/")
        toc_all += f'<h2><a href="/lunyu/{slug}/">{pfull}</a></h2><ol class="toc">{lis}</ol>'
    write("lunyu/index.html", page("《论语》逐章原文与读法｜一孔录", "《论语》逐章原文、朱熹注、诸家说法与一孔录的读法，附讲解视频。", f"{DOMAIN}/lunyu/",
          f"<h1>论语</h1><p>按篇按章排，持续更新。底本：{SOURCE}。</p>{toc_all}"))
    urls.append(f"{DOMAIN}/lunyu/")

    home = f"""<section class="hero"><h1>一孔录</h1><p class="sub">在故事里读经典</p>
<p>一孔录逐章讲读中国经典，现在读的是《论语》。每一章都从原文和注家原页读起，引文核过原书，核不到出处的话不放。</p>
<p><a class="btn" href="/lunyu/">从《论语》第一章读起</a></p></section>
<section><h2>最近讲到</h2><ol class="toc">{''.join(f'<li><a href="/{rel}"><b>{c}</b> {esc(t)}</a></li>' for p in sorted(by_pian, key=int) for c,t,rel,_ in by_pian[p][-4:])}</ol></section>"""
    write("index.html", page("一孔录｜在故事里读经典", "一孔录逐章讲读《论语》等中国经典：原文、注家原页、诸家说法与一孔录的读法，附讲解视频。", f"{DOMAIN}/", home,
          {"@context": "https://schema.org", "@type": "Organization", "name": "一孔录", "url": DOMAIN}))
    urls.insert(0, f"{DOMAIN}/")
    about = f"""<h1>关于一孔录</h1>
<p>一孔录是一个逐章讲读中国经典的频道，用讲书动画和几位固定的人物，把一句原文落到具体的人和处境上。默认你没读过原书，也不用看过前几期。</p>
<h2>我们的承诺</h2>
<ul><li>原文和注家的话都从古刻本原页取，页面写明底本。</li><li>先讲注家怎么说，再讲我们怎么读；我们自己的看法明说是一孔录的读法，不冒充古人。</li><li>核不到出处的话不放。发现错误请告诉我们，勘误公开。</li></ul>
<h2>在哪里看</h2><p>YouTube、B站、视频号「一孔录」，播客「一孔录｜在故事里读经典」（Spotify、Apple 播客、小宇宙），公众号「一孔录」。</p>"""
    write("about.html", page("关于一孔录", "一孔录是什么、怎么读经典、在哪里看。", f"{DOMAIN}/about.html", about))
    urls.append(f"{DOMAIN}/about.html")

    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    llms = [f"# 一孔录\n\n> 逐章讲读中国经典（现为《论语》）。每章含原文、朱熹《论语集注》里的关键字、诸家说法与一孔录的读法，附讲解视频。底本：{SOURCE}。引用请注明“一孔录”。\n\n## 论语\n"]
    for p in sorted(by_pian, key=int):
        for c, t, rel, l in by_pian[p]:
            llms.append(f"- [{c} {t}]({DOMAIN}/{rel}): {l}\n")
    write("llms.txt", "".join(llms))
    write("CNAME", "yikonglu.com\n")
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    write("style.css", css)
    print(f"生成 {len(urls)} 页 → {outdir}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
