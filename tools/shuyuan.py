"""一孔书院入院页 /shuyuan/ruyuan.html：11-16 起只讲“题名”（旧会员权益、书友圈、院落学籍已撤）。
简体全文，繁体由简体转；外文页一律出英文摘要。意愿只计数：yikonglu-live 的 /intent（满 20 才显示人数）、/intent/stats。
文案源：评审/2026-11-16-书院题名开卖/入院页-题名-文案-v1.1.md。"""
import html, json

def esc(s): return html.escape(s or "", quote=True)

LINK = {"zh": "一孔书院 · 题名", "en": "Yikonglu Academy"}

AFDIAN = "https://afdian.com/item/d667fd6ae19d11f1a65c5254001e7c00"  # 11-16 主人在爱发电上架题名（一个商品两个型号）
KOFI = "https://ko-fi.com/s/97c7197047"  # 11-16 Ko-fi 题名商品（主人上架）

# 11-16 主人点卡：书院先开“题名”，入院页整页换成题名（文案 评审/2026-11-16-书院题名开卖/入院页-题名-文案-v1.1.md）；旧权益表、书友圈、院落学籍撤下
TM_ZH = dict(title="一孔书院 · 题名", sub="把名字题在《论语》年历的一天上", motto="免费的，管读懂；书院，管留名。",
             p1="一孔录的片子、原文、白话、读本、年历，永远免费，谁都能读，不会因为书院变薄。书院不卖内容，只做一件事：让愿意出一份力的书友，把名字题在《论语》年历的某一天上。",
             btn="我想题一天", done="已记下，谢谢。", cnt="已有 {n} 位书友想题一天")
TM_EN = dict(title="Yikonglu Academy · Name a Day", sub="Put your name on one day of the 2027 Analects calendar", motto="The free side helps you understand; the Academy keeps your name.",
             p1="Everything on Yikonglu stays free for everyone: the videos, the text, the plain renderings, the readers and the calendar. The Academy sells no content. It does one thing: readers who want to support the work can put their name on one day of the Analects calendar.",
             btn="I'd like to name a day", done="Noted, thank you.", cnt="{n} readers would like to name a day")


PRICE_HANS = '<ul><li>题一日：199 元，题一年。前一百位是创始书友，以后每年按 199 元续题同一天；之后 365 元。</li><li>题一篇：2,000 元，题一年。《论语》二十篇，每篇只收一位，名字写在这一篇的篇页和 2027 年全本读本的牌记页上。</li><li>海外在 Ko-fi 用美元付：题一日 US$29，题一篇 US$299。创始一百位国内外合算。</li></ul>'
PRICE_HANT = '<ul><li>题一日：US$29（在 Ko-fi 付款），题一年。前一百位是创始书友，以后每年按此价续题同一天。中国大陆的书友在爱发电付 199 元，创始一百位两边合算。</li><li>题一篇：US$299（爱发电 2,000 元），题一年。《论语》二十篇，每篇只收一位，名字写在这一篇的篇页和 2027 年全本读本的牌记页上。</li></ul>'


