"""逐句对照：章页原文同屏原页（点一句亮原页那一列）、“译”随文白话、点句/划选小卡。

数据（共享盘，不进仓库）：
  数据/网站素材/_句列/<章>.json      校平线程出：页图尺寸、经文大字逐字框 chars=[字,页,列,x0,y0,x1,y1]（按诵读顺序）
  数据/网站素材/_句列/页图/pNNN.png  校平后的页图；坐标就在这张图上，建站时换掉 tools/yuanye/pNNN.jpg
  数据/网站素材/_逐句/<章>.json      每句的白话、朱注、集解、一孔读法（网站线程写）
开关：tools/zhuju.json {"chapters": [...]}，只给列在里面的章出（样板先 1.1，主人“过”了再铺开）。
句的切法以网站 split_ju 为准：把 chars 的字序按每句去标点后的字数依次分给各句。
"""
import json, os, re, glob
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "yuanye_wm"))
import wm as WM  # 原页切边、角标（11-14）

SRC = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材"
JL_DIR = os.path.join(SRC, "_句列")
ZJ_DIR = os.path.join(SRC, "_逐句")
HERE = os.path.dirname(os.path.abspath(__file__))
PUNCT = re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》〈〉·…—,.;:?!()\[\]]")


def load():
    on = set(json.load(open(os.path.join(HERE, "zhuju.json"), encoding="utf-8")).get("chapters", [])) if os.path.exists(os.path.join(HERE, "zhuju.json")) else set()
    jl, zj = {}, {}
    for f in glob.glob(os.path.join(JL_DIR, "*.json")):
        c = os.path.basename(f)[:-5]
        if c.startswith("_"): continue
        jl[c] = json.load(open(f, encoding="utf-8"))
    for f in glob.glob(os.path.join(ZJ_DIR, "*.json")):
        c = os.path.basename(f)[:-5]
        if c.startswith("_"): continue
        zj[c] = json.load(open(f, encoding="utf-8"))
    on |= set(jl) & set(zj)  # 11-15：句列、逐句都有的章自动开（原先靠手加名单，6.21—7.10 讲过了却漏开，原页不显示）
    return {"on": on, "jl": jl, "zj": zj}


def swap_pages(Z, ydir):
    """句列表里用到、且校平过（angle≠0）的页，用校平图替换 tools/yuanye/pNNN.jpg。尺寸不同才重出，免得每次重压。"""
    from PIL import Image
    done = set()
    for c, d in Z["jl"].items():
        for p, meta in d.get("pages", {}).items():
            if p in done or not (meta.get("deskew") or {}).get("angle"): continue
            png = os.path.join(JL_DIR, "页图", meta.get("image") or (p + ".png"))
            if not os.path.exists(png): continue
            jpg = os.path.join(ydir, p + ".jpg")
            im = Image.open(png)
            tw = min(1400, im.width); th = round(im.height * tw / im.width)
            if os.path.exists(jpg) and Image.open(jpg).size == (tw, th):
                done.add(p); continue
            im = im.convert("RGB")
            if im.width != tw: im = im.resize((tw, th))
            im.save(jpg, quality=78, optimize=True, progressive=True)
            done.add(p)
    return done


_VAR = str.maketrans({"脩": "修", "愼": "慎", "闲": "间", "閒": "间", "衞": "卫", "雕": "彫", "衆": "众", "犂": "犁", "甯": "寗", "縲": "缧", "絏": "绁", "䯄": "騧", "泛": "汎", "𫐐": "輗", "𫐄": "軏", "𦰏": "蓧"})
def _vn(t): return t.translate(_VAR)


