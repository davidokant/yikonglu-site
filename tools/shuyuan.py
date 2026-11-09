"""一孔书院筹备页 /shuyuan.html（11-09 主人：把会员权益展示清楚，价格先不放；年底送电子版珍藏读本）。
简体全文，繁体由简体转；外文页一律出英文摘要。意愿只计数：yikonglu-live 的 /intent（满 20 才显示人数）、/intent/stats。
文案源：评审/2026-11-06-尽快变现/书院筹备页-文案-v1.md。"""
import html, json

def esc(s): return html.escape(s or "", quote=True)

WANT = [("shiyong", "这句话怎么用", "How to use this line"), ("shuhou", "书后面的事", "Behind the text"),
        ("shuyou", "书友圈", "A circle of like-minded readers"), ("gongdu", "共读", "Reading together"), ("wenda", "问一孔必答", "Every question answered"),
        ("gongju", "工具", "Tools"), ("zhencang", "珍藏读本", "Year-end keepsake reader")]

LINK = {"zh": "一孔书院 · 筹备中", "en": "Yikonglu Academy · coming"}
CAST = [("youli", "上官有理"), ("zhaojin", "孔照今"), ("shouzhuo", "林守拙"), ("luchuan", "陆川"), ("liuqi", "阮流绮"), ("shahela", "莎赫拉")]

ZH = dict(
    title="一孔书院（筹备中）", sub="会员书院 · 还没开门，先看看里面有什么",
    motto="免费的，管读懂；书院，管用上，和一起读。",
    p1="一孔录的片子、原文、白话、读本，永远免费，不会因为书院变薄。书院是给读懂了还想把书用到日子里、想有人一起读的书友准备的。",
    th=("", "免费（一直有）", "书院会员"),
    rows=[("逐章讲读视频、播客", "✓", "✓"), ("原文、白话、原页、读本 PDF", "✓", "✓"),
          ("问一孔", "每周选答", "<b>保证有答</b>"),
          ("每周一集“这句话怎么用”（处境读法）", "—", "✓"),
          ("每月一集“书后面的事”（注家怎么争、一孔按展开、跨章串读）", "—", "✓"),
          ("书友圈：志趣相投的人聚在一处，读到哪聊到哪", "—", "✓"),
          ("每季共读（孔照今主持）＋每月音频答疑", "—", "✓"),
          ("逐句全注对照、高清原页标注、打印版全书读本", "—", "✓"),
          ("致谢页署名、年底电子版珍藏读本", "—", "✓")],
    h_tbl="免费与书院，一张表看清", h_cards="书院里有什么",
    main=("主菜：每周一集“这句话怎么用”", ["从一章里挑一句，放进今天的处境：带孩子、跟上司相处、跟朋友闹翻、自己想放弃的时候，这句话能怎么用。",
                                    "书友在问一孔里问的真实处境，优先拿来讲。",
                                    "一集十来分钟，不用懂注疏也听得进去。",
                                    "样子跟免费片不一样：不是满屏书页和字，而是一孔录原创角色在想象的场景里碰上事、争起来、翻出这句话；原文只在关键处亮一次，出处照样可核。"]),
    cast_note="演这些短剧的，是一孔录原创角色：",
    cards=[("加餐：每月一集“书后面的事”", ["给想往深里走的书友。", "<b>注家怎么争</b>：一句话，汉儒、朱子、清儒各怎么说，原页摆出来。",
                                     "<b>一孔按展开</b>：片子里一句带过的判断，讲清楚为什么这样定。",
                                     "<b>跨章串读</b>：同一个字、同一件事，全书前后怎么呼应。"]),
           ("书友圈", ["把读同一部书、口味相近的人聚在一起：读到哪聊到哪，有人接话，有人较真。",
                     "每季一次共读：按进度表一起读一篇，孔照今招呼大家、点名、串场。",
                     "书友的“问一孔”，保证有答；每月一期音频答疑。"]),
           ("工具", ["逐句全注对照（网站会员版）。", "高清原页标注下载。", "打印版全书读本。"]),
           ("名字留下", ["致谢页署你的网名。", "每年年底送一本电子版珍藏读本。"])],
    h_how="", how_lead="智器主持，一孔把关，句句可核，人人有回音。", how="书院里的角色都是一孔录原创角色，由智器主持，每句读法有人审过。",
    h_plan="预计", plan=["<b>按书走</b>：一年跟着读完一部（先论语，后三字经、道德经）。",
                       "<b>开门时间</b>：想加入的书友够了就开。在哪里聚、怎么加入，开门时一并告诉第一批书友。"],
    h_join="想第一批加入？", btn="我想第一批加入", done="已记下，谢谢。", cnt="已有 {n} 位书友想第一批加入",
    want_q="再告诉我们，你最想要哪样（可多选）：", want_btn="提交", want_ok="收到，谢谢。",
    notify="想开门时被通知：公众号「一孔录」回复“书院”，或发邮件到 yikonglu99@gmail.com，主题写“书院”。",
    fine="本页只记人数，不收姓名、邮箱、电话。点按钮不代表付款，也不代表报名成功。", wl=1)

