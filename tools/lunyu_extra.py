# -*- coding: utf-8 -*-
"""只为《论语》做的几样（11-14 主人定）：论语年历 /nianli/、场合用句 /changhe/、课本十二章带读 /daidu/。先只简繁。

数据都在共享盘，网站只读：
- 年历：评审/2026-11-14-终极目标落地/论语年历-v*.json（365 课，北京日期对应当天那一课；闰年 2 月 29 日补读日）
- 场合：数据/网站素材/_场合/场合用句-v*.json（slug 定了不改）
- 带读：评审/2026-11-14-终极目标落地/带读包-课本十二章-v*.md（标【待核】的课本注释说法上网改写“各版课本注释不一”）
原文、白话、原页按章号从网站现成数据取。
"""
import glob, html, json, os, re

ROOT = "/mnt/project-files/一孔学-内-自媒体"
LUODI = os.path.join(ROOT, "评审", "2026-11-14-终极目标落地")
CH_DIR = os.path.join(ROOT, "数据", "网站素材", "_场合")
NL0 = 20819  # 2027-01-01（北京日期）距 1970-01-01 的天数：这天起首页“今日《论语》”按年历取章
ZH = ("zh-Hans", "zh-Hant")
esc = lambda s: html.escape(s or "", quote=True)
MONTH = "一二三四五六七八九十"


def _latest(pat):
    fs = sorted(glob.glob(pat))
    return fs[-1] if fs else None


LIVE = {"nl": True, "ch": True, "dd": True}  # 11-14 主人看过样张“可以。上。”  # 主人看过样张、说“上”之后逐样改 True；样张用 YK_LX=1 本地出


def load():
    """返回 {"nl": [...], "nlc": {章: (课, 日期)}, "ch": [...], "dd": [...]}；缺哪样就空着，页不出。"""
    out = {"nl": [], "nlc": {}, "ch": [], "dd": []}
    on = lambda k: LIVE[k] or os.environ.get("YK_LX") == "1"
    f = _latest(os.path.join(LUODI, "论语年历-v*.json"))
    if f and on("nl"):
        rows = json.load(open(f, encoding="utf-8"))["rows"]
        for r in rows:
            cs = r["章"].split()
            m, d = re.match(r"(\d+)月(\d+)日", r["日期"]).groups()
            out["nl"].append({"n": r["课"], "md": f"{int(m)}-{int(d)}", "m": int(m), "d": int(d), "date": r["日期"], "cs": cs, "c": r["主章"],
                              "q": r.get("今日一句") or "", "add": re.findall(r"\d+\.\d+", r.get("加读") or ""), "addt": r.get("加读") or ""})
            for c in cs: out["nlc"].setdefault(c, (r["课"], r["日期"]))
    f = _latest(os.path.join(CH_DIR, "场合用句-v*.json"))
    if f and on("ch"): out["ch"] = json.load(open(f, encoding="utf-8"))["pages"]
    f = _latest(os.path.join(LUODI, "带读包-课本十二章-v*.md"))
    if f and on("dd"): out["dd"] = parse_daidu(open(f, encoding="utf-8").read())
    return out


def _clean_daihe(s):  # 【待核】的课本注释说法：上网不写，改成“各版课本注释不一”
    if "【待核】" not in s: return s
    s = re.sub(r"[^。；]*【待核】[。；]?", "", s).rstrip("；，、 ")
    return (s + ("" if s.endswith("。") or not s else "。")) + "各版课本注释不一。"