def spans_of(c, sents, Z):
    from opencc import OpenCC
    t2s = OpenCC("t2s").convert
    """返回 (pages, per)：pages={页:{w,h}}；per[i]=这一句在各页各列的框 [[页,x0,y0,x1,y1],...]，合并同列相邻字。"""
    d = Z["jl"].get(c)
    if not d: return None, None
    chars = d.get("chars") or [ch for s in d.get("sentences", []) for ch in s.get("chars", [])]
    per, k = [], 0
    for s in sents:
        need = PUNCT.sub("", s)
        got = chars[k:k + len(need)]; k += len(need)
        if _vn(t2s("".join(x[0] for x in got))) != _vn(need):  # 底本异体字（脩/修、愼/慎、閒/间、衞/卫、雕/彫）不算对不上
            print(f"  句列对不上 {c}：{need} ≠ {''.join(x[0] for x in got)}")
        boxes = []
        for ch, p, col, x0, y0, x1, y1 in got:
            if boxes and boxes[-1][0] == p and boxes[-1][5] == col:
                b = boxes[-1]; b[1] = min(b[1], x0); b[3] = max(b[3], x1); b[2] = min(b[2], y0); b[4] = max(b[4], y1)
            else:
                boxes.append([p, x0, y0, x1, y1, col])
        per.append([b[:5] for b in boxes])
    if k != len(chars): print(f"  句列字数不符 {c}：网站 {k} 字，表里 {len(chars)} 字")
    pages = {p: {"w": m["w"], "h": m["h"]} for p, m in d["pages"].items()}
    return pages, per


def frame_rows(p, ydir, w, h):
    """主人 11-07：原页面板裁掉上下白边。按版框横线找：整行四分之一以上是深色像素的最上和最下一行，各留 36 像素。找不到就整页。"""
    try:
        from PIL import Image
        import numpy as np
        im = np.array(Image.open(os.path.join(ydir, p + ".jpg")).convert("L"))
        sx = im.shape[1] / w
        dark = (im < 110).sum(axis=1)
        rows = np.where(dark > im.shape[1] * 0.25)[0]
        if len(rows) < 2: return 0, h
        y0, y1 = int(rows.min() / sx) - 36, int(rows.max() / sx) + 36
        return max(0, y0), min(h, y1)
    except Exception:
        return 0, h


def page_pane(c, pages, per, label, ydir=None, alt=None):  # alt：图片说明模板（{n}＝页码），给图片搜索与读屏用
    """原页面板：每页一张 svg（底图＋各句的高亮框，默认隐藏），点句时由 ZJ_JS 显示该句框并滚到那里。viewBox 只取版框上下，白边不显示。"""
    out = []
    order = sorted(pages, key=lambda p: int(re.sub(r"\D", "", p)), reverse=False)
    for p in order:
        w, h = pages[p]["w"], pages[p]["h"]
        n = int(re.sub(r"\D", "", p))
        aria = alt.format(n=n) if alt else f'{label} {n}'
        if ydir and os.path.exists(os.path.join(ydir, p + ".jpg")):  # 11-14 起原页图切白边、加角标（yuanye_wm）：底图就是切好的那块，句框坐标平移到切图上
            from PIL import Image
            jp = os.path.join(ydir, p + ".jpg"); k = Image.open(jp).width / w
            bx0, by0, bx1, by1 = [v / k for v in WM.crop_box(jp, p)]
            iw, ih = round(bx1 - bx0, 1), round(by1 - by0, 1)
            rects = "".join(f'<rect class="hl" data-s="{i}" x="{round(x0 - bx0, 1)}" y="{round(y0 - by0, 1)}" width="{x1 - x0}" height="{y1 - y0}" rx="6"/>'
                            for i, bx in enumerate(per, 1) for (pp, x0, y0, x1, y1) in bx if pp == p)
            out.append(f'<a class="yyp" href="/yuanye/{p}.jpg" target="_blank" data-p="{p}"><svg viewBox="0 0 {iw} {ih}" role="img" aria-label="{aria}">'
                       f'<image href="/yuanye/{p}.jpg" width="{iw}" height="{ih}"/>{rects}</svg><span>{label} {n}</span></a>')
            continue
        fy0, fy1 = frame_rows(p, ydir, w, h) if ydir else (0, h)
        rects = "".join(f'<rect class="hl" data-s="{i}" x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6"/>'
                        for i, bx in enumerate(per, 1) for (pp, x0, y0, x1, y1) in bx if pp == p)
        out.append(f'<a class="yyp" href="/yuanye/{p}.jpg" target="_blank" data-p="{p}"><svg viewBox="0 {fy0} {w} {fy1 - fy0}" role="img" aria-label="{aria}">'
                   f'<image href="/yuanye/{p}.jpg" width="{w}" height="{h}"/>{rects}</svg><span>{label} {n}</span></a>')
    return "".join(out)