EN = dict(
    title="Yikonglu Academy (coming)", sub="A members' circle · not open yet",
    motto="The free side helps you understand; the Academy helps you use it, and read together.",
    p1="Everything free on Yikonglu stays free: videos, text, plain renderings, readers. The Academy is for readers who want to bring the classics into daily life and read with others. It is not open yet; it opens when enough readers want it. The Academy itself is in Chinese.",
    th=("", "Free (always)", "Academy members"),
    rows=[("Chapter videos and podcast", "✓", "✓"), ("Text, plain rendering, facsimile pages, PDF readers", "✓", "✓"),
          ("Ask Yikonglu", "Selected weekly", "<b>Always answered</b>"),
          ("Weekly “How to use this line”: one line, today's situations, acted out by our original characters", "—", "✓"),
          ("Monthly “Behind the text”: how the commentators disagree, our reading explained", "—", "✓"),
          ("A circle of like-minded readers, reading and talking together", "—", "✓"),
          ("Seasonal group reading + monthly audio Q&A", "—", "✓"),
          ("Full sentence-by-sentence commentary, annotated hi-res pages, print-ready full reader", "—", "✓"),
          ("Your name on the thanks page; a year-end keepsake e-reader", "—", "✓")],
    h_tbl="Free vs. Academy", h_cards="", main=None, cast_note="", cards=[],
    h_how="", how_lead="Hosted by AI, checked by Yikonglu: every line verifiable, every reader answered.", how="The characters in the Academy are Yikonglu's original characters, hosted by AI; every reading is reviewed by a person.",
    h_plan="", plan=[],
    h_join="Want to be in the first group?", btn="I'd like to join the first group", done="Noted, thank you.", cnt="{n} readers want to join the first group",
    want_q="What would you want most? (choose any)", want_btn="Send", want_ok="Thank you.",
    notify="To be told when it opens, email yikonglu99@gmail.com with the subject “Academy”.",
    fine="This page counts clicks only. No name, email or phone is collected. Clicking is not a payment or a registration.", wl=2)

def body(L, live):
    T = ZH if L.code.startswith("zh") else EN
    th = "".join(f"<th>{x}</th>" for x in T["th"])
    trs = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in T["rows"])
    cards = "".join(f'<div class="sycard"><h3>{h}</h3><ul>{"".join(f"<li>{x}</li>" for x in xs)}</ul></div>' for h, xs in T["cards"])
    main = ""
    if T["main"]:
        h, xs = T["main"]
        cast = "".join(f'<figure><img src="/gushi/img/{k}-full.png" alt="{n}" width="600" height="900" loading="lazy"><figcaption>{n}</figcaption></figure>' for k, n in CAST)
        main = f'<div class="sycard symain"><h3>{h}</h3><ul>{"".join(f"<li>{x}</li>" for x in xs)}</ul><p class="sycastn">{T["cast_note"]}</p><div class="sycast">{cast}</div></div>'
    wants = "".join(f'<label><input type="checkbox" value="{k}"> {zh if T["wl"] == 1 else en}</label>' for k, zh, en in WANT)
    out = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{T["sub"]}</span>{T["title"]}</h1></div></div>
