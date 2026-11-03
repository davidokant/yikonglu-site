#!/usr/bin/env python3
"""一孔录 yikonglu.com 静态站生成器（多语种）。
输入：读法札记/*.md（只取“片里的读法”，丢“书里可走处”“观众疑问”和待核内容）、
      yuanwen.json（章号→原文）、episodes.json（集名→章号与平台 ID，只列已公开的集）、assets/（横幅、印章）、
      共享盘 数据/网站素材/<期名>/（定版稿：引文取处、读音表；原页 png）、数据/网站勘误.md、
      i18n/<lang>.json（界面与各章译文；缺的章回落到中文并标注）。
语种：zh-Hans（根目录）、zh-Hant（/zh-hant/，OpenCC 自动转台湾用字）、en（/en/）。
用法：python3 tools/build.py <读法札记目录> docs
"""
import json, re, sys, html, os, shutil, datetime, glob

DOMAIN = "https://yikonglu.com"
HERE = os.path.dirname(os.path.abspath(__file__))
PIAN = {"1": ("学而", "xue-er", "学而第一", 16), "2": ("为政", "wei-zheng", "为政第二", 24),
        "3": ("八佾", "ba-yi", "八佾第三", 26), "4": ("里仁", "li-ren", "里仁第四", 26)}
FIELDS = [("常见读法", "f_common", "常"), ("字眼", "f_keys", "注"), ("诸家", "f_others", "家"), ("片里落点", "f_ours", "读")]
SOURCE = "朱熹《论语集注》（《四部备要》本）"
TAGLINE = "逐字读经典原文"
GAO_DIR = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材"  # 定版稿只在共享盘读取，不进公开仓库
KANWU_DEFAULT = "/mnt/project-files/一孔学-内-自媒体/数据/网站勘误.md"
INTERNAL = re.compile(r"（[^（）]*(只|转述|不上屏|不念|常识|核不到|见注|今读)[^（）]*）")

HANT_FIX = {"余力": "餘力", "余，": "餘，", "余者": "餘者", "诗云": "詩云", "子云": "子云", "干禄": "干祿"}  # 护住后手工给的繁体
LANGS = {  # code: (路径前缀, 自称, hreflang)
    "zh-Hans": ("", "简体中文", "zh-Hans"),
    "zh-Hant": ("zh-hant/", "繁體中文", "zh-Hant"),
    "en": ("en/", "English", "en"),
    "ja": ("ja/", "日本語", "ja"),
    "ko": ("ko/", "한국어", "ko"),
    "fr": ("fr/", "Français", "fr"),
    "es": ("es/", "Español", "es"),
}