def card_data(c, Z, n_sent):
    z = Z["zj"].get(c)
    if not z: return None
    ss = z.get("句", [])
    if len(ss) != n_sent: print(f"  逐句条数不符 {c}：网站 {n_sent} 句，_逐句 {len(ss)} 句")
    return ss


# 点句或划选：开小卡（白话、朱注、集解、一孔读法四签＋复制带出处、分享图）；同时亮原页那几列。
# “译”：每句原文下压一段灰底白话，默认关，记在 localStorage（读不到就当关）。
# 原生复制（Ctrl+C／长按复制）原文里的字，也自动带出处。
ZJ_JS = """<div id="zjcard" class="zjcard" hidden><div class="znav"><button type="button" data-a="pv" aria-label="上一句">‹ 上一句</button><button type="button" data-a="nx" aria-label="下一句">下一句 ›</button></div><p class="zq"></p><div class="zt"></div><div class="zb"></div><div class="za"><button data-a="q">@COPY@</button><button data-a="img">@IMG@</button><button data-a="l">@LINK@</button></div><p class="zx"></p></div>
<script>
(function(){var F=document.querySelector('.yuanwen.dz');if(!F)return;var Q=F.querySelector('blockquote'),C=document.getElementById('zjcard'),S=[];try{S=JSON.parse(F.querySelector('.zjdata').textContent)}catch(e){}
var TABS=@TABS@,cur=null,sel='',tab='bh';
function hl(n){F.querySelectorAll('.yyp .hl').forEach(function(r){r.classList.toggle('on',r.dataset.s==n)});var r=F.querySelector('.yyp .hl[data-s="'+n+'"]'),P=F.querySelector('.yypane');if(r&&P&&P.scrollHeight>P.clientHeight+4){var a=r.getBoundingClientRect(),b=P.getBoundingClientRect();P.scrollTo({top:P.scrollTop+a.top-b.top-(b.height-a.height)/2,left:P.scrollLeft+a.left-b.left-(b.width-a.width)/2,behavior:'smooth'})}else if(r){var q=r.getBoundingClientRect();if(q.top<0||q.bottom>innerHeight)r.scrollIntoView({block:'nearest',behavior:'smooth'})}}
function esc(t){var d=document.createElement('div');d.textContent=t;return d.innerHTML}
function body(){var d=S[cur.dataset.n-1]||{},B=C.querySelector('.zb'),v=d[tab];C.querySelectorAll('.zt button').forEach(function(b){b.classList.toggle('on',b.dataset.t===tab)});
if(!v||!v.length){B.innerHTML='<p><small>@NONE@</small></p>';return}
if(typeof v==='string'){B.innerHTML='<p>'+esc(v)+'</p>';return}
B.innerHTML=v.map(function(x){return '<p>'+esc(x[0])+(x[1]?'<small>'+esc(x[1])+'</small>':'')+(x[2]?'<small class="dai">'+esc(x[2])+'</small>':'')+'</p>'}).join('')}
function open(s,txt){cur=s;sel=txt||'';F.querySelectorAll('.ju.on').forEach(function(x){x.classList.remove('on')});s.classList.add('on');hl(s.dataset.n);
C.querySelector('.zq').textContent=sel||s.textContent;var d=S[s.dataset.n-1]||{};
C.querySelector('.zt').innerHTML=TABS.filter(function(t){return d[t[0]]&&d[t[0]].length}).map(function(t){return '<button type="button" data-t="'+t[0]+'">'+t[1]+'</button>'}).join('');
if(!(d[tab]&&d[tab].length)){var f0=TABS.filter(function(t){return d[t[0]]&&d[t[0]].length})[0];tab=f0?f0[0]:'bh'}body();
var R=[];try{R=JSON.parse(Q.dataset.reads||'[]')}catch(e){}var t=s.textContent,hit=R.filter(function(x){return x[1].split('\\u3001').some(function(p){return p&&t.indexOf(p)>=0})});
C.querySelector('.zx').textContent=hit.length?Q.dataset.rl+hit.map(function(x){return x[0]+' '+x[2]}).join(' \\u00b7 '):'';
var r=(window.getSelection&&sel&&getSelection().rangeCount?getSelection().getRangeAt(0):s).getBoundingClientRect();C.hidden=false;C.style.top=(window.scrollY+r.bottom+8)+'px';C.style.left=Math.max(8,Math.min(window.scrollX+r.left,document.documentElement.clientWidth-C.offsetWidth-8))+'px';
var N=F.querySelectorAll('.ju[data-n]').length,k=+s.dataset.n;C.querySelector('[data-a=pv]').disabled=k<=1;C.querySelector('[data-a=nx]').disabled=k>=N;
try{history.replaceState(null,'','#'+s.id)}catch(e){}}
function step(d){if(!cur)return;var s=F.querySelector('.ju[data-n="'+(+cur.dataset.n+d)+'"]');if(s){open(s);var r=s.getBoundingClientRect();if(r.top<60||r.bottom>innerHeight-40)s.scrollIntoView({block:'center',behavior:'smooth'})}}
function close(){C.hidden=true;if(cur)cur.classList.remove('on');cur=null}
function cite(t,s){return '\\u201c'+t+'\\u201d\\u2014\\u2014'+Q.dataset.src+(Q.dataset.short?' '+Q.dataset.short:Q.dataset.sep+Q.dataset.url+'#'+s.id)}
function put(t,b){var o=b.textContent,done=function(){b.textContent='@DONE@';setTimeout(function(){b.textContent=o},1200)};if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(done,function(){prompt('',t)});else prompt('',t)}
Q.addEventListener('click',function(e){var s=e.target.closest('.ju');if(!s)return;var g=window.getSelection?String(getSelection()).trim():'';if(g&&s.contains(getSelection().anchorNode))open(s,g.replace(/\\s+/g,''));else open(s)});
Q.addEventListener('keydown',function(e){if(e.key==='Enter'){var s=e.target.closest('.ju');if(s)open(s)}});
document.addEventListener('selectionchange',function(){var g=getSelection();if(!g.rangeCount||g.isCollapsed)return;var n=g.anchorNode&&(g.anchorNode.nodeType===1?g.anchorNode:g.anchorNode.parentNode),s=n&&n.closest&&n.closest('.ju');if(s&&Q.contains(s)){clearTimeout(window._zjt);window._zjt=setTimeout(function(){var t=String(getSelection()).trim().replace(/\\s+/g,'');if(t)open(s,t)},450)}});
C.addEventListener('click',function(e){var b=e.target.closest('button');if(!b||!cur)return;if(b.dataset.t){tab=b.dataset.t;body();return}
var a=b.dataset.a;if(a==='pv'||a==='nx'){step(a==='pv'?-1:1);return}if(a==='q'){put(cite(sel||cur.textContent,cur),b);if(window.yklCopy)window.yklCopy(cur.id)}else if(a==='l')put(Q.dataset.url+'#'+cur.id,b);else if(a==='img'){if(window.ykPickSent)window.ykPickSent(+cur.dataset.n);else if(window.yklCard)window.yklCard({y:sel||cur.textContent,u:Q.dataset.url+'#'+cur.id,n:cur.dataset.n})}});
document.addEventListener('click',function(e){if(!C.hidden&&!C.contains(e.target)&&!e.target.closest('.ju')&&!e.target.closest('.dztools'))close()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')close();else if(!C.hidden&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){e.preventDefault();step(e.key==='ArrowLeft'?-1:1)}});
var tx=null;C.addEventListener('touchstart',function(e){tx=e.touches[0].clientX},{passive:true});C.addEventListener('touchend',function(e){if(tx===null)return;var dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>50)step(dx<0?1:-1)},{passive:true});
var TP=document.querySelector('.top');function th(){if(TP)document.documentElement.style.setProperty('--toph',TP.offsetHeight+'px')}th();addEventListener('resize',th);
Q.addEventListener('copy',function(e){var g=getSelection(),t=String(g).replace(/\\s+/g,'');if(!t||!e.clipboardData)return;var n=g.anchorNode&&(g.anchorNode.nodeType===1?g.anchorNode:g.anchorNode.parentNode),s=n&&n.closest&&n.closest('.ju')||Q.querySelector('.ju');e.clipboardData.setData('text/plain',cite(t,s));e.preventDefault()});
var Y=F.querySelector('.yibtn'),YK='yk_yi';function yi(on){Y.setAttribute('aria-pressed',on?'true':'false');F.classList.toggle('yion',on);F.querySelectorAll('.yi').forEach(function(x){x.hidden=!on});try{localStorage.setItem(YK,on?'1':'0')}catch(e){}}
if(Y){var on0=false;try{on0=localStorage.getItem(YK)==='1'}catch(e){}yi(on0);Y.addEventListener('click',function(){yi(Y.getAttribute('aria-pressed')!=='true')})}
var h=location.hash.slice(1);if(/^s\\d+$/.test(h)){var t=document.getElementById(h);if(t&&Q.contains(t)){t.classList.add('on');setTimeout(function(){hl(t.dataset.n)},300)}}
})();
</script>"""


