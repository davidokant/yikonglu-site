"""逐句对照：章页原文同屏原页（点一句亮原页那一列）、“译”随文白话、点句/划选小卡。

数据（共享盘，不进仓库）：
  数据/网站素材/_句列/<章>.json      校平线程出：页图尺寸、经文大字逐字框 chars=[字,页,列,x0,y0,x1,y1]（按诵读顺序）
  数据/网站素材/_句列/页图/pNNN.png  校平后的页图；坐标就在这张图上，建站时换掉 tools/yuanye/pNNN.jpg
  数据/网站素材/_逐句/<章>.json      每句的白话、朱注、集解、一孔读法（网站线程写）
开关：tools/zhuju.json {"chapters": [...]}，只给列在里面的章出（样板先 1.1，主人“过”了再铺开）。
句的切法以网站 split_ju 为准：把 chars 的字序按每句去标点后的字数依次分给各句。
"""
import json, os, re, glob

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
        jl[c] = json.load(open(f, encoding="utf-8"))
    for f in glob.glob(os.path.join(ZJ_DIR, "*.json")):
        c = os.path.basename(f)[:-5]
        zj[c] = json.load(open(f, encoding="utf-8"))
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
        if t2s("".join(x[0] for x in got)) != need:
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


def page_pane(c, pages, per, label, ydir=None):
    """原页面板：每页一张 svg（底图＋各句的高亮框，默认隐藏），点句时由 ZJ_JS 显示该句框并滚到那里。viewBox 只取版框上下，白边不显示。"""
    out = []
    order = sorted(pages, key=lambda p: int(re.sub(r"\D", "", p)), reverse=False)
    for p in order:
        w, h = pages[p]["w"], pages[p]["h"]
        fy0, fy1 = frame_rows(p, ydir, w, h) if ydir else (0, h)
        rects = "".join(f'<rect class="hl" data-s="{i}" x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6"/>'
                        for i, bx in enumerate(per, 1) for (pp, x0, y0, x1, y1) in bx if pp == p)
        n = int(re.sub(r"\D", "", p))
        out.append(f'<a class="yyp" href="/yuanye/{p}.jpg" target="_blank" data-p="{p}"><svg viewBox="0 {fy0} {w} {fy1 - fy0}" role="img" aria-label="{label} {n}">'
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
ZJ_JS = """<div id="zjcard" class="zjcard" hidden><p class="zq"></p><div class="zt"></div><div class="zb"></div><div class="za"><button data-a="q">@COPY@</button><button data-a="img">@IMG@</button><button data-a="l">@LINK@</button></div><p class="zx"></p></div>
<script>
(function(){var F=document.querySelector('.yuanwen.dz');if(!F)return;var Q=F.querySelector('blockquote'),C=document.getElementById('zjcard'),S=[];try{S=JSON.parse(F.querySelector('.zjdata').textContent)}catch(e){}
var TABS=@TABS@,cur=null,sel='',tab='bh';
function hl(n){F.querySelectorAll('.yyp .hl').forEach(function(r){r.classList.toggle('on',r.dataset.s==n)});var r=F.querySelector('.yyp .hl[data-s="'+n+'"]'),P=F.querySelector('.yypane');if(r&&P){var a=r.getBoundingClientRect(),b=P.getBoundingClientRect();P.scrollTo({top:P.scrollTop+a.top-b.top-(b.height-a.height)/2,left:P.scrollLeft+a.left-b.left-(b.width-a.width)/2,behavior:'smooth'})}}
function esc(t){var d=document.createElement('div');d.textContent=t;return d.innerHTML}
function body(){var d=S[cur.dataset.n-1]||{},B=C.querySelector('.zb'),v=d[tab];C.querySelectorAll('.zt button').forEach(function(b){b.classList.toggle('on',b.dataset.t===tab)});
if(!v||!v.length){B.innerHTML='<p><small>@NONE@</small></p>';return}
if(typeof v==='string'){B.innerHTML='<p>'+esc(v)+'</p>';return}
B.innerHTML=v.map(function(x){return '<p>'+esc(x[0])+(x[1]?'<small>'+esc(x[1])+'</small>':'')+(x[2]?'<small class="dai">'+esc(x[2])+'</small>':'')+'</p>'}).join('')}
function open(s,txt){cur=s;sel=txt||'';F.querySelectorAll('.ju.on').forEach(function(x){x.classList.remove('on')});s.classList.add('on');hl(s.dataset.n);
C.querySelector('.zq').textContent=sel||s.textContent;var d=S[s.dataset.n-1]||{};
C.querySelector('.zt').innerHTML=TABS.filter(function(t){return d[t[0]]&&d[t[0]].length}).map(function(t){return '<button type="button" data-t="'+t[0]+'">'+t[1]+'</button>'}).join('');
if(!(d[tab]&&d[tab].length))tab='bh';body();
var R=[];try{R=JSON.parse(Q.dataset.reads||'[]')}catch(e){}var t=s.textContent,hit=R.filter(function(x){return x[1].split('\\u3001').some(function(p){return p&&t.indexOf(p)>=0})});
C.querySelector('.zx').textContent=hit.length?Q.dataset.rl+hit.map(function(x){return x[0]+' '+x[2]}).join(' \\u00b7 '):'';
var r=(window.getSelection&&sel&&getSelection().rangeCount?getSelection().getRangeAt(0):s).getBoundingClientRect();C.hidden=false;C.style.top=(window.scrollY+r.bottom+8)+'px';C.style.left=Math.max(8,Math.min(window.scrollX+r.left,document.documentElement.clientWidth-C.offsetWidth-8))+'px';
try{history.replaceState(null,'','#'+s.id)}catch(e){}}
function close(){C.hidden=true;if(cur)cur.classList.remove('on');cur=null}
function cite(t,s){return '\\u201c'+t+'\\u201d\\u2014\\u2014'+Q.dataset.src+Q.dataset.sep+Q.dataset.url+'#'+s.id}
function put(t,b){var o=b.textContent,done=function(){b.textContent='@DONE@';setTimeout(function(){b.textContent=o},1200)};if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(done,function(){prompt('',t)});else prompt('',t)}
Q.addEventListener('click',function(e){var s=e.target.closest('.ju');if(!s)return;var g=window.getSelection?String(getSelection()).trim():'';if(g&&s.contains(getSelection().anchorNode))open(s,g.replace(/\\s+/g,''));else open(s)});
Q.addEventListener('keydown',function(e){if(e.key==='Enter'){var s=e.target.closest('.ju');if(s)open(s)}});
document.addEventListener('selectionchange',function(){var g=getSelection();if(!g.rangeCount||g.isCollapsed)return;var n=g.anchorNode&&(g.anchorNode.nodeType===1?g.anchorNode:g.anchorNode.parentNode),s=n&&n.closest&&n.closest('.ju');if(s&&Q.contains(s)){clearTimeout(window._zjt);window._zjt=setTimeout(function(){var t=String(getSelection()).trim().replace(/\\s+/g,'');if(t)open(s,t)},450)}});
C.addEventListener('click',function(e){var b=e.target.closest('button');if(!b||!cur)return;if(b.dataset.t){tab=b.dataset.t;body();return}
var a=b.dataset.a;if(a==='q'){put(cite(sel||cur.textContent,cur),b);if(window.yklCopy)window.yklCopy(cur.id)}else if(a==='l')put(Q.dataset.url+'#'+cur.id,b);else if(a==='img'&&window.yklCard){window.yklCard({y:sel||cur.textContent,u:Q.dataset.url+'#'+cur.id,n:cur.dataset.n})}});
document.addEventListener('click',function(e){if(!C.hidden&&!C.contains(e.target)&&!e.target.closest('.ju')&&!e.target.closest('.dztools'))close()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')close()});
Q.addEventListener('copy',function(e){var g=getSelection(),t=String(g).replace(/\\s+/g,'');if(!t||!e.clipboardData)return;var n=g.anchorNode&&(g.anchorNode.nodeType===1?g.anchorNode:g.anchorNode.parentNode),s=n&&n.closest&&n.closest('.ju')||Q.querySelector('.ju');e.clipboardData.setData('text/plain',cite(t,s));e.preventDefault()});
var Y=F.querySelector('.yibtn'),YK='yk_yi';function yi(on){Y.setAttribute('aria-pressed',on?'true':'false');F.classList.toggle('yion',on);F.querySelectorAll('.yi').forEach(function(x){x.hidden=!on});try{localStorage.setItem(YK,on?'1':'0')}catch(e){}}
if(Y){var on0=false;try{on0=localStorage.getItem(YK)==='1'}catch(e){}yi(on0);Y.addEventListener('click',function(){yi(Y.getAttribute('aria-pressed')!=='true')})}
var h=location.hash.slice(1);if(/^s\\d+$/.test(h)){var t=document.getElementById(h);if(t&&Q.contains(t)){t.classList.add('on');setTimeout(function(){hl(t.dataset.n)},300)}}
})();
</script>"""