ZH_UI = {
 "tagline": TAGLINE, "nav_books": "书目", "nav_search": "检索", "nav_errata": "勘误", "nav_about": "关于",
 "motto": "一孔录讲过的每一句，都能在这里核。",
 "intro": "原文、底本页码、注家原话、读音、我们的读法、公开勘误，按书按章排好。视频在各平台看，核对来这里。",
 "search_ph": "搜原文、注家原话，如：鸟数飞", "btn_books": "按书目找", "btn_errata": "看勘误",
 "p1t": "底本可查", "p1": "原文和注都从古刻本原页取，每条引文标出底本页，原页图可放大看。",
 "p2t": "注家原话", "p2": "引到谁就写谁，朱熹、程子、谢氏分开标；转述和原话分开，核不到出处的不放。",
 "p3t": "勘误公开", "p3": "讲错的地方改了就记：哪集哪句、原来怎么说、改成什么、依据是什么。",
 "books": "书目", "recent": "最近收录", "lunyu": "论语", "lunyu_sub": "二十篇 · 持续更新",
 "by_chapter": f"按篇按章排。底本：{SOURCE}。",
 "book_lead": "每章有原文、注里的关键字、诸家说法和一孔录的读法，附视频。", "covered": "已讲 {done} / {total} 章",
 "f_common": "常见的理解", "f_keys": "注里的关键字", "f_others": "诸家怎么说", "f_ours": "一孔录这样读",
 "cites": "本章引文逐条核对", "cites_note": "视频里引到的每一句注：原话、出自谁、在底本哪一页。标“转述”的是我们概括的意思，不是原话。",
 "th_quote": "引文原话", "th_src": "出自", "th_page": "底本页", "para": "转述", "pg": "原页 {n}", "other_ed": "另本",
 "reads": "读音", "th_zi": "字", "th_pos": "位置", "th_du": "读", "shots": "底本原页",
 "kw": "本章勘误", "kw_note": "", "cite": "引用本页", "copy": "复制", "copied": "已复制",
 "checked": "本页最后核对：{d}。改动记在", "errata_page": "勘误页",
 "video": "看这一章的视频", "video_in": "这一章在一孔录《{ep}》里讲：", "cn_note": "（大陆请点 B站）",
 "prev": "上一章", "next": "下一章", "chapter_no": "{book} · 第 {n} 章", "book_no": "《论语》第 {n} 篇 · 已讲 {done} / {total} 章",
 "source_line": f"原文与注据{SOURCE}", "rendering": "",
 "errata_title": "公开勘误", "errata_sub": "原文·引文·出处·读音·读法",
 "errata_p1": "一孔录讲错或说满的地方，改了就记在这里，按时间倒排，旧记录不删。画面上的小问题不记，只记内容。",
 "errata_p2": "发现错误，请写邮件到下面这个邮箱，写明哪集哪句、依据是什么，再写上你想署的网名。核实后记入此页，勘误者一栏署你的网名。也可以在任一平台「一孔录」视频下留言。", "mail_note": "邮箱做成了图片防垃圾邮件，请手动输入。", "report": "本章有错？写信告诉我们，核实后署你的网名记入勘误：", "errata_empty": "目前没有勘误。",
 "search_title": "检索", "search_sub": "原文 · 注家原话 · 读法", "search_ph2": "输入几个字，如：鸟数飞、主一无适、孝弟",
 "search_n": "找到 {n} 章", "search_none": "没有找到。已收录的只有讲过的章节。",
 "about_title": "关于一孔录", "about_p": "一孔录是一个逐字逐章读中国经典原文的频道，用讲书动画和几位固定的人物，把一句原文落到具体的人和处境上。默认你没读过原书，也不用看过前几期。",
 "about_h1": "这个网站做什么", "about_site": "平台上的视频面向大众，这里面向想核对的人：一孔录讲过的每一句，原文、底本页码、注家原话、读音、我们的读法，都能在这里查到，讲错的地方在<a href=\"kanwu.html\">勘误页</a>公开记录。",
 "about_h2": "我们的承诺", "about_c1": "原文和注家的话都从古刻本原页取，页面写明底本。", "about_c2": "先讲注家怎么说，再讲我们怎么读；我们自己的看法明说是一孔录的读法，不冒充古人。", "about_c3": "核不到出处的话不放。发现错误请告诉我们，勘误公开。",
 "about_h3": "在哪里看", "about_where": "YouTube、B站、视频号「一孔录」，播客「一孔录」（Spotify、Apple 播客、小宇宙、喜马拉雅），公众号「一孔录」。",
 "foot_src": "引文均据古刻本原页，各页注明底本。发现错误请告诉我们，勘误公开。", "foot_where": "YouTube · B站 · 视频号 · 公众号 · 播客：搜「一孔录」",
 "lang_bar": "", "lang_go": "", "lang_close": "", "translated_note": "",
 "cite_fmt": "一孔录《论语·{book}》{c}“{title}”，{url}，{d} 版。",
 "hant_note": "繁體頁面由簡體自動轉換，用字按台灣習慣；原文以底本原頁為準。",
}

def esc(s): return html.escape(s, quote=True)

def clean(text):
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
    return re.sub(r"“([^”]+)”", r'<span class="q">“\1”</span>', esc(s).replace("&quot;", '"'))

def md_tables(lines, start_pat):
    rows, on, intable = [], False, False
    for l in lines:
        if re.match(r"^## ", l):
            if on and rows: break
            on = bool(re.match(start_pat, l)); continue
        if not on: continue
        if l.startswith("|"):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells): intable = True; continue
            if intable: rows.append(cells)
        elif intable and rows and not l.strip(): break
    return rows

CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
def cn2int(t):
    if t.isdigit(): return int(t)
    if len(t) == 1: return CN[t]
    if t[0] == "十": return 10 + CN[t[1]]
    if t[-1] == "十": return CN[t[0]] * 10
    return CN[t[0]] * 10 + CN[t[2]]
PIAN_NUM = {"学而": "1", "为政": "2", "八佾": "3", "里仁": "4"}

def parse_gao(path, yw):
    L = open(path, encoding="utf-8").read().replace("\r", "").split("\n")
    kmap, cur = {}, None
    for l in L:
        m = re.match(r"^### 第(.+?)章", l)
        if m: cur = m.group(0)
        if re.match(r"^### (开场|片尾)", l): cur = None
        k = re.match(r"^\*\*(K\d+)", l)
        if k and cur: kmap[k.group(1)] = cur
    pnum = next((v for k2, v in PIAN_NUM.items() if k2 in os.path.basename(path)), None)
    out = {}
    sec2ch = {sec: f"{pnum}.{cn2int(re.match(r'^### 第(.+?)章', sec).group(1))}" for sec in set(kmap.values())} if pnum else {}
    for row in md_tables(L, r"^## 引文取处"):
        if len(row) < 4: continue
        k, text, src, page = row[:4]
        c = sec2ch.get(kmap.get(k))
        if not c or "待核" in page or "待核" in text: continue
        para = bool(re.search(r"（[^（）]*(转述)[^（）]*）", text)) and not re.search(r"只原样念|前半转述|前后转述", text)
        text = INTERNAL.sub("", text).strip("；; ")
        if src == "经文" or not text: continue
        pages = re.findall(r"PDF0*(\d+)", page)
        other = ""
        if not pages:
            m = re.search(r"核到（([^（）]*)", page)
            other = m.group(1).split("，")[0].split("；")[0] if m else ""
        out.setdefault(c, {"cites": [], "reads": []})["cites"].append({"text": text, "src": src.replace("**", ""), "pages": pages, "para": para, "other": other})
    for row in md_tables(L, r"^## 读音"):
        if len(row) < 3: continue
        zi, pos, du = row[:3]
        if "见注" in du: continue
        for c in sec2ch.values():
            if c in yw and pos and any(x and x in yw[c] for x in pos.split("、")):
                r = out.setdefault(c, {"cites": [], "reads": []})["reads"]
                if (zi, pos) not in [(a["zi"], a["pos"]) for a in r]:
                    r.append({"zi": zi, "pos": pos, "du": du})
    return out