# 外文章页（11-13）：原文旁同屏原页，点句只亮原页那几列（小卡的白话、朱注是中文，只在简繁页出）；手机上点原页放大看原图
HL_JS = """<script>(function(){var F=document.querySelector('.yuanwen.dz.nocard');if(!F)return;var Q=F.querySelector('blockquote');
function hl(n){F.querySelectorAll('.yyp .hl').forEach(function(r){r.classList.toggle('on',r.dataset.s==n)});var r=F.querySelector('.yyp .hl[data-s="'+n+'"]'),P=F.querySelector('.yypane');
if(r&&P&&P.scrollHeight>P.clientHeight+4){var a=r.getBoundingClientRect(),b=P.getBoundingClientRect();P.scrollTo({top:P.scrollTop+a.top-b.top-(b.height-a.height)/2,behavior:'smooth'})}}
Q.addEventListener('click',function(e){var s=e.target.closest('.ju');if(!s)return;F.querySelectorAll('.ju.lit').forEach(function(x){x.classList.remove('lit')});s.classList.add('lit');hl(s.dataset.n)});
var h=location.hash.slice(1);if(/^s\\d+$/.test(h)){var t=document.getElementById(h);if(t&&Q.contains(t))setTimeout(function(){hl(t.dataset.n)},300)}})();</script>"""


