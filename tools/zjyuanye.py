"""《论语》诸家原页（11-16）：章页“各家注本”里加书名切换，看这一章在集解·邢疏、皇疏、正义、郑注残卷、释文原刻本里的那几页。
图在 yikonglu-zhuben 仓库（https://zhuben.yikonglu.com/<键>/<图名>.jpg），逐章页码索引在共享盘 _诸家原页/，宽高在 tools/zhuben_sizes.json。"""
import json, os, html

ZJ_DIR = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_诸家原页"
ZB_IMG = os.environ.get("YK_ZHUBEN", "https://zhuben.yikonglu.com").rstrip("/")
HERE = os.path.dirname(os.path.abspath(__file__))
# 键, 书名短称, 全名（注家朝代）, 版本, 馆藏, 附注
BOOKS = [
    ("zhushu", "集解·邢疏", "何晏（魏）《论语集解》·邢昺（宋）《论语注疏》", "清光绪十八年（1892）湖南宝庆务本书局重镌阮元本", "韩国国立中央图书馆", ""),
    ("huangshu", "皇疏", "皇侃（梁）《论语义疏》", "学而至里仁：知不足斋丛书本；公冶长至尧曰：日本宽延三年（1750）根本逊志校刻本", "早稻田大学图书馆等", "一叶扫成左右两半，本章在哪半叶未分，两半都列出"),
    ("zhengyi", "正义", "刘宝楠（清）《论语正义》", "《皇清经解续编》南菁书院本（1888）", "中国国家图书馆、日本永青文库", "页上的“国”字大印是馆方的数字水印"),
    ("zhengzhu", "郑注残卷", "郑玄（东汉）《论语注》敦煌唐写本残卷", "1926 年东京文求堂影印本（依上虞罗氏本），只存述而 7.12 至乡党 10.17", "台湾大学图书馆", ""),
    ("shiwen", "释文", "陆德明（唐）《经典释文·论语音义》", "通志堂清刻本，卷二十四", "中国国家图书馆", "《音义》只摘字注音、不分章，这里列的是本篇全部"),
]
_D = None


def load():
    global _D
    if _D is not None: return _D
    _D = {"ch": {}, "sw": {}, "sz": {}}
    try:
        _D["sz"] = json.load(open(os.path.join(HERE, "zhuben_sizes.json"), encoding="utf-8"))
        for k in ("zhushu", "zhengyi", "zhengzhu", "huangshu"):
            for r in json.load(open(os.path.join(ZJ_DIR, k + ".json"), encoding="utf-8")):
                _D["ch"].setdefault(r["章"], {})[k] = r
        _D["sw"] = json.load(open(os.path.join(ZJ_DIR, "shiwen.json"), encoding="utf-8"))
    except FileNotFoundError:
        print("  诸家原页：共享盘数据不在，章页不出诸家原页")
        _D = {"ch": {}, "sw": {}, "sz": {}}
    return _D