def parse_daidu(md):
    items = []
    for sec in re.split(r"\n## ", md)[1:]:
        lines = sec.split("\n")
        m = re.match(r"(\d+)\.\s*(.+?)（(\S+) (\d+\.\d+)）", lines[0])
        if not m: continue
        it = {"k": int(m.group(1)), "t": m.group(2), "pian": m.group(3), "c": m.group(4), "q": []}
        body = "\n".join(lines[1:])
        for key, name in (("yw", "原文"), ("du", "读音"), ("bh", "白话"), ("zhu", "朱熹注"), ("zj", "诸家")):
            mm = re.search(rf"^{name}：(.*)$", body, re.M)
            it[key] = mm.group(1).strip() if mm else ""
        it["zj"] = _clean_daihe(it["zj"])
        if "无难字" in it["du"]: it["du"] = ""
        tl = body.split("讨论：", 1)[1] if "讨论：" in body else ""
        it["q"] = [re.sub(r"^\d+\.\s*", "", x).strip() for x in tl.split("\n") if re.match(r"^\d+\.\s", x.strip())]
        items.append(it)
    return items


def fix_reads(du, c, zidian):
    """带读稿的读音按网站难字字典（朱注逐字）对一遍：同字读音不同的，取字典，免得同站两种读法。返回 (改后, 改了哪些)。"""
    per = {}
    for x in zidian.get(c, []):
        z, p = x[2].split("|"); per.setdefault(z, p)
    fixed = []
    def rep(m):
        z, p = m.group(1), m.group(2)
        if len(z) == 1 and z in per and per[z] != p:
            fixed.append(f"{c} {z} {p}→{per[z]}"); return f"{z} {per[z]}"
        return m.group(0)
    return re.sub(r"(\S+) ([a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+)", rep, du), fixed


def nl_tag(L, P, X, c):
    """章页抬头下一行：“年历第 N 课 · 1月1日”（简繁）。"""
    if L.code not in ZH or c not in X["nlc"]: return ""
    n, date = X["nlc"][c]
    return f'<p class="nltag"><a href="{P}nianli/#k{n}">年历第 {n} 课 · {date}</a></p>'