# ---------- 11-15 原页开卷（跟镜头、取字、画红框）与听读同步（逐字亮、慢速、跟读） ----------
# 逐字时间：数据/网站素材/_逐字时间/<章>.json（炫技演示线程出，朗读重配后用它的 align_all.py 重出），只用 conf＝“稳”的章
TM_DIR = os.path.join(SRC, "_逐字时间")
CJK = re.compile(r"[㐀-鿿豈-﫿\U00020000-\U0002ffff]")
_SHIFT = {}


def _shift(p, ydir, w):
    """原页面板切过白边的页，句框坐标要平移（同 page_pane）；没切的页不平移。w＝句列表里这页的宽。"""
    if p in _SHIFT: return _SHIFT[p]
    s = (0, 0)
    jp = os.path.join(ydir, p + ".jpg") if ydir else ""
    if jp and os.path.exists(jp):
        from PIL import Image
        k = Image.open(jp).width / w
        bx0, by0, _, _ = [v / k for v in WM.crop_box(jp, p)]
        s = (bx0, by0)
    _SHIFT[p] = s
    return s


def timing(c):
    f = os.path.join(TM_DIR, c + ".json")
    if not os.path.exists(f): return None
    d = json.load(open(f, encoding="utf-8"))
    return d if d.get("conf") == "稳" else None