def body(L, live):
    zh = L.code.startswith("zh"); T = TM_ZH if zh else TM_EN; P = "/" + L.prefix
    if zh:
        main = f'''<p class="symotto">{T["motto"]}</p><p>{T["p1"]}</p>
<h2>题名是什么</h2><p>2027 年元旦起，一孔录按<a href="{P}nianli/">年历</a>每天读一章《论语》，全书排成 365 课，年年同一天读同一章。你可以把其中一天题下来。这一天的年历页、这一章的章页、公众号当天的文末，都会写上你的名字和你的一句话。</p>
<p>样子是这样的：</p><blockquote class="tmeg"><p>1 月 1 日 · 第 1 课 · 学而时习之，不亦说乎</p><p>青山题：给十八岁的女儿，愿你一生有书可读。</p></blockquote>
<h2>题哪一天</h2><ul><li>生日：你的，孩子的，父母的。先在<a href="{P}nianli/#nlbday">年历页</a>查一查，那天读哪一章。</li><li>想记住的日子：结婚、开学、退休、一件事做成的那天。</li><li>你最喜欢的那一章所在的那一天。</li></ul>
<p>挑之前先看那天读什么。比如 3 月 14 日是第 73 课，读 5.9“朽木不可雕也”，不一定适合题给孩子。</p>
<h2>你得到什么</h2><ul><li>这一天归你题名一年：年历页、章页、公众号当日文末署名，加一句不超过 20 字的题记。</li><li>一张题名帖，可以存，可以转给你想送的人。</li><li>名字写进“2027 首轮题名录”，名录满 20 位后公开。</li><li>你的问题，一孔必答：每月至多一问，答案公开，署你的网名。</li></ul>
<h2>多少钱</h2>{PRICE_HANT if L.code == "zh-Hant" else PRICE_HANS}
<h2>规矩</h2><ul><li>一天只收一位，先到先得；续题的人优先。</li><li>题记写给人，或者写给自己，不超过 20 字。不收商号、网址、联系方式，不谈时政。不合规矩的，一孔会请你改。</li><li>题名不碰讲读。每一句读法照样句句可核，不因为谁题了名改一个字。</li><li>用网名就行。本页不收真名、电话。</li></ul>
<h2>退款</h2><ul><li>付款七日内，不问理由全退。</li><li>年历在你的日子之前停更的，全退。</li><li>题记被请改而你不愿改的，全退。</li></ul>
<h2 id="join">怎么题</h2><ol><li>在<a href="{P}nianli/">年历页</a>查好日子，看那天读哪一章，有没有人题过。</li><li>国内到爱发电下单；海外到 Ko-fi 下单（美元付款，题一日 US$29、题一篇 US$299）。都按提示填日期（或篇名）、网名、题记。</li><li>三天内收到题名帖。名字和题记会出现在年历页的这一天上。</li></ol>
<p class="cta"><a class="btn" href="{AFDIAN}" target="_blank" rel="noopener">国内 · 在爱发电题名</a> <a class="btn ghost" href="{KOFI}" target="_blank" rel="noopener">海外 · 在 Ko-fi 题名</a></p>'''
    else:
        main = f'''<p class="symotto">{T["motto"]}</p><p>{T["p1"]}</p>
<h2>What it is</h2><p>From 1 January 2027, Yikonglu reads one passage of the Analects of Confucius each day: 365 lessons a year, the same passage on the same date every year. Name a day, and your name with a dedication of up to 20 Chinese characters (or 60 Latin letters) appears on that day's calendar entry and on the passage's page at yikonglu.com, for one year.</p>
<h2>What you receive</h2><ul><li>The day is yours for a year: your name and dedication on the calendar and the passage page.</li><li>A keepsake card you can keep or give.</li><li>A place in the 2027 First Round list, published once it reaches 20 names.</li><li>One question a month answered by Yikonglu, publicly, under your name.</li></ul>
<h2>Price</h2><ul><li>Name a Day: US$29 for one year. The first hundred readers are founding members and can renew the same day at this price each year.</li><li>Name a Book: US$299 for one year. The Analects has twenty books; each can be named by one person only. Your name goes on that book's page and in the colophon of the 2027 complete reader.</li></ul>
<h2>Rules</h2><ul><li>One person per day, first come first served; renewals come first.</li><li>Write your dedication to someone, or to yourself. No business names, links, contact details or politics; we may ask you to change it.</li><li>Naming never touches the readings: every line stays checkable, and nothing is changed for anyone.</li><li>A screen name is enough. We do not need your real name or phone number.</li></ul>
<h2>Refunds</h2><ul><li>Full refund within 7 days of payment, no questions asked.</li><li>Full refund if the calendar stops before your day.</li><li>Full refund if we ask you to change your dedication and you prefer not to.</li></ul>
<h2 id="join">How</h2><ol><li>Check the <a href="/nianli/">calendar</a> (Chinese) to see which passage your day reads and whether it is taken.</li><li>Order on Ko-fi and give the date (or book), the name to show and your dedication.</li><li>Your keepsake card arrives within three days, and your name appears on the calendar.</li></ol>
<p class="cta"><a class="btn" href="{KOFI}" target="_blank" rel="noopener">Name a day on Ko-fi</a></p>'''
    out = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{T["sub"]}</span>{T["title"]}</h1></div></div>