def parse_kanwu(path):
    rows = []
    if not os.path.exists(path): return rows
    for l in open(path, encoding="utf-8"):
        if l.startswith("|") and not l.startswith("| 日期") and not re.match(r"^\|[-| ]+\|$", l.strip()):
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            if len(c) >= 7 and re.match(r"\d{4}-\d{2}-\d{2}", c[0]):
                r = [x.replace("线程", "") for x in c[:8]] + [""] * (8 - len(c[:8]))
                if not r[7] or r[7] in ("—", "-", "自查", "一孔录"): r[7] = "一孔录自查"
                rows.append(r)
    return rows

HEAD_FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;900&family=Noto+Serif+JP:wght@400;600;900&family=Noto+Serif+KR:wght@400;600;900&display=swap" rel="stylesheet" media="print" onload="this.media=\'all\'">'
MAIL = '<picture class="mail"><source srcset="/assets/mail-dark.png" media="(prefers-color-scheme:dark)"><img src="/assets/mail.png" alt="email (image)" width="211" height="26"></picture>'
CSSV = __import__("hashlib").md5(open(os.path.join(HERE, "style.css"), "rb").read()).hexdigest()[:8]

LANG_JS = """<script>
(function(){var P=document.documentElement.lang,K='yk_lang';try{var s=localStorage.getItem(K)}catch(e){var s=null}
document.querySelectorAll('[data-lang]').forEach(function(a){a.addEventListener('click',function(){try{localStorage.setItem(K,a.dataset.lang)}catch(e){}})});
if(s)return;var n=(navigator.language||'').toLowerCase(),w=null;
if(n.startsWith('en'))w='en';else if(n.startsWith('ja'))w='ja';else if(n.startsWith('ko'))w='ko';else if(n.startsWith('fr'))w='fr';else if(n.startsWith('es'))w='es';else if(n.startsWith('zh')&&/tw|hk|mo|hant/.test(n))w='zh-Hant';else if(n.startsWith('zh'))w='zh-Hans';
if(!w||w===P)return;var a=document.querySelector('link[hreflang="'+w+'"]');if(!a)return;
var t={en:['This page is available in English.','Switch to English'],ja:['このページには日本語版があります。','日本語に切り替える'],ko:['이 페이지는 한국어판이 있습니다.','한국어로 전환'],fr:['Cette page existe en français.','Passer au français'],es:['Esta página está disponible en español.','Cambiar a español'],'zh-Hant':['本頁有繁體中文版。','切換到繁體'],'zh-Hans':['本页有简体中文版。','切换到简体']}[w];
var b=document.createElement('div');b.className='langbar';b.innerHTML='<span>'+t[0]+'</span><a href="'+a.href+'">'+t[1]+' →</a><button aria-label="close">×</button>';
b.querySelector('a').onclick=function(){try{localStorage.setItem(K,w)}catch(e){}};b.querySelector('button').onclick=function(){try{localStorage.setItem(K,P)}catch(e){}b.remove()};
document.body.prepend(b)})();
</script>"""

class Lang:
    def __init__(self, code, ui, tr=None):
        self.code = code; self.prefix, self.name, self.hreflang = LANGS[code]
        self.ui = ui; self.tr = tr or {}
    def t(self, k, **kw):
        s = self.ui.get(k, ZH_UI.get(k, k))
        return s.format(**kw) if kw else s
    def ch(self, c): return self.tr.get("chapters", {}).get(c, {})
    def src(self, s): return self.tr.get("src", {}).get(s, s)
    def book(self, p):
        return self.tr.get("books", {}).get(p, PIAN[p][2])