KJ_RECUT = set()


def kj_data(c, sents, Z, ydir):
    """章页原页开卷与听读同步的数据：z＝每个字在原页面板上的框 [页, x, y, w, h]（按诵读顺序，与原文里的汉字一一对应）；
    t＝每个字的起止秒（只稳的章）；k＝小句 [起字, 止字]。字数对不上就不给。"""
    d = Z["jl"].get(c)
    if not d: return None
    from opencc import OpenCC
    t2s = OpenCC("t2s").convert
    text = "".join(sents); zs = CJK.findall(text)
    chars = d.get("chars") or [ch for s in d.get("sentences", []) for ch in s.get("chars", [])]
    if len(chars) < len(zs) or _vn(t2s("".join(x[0] for x in chars[:len(zs)]))) != _vn("".join(zs)): return None
    z = []
    for ch, p, col, x0, y0, x1, y1 in chars[:len(zs)]:
        sx, sy = _shift(p, ydir, d["pages"][p]["w"])
        z.append([p, round(x0 - sx, 1), round(y0 - sy, 1), round(x1 - x0, 1), round(y1 - y0, 1)])
    out = {"z": z}
    tm = timing(c)
    if tm and len(tm["chars"]) == len(zs) and _vn(t2s("".join(x[0] for x in tm["chars"]))) == _vn("".join(zs)):
        out["t"] = [[round(a, 3), round(b, 3)] for _, a, b in tm["chars"]]
        k, i = [], 0
        for txt, a, b in tm.get("clauses") or []:
            n = len(CJK.findall(txt)); k.append([i, i + n]); i += n
        # 小句按现在的原文标点：逐字时间的 clauses 若是按旧标点切的（边界落在没有标点的地方），就照现在的原文重切
        cut, j = set(), 0
        for ch in text:
            if CJK.match(ch): j += 1
            elif ch in "，。；：？！、" and j: cut.add(j)
        cut.add(len(zs))
        if i != len(zs) or any(b not in cut for _, b in k):
            k, a = [], 0
            for b in sorted(x for x in cut if x > 0):
                if b > a: k.append([a, b]); a = b
            i = a; KJ_RECUT.add(c)
        if i == len(zs): out["k"] = k
        out["d"] = tm.get("dur")
    return out


KJ_JS = ("<script>" + re.sub(r"/\*.*?\*/", "", open(os.path.join(HERE, "kaijuan.js"), encoding="utf-8").read(), flags=re.S) + "</script>") if os.path.exists(os.path.join(HERE, "kaijuan.js")) else ""


def kj_tag(c, sents, Z, ydir):
    d = kj_data(c, sents, Z, ydir)
    return f'<script type="application/json" class="zjkj">{json.dumps(d, ensure_ascii=False, separators=(",", ":"))}</script>' if d else ""


# ---------- 11-15 注音答案卡（十一项之 5）：数据/网站素材/_注音/<章>.json（炫技演示线程出，zi＝[字, 拼音, 注音符号, 多音字1, 依据]）----------
# 只上：没有“待核”的章；与本章网站读音表（reads）每处都一致的章。对不上的章不上，等人核。
ZY_DIR = os.path.join(SRC, "_注音")
ZY_SKIP = {}


