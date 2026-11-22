"""问易 /wenyi/（11-20 主人：问易线程对完后上线，免费试运营；版式与站内一致）。
交接单 评审/2026-11-20-问易/交接-网站-1120/交接单.md。只出简体页。
正文 tools/wenyi/zhouyi-450.json（[卦序, 爻位, 经文, 拼音, 朱注, 四库页, 朱熹音注, 白话]）按卦拆成 /wenyi/d/<卦序>.json，
起出哪一卦才取哪一卦（项目规矩：网站不放成批读音数据）。宋本原页 tools/root/wenyi/yb/*.webp，框坐标 tools/wenyi/yb.json 跟着拆进每卦文件。
问的那句话只存读者本机浏览器，不上传。"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

BODY = '''<main class="wrap narrow wy">
<section id="s-intro" class="wyst">
<p class="wyjing">初筮告，再三瀆，瀆則不告。</p>
<p class="note">《周易·蒙》卦辞。同一件事只问一次，一天只起一卦。</p>
<label class="wyst" for="q"><span>把要问的事写下来，一件事，写清楚。写好才能起筮。</span>
<textarea id="q" maxlength="200" placeholder="比如：明年春天该不该换工作"></textarea></label>
<p class="note">你写的这句话只存在你自己这台手机或电脑的浏览器里，不会发给一孔录，也不会发给任何人。清掉浏览器数据就没了。</p>
<p><button class="btn wymain" id="start" type="button">起筮</button></p>
<p class="note">照朱熹《周易本义》书前《筮仪》和《系辞上》“大衍之数”一章，十八变一步不少。每一爻由你亲手分第一下，后两变照规矩接着走；第一爻会一步一步讲每个动作的意思。约两分钟。</p>
</section>
<section id="s-ritual" class="wyst" hidden>
<div class="wyrow wyhd"><div><span class="wytag">进度</span><h2 id="prog">第一爻 · 第一变</h2></div><div class="gua sm" id="mini" aria-label="已成的爻"></div></div>
<div id="yi" aria-live="polite"><span class="wytag" id="yi-tag">《系辞上》</span><span class="yw" id="yi-yw"></span><span class="bh" id="yi-bh"></span></div>
<div id="field" aria-label="蓍草。在草上左右划，松手处分成两堆"><div id="tray" aria-label="指间的蓍草"></div><div id="cut" hidden></div></div>
<div class="capbox"><img class="ava" src="/assets/lead/luchuan-ban.webp" alt="陆川" width="40" height="40"><p id="cap">用手指在蓍草上划，松手的地方就是分开的地方。</p></div>
<div class="wyrow"><button class="btn" id="next" type="button" hidden>明白了，往下</button><button class="btn ghost" id="auto1" type="button">替我分这一次</button><button class="btn ghost" id="snd" type="button" aria-pressed="true">声音：开</button></div>
</section>
<section id="s-result" class="wyst" hidden>
<span class="wytag" id="r-date"></span>
<div class="pair" id="r-pair"></div>
<div class="wyst"><h2>该读哪一句</h2><p id="r-rule"></p><p class="note">取法照朱熹《易学启蒙·考变占》七条。</p></div>
<div class="capbox"><img class="ava" src="/assets/lead/luchuan-ban.webp" alt="陆川" width="40" height="40"><p>这是你起出来的那一句。怎么读，你自己定。</p></div>
<div class="wyst" id="r-texts"></div>
<h2>卦帖</h2>
<div id="tie"></div>
<div class="wyrow"><button class="btn" id="share" type="button">分享卦帖</button><span class="note" id="share-msg"></span></div>
<img id="share-img" alt="分享用的卦帖图" hidden>
<p class="note">分享图里只有卦和爻辞，你写的问题不会进图。</p>
<h2>我的筮记</h2>
<label class="wyst" for="memo"><span class="note">只存在这台设备上。</span><textarea id="memo" placeholder="今天问的事，自己怎么读这一句"></textarea></label>
<div class="wyrow"><button class="btn ghost" id="save" type="button">记下</button><span class="note" id="saved"></span></div>
<ul id="log"></ul>
<p><button class="btn ghost" id="again" type="button">再求一次</button></p>
</section>
<section id="s-gate" class="wyst" hidden>
<h2 id="g-title"></h2><p id="g-body"></p>
<p><button class="btn ghost" id="back" type="button">回到开头</button></p>
</section>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js" defer></script>
<script>%s</script>'''


def build(L, write, page, DOMAIN):
    if L.code != "zh-Hans": return []
    rows = json.load(open(os.path.join(HERE, "wenyi", "zhouyi-450.json"), encoding="utf-8"))
    yb = json.load(open(os.path.join(HERE, "wenyi", "yb.json"), encoding="utf-8"))
    by = {}
    for r in rows: by.setdefault(r[0], []).append(r)
    for n, rs in by.items():
        ks = {f"{n}-{r[1]}" for r in rs}
        ybn = {k: v for k, v in yb["YB"].items() if k in ks}
        g = {h: yb["YBG"][h] for v in ybn.values() for h, _ in v if h in yb["YBG"]}
        write(f"wenyi/d/{n}.json", json.dumps({"r": rs, "yb": ybn, "g": g}, ensure_ascii=False, separators=(",", ":")))
    js = open(os.path.join(HERE, "wenyi", "wenyi.js"), encoding="utf-8").read()
    try: _live = (json.load(open(os.path.join(HERE, "analytics.json"), encoding="utf-8")).get("live") or "").rstrip("/")
    except Exception: _live = ""
    js = js.replace("@LIVE@", _live)  # 11-22 问易计数（只计数，不显示、不带编号）
    head = '<div class="chhead"><div class="wrap"><h1><span class="no">照朱熹《筮仪》起一卦 · 试运营</span>问易</h1></div></div>'
    write("wenyi/index.html", page(L, "问易：照朱熹《筮仪》起一卦，读《周易》原文与朱注｜一孔录",
                                   "照朱熹《周易本义·筮仪》十八变起一卦，按《易学启蒙》取辞，读经文、白话、朱熹注和宋本原页。一天一卦，问的话只存在你自己的设备上。",
                                   "wenyi/", head + BODY % js.replace("</script", "<\\/script")))
    return [f"{DOMAIN}/wenyi/"]
