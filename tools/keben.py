"""11-16 课本选段着陆页（网站改动单一，属收录；主人在决定卡上选“两件都做”）。
只出简繁：每课一页（七上《论语》十二章、高中选必上《论语》十二章、必修下《侍坐》），另有“论语中的成语”“论语名句”两页。
每章：原文、读音（本章读音表）、一句白话、链到章页和已公开的视频。章号一律朱注本。数据 keben.json。"""
import json, os, html, datetime

esc = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
ZH = ("zh-Hans", "zh-Hant")
# 课 → 着陆页（slug 定了不改）
LESSON = {"chu7": ("lunyu-shierzhang", "论语十二章原文及翻译、读音（七年级上册）", "七年级上册", "《论语》十二章"),
          "xuanbi": ("lunyu-shierzhang-gaozhong", "论语十二章原文及翻译、读音（高中选择性必修上册）", "高中选择性必修上册", "《论语》十二章"),
          "bixiu": ("shizuo", "子路曾皙冉有公西华侍坐原文及翻译、读音（高中必修下册）", "高中必修下册", "子路、曾皙、冉有、公西华侍坐")}
PAGES = [f"zhuanti/{v[0]}.html" for v in LESSON.values()] + ["zhuanti/lunyu-chengyu.html", "zhuanti/lunyu-mingju.html", "zhuanti/kongzi-shuoguo.html"]


def load():
    f = os.path.join(HERE, "keben.json")
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {"chengyu": [], "mingju": []}


def video(D, c):
    """本章已公开的视频：(网址, 期名)；没有就 None。"""
    ep = D["ch2ep"].get(c)
    if not ep: return None
    yt, pa = ep[1].get("youtube"), ep[1].get("public_at")
    if not yt or (pa and datetime.datetime.fromisoformat(pa) > datetime.datetime.now(datetime.timezone.utc)): return None
    st = ep[1].get("starts", {}).get(c) or D["starts"].get(yt, {}).get(c)
    return f"https://www.youtube.com/watch?v={yt}" + (f"&amp;t={st}s" if st else ""), ep[0]


def reads_line(D, c):
    rs = D["gao"].get(c, {}).get("reads") or []
    return "　".join(f'{esc(r["zi"])} <b>{esc(r["du"])}</b>' + (f'<small>（今多读 {esc(r["jin"])}）</small>' if r.get("jin") else "") for r in rs)