def page(L, title, desc, rel, body, jsonld=None, cls="", alts=None):
    """rel：不带语种前缀的站内路径（"" 为首页）。"""
    url = f"{DOMAIN}/{L.prefix}{rel}"
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    alt_links = "".join(f'<link rel="alternate" hreflang="{LANGS[k][2]}" href="{DOMAIN}/{LANGS[k][0]}{rel}">' for k in LANGS)
    alt_links += f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/{rel}">'
    sw = "".join(f'<a href="{DOMAIN}/{LANGS[k][0]}{rel}" data-lang="{k}"{" class=cur" if k == L.code else ""}>{LANGS[k][1]}</a>' for k in LANGS)
    P = "/" + L.prefix
    note = f'<p class="trnote wrap">{L.t("translated_note")}</p>' if L.t("translated_note") else ""
    return f"""<!doctype html>
<html lang="{L.hreflang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
{alt_links}
<link rel="icon" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/seal-180.png">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="一孔录">
<meta property="og:image" content="{DOMAIN}/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
{HEAD_FONTS}
<link rel="stylesheet" href="/style.css?v={CSSV}">
{ld}
</head>
<body class="{cls}">
<header class="top"><div class="wrap">
<a href="{P}" class="brand"><img src="/assets/seal-180.png" alt="" width="30" height="30">一孔录</a>
<nav><a href="{P}lunyu/">{L.t("nav_books")}</a><a href="{P}search.html">{L.t("nav_search")}</a><a href="{P}kanwu.html">{L.t("nav_errata")}</a><a href="{P}about.html">{L.t("nav_about")}</a>
<details class="lang"><summary>{L.name}</summary><div>{sw}</div></details></nav>
</div></header>
{note}
{body}
<footer><div class="wrap">
<div class="fbrand"><img src="/assets/seal-180.png" alt="" width="36" height="36"><div><b>一孔录</b><span>{L.t("tagline")}</span></div></div>
<p>{L.t("foot_src")}</p>
<p class="where">{L.t("foot_where")}</p>
<p class="langs">{sw}</p>
</div></footer>
{LANG_JS}
</body>
</html>
"""