<main class="wrap narrow prose shuyuan"><p class="symotto">{T["motto"]}</p><p>{T["p1"]}</p>
<p class="cta"><a class="btn" href="#join">{T["h_join"]}</a></p>
<h2>{T["h_tbl"]}</h2><div class="sytw"><table class="sytab"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>
{f'<h2>{T["h_cards"]}</h2>{main}<div class="sycards">{cards}</div>' if cards else ""}
{f'<p class="sytrust"><b>{T["how_lead"]}</b>{T["how"]}</p>' if T["how_lead"] else ""}
{f'<h2>{T["h_plan"]}</h2><ul>{"".join(f"<li>{x}</li>" for x in T["plan"])}</ul>' if T["plan"] else ""}
<h2 id="join">{T["h_join"]}</h2>
<div class="syjoin"><button type="button" class="btn" id="syb">{T["btn"]}</button><p class="sycnt" id="syn" hidden></p>
<div class="sywant" id="syw" hidden><p>{T["want_q"]}</p><div class="syopts">{wants}</div><button type="button" class="btn ghost" id="sywb">{T["want_btn"]}</button></div></div>
<p>{T["notify"]}</p><p class="note">{T["fine"]}</p></main>'''
    if live:
        out += ("<script>(function(){var U=" + json.dumps(live.rstrip("/")) + ",T=" + json.dumps({k: T[k] for k in ("done", "cnt", "want_ok")}, ensure_ascii=False) + r""";
var b=document.getElementById('syb'),n=document.getElementById('syn'),w=document.getElementById('syw'),wb=document.getElementById('sywb');
function g(k){try{return localStorage.getItem(k)}catch(e){return null}}function s(k){try{localStorage.setItem(k,'1')}catch(e){}}
function show(x){if(x&&x.n){n.textContent=T.cnt.replace('{n}',x.n);n.hidden=false}}
fetch(U+'/intent').then(function(r){return r.json()}).then(show).catch(function(){});
if(g('yk_sy')){b.disabled=true;b.textContent=T.done;if(!g('yk_syw'))w.hidden=false}
b.onclick=function(){if(g('yk_sy'))return;s('yk_sy');b.disabled=true;b.textContent=T.done;w.hidden=false;
fetch(U+'/intent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({join:true})}).then(function(r){return r.json()}).then(show).catch(function(){})};
wb.onclick=function(){var v=[].slice.call(w.querySelectorAll('input:checked')).map(function(i){return i.value});if(!v.length||g('yk_syw'))return;s('yk_syw');
fetch(U+'/intent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({want:v})}).catch(function(){});w.innerHTML='<p>'+T.want_ok+'</p>'};
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
    return f'<a href="{P}shuyuan/ruyuan.html" class="sylink">{LINK["zh" if L.code.startswith("zh") else "en"]}</a>'

# 书院首页（11-09 主人：书院介绍提到台前，人物线索深入一层，“跟着人物读”并入主题）
COURTS = [("menkou", "山门", "谁都能进", "书院介绍、院规、新人报到。上官有理在这里迎新。"),
          ("lunyu", "共读堂", "论语", "按篇开帖，一篇一帖。孔照今每周发进度，周五点名。"),
          ("shiyong", "明用斋", "这句话怎么用", "每周会员片一帖，下面聊自己的处境。"),
          ("shuhou", "藏书阁", "书后面的事", "每月加餐：注家怎么争、一孔按展开、跨章串读。"),
          ("wen", "问津亭", "问一孔", "书友提问，保证有答。"),
          ("xiantan", "茶寮", "闲谈", "读书之外的话。")]
IDENTS = ["书生", "游侠", "商旅", "医者", "匠人", "方外"]
RANKS = ["初入院", "学童", "生员", "斋长", "讲友"]

def hub(P, mapimg, n_ppl, nowtxt):
    T = ZH
    feats = [("每周", "这句话怎么用", "从一章里挑一句，放进今天的处境。一孔录原创角色演成情景短剧，不是满屏书页。"),
             ("每月", "书后面的事", "注家怎么争、一孔按展开、跨章串读，给想往深里走的书友。"),
             ("常驻", "书友圈", "把读同一部书、口味相近的人聚在一起：读到哪聊到哪，有人接话，有人较真。"),
             ("保证", "问一孔必答", "书友的问题保证有答；每季共读、每月音频答疑，年底送电子版珍藏读本。")]
    ft = "".join(f'<div class="syfeat"><span>{a}</span><b>{b}</b><p>{c}</p></div>' for a, b, c in feats)
    ct = "".join(f'<div class="sycourt c-{k}"><b>{n}</b><span>{s}</span><p>{d}</p></div>' for k, n, s, d in COURTS)
    host = "".join(f'<figure><img src="/gushi/img/{k}-head.png" alt="" loading="lazy" width="96" height="96"><figcaption><b>{n}</b>{r}</figcaption></figure>'
                   for k, n, r in (("youli", "上官有理", "迎新、院规、日常提醒"), ("zhaojin", "孔照今", "主持共读、点名、串场")))
    return f'''<div class="syhero"><img src="{mapimg}" alt="" width="2000" height="1150"><div class="wrap"><span class="ov">会员书院 · 筹备中</span><h1>一孔书院</h1>
<p class="symotto">{T["motto"]}</p><p class="syhbtn"><a class="btn" href="{P}shuyuan/ruyuan.html#join">我想第一批加入</a><a class="btn ghost" href="{P}shuyuan/ruyuan.html">看会员有什么 ›</a></p></div></div>
<main class="wrap narrow gsmain shuyuan">
<p class="lead">{T["p1"]}</p>
<h2 class="ph">书院里有什么</h2><div class="syfeats">{ft}</div>
<h2 class="ph">书院的样子<small>开门后在书友圈里</small></h2>
<p class="note">书友圈做成一座书院：进山门，按院落分区。入院时挑一个身份（{"、".join(IDENTS)}），发言越多学籍越高：{" → ".join(RANKS)}；会员名旁挂“书院门人”。</p>
<div class="sycourts">{ct}</div>
<div class="syhosts">{host}</div>
<p class="sytrust"><b>{T["how_lead"]}</b>{T["how"]}</p>
<a class="syjoincard" href="{P}shuyuan/ruyuan.html"><span class="ov">书院会员 · 筹备中</span><b>免费与书院，一张表看清</b><span>权益逐条列出；想第一批加入就点一下，只记人数 ›</span></a>
<h2 class="ph">书院里的人和地方</h2>
<div class="sydeep"><a href="{P}shuyuan/juese.html"><b>一孔录原创角色</b><span>{n_ppl} 位常驻书院的人：身份、本领、在哪些章出场 ›</span></a><a href="{P}shuyuan/ditu/"><b>经典世界地图</b><span>片里的世界，一层层点到书区{nowtxt} ›</span></a></div>
</main>'''