def zhuyin(c, sents, reads):
    f = os.path.join(ZY_DIR, c + ".json")
    if not os.path.exists(f): return None
    zi = json.load(open(f, encoding="utf-8")).get("zi") or []
    if any("待核" in str(x[-1]) for x in zi): ZY_SKIP[c] = "待核"; return None
    from opencc import OpenCC
    t2s = OpenCC("t2s").convert
    zs = CJK.findall("".join(sents))
    if len(zs) != len(zi) or _vn(t2s("".join(zs))) != _vn(t2s("".join(x[0] for x in zi))): ZY_SKIP[c] = "字对不上"; return None
    for r in reads or []:
        # 同一字在读音表里分几行（如 6.21 乐水的乐 yào、知者乐的乐 lè）：注音里的每个读法只要落在这几行之一就算对上
        du = " ".join(re.sub(r"（.*?）", "", x.get("du", "")).strip() for x in reads if x.get("zi") == r.get("zi"))
        occ = [x[1] for x in zi if x[0] == r.get("zi")]
        if not occ: continue
        # 读音表“位置”能在原文里找到的，只核那几处（同一章里同一字别处另读，如 2.18 行 xíng／xìng）
        hz = "".join(x[0] for x in zi); at = []
        for part in (r.get("pos") or "").split("、"):
            pt = "".join(CJK.findall(part)); o = pt.find(r.get("zi") or "\0")
            if len(pt) < 2 or o < 0: continue
            i = hz.find(pt)
            while i >= 0: at.append(i + o); i = hz.find(pt, i + 1)
        if at: occ = [zi[i][1] for i in sorted(set(at))]
        multi = any(s in du for s in (" ", "；", "/", "，"))
        if (multi and not all(o in du for o in occ)) or (not multi and any(o != du for o in occ)):
            ZY_SKIP[c] = f"与网站读音表不一致：{r.get('zi')} 网站 {r.get('du')}，注音 {'/'.join(occ)}"; return None
    return [[x[1], x[2], 1 if len(x) > 4 and x[3] == 1 and x[4] else 0] for x in zi]  # 赭色只标有依据（朗读换字、难字字典）的多音字，常见字不标


def zhuyin_book(book, c, sents):
    """11-18 道德经、三字经注音卡：数据/网站素材/_<书>/_注音/<章或讲>.json，格式同论语。有“待核”或字对不上就不上。"""
    f = os.path.join(SRC, "_" + book, "_注音", str(c) + ".json")
    if not os.path.exists(f): return None
    zi = json.load(open(f, encoding="utf-8")).get("zi") or []
    if any("待核" in str(x[-1]) for x in zi): ZY_SKIP[f"{book}{c}"] = "待核"; return None
    from opencc import OpenCC
    t2s = OpenCC("t2s").convert
    zs = CJK.findall("".join(sents))
    if len(zs) != len(zi) or _vn(t2s("".join(zs))) != _vn(t2s("".join(x[0] for x in zi))): ZY_SKIP[f"{book}{c}"] = "字对不上"; return None
    return [[x[1], x[2], 1 if len(x) > 4 and x[3] == 1 and x[4] else 0] for x in zi]


def zy_section(c, sents, zy, bh_rows, esc, note=None):
    """静态的逐句拼音、注音、意思、上一句下一句（搜索引擎看得到）。"""
    k, out = 0, []
    for j, s in enumerate(sents):
        py, bp = [], []
        for ch in s:
            if CJK.match(ch) and k < len(zy):
                py.append(zy[k][0]); bp.append(zy[k][1]); k += 1
            elif py and not ch.isspace():
                py[-1] += ch; bp[-1] += ch
        bh = (bh_rows[j].get("bh") if j < len(bh_rows) else "") or ""
        nb = []
        if j > 0: nb.append(f"上一句：{esc(sents[j-1])}")
        if j + 1 < len(sents): nb.append(f"下一句：{esc(sents[j+1])}")
        out.append(f'<div class="zyju"><h3 lang="zh-Hans">{esc(s)}</h3><p class="zypy">{esc(" ".join(py))}</p><p class="zybp">{esc(" ".join(bp))}</p>'
                   + (f'<p><b>意思：</b>{esc(bh)}</p>' if bh else "") + (f'<p class="note">{"　".join(nb)}</p>' if nb else "") + "</div>")
    return ('<section class="sec sec-音" id="zhuyin"><h2><i>音</i>逐句拼音、注音与意思</h2>'
            '<p class="note">' + (note or "读音照朱熹注定，和朗读一致。") + '原文上方按“注”，可以把拼音或注音符号标在每个字上。</p>' + "".join(out) + "</section>")