def build(L, D, KEBEN, write, page, P, href, ctitle, tx, pubset, PIAN, DOMAIN, MAIL):
    if L.code not in ZH: return []
    X = load(); urls = []
    pn = lambda c: PIAN[c.split(".")[0]][0]
    wjtag = lambda c: "" if c in pubset else '<i class="wjtag">未讲</i>'
    def links(c):
        v = video(D, c)
        return (f'<p class="kblk"><a href="{href(c)}">逐句讲解、原页与朱熹注 →</a>'
                + (f' <a class="kbv" href="{v[0]}" rel="noopener">看视频</a>' if v else "") + "</p>")
    for kid, kname, knote, kcs in KEBEN:
        slug, ttl, grade, lname = LESSON[kid]
        beisong = "".join(f'<p lang="zh-Hans">{esc(tx(c))}</p>' for c in kcs)
        items = ""
        for k, c in enumerate(kcs, 1):
            bh = D["baihua"].get(c) or ""; rl = reads_line(D, c)
            items += (f'<li id="c{c}"><h3><em>{k}</em><a href="{href(c)}">{pn(c)} {c}　{esc(ctitle(c))}</a>{wjtag(c)}</h3>'
                      f'<p class="zy" lang="zh-Hans">{esc(tx(c))}</p>'
                      + (f'<p class="kbdu"><span>读音</span>{rl}</p>' if rl else "")
                      + (f'<p class="zd"><span>白话</span>{esc(bh)}</p>' if bh else "") + links(c) + "</li>")
        others = "".join(f'<a class="ztcard" href="{P}zhuanti/{LESSON[k2][0]}.html"><b>{esc(LESSON[k2][2])}</b><small>{esc(LESSON[k2][3])}</small></a>' for k2, *_ in KEBEN if k2 != kid)
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a> › <a href="{P}zhuanti/keben.html">语文课本里的《论语》</a></p><h1><span class="no">统编语文 · {esc(grade)}</span>{esc(lname)}</h1></div></div>
<main class="wrap narrow keben"><p class="lead">{esc(knote)}共 {len(kcs)} 章。下面先是全文，再逐章给原文、读音、白话，点章名看这一章的原页、逐句朱熹注和各家注本。</p>
<section class="kbqw"><h2 class="ph">全文</h2>{beisong}</section>
<section><h2 class="ph">逐章：原文、读音、白话</h2><ol class="kbl">{items}</ol></section>
<p class="note">原文照朱熹《论语集注》（《四部备要》本），标点、个别用字可能和课本不同；章号按朱注分章，课本注释多用杨伯峻本，章号有时差一两号。读音照朱注反切，和今天通行读法不同的另注“今多读”。标“未讲”的章视频还在做，网站先放原文、白话和注。发现错处请写信：{MAIL}</p>
<div class="ztcards">{others}<a class="ztcard" href="{P}zhuanti/lunyu-chengyu.html"><b>论语中的成语</b><small>{len(X["chengyu"])} 条</small></a><a class="ztcard" href="{P}zhuanti/lunyu-mingju.html"><b>论语名句</b><small>{len(X["mingju"])} 句</small></a></div></main>'''
        desc = f"统编语文{grade}{lname}：全文、逐章原文、读音、白话翻译，每章链到朱熹《论语集注》原页、逐句注和讲解视频。"
        write(f"zhuanti/{slug}.html", page(L, f"{ttl}｜一孔录", desc, f"zhuanti/{slug}.html", body, codes=list(ZH)))
        urls.append(f"{DOMAIN}/{L.prefix}zhuanti/{slug}.html")
    # ---------- 论语中的成语 ----------
    if X["chengyu"]:
        rows, cur = "", None
        for x in X["chengyu"]:
            p = x["c"].split(".")[0]
            if p != cur:
                if cur: rows += "</ol></section>"
                rows += f'<section><h2 class="ph">{PIAN[p][0]}</h2><ol class="cyl">'; cur = p
            rows += (f'<li><b class="cy">{esc(x["cy"])}</b><span class="cyk">{"出自" if x["kind"] == "原文" else "化自"} <a href="{href(x["c"])}">{pn(x["c"])} {x["c"]}</a></span>'
                     f'<q lang="zh-Hans">{esc(x["q"])}</q>' + (f'<small>{esc(x["note"])}</small>' if x.get("note") else "") + "</li>")
        rows += "</ol></section>"
        n = len(X["chengyu"])
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a> › <a href="{P}zhuanti/keben.html">语文课本里的《论语》</a></p><h1><span class="no">逐条注出处章号</span>论语中的成语</h1></div></div>
<main class="wrap narrow keben"><p class="lead">常用成语里出自《论语》的 {n} 条，按篇章顺序排。每条写明出自哪一章、原句怎么说，点章号看这一章的原页和朱熹注。“出自”是成语的字句原文里就有；“化自”是从原句压缩或改写来的。</p>
{rows}<p class="note">章号按朱熹《论语集注》分章，和杨伯峻本等有时差一两号。出处只收《论语》本文；孔子引《诗》的句子（如“思无邪”）出处在《诗经》，不收。有漏的、有错的请写信：{MAIL}</p></main>'''
        write("zhuanti/lunyu-chengyu.html", page(L, f"论语中的成语 {n} 条：出处章号、原句｜一孔录", f"出自《论语》的成语 {n} 条：温故知新、不耻下问、三人行必有我师、举一反三、己所不欲勿施于人……每条注出处章号和原句，链到朱熹注原页。", "zhuanti/lunyu-chengyu.html", body, codes=list(ZH)))
        urls.append(f"{DOMAIN}/{L.prefix}zhuanti/lunyu-chengyu.html")
    # ---------- 论语名句 ----------
    if X["mingju"]:
        n = len(X["mingju"])
        lis = "".join(f'<li><q lang="zh-Hans">{esc(x["q"])}</q><span class="cyk"><a href="{href(x["c"])}">{pn(x["c"])} {x["c"]}</a></span>'
                      + (f'<p class="zd"><span>白话</span>{esc(D["baihua"].get(x["c"]))}</p>' if D["baihua"].get(x["c"]) else "") + "</li>" for x in X["mingju"])
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a></p><h1><span class="no">原文 · 出处 · 白话</span>论语名句</h1></div></div>
<main class="wrap narrow keben"><p class="lead">《论语》里最常被引用的 {n} 句，按篇章顺序排。每句注出处章号，附整章白话；点章号看原页、逐句朱熹注和讲解视频。</p>
<ol class="mjl">{lis}</ol>
<p class="note">原文照朱熹《论语集注》（《四部备要》本），章号按朱注分章。想每天读一句，可以看 <a href="{P}nianli/">《论语》年历</a>。网上流传的“孔子曰”哪些是真的，见 <a href="{P}zhuanti/kongzi-shuoguo.html">孔子真说过吗？</a></p></main>'''
        write("zhuanti/lunyu-mingju.html", page(L, f"论语名句 {n} 句：原文、出处章号、白话｜一孔录", f"《论语》名句 {n} 句：学而时习之、温故而知新、三人行必有我师、己所不欲勿施于人……每句注出处章号和白话，链到朱熹注原页。", "zhuanti/lunyu-mingju.html", body, codes=list(ZH)))
        urls.append(f"{DOMAIN}/{L.prefix}zhuanti/lunyu-mingju.html")
    # ---------- 孔子真说过吗（11-16 改动单四之 1） ----------
    if X.get("mingyan"):
        V = {"在": ("ok", "在《论语》里"), "改": ("mid", "有出入"), "不在": ("todo", "不在《论语》里")}
        H2 = {"在": "确实在《论语》里", "改": "在《论语》里，但有出入", "不在": "《论语》里没有"}
        secs = ""
        for v, (cls, lab) in V.items():
            rs = [x for x in X["mingyan"] if x["v"] == v]
            if not rs: continue
            lis = ""
            for x in rs:
                if v == "不在":
                    lis += (f'<li><b class="cy">“{esc(x["q"])}”</b><span class="hm {cls}">{lab}</span>'
                            + (f'<p class="zd"><span>出处</span>{esc(x["src"])}{"：" + esc(x["note"]) if x["note"] else ""}</p>' if x["src"] else "")
                            + '<small>查过：朱熹《论语集注》本全书 498 章，没有这句。</small></li>')
                else:
                    lis += (f'<li><b class="cy">“{esc(x["q"])}”</b><span class="hm {cls}">{lab}</span>'
                            f'<p class="zy" lang="zh-Hans">{esc(x["yq"])}<a class="cyk" href="{href(x["c"])}">{pn(x["c"])} {x["c"]}</a></p>'
                            + (f'<small>{esc(x["note"])}</small>' if x["note"] else "") + "</li>")
            secs += f'<section><h2 class="ph">{H2[v]}<small>{len(rs)} 条</small></h2><ol class="myl">{lis}</ol></section>'
        n = len(X["mingyan"]); nz = sum(1 for x in X["mingyan"] if x["v"] == "在"); ng = sum(1 for x in X["mingyan"] if x["v"] == "改"); nb = n - nz - ng
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a></p><h1><span class="no">流传的“孔子曰”逐条核对</span>孔子真说过吗？</h1></div></div>
<main class="wrap narrow keben"><p class="lead">网上常见的“孔子说”，我们拿朱熹《论语集注》本全书 498 章逐条核了一遍：{nz} 条确实在《论语》里；{ng} 条在《论语》里，但流传的说法改了字、省了半句，或者不是孔子说的；{nb} 条《论语》里根本没有，下面写明它真正的出处。在《论语》里的，点章号看原页和朱熹注。</p>
{secs}<p class="note">“查过”指在本站《论语》原文（朱熹《论语集注》，《四部备要》本）全文里找这几个字连着出现，没有找到。别书的出处按通行本，“通行说法”的是一般认为的出处。还有想核的“孔子曰”，或者发现我们核错了，请写信：{MAIL}</p></main>'''
        write("zhuanti/kongzi-shuoguo.html", page(L, "孔子真说过吗？流传的“孔子曰”逐条核对｜一孔录", f"网上流传的“孔子说”{n} 条，逐条对《论语》原文：哪些真在《论语》里，哪些被改了字、不是孔子说的，哪些根本出自《礼记》《孟子》《三字经》。", "zhuanti/kongzi-shuoguo.html", body, codes=list(ZH)))
        urls.append(f"{DOMAIN}/{L.prefix}zhuanti/kongzi-shuoguo.html")
    return urls