def write_data(L, X, out_root, href, tx, baihua):
    """data/nianli-<语种>.json：{"M-D": [课, 主章, 链接, 今日一句, 白话(短的才给), 加读[[章, 链接]]]}，首页卡与全站细条 2027 元旦起用。"""
    if L.code not in ZH or not X["nl"] or not out_root: return
    os.makedirs(os.path.join(out_root, "data"), exist_ok=True)
    o = {}
    for r in X["nl"]:
        b = baihua.get(r["c"]) or ""
        o[r["md"]] = [r["n"], r["c"], href(r["c"]), r["q"], b if len(b) <= 60 else "", [[a, href(a)] for a in r["add"]], " ".join(r["cs"])]
    json.dump(o, open(os.path.join(out_root, "data", f"nianli-{L.code}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


def _pages_of(c, D):
    g = D["gao"].get(c) or {}
    ps = [str(x) for x in (g.get("qw_pages") or [])]
    if not ps and D["qw"].get(c, {}).get("pdf_page"): ps = [str(D["qw"][c]["pdf_page"])]
    return sorted(set(ps), key=int)


def _thumbs(c, D, pname):
    return "".join(f'<a class="ypg" href="/yuanye/p{int(x):03d}.jpg" target="_blank"><img loading="lazy" src="/yuanye/p{int(x):03d}.jpg" alt="论语 {c} 朱熹集注原页：四部备要本第 {x} 页"><span>原页 第 {x} 页</span></a>'
                   for x in _pages_of(c, D) if x in D["pages_avail"])


def build(L, D, X, write, page, P, href, ctitle, tx, pubset, PIAN, DOMAIN, zidian):
    if L.code not in ZH: return []
    urls, codes = [], list(ZH)
    pn = lambda c: PIAN[c.split(".")[0]][0]
    wj = lambda c: "" if c in pubset else " wj"
    wjtag = lambda c: "" if c in pubset else '<i class="wjtag">未讲</i>'
    # ---------- 年历 ----------
    if X["nl"]:
        mon = ""
        for m in range(1, 13):
            rs = [r for r in X["nl"] if r["m"] == m]
            lis = "".join(
                f'<li id="k{r["n"]}" data-md="{r["md"]}" data-cs="{esc(json.dumps(r["cs"]))}"><em>{r["date"]}</em><b>第 {r["n"]} 课</b>'
                f'<span class="nlc">' + "".join(f'<a class="{wj(c).strip()}" href="{href(c)}">{pn(c)} {c}</a>' for c in r["cs"]) + "</span>"
                f'<q lang="zh-Hans">{esc(r["q"])}</q>' + (f'<small class="nladd">' + re.sub(r"(\d+\.\d+)", lambda m_: f'<a href="{href(m_.group(1))}">{pn(m_.group(1))} {m_.group(1)}</a>', esc(r["addt"])) + "</small>" if r["add"] else "") + "</li>"
                for r in rs)
            if m == 2: lis += '<li class="nlbu" data-md="2-29"><em>2月29日</em><b>补读日</b><span class="nlc">闰年才有这一天，不排新课，前几天落下的课今天补上。</span></li>'
            mon += f'<section class="nlm" id="m{m}"><h2 class="ph">{MONTH[m-1] if m <= 10 else "十" + MONTH[m-11]}月<small>{len(rs)} 课</small></h2><ol class="nll">{lis}</ol></section>'
        chips = "".join(f'<a href="#m{m}">{m} 月</a>' for m in range(1, 13))
        first, last = X["nl"][0], X["nl"][-1]
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a></p><h1><span class="no">一年读完一遍 · 每天一课</span>《论语》年历</h1></div></div>
<main class="wrap narrow nianli"><p class="lead">《论语》全书 498 章，排成 365 课。1 月 1 日读第 1 课“{esc(first["q"])}”，12 月 31 日读第 365 课“{esc(last["q"])}”。年年同一天读同一章，哪天开始都行：从那天那一课读起，读满一年正好一轮。</p>
<p class="note">2027 年元旦起，首页的“今日《论语》”就按这张表每天一课。一课多是一章，短章两三章并成一课，只在同一篇里并。闰年 2 月 29 日不排新课，做补读日。教师节、孔子诞辰另有加读一章，不挪正课。</p>
<div class="nltoday" id="nltoday" hidden></div>
<p class="nlchips">{chips}</p>{mon}
<p class="note">标“未讲”的章视频还在做，网站先放原文、原页、白话和朱熹注。读过的课（这台设备上读过这一课所有的章）打勾，进度只存在你自己的设备上。</p></main>
<script>(function(){{var n=Date.now(),bj=new Date(n+288e5),md=(bj.getUTCMonth()+1)+"-"+bj.getUTCDate(),li=document.querySelector('.nll li[data-md="'+md+'"]'),T=document.getElementById("nltoday");
var S;try{{S=JSON.parse(localStorage.getItem("yk_xd")||"{{}}")}}catch(e){{S={{}}}}var seen=((S.b||{{}}).lunyu||{{}}).seen||[];
document.querySelectorAll(".nll li[data-cs]").forEach(function(x){{if(JSON.parse(x.getAttribute("data-cs")).every(function(c){{return seen.indexOf(c)>=0}}))x.classList.add("done")}});
if(!li)return;li.classList.add("now");var a=li.querySelector(".nlc a"),q=li.querySelector("q");
T.innerHTML='<p><b>今天 '+li.querySelector("em").textContent+(li.querySelector("b")?" · "+li.querySelector("b").textContent:"")+'</b></p>'+(q?'<blockquote lang="zh-Hans">'+q.textContent+'</blockquote>':'')+(a?'<p><a class="btn" href="'+a.getAttribute("href")+'">读今天这一课 →</a> <a class="btn ghost" href="#'+li.id+'">在表里看</a></p>':'<p>'+li.querySelector(".nlc").textContent+'</p>');T.hidden=false}})();</script>'''
        write("nianli/index.html", page(L, "《论语》年历：一年 365 课，每天一课读完全书｜一孔录",
                                        "《论语》498 章排成 365 课，1 月 1 日“学而时习之”，12 月 31 日“不知命，无以为君子也”。年年同一天读同一章，从今天那一课读起，一年一轮。", "nianli/", body, codes=codes))
        urls.append(f"{DOMAIN}/{L.prefix}nianli/")
    # ---------- 场合用句 ----------
    if X["ch"]:
        cards = ""
        for pg in X["ch"]:
            items = ""
            for it in pg["items"]:
                c = it["c"]
                if c not in D["qw"] and c not in pubset: continue
                full, bh = tx(c), D["baihua"].get(c) or ""
                same = re.sub(r"[^㐀-鿿]", "", it["q"]) == re.sub(r"[^㐀-鿿]", "", full)
                items += (f'<li class="chi{wj(c)}" id="c{c}"><p class="chq" lang="zh-Hans">{esc(it["q"])}</p>'
                          f'<p class="chsrc"><a href="{href(c)}">论语 {c} · {pn(c)}</a>{wjtag(c)}</p>'
                          f'<p class="chuse">{esc(it["use"])}</p>'
                          + (f'<p class="chcare"><b>小心</b>{esc(it["care"])}</p>' if it.get("care") else "")
                          + (f'<p class="chzhu"><b>诸家</b>{esc(it["zhu"])}</p>' if it.get("zhu") else "")
                          + f'<details class="chfull"><summary>整章原文、白话、原页</summary>'
                          + ("" if same else f'<p class="chyw" lang="zh-Hans">{esc(full)}</p>')
                          + (f'<p class="chbh"><b>白话</b>{esc(bh)}</p>' if bh else "")
                          + f'<div class="ypgs">{_thumbs(c, D, pn(c))}</div><p><a href="{href(c)}">去这一章：逐句朱熹注、读音、各家注本 ›</a></p></details></li>')
            body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a> › <a href="{P}changhe/">场合用句</a></p><h1><span class="no">《论语》里的话 · {len(pg["items"])} 章</span>{esc(pg["name"])}</h1></div></div>
<main class="wrap narrow changhe"><p class="lead">{esc(pg["intro"])}</p><ol class="chl">{items}</ol>
{f'<section class="chpcare"><h2 class="ph">别用错</h2><p>{esc(pg["care"])}</p></section>' if pg.get("care") else ""}
<p class="note">原文照朱熹《论语集注》（《四部备要》本），章号按朱注分章。大字是摘句，“……”是中间有省略；用之前请点开看整章，免得断章取义。</p>
<p class="chmore">别的场合：''' + "".join(f'<a href="{P}changhe/{q["slug"]}.html">{esc(q["name"])}</a>' for q in X["ch"] if q["slug"] != pg["slug"]) + "</p></main>"
            desc = f"{pg['name']}用《论语》里的哪句话：{pg['intro'][:70]}"
            write(f"changhe/{pg['slug']}.html", page(L, f"{pg['name']}用《论语》哪句话：{len(pg['items'])} 章原文、白话与用法｜一孔录", desc, f"changhe/{pg['slug']}.html", body, codes=codes))
            urls.append(f"{DOMAIN}/{L.prefix}changhe/{pg['slug']}.html")
            q0 = pg["items"][0]["q"]
            cards += f'<a class="chcard" href="{P}changhe/{pg["slug"]}.html"><b>{esc(pg["name"])}</b><q lang="zh-Hans">{esc(q0)}</q><small>{len(pg["items"])} 章</small></a>'
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a></p><h1><span class="no">取名、开学、结婚、送别……</span>场合用句</h1></div></div>
<main class="wrap narrow changhe"><p class="lead">人生里要说一句像样的话的时候，从《论语》里挑。十二个场合，每章都写了怎么用、哪里容易用反，点开能看整章原文、白话和原页。</p>
<div class="chcards">{cards}</div><p class="note">摘句都是原文连续的一段，章号按朱熹《论语集注》分章。</p></main>'''
        write("changhe/index.html", page(L, "场合用句：取名、开学、结婚、祝寿、送别，用《论语》里的哪句话｜一孔录",
                                         "十二个人生场合，从《论语》里挑一句：每章写明怎么用、哪里容易用反，附整章原文、白话与朱熹集注原页。", "changhe/", body, codes=codes))
        urls.append(f"{DOMAIN}/{L.prefix}changhe/")
    # ---------- 课本十二章带读 ----------
    fixed_all = []
    if X["dd"]:
        secs, toc = "", ""
        for it in X["dd"]:
            c = it["c"]
            du, fx = fix_reads(it["du"], c, zidian); fixed_all += fx
            nl = X["nlc"].get(c)
            qs = "".join(f"<li>{esc(q)}</li>" for q in it["q"])
            secs += (f'<section class="ddc{wj(c)}" id="d{it["k"]}"><h2 class="ph"><span class="ddk">第 {it["k"]} 章</span>{esc(it["t"])}<small>{esc(it["pian"])} {c}{" · 年历 " + nl[1] if nl else ""}</small></h2>'
                     f'<p class="ddyw" lang="zh-Hans">{esc(it["yw"] or tx(c))}</p>'
                     + (f'<p class="dddu"><b>读音</b>{esc(du)}</p>' if du else "")
                     + (f'<p><b>白话</b>{esc(it["bh"])}</p>' if it["bh"] else "")
                     + (f'<p><b>朱熹注</b><span lang="zh-Hans">{esc(it["zhu"])}</span></p>' if it["zhu"] else "")
                     + (f'<p><b>诸家</b>{esc(it["zj"])}</p>' if it["zj"] else "")
                     + f'<div class="ypgs">{_thumbs(c, D, it["pian"])}</div>'
                     + f'<div class="ddq"><b>讨论</b><ol>{qs}</ol></div>'
                     + f'<p class="ddgo"><a href="{href(c)}">去这一章：逐句朱熹注、各家注本{"、视频" if c in pubset else ""} ›</a></p></section>')
            toc += f'<a href="#d{it["k"]}"><em>{it["k"]}</em>{esc(it["t"])}</a>'
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a> › <a href="{P}zhuanti/keben.html">语文课本里的《论语》</a></p><h1><span class="no">给老师、家长、中文学校</span>课本《论语》十二章 · 带读</h1></div></div>
<main class="wrap narrow daidu"><p class="lead">语文课本里最常选的《论语》十二章，每章一页：原文、读音、白话、朱熹注一句、诸家异同、原页，再加三道讨论题。第一道人人能答，第二道对照注家，第三道落到自己身上。</p>
<p class="note">怎么用：一周一章，十二周一学期；或者跟着《论语》年历，那一章轮到哪天就哪天读。每章先读原文两遍，再看原页，再讨论。读音以今音为主；各版课本的注释说法不完全一样，以你手上的课本为准。</p>
<nav class="ddtoc">{toc}</nav>{secs}
<p class="note">原文照朱熹《论语集注》（《四部备要》本）。打印：用浏览器“打印”即可，每章自动分页。发现错处请告诉我们，勘误公开。</p></main>'''
        write("daidu/index.html", page(L, "课本《论语》十二章带读：原文、读音、翻译、朱熹注与讨论题｜一孔录",
                                       "语文课本《论语》十二章，每章原文、读音、白话、朱熹注、诸家异同、原页和三道讨论题。给语文老师、家长和海外中文学校用，免费。", "daidu/", body, codes=codes))
        urls.append(f"{DOMAIN}/{L.prefix}daidu/")
    if fixed_all and L.code == "zh-Hans": print("  带读读音按难字字典改：" + "；".join(fixed_all))
    return urls