<main class="wrap narrow prose shuyuan">{main}
<div class="syjoin"><button type="button" class="btn ghost" id="syb">{T["btn"]}</button><p class="sycnt" id="syn" hidden></p></div>
<p class="note">{"本页只记人数，不收姓名、邮箱、电话。点“我想题一天”不代表付款，也不代表订下了哪一天。" if zh else "This page counts clicks only; no personal data is collected."}</p></main>'''
    if live:  # 意愿计数照旧走 /intent（join），满 20 才显示人数
        out += ("<script>(function(){var U=" + json.dumps(live.rstrip("/")) + ",T=" + json.dumps({k: T[k] for k in ("done", "cnt")}, ensure_ascii=False) + r""";
var b=document.getElementById('syb'),n=document.getElementById('syn');
function g(k){try{return localStorage.getItem(k)}catch(e){return null}}function s(k){try{localStorage.setItem(k,'1')}catch(e){}}
function show(x){if(x&&x.n){n.textContent=T.cnt.replace('{n}',x.n);n.hidden=false}}
fetch(U+'/intent').then(function(r){return r.json()}).then(show).catch(function(){});
if(g('yk_sy')){b.disabled=true;b.textContent=T.done}
b.onclick=function(){if(g('yk_sy'))return;s('yk_sy');b.disabled=true;b.textContent=T.done;
fetch(U+'/intent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({join:true})}).then(function(r){return r.json()}).then(show).catch(function(){})};
})();</script>""")
    return out, T

def redirect(to):  # 搬走的旧网址：只留一张转跳页，不进站点地图
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>一孔书院</title><link rel="canonical" href="https://yikonglu.com{to}">'
            f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={to}"><script>location.replace({json.dumps(to)}+location.hash)</script></head>'
            f'<body><main><p>已搬到 <a href="{to}">{to}</a></p></main></body></html>')

def build(L, write, page, live, DOMAIN):
    b, T = body(L, live)
    if L.code.startswith("zh"): b = b.replace('<div class="chhead"><div class="wrap"><h1>', f'<div class="chhead"><div class="wrap"><p class="crumb"><a href="/{L.prefix}shuyuan/">一孔书院</a></p><h1>', 1)
    write("shuyuan/ruyuan.html", page(L, f'{T["title"]}｜一孔录', T["p1"][:120], "shuyuan/ruyuan.html", b))
    write("shuyuan.html", redirect(f"/{L.prefix}shuyuan/ruyuan.html"))
    return [f"{DOMAIN}/{L.prefix}shuyuan/ruyuan.html"]

def link(L, P):
    return f'<a href="{P}shuyuan/ruyuan.html" class="sylink">{LINK["zh"] if L.code.startswith("zh") else L.ui.get("academy") or LINK["en"]}</a>'

def hub(P, mapimg, n_ppl, nowtxt):
    """11-16 主人点卡：书院先开题名；首页页首句与入院页一致，介绍压成一段指向入院页；院落、学籍、书友圈雏形撤下（书友圈留到每周读满四天过 300 人）。"""
    T = TM_ZH
    return f'''<div class="syhero"><img src="{mapimg}" alt="" width="2000" height="1150"><div class="wrap"><span class="ov">一孔书院</span><h1>一孔书院</h1>
<p class="symotto">{T["motto"]}</p><p class="syhbtn"><a class="btn" href="{P}shuyuan/ruyuan.html">在年历上题一天 ›</a><a class="btn ghost" href="{P}nianli/">看《论语》年历</a></p></div></div>
<main class="wrap narrow gsmain shuyuan">
<p class="lead">一孔录的片子、原文、白话、读本、年历永远免费。书院不卖内容，只做一件事：2027 年元旦起，一孔录按年历每天读一章《论语》，愿意出一份力的书友，可以把名字和一句不超过 20 字的题记，题在年历的某一天上，那一天的年历页、章页和公众号文末都会写上。<a href="{P}shuyuan/ruyuan.html">看题名怎么题 ›</a></p>
<h2 class="ph">书院里的人和地方</h2>
<div class="sydeep"><a href="{P}shuyuan/juese.html"><b>一孔录原创角色</b><span>{n_ppl} 位常驻书院的人：身份、本领、在哪些章出场 ›</span></a><a href="{P}shuyuan/ditu/"><b>经典世界地图</b><span>片里的世界，一层层点到书区{nowtxt} ›</span></a></div>
</main>'''