def html_for(c, lang_code, conv=None):
    """章 c 的诸家原页块；只出简繁。conv：繁体转换函数。"""
    if not lang_code.startswith("zh"): return ""
    D = load()
    if not D["sz"]: return ""
    T = conv or (lambda s: s)
    e = lambda s: html.escape(T(s))
    rows = D["ch"].get(c, {})
    tabs, panels = "", ""
    for k, short, full, ed, lib, extra in BOOKS:
        if k == "shiwen":
            pages, odd = D["sw"].get(c.split(".")[0]) or [], False
        else:
            r = rows.get(k)
            if not r: continue
            pages, odd = r["页"], not (r["状态"] == "认" or r["状态"].startswith("沿用"))
        pages = [p for p in pages if f"{k}/{p}" in D["sz"]]
        if not pages: continue
        imgs = [f"{ZB_IMG}/{k}/{p}.jpg|{D['sz'][k + '/' + p][0]}|{D['sz'][k + '/' + p][1]}" for p in pages]
        note = "；".join(x for x in (extra, "古注分章与朱注不同，这里的页段供参考" if odd else "") if x)
        tabs += f'<button type="button" data-k="{k}" aria-expanded="false">{e(short)}</button>'
        panels += (f'<div class="zjp" data-k="{k}" hidden data-i=\'{html.escape(json.dumps(imgs))}\'>'
                   f'<figure><a class="zjo" target="_blank" rel="noopener"><img alt="{e(f"论语 {c}，{full}原页")}" decoding="async"></a>'
                   f'<figcaption><span class="zjn"><button type="button" class="pv" aria-label="{e("上一页")}">‹</button><b>1 / {len(imgs)}</b><button type="button" class="nx" aria-label="{e("下一页")}">›</button></span>'
                   f'<span class="zjm"><b>{e(full)}</b>{e(ed)}，{e(lib)}藏。{e("公有领域，图源 Wikimedia Commons")}' + (f'<br><small>{e(note)}。</small>' if note else "") + "</span></figcaption></figure></div>")
    if not tabs: return ""
    return (f'<div class="zjy" id="zjy"><h3>{e("诸家原页")}<small>{e("点书名，看这一章在别家原刻本里的那几页")}</small></h3>'
            f'<div class="zjt">{tabs}</div>{panels}</div>'
            '<script>(function(){var R=document.getElementById("zjy");if(!R)return;function show(P,i){var L=JSON.parse(P.dataset.i),n=L.length;i=(i+n)%n;P._i=i;var a=L[i].split("|"),im=P.querySelector("img");im.width=+a[1];im.height=+a[2];im.src=a[0];P.querySelector(".zjo").href=a[0];P.querySelector(".zjn b").textContent=(i+1)+" / "+n;P.querySelector(".pv").hidden=P.querySelector(".nx").hidden=n<2}'
            'R.querySelectorAll(".zjt button").forEach(function(b){b.onclick=function(){var on=b.getAttribute("aria-expanded")=="true";R.querySelectorAll(".zjt button").forEach(function(x){x.setAttribute("aria-expanded","false")});R.querySelectorAll(".zjp").forEach(function(p){p.hidden=true});if(on)return;b.setAttribute("aria-expanded","true");var P=R.querySelector(\'.zjp[data-k="\'+b.dataset.k+\'"]\');P.hidden=false;if(P._i==null)show(P,0)}});'
            'R.querySelectorAll(".zjp").forEach(function(P){P.querySelector(".pv").onclick=function(){show(P,P._i-1)};P.querySelector(".nx").onclick=function(){show(P,P._i+1)}})})();</script>')


_DZ = None


def dz_html(c, lang_code, conv=None):
    """11-16 定州汉简《论语》异文：每条简本→今本、该书注释首句、书页。书在版权期，只上这份摘要，不上书影与整段释文；章号待核的不上。"""
    global _DZ
    if not lang_code.startswith("zh"): return ""
    if _DZ is None:
        try: _DZ = json.load(open(os.path.join(ZJ_DIR, "dingzhou.json"), encoding="utf-8")).get("异文", {})
        except FileNotFoundError: _DZ = {}
    rows = [r for r in _DZ.get(c, []) if r.get("状态") == "认"]
    if not rows: return ""
    T = conv or (lambda s: s)
    e = lambda s: html.escape(T(s))
    li = ""
    for r in rows:
        head = (f'<b lang="zh-Hant">{html.escape(r["简本"])}</b>' + (f'<span>{e("今本作")}</span><b lang="zh-Hant">{html.escape(r["今本"])}</b>' if r["今本"] else "")) if r["简本"] else ""
        li += f'<li>{head}<q lang="zh-Hant">{html.escape(r["校记"])}</q><small>{e(f"第 {r['书页']} 页")}</small></li>'
    return (f'<div class="zb dzy" id="dingzhou"><h3>{e("定州汉简异文")}<small>{e("西汉中期竹简本，1973 年河北定州出土；与今本字句不同处")}</small></h3>'
            f'<ul>{li}</ul><p class="note">{e("据《定州汉墓竹简〈论语〉》（文物出版社，1997）的释文注释摘录，引的是该书注释的第一句，页码为该书页码。")}</p></div>')