def build_lang(L, D, write):
    """D：公共数据。write(rel, html) 写到该语种目录。返回本语种 URL 列表。"""
    notes, yw, gao, kw, pub, by_pian, ch2ep, pages_avail, today = (D[k] for k in ("notes", "yw", "gao", "kw", "pub", "by_pian", "ch2ep", "pages_avail", "today"))
    P = "/" + L.prefix
    urls = []
    def rel_of(c):
        p, n = c.split("."); return f"lunyu/{PIAN[p][1]}/{n}.html"
    def title_of(c): return L.ch(c).get("title") or notes[c]["title"]
    def field(c, k):
        v = L.ch(c).get(k)
        return (v, True) if v else (notes[c]["fields"].get(k), False)
    search_idx = []

    for i, c in enumerate(pub):
        n = notes[c]; pnum, cnum = c.split("."); pname, slug, pfull, _ = PIAN[pnum]
        epname, ep = ch2ep[c]; rel = rel_of(c); url = f"{DOMAIN}/{L.prefix}{rel}"
        bname = L.book(pnum)
        name = f"《论语·{pname}》{c} {n['title']}" if L.code == "zh-Hans" else f"{L.t('lunyu')} {c} {title_of(c)}"
        desc = f"{yw[c][:60]}……原文、朱熹注的关键字、诸家说法与一孔录的读法。" if L.code == "zh-Hans" else f"{yw[c][:40]}… {L.t('book_lead')}"
        secs = ""
        for k, lab, mark in FIELDS:
            v, translated = field(c, k)
            if not v: continue
            secs += f'<section class="sec sec-{mark}"><h2><i>{mark}</i>{L.t(lab)}</h2><p{"" if translated or L.code=="zh-Hans" else " lang=zh-Hans"}>{quotes(v)}</p></section>'
        prev_c = pub[i-1] if i > 0 else None; next_c = pub[i+1] if i+1 < len(pub) else None
        def card(cc, lab, cls):
            if not cc: return '<span></span>'
            return f'<a class="pncard {cls}" href="{P}{rel_of(cc)}"><small>{lab}</small><b>{cc}　{esc(title_of(cc))}</b></a>'
        side = "".join(f'<li{" class=cur" if cc == c else ""}><a href="{P}{rel_of(cc)}"><em>{cc.split(".")[1]}</em>{esc(title_of(cc))}</a></li>' for cc in by_pian[pnum])
        yt = ep["youtube"]; g = gao.get(c, {"cites": [], "reads": []})
        def pg(nums):
            return " ".join(f'<a class="pg" href="/yuanye/p{int(x):03d}.jpg" target="_blank">{L.t("pg", n=x)}</a>' if x in pages_avail else f'<span class="pg">{L.t("pg", n=x)}</span>' for x in nums)
        extra = ""
        if g["cites"]:
            extra += (f'<section class="sec cites"><h2><i>核</i>{L.t("cites")}</h2><p class="note">{L.t("cites_note")}</p><table><thead><tr><th>{L.t("th_quote")}</th><th>{L.t("th_src")}</th><th>{L.t("th_page")}</th></tr></thead><tbody>'
                      + "".join(f'<tr><td lang="zh-Hans">{"<span class=para>" + L.t("para") + "</span>" + esc(x["text"]) if x["para"] else "“" + esc(x["text"]) + "”"}</td><td>{esc(L.src(x["src"]))}</td><td>{pg(x["pages"]) if x["pages"] else "<span class=oth>" + esc(x["other"] or L.t("other_ed")) + "</span>"}</td></tr>' for x in g["cites"]) + "</tbody></table></section>")
        if g["reads"]:
            extra += (f'<section class="sec reads"><h2><i>音</i>{L.t("reads")}</h2><table><thead><tr><th>{L.t("th_zi")}</th><th>{L.t("th_pos")}</th><th>{L.t("th_du")}</th></tr></thead><tbody>'
                      + "".join(f'<tr><td class="zi">{esc(x["zi"])}</td><td>{esc(x["pos"])}</td><td>{esc(x["du"])}</td></tr>' for x in g["reads"]) + "</tbody></table></section>")
        allpages = sorted({x for r in g["cites"] for x in r["pages"]}, key=int)
        imgs = "".join(f'<a href="/yuanye/p{int(x):03d}.jpg" target="_blank"><img loading="lazy" src="/yuanye/p{int(x):03d}.jpg" alt="{L.t("pg", n=x)}"><span>{L.t("pg", n=x)}</span></a>' for x in allpages if x in pages_avail)
        if imgs: extra += f'<section class="sec shots"><h2><i>页</i>{L.t("shots")}</h2><div class="pages">{imgs}</div></section>'
        mine = [r for r in kw if r[2] == c]
        if mine:
            extra += (f'<section class="sec kw"><h2><i>勘</i>{L.t("kw")}</h2>{"<p class=note>" + L.t("kw_note") + "</p>" if L.t("kw_note") else ""}<ul lang="zh-Hans">' + "".join(
                f'<li><b>{esc(r[0])}　{esc(r[3])}</b>原来：{esc(r[4])}；改为：{esc(r[5])}（依据：{esc(r[6])}；勘误者：{esc(r[7])}）</li>' for r in mine) + '</ul></section>')
        cite_txt = L.t("cite_fmt", book=(pname if L.code == "zh-Hans" else bname), c=c, title=title_of(c), url=url, d=today)
        extra += f'<section class="citeit"><b>{L.t("cite")}</b><code>{esc(cite_txt)}</code><button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent);this.textContent=\'{L.t("copied")}\'">{L.t("copy")}</button><p>{L.t("checked", d=today)}<a href="{P}kanwu.html">{L.t("errata_page")}</a>.</p><p class="mailp">{L.t("report")} {MAIL}</p></section>'
        search_idx.append({"c": c, "t": title_of(c), "u": P + rel, "y": yw[c],
                           "x": " ".join(v for k, _, _ in FIELDS for v in [field(c, k)[0]] if v) + " " + " ".join(x["text"] + x["src"] for x in g["cites"])})
        rend = L.ch(c).get("yw")
        rend_html = f'<p class="rend">{esc(rend)}</p><figcaption>{L.t("rendering")}</figcaption>' if rend else ""
        body = f"""<div class="chhead"><div class="wrap">
<p class="crumb"><a href="{P}lunyu/">{L.t("lunyu")}</a> › <a href="{P}lunyu/{slug}/">{bname}</a></p>
<h1><span class="no">{L.t("chapter_no", book=(pname if L.code=="zh-Hans" else bname), n=cnum)}</span>{esc(title_of(c))}</h1>
</div></div>
<main class="wrap chapter">
<article>
<figure class="yuanwen"><blockquote lang="zh-Hans">{esc(yw[c])}</blockquote><figcaption>{L.t("source_line")}</figcaption>{rend_html}</figure>
{secs}
{extra}
<section class="video"><h2><i>看</i>{L.t("video")}</h2>
<div class="vid"><iframe loading="lazy" src="https://www.youtube-nocookie.com/embed/{yt}" title="{esc(epname)}" allowfullscreen></iframe></div>
<p class="vlinks">{L.t("video_in", ep=epname)}<a href="https://www.youtube.com/watch?v={yt}">YouTube</a><a href="https://www.bilibili.com/video/{ep['bilibili']}">Bilibili</a>{L.t("cn_note")}</p></section>
<p class="tags">{''.join(f'<span>#{esc(t)}</span>' for t in n['tags'])}</p>
<nav class="pn">{card(prev_c, L.t("prev"), 'prev')}{card(next_c, L.t("next"), 'next')}</nav>
</article>
<aside><h3>{bname}</h3><ol>{side}</ol></aside>
</main>"""
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": name,
              "inLanguage": L.hreflang, "url": url, "dateModified": today, "image": f"{DOMAIN}/assets/og.jpg",
              "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN},
              "publisher": {"@type": "Organization", "name": "一孔录", "url": DOMAIN, "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/assets/seal-180.png"}},
              "about": {"@type": "Book", "name": "论语"},
              "isBasedOn": {"@type": "Book", "name": "论语集注", "author": {"@type": "Person", "name": "朱熹"}},
              "video": {"@type": "VideoObject", "name": f"一孔录《{epname}》", "description": f"一孔录讲读《论语·{pname}》，含本章。",
                        "embedUrl": f"https://www.youtube.com/embed/{yt}", "url": f"https://www.youtube.com/watch?v={yt}",
                        "thumbnailUrl": f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg"}}
        ttl = f"{name}｜原文与读法｜一孔录" if L.code == "zh-Hans" else f"{name} | 一孔录 Yikonglu"
        write(rel, page(L, ttl, desc, rel, body, ld, "pg-chapter")); urls.append(url)

    def toc(cs):
        return '<ol class="toc">' + "".join(
            f'<li><a href="{P}{rel_of(c)}"><em>{c}</em><b>{esc(title_of(c))}</b><span>{esc((field(c, "片里落点")[0] or "").split("；")[0].split(". Today")[0])}</span></a></li>' for c in cs) + "</ol>"
    def pcard(p):
        pname, slug, pfull, total = PIAN[p]; done = len(by_pian[p]); pct = round(done * 100 / total)
        return (f'<a class="pcard" href="{P}lunyu/{slug}/"><b>{pname}</b><small>{L.book(p)}</small><span class="bar"><i style="width:{pct}%"></i></span><em>{L.t("covered", done=done, total=total)}</em></a>')

    toc_all = ""
    for p in sorted(by_pian, key=int):
        pname, slug, pfull, total = PIAN[p]
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">{L.t("lunyu")}</a></p>
<h1><span class="no">{L.t("book_no", n=p, done=len(by_pian[p]), total=total)}</span>{L.book(p)}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("book_lead")}</p>{toc(by_pian[p])}</main>'''
        ttl = f"《论语·{pname}》逐章原文与读法｜一孔录" if L.code == "zh-Hans" else f"{L.t('lunyu')} · {L.book(p)} | 一孔录 Yikonglu"
        write(f"lunyu/{slug}/index.html", page(L, ttl, L.t("book_lead"), f"lunyu/{slug}/", body)); urls.append(f"{DOMAIN}/{L.prefix}lunyu/{slug}/")
        toc_all += f'<h2 class="ph"><a href="{P}lunyu/{slug}/">{L.book(p)}</a></h2>{toc(by_pian[p])}'
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("lunyu_sub")}</span>{L.t("lunyu")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("by_chapter")}</p><div class="pcards">{"".join(pcard(p) for p in sorted(by_pian, key=int))}</div>{toc_all}</main>'''
    write("lunyu/index.html", page(L, ("《论语》逐章原文与读法｜一孔录" if L.code == "zh-Hans" else f"{L.t('lunyu')} | 一孔录 Yikonglu"), L.t("by_chapter"), "lunyu/", body)); urls.append(f"{DOMAIN}/{L.prefix}lunyu/")

    recent = pub[-6:][::-1]
    home = f'''<section class="banner"><picture><source media="(max-width:700px)" srcset="/assets/banner-1000.jpg"><img src="/assets/banner.jpg" alt="一孔录" width="3072" height="1024" style="width:100%;height:auto;max-height:420px;object-fit:cover"></picture></section>
<main class="home">
<section class="intro wrap narrow">
<h1>一孔录<small>{L.t("tagline")}</small></h1>
<p class="motto">{L.t("motto")}</p>
<p>{L.t("intro")}</p>
<form class="sbox" action="{P}search.html"><input name="q" placeholder="{esc(L.t("search_ph"))}"><button>{L.t("nav_search")}</button></form>
<p class="cta"><a class="btn" href="{P}lunyu/">{L.t("btn_books")}</a><a class="btn ghost" href="{P}kanwu.html">{L.t("btn_errata")}</a></p>
</section>
<section class="pillars wrap">
<div><i>原</i><b>{L.t("p1t")}</b><p>{L.t("p1")}</p></div>
<div><i>注</i><b>{L.t("p2t")}</b><p>{L.t("p2")}</p></div>
<div><i>勘</i><b>{L.t("p3t")}</b><p>{L.t("p3")}</p></div>
</section>
<section class="wrap narrow"><h2 class="ph">{L.t("books")}</h2><h3 class="bookh"><a href="{P}lunyu/">《论语》{" · " + L.t("lunyu") if L.code in ("en", "fr", "es") else ""}</a></h3><div class="pcards">{"".join(pcard(p) for p in sorted(by_pian, key=int))}</div></section>
<section class="wrap narrow"><h2 class="ph">{L.t("recent")}</h2>{toc(recent)}</section>
</main>'''
    write("index.html", page(L, (f"一孔录｜{TAGLINE}" if L.code == "zh-Hans" else f"一孔录 Yikonglu | {L.t('tagline')}"), L.t("intro"), "", home,
          {"@context": "https://schema.org", "@type": "Organization", "name": "一孔录", "alternateName": "Yikonglu", "url": DOMAIN, "logo": f"{DOMAIN}/assets/seal-180.png"}, "pg-home"))
    urls.insert(0, f"{DOMAIN}/{L.prefix}")
    about = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("tagline")}</span>{L.t("about_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("about_p")}</p>
<h2>{L.t("about_h1")}</h2><p>{L.t("about_site").replace('href="kanwu.html"', f'href="{P}kanwu.html"').replace('href="errata.html"', f'href="{P}kanwu.html"')}</p>
<h2>{L.t("about_h2")}</h2><ul><li>{L.t("about_c1")}</li><li>{L.t("about_c2")}</li><li>{L.t("about_c3")}</li></ul>
<h2>{L.t("about_h3")}</h2><p>{L.t("about_where")}</p></main>'''
    write("about.html", page(L, L.t("about_title"), L.t("about_p")[:120], "about.html", about)); urls.append(f"{DOMAIN}/{L.prefix}about.html")

    if kw:
        trs = "".join(f"<tr><td>{esc(r[0])}</td><td>{esc(r[1])} {esc(r[2])}</td><td>{esc(r[3])}</td><td>{esc(r[4])}</td><td>{esc(r[5])}</td><td>{esc(r[6])}</td><td class=\"who\">{esc(r[7])}</td></tr>" for r in reversed(kw))
        ktable = f'<div class="tw"><table lang="zh-Hans"><thead><tr><th>日期</th><th>集·章</th><th>类别</th><th>原来</th><th>改为</th><th>依据</th><th>勘误者</th></tr></thead><tbody>{trs}</tbody></table></div>'
    else:
        ktable = f'<p class="empty">{L.t("errata_empty")}</p>'
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("errata_sub")}</span>{L.t("errata_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("errata_p1")}</p><p>{L.t("errata_p2")}</p><p class="mailp">{MAIL}<small>{L.t("mail_note")}</small></p>{"<p class=note>" + L.t("kw_note") + "</p>" if L.t("kw_note") else ""}{ktable}</main>'''
    write("kanwu.html", page(L, f'{L.t("errata_title")}｜一孔录', L.t("errata_p1"), "kanwu.html", body)); urls.append(f"{DOMAIN}/{L.prefix}kanwu.html")
    write("search.json", json.dumps(search_idx, ensure_ascii=False))
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("search_sub")}</span>{L.t("search_title")}</h1></div></div>
<main class="wrap narrow"><form class="sbox" onsubmit="go();return false"><input id="q" placeholder="{esc(L.t("search_ph2"))}"><button>{L.t("nav_search")}</button></form><div id="res"></div></main>
<script>
let D=null;const q=document.getElementById('q'),R=document.getElementById('res');
const E=s=>s.replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
function cut(s,k){{const i=s.indexOf(k);if(i<0)return E(s.slice(0,60));const a=Math.max(0,i-24);return(a?'…':'')+E(s.slice(a,i))+'<mark>'+E(k)+'</mark>'+E(s.slice(i+k.length,i+k.length+36))+'…'}}
async function go(){{const k=q.value.trim();if(!k){{R.innerHTML='';return}}
if(!D){{try{{D=await (await fetch('{P}search.json')).json()}}catch(e){{R.textContent='…';return}}}}
history.replaceState(null,'','?q='+encodeURIComponent(k));
const hit=D.filter(d=>(d.y+d.t+d.x).includes(k));
R.innerHTML=hit.length?'<p class="lead">'+{json.dumps(L.t("search_n", n="N"))}.replace('N',hit.length)+'</p><ol class="toc">'+hit.map(d=>'<li><a href="'+d.u+'"><em>'+d.c+'</em><b>'+E(d.t)+'</b><span>'+cut(d.y.includes(k)?d.y:d.x,k)+'</span></a></li>').join('')+'</ol>':{json.dumps("<p class=empty>" + L.t("search_none") + "</p>")}}}
const p=new URLSearchParams(location.search).get('q');if(p){{q.value=p;go()}}
</script>'''
    write("search.html", page(L, f'{L.t("search_title")}｜一孔录', L.t("search_sub"), "search.html", body))
    llms = [f"# 一孔录 Yikonglu ({L.name})\n\n> {L.t('motto')} {L.t('intro')}\n\n## 论语 {L.t('lunyu')}\n"]
    for c in pub:
        llms.append(f"- [{c} {title_of(c)}]({DOMAIN}/{L.prefix}{rel_of(c)}): {field(c, '片里落点')[0] or ''}\n")
    write("llms.txt", "".join(llms))
    return urls

def main(zdir, outdir, kanwu=None):
    yw = json.load(open(os.path.join(HERE, "yuanwen.json"), encoding="utf-8"))
    eps = json.load(open(os.path.join(HERE, "episodes.json"), encoding="utf-8"))
    notes = {}
    for f in sorted(os.listdir(zdir)):
        if f.endswith(".md") and f not in ("说明.md", "主题线.md"):
            notes.update(parse_zhaji(os.path.join(zdir, f)))
    gao = {}
    for f in sorted(glob.glob(os.path.join(GAO_DIR, "*", "*稿*.md"))):
        for c, v in parse_gao(f, yw).items():
            gao.setdefault(c, {"cites": [], "reads": []}); gao[c]["cites"] += v["cites"]; gao[c]["reads"] += v["reads"]
    ch2ep = {c: (name, e) for name, e in eps.items() for c in e["chapters"]}
    key = lambda c: tuple(map(int, c.split(".")))
    pub = [c for c in sorted(ch2ep, key=key) if c in notes and c in yw]
    for c in sorted(ch2ep, key=key):
        if c not in pub: print("跳过（缺札记或原文）", c)
    by_pian = {}
    for c in pub: by_pian.setdefault(c.split(".")[0], []).append(c)
    today = datetime.date.today().isoformat()
    if os.path.isdir(outdir):
        for x in os.listdir(outdir):
            p = os.path.join(outdir, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(outdir, exist_ok=True)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(outdir, "assets"))
    ydir = os.path.join(HERE, "yuanye"); os.makedirs(ydir, exist_ok=True)
    for png in sorted(glob.glob(os.path.join(GAO_DIR, "*", "p*.png"))):
        jpg = os.path.join(ydir, os.path.basename(png)[:-4] + ".jpg")
        if not os.path.exists(jpg):
            from PIL import Image
            im = Image.open(png).convert("RGB")
            if im.width > 1400: im = im.resize((1400, int(im.height * 1400 / im.width)))
            im.save(jpg, quality=78, optimize=True, progressive=True)
    shutil.copytree(ydir, os.path.join(outdir, "yuanye"))
    pages_avail = {re.sub(r"\D", "", f).lstrip("0") for f in os.listdir(ydir) if f.endswith(".jpg")}
    D = dict(notes=notes, yw=yw, gao=gao, kw=parse_kanwu(kanwu or KANWU_DEFAULT), pub=pub, by_pian=by_pian, ch2ep=ch2ep, pages_avail=pages_avail, today=today)

    def writer(prefix, post=None):
        def write(rel, text):
            p = os.path.join(outdir, prefix, rel); os.makedirs(os.path.dirname(p) or outdir, exist_ok=True)
            open(p, "w", encoding="utf-8").write(post(text) if post else text)
        return write

    urls = build_lang(Lang("zh-Hans", ZH_UI), D, writer(""))
    # 繁体：由简体页面整页转换，台湾用字；站内链接改前缀
    from opencc import OpenCC
    cc = OpenCC("s2twp")
    keep = ("/assets/", "/yuanye/", "/style.css", "https://", "http://", "#")
    # 古文与人名里不能按今字转的（简繁同形或 OpenCC 会转错），先护住再转
    PROTECT = ["范祖禹", "范氏", "游酢", "游氏", "坐如尸", "尸", "咸", "丑", "干禄", "云：", "云，", "子云", "诗云", "余力", "余，", "余者"]
    def to_hant(text):
        for i, w in enumerate(PROTECT): text = text.replace(w, f"\ue000{i}\ue001")
        t = cc.convert(text)
        for i, w in enumerate(PROTECT): t = t.replace(f"\ue000{i}\ue001", HANT_FIX.get(w, w))
        t = re.sub(r'(href|action|src)="/(?!zh-hant/)([^"]*)"', lambda m: m.group(0) if m.group(2).startswith(("assets/", "yuanye/", "style.css")) else f'{m.group(1)}="/zh-hant/{m.group(2)}"', t)
        t = t.replace("fetch('/search.json')", "fetch('/zh-hant/search.json')")
        t = t.replace('"u": "/lunyu', '"u": "/zh-hant/lunyu')
        return t
    hant_ui = dict(ZH_UI); hant_ui["translated_note"] = ZH_UI["hant_note"]
    urls += build_lang(Lang("zh-Hant", hant_ui), D, writer("zh-hant", to_hant))
    for code in ("en", "ja", "ko", "fr", "es"):
        tr = json.load(open(os.path.join(HERE, "i18n", code + ".json"), encoding="utf-8"))
        urls += build_lang(Lang(code, tr["ui"], tr), D, writer(code))

    open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(outdir, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    open(os.path.join(outdir, "CNAME"), "w").write("yikonglu.com\n")
    open(os.path.join(outdir, ".nojekyll"), "w").write("")
    shutil.copy(os.path.join(HERE, "style.css"), os.path.join(outdir, "style.css"))
    print(f"生成 {len(urls)} 页 → {outdir}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
