"""《论语》智器重建本的关系（11-14 主人“过”，网站“全做”）：章页“这一章连着”一栏，和可点的关系图页 /lunyu/guanxi/（11-14 主人定挪到《论语》下，旧 /guanxi/ 与人物总页 /renwu/ 跳过来）。
数据：tools/lunyu_guanxi.json（读本线程出的统一关系表，PDF 与网站同源；新版到了整份换掉）。先只简繁。
一条关系 a 端是论语章，b 端可无；本书互见每条只记一次，两端都显示。"""
import json, os, re, html, collections

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lunyu_guanxi.json")
esc = html.escape
KIND = {"出处": "出处", "注家引": "注家引", "相通": "一孔录对读"}
CH_KIND = {"可用": "可以用", "别用": "别用错", "小心": "用时小心"}
ORDER = ["同问异答", "互见", "书外互见", "人物", "场合", "争议", "异文", "年历"]
HEAD = {"同问异答": "同问异答", "互见": "本书互见", "书外互见": "别的书", "人物": "人物", "场合": "场合", "争议": "读法之争", "异文": "异文", "年历": "年历"}


def load():
    if not os.path.exists(FILE): return None
    d = json.load(open(FILE, encoding="utf-8"))
    by = collections.defaultdict(list)
    for i, r in enumerate(d["rels"]): r["_i"] = str(i)  # 外文译文按关系序号对（i18n/gx-<语种>.json 的 X）
    for r in d["rels"]:
        if ":" not in r["a"]: continue  # a＝"lunyu" 是说整部书（如三字经“论语者，二十篇”），不挂在哪一章
        c = r["a"].split(":")[1]; by[c].append(r)
        if r["type"] == "互见" and r.get("b", "").startswith("lunyu:"): by[r["b"].split(":")[1]].append({**r, "a": r["b"], "b": r["a"]})
    wd = {g["id"]: g for g in d["groups"]["wenda"]}
    rw = {g["id"]: g for g in d["groups"]["renwu"]}
    return {"by": by, "wd": wd, "rw": rw, "raw": d}


def _c(x): return x.split(":", 1)[1]


def section(G, c, P, href, short):
    """章页一栏。href(c)→论语章网址；short(c)→章的短题（原文头几个字）。"""
    if not G: return ""
    rs = G["by"].get(c) or []
    if not [r for r in rs if r["type"] != "年历"]: return ""
    T = collections.defaultdict(list)
    for r in rs: T[r["type"]].append(r)
    row = []
    for g in dict.fromkeys(r["group"] for r in T["同问异答"]):
        w = G["wd"][g]
        li = "".join(f'<li{" class=on" if _c(it["c"]) == c else ""}><a href="{href(_c(it["c"]))}">{_c(it["c"])}</a> {esc(it["who"])}：{esc(it["a"])}</li>' for it in w["items"])
        row.append(("同问异答", f'<p>{esc(w["q"])}，全书 {len(w["items"])} 次，问的人不同，答得不同：</p><ol class="gxwd">{li}</ol><p class="gxmore"><a href="{P}lunyu/guanxi/#{g}">在关系图里看</a></p>'))
    if T["互见"]:
        row.append(("互见", "<ul>" + "".join(f'<li><a href="{href(_c(r["b"]))}">论语 {_c(r["b"])}</a> {esc(short(_c(r["b"])))}</li>' for r in T["互见"]) + "</ul>"))
    if T["书外互见"]:
        li = ""
        for r in sorted(T["书外互见"], key=lambda r: (r.get("book", ""), int(re.sub(r"\D", "", r.get("b", "0")) or 0))):
            b = r.get("b", ""); bk = r.get("book", "")
            if b.startswith("ddj:"): where = f'<a href="{P}daodejing/{_c(b)}.html">道德经 {_c(b)}</a>'
            elif b.startswith("szj:"): where = f'<a href="{P}sanzijing/{_c(b)}.html">三字经 {_c(b)}</a>'
            elif r.get("url"): where = f'<a href="{esc(r["url"])}" target="_blank" rel="noopener">《{esc(bk)}》</a>'
            else: where = f"《{esc(bk)}》"
            li += f'<li><span class="gxk">{KIND.get(r.get("kind"), esc(r.get("kind", "")))}</span>{where}：{esc(r["note"])}</li>'
        row.append(("书外互见", f"<ul>{li}</ul>"))
    if T["人物"]:
        ch = []
        for r in T["人物"]:
            p = G["rw"].get(r.get("group")); nm = (p or {}).get("common") or r["who"]
            n = len((p or {}).get("chs") or [])
            ch.append(f'<a href="{P}lunyu/guanxi/#p-{r.get("group")}">{esc(nm)}{f"<small>全书 {n} 章</small>" if n > 1 else ""}</a>')
        row.append(("人物", '<p class="gxchips">' + "".join(ch) + "</p>"))
    if T["场合"]:
        row.append(("场合", "<ul>" + "".join(f'<li><span class="gxk">{CH_KIND.get(r.get("kind"), "")}</span><a href="{P}changhe/{r.get("group")}.html">{esc(r["note"].split("：")[0])}</a>：{esc(r.get("txt") or r["note"])}</li>' for r in T["场合"]) + "</ul>"))
    if T["争议"]:
        row.append(("争议", "<ul>" + "".join(f'<li>一孔录取“{esc(re.sub(r"^[甲乙丙丁戊]\s*", "", r.get("pick", "")))}”。<a href="#ykan">看一孔按</a></li>' for r in T["争议"]) + "</ul>"))
    if T["异文"]:
        row.append(("异文", "<ul>" + "".join(f'<li>{esc(r["note"])}</li>' for r in T["异文"]) + "</ul>"))
    if T["年历"]:
        row.append(("年历", f'<p><a href="{P}nianli/">{esc(T["年历"][0]["note"])}</a></p>'))
    row.sort(key=lambda x: ORDER.index(x[0]))
    return (f'<section class="gx" id="lian"><h2>这一章连着<small>智器把全书 498 章两两比对找线，人逐条核到原页</small></h2><dl>'
            + "".join(f"<dt>{HEAD[k]}</dt><dd>{v}</dd>" for k, v in row)
            + f'</dl><p class="gxmore"><a href="{P}lunyu/guanxi/">全书关系图</a> · <a href="{P}duben.html">《论语》智器重建本 PDF</a></p></section>')


GX_JS = r"""<script>
(function(){var D=JSON.parse(document.getElementById('gxdata').textContent),NS='http://www.w3.org/2000/svg';
function el(t,a,p){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e}
function tabs(){var h=location.hash.slice(1),v=/^p-/.test(h)?'rw':(D.wd.some(function(g){return g.id===h})?'wd':(h==='rw'||h==='wd'?h:'all'));
document.querySelectorAll('.gxtab button').forEach(function(b){b.classList.toggle('on',b.dataset.v===v)});document.querySelectorAll('.gxview').forEach(function(s){s.hidden=s.id!=='v-'+v});
if(v==='rw')person(/^p-/.test(h)?h.slice(2):D.rw[0].id);if(v==='wd'&&h&&h!=='wd'){var g=document.getElementById(h);if(g)g.scrollIntoView()}}
document.querySelectorAll('.gxtab button').forEach(function(b){b.onclick=function(){location.hash=b.dataset.v}});
/* 全书一张网 */
var S=document.getElementById('gxall'),W=760,R=330,C=380,N=D.ch.length,gap=0.035,tot=2*Math.PI-gap*20,pos={},info=document.getElementById('gxinfo');
var k=0,pi=-1;D.ch.forEach(function(x,i){if(x[1]!==pi){pi=x[1];k++}var a=-Math.PI/2+gap*(k-1)+tot*i/N+gap/2;pos[x[0]]=[C+R*Math.cos(a),C+R*Math.sin(a),a]});
var gE=el('g',{},S),gN=el('g',{},S);
function arc(a,b,cls){var p=pos[a],q=pos[b];if(!p||!q)return;el('path',{d:'M'+p[0]+' '+p[1]+' Q'+C+' '+C+' '+q[0]+' '+q[1],'class':'gxe '+cls,'data-a':a,'data-b':b},gE)}
D.hj.forEach(function(e){arc(e[0],e[1],'hj')});D.wd.forEach(function(g){var m=g.items.map(function(x){return x[0]});for(var i=0;i<m.length;i++)for(var j=i+1;j<m.length;j++)arc(m[i],m[j],'wd')});
var PN=D.pian,PA={};D.ch.forEach(function(x){var p=pos[x[0]],n=el('circle',{cx:p[0],cy:p[1],r:x[3]?3.6:2.4,'class':'gxn'+(x[3]?' on':''),'data-c':x[0]},gN);n.addEventListener('click',function(){pick(x[0])});
var A=PA[x[1]]||(PA[x[1]]=[p[2],p[2]]);A[1]=p[2]});
Object.keys(PA).forEach(function(q){var a=(PA[q][0]+PA[q][1])/2,t=el('text',{x:C+(R+26)*Math.cos(a),y:C+(R+26)*Math.sin(a)+5,'class':'gxp','text-anchor':'middle'},gN);t.textContent=PN[q]});
var byc={};D.ch.forEach(function(x){byc[x[0]]=x});
function pick(c){var x=byc[c];S.querySelectorAll('.gxe').forEach(function(e){var o=e.dataset.a===c||e.dataset.b===c;e.classList.toggle('hi',o)});S.querySelectorAll('.gxn').forEach(function(n){n.classList.toggle('sel',n.dataset.c===c)});
var nb=[];S.querySelectorAll('.gxe.hi').forEach(function(e){var o=e.dataset.a===c?e.dataset.b:e.dataset.a;if(nb.indexOf(o)<0)nb.push(o)});
info.innerHTML='<b><a href="'+x[2]+'">论语 '+c+'</a></b> '+esc(x[4])+(nb.length?'<br>连着：'+nb.map(function(o){return '<a href="'+byc[o][2]+'">'+o+'</a>'}).join(' '):'<br><small>这一章在图上没有连线，章页“这一章连着”里还有人物、别的书等</small>')}
function esc(t){var d=document.createElement('div');d.textContent=t;return d.innerHTML}
/* 人物 */
var P=document.getElementById('gxrw'),L=document.getElementById('gxrwlist'),Q=document.getElementById('gxq'),byp={};D.rw.forEach(function(p){byp[p.id]=p});
function list(f){L.innerHTML=D.rw.filter(function(p){return !f||(p.name+p.common+p.alias).indexOf(f)>=0}).slice(0,f?60:40).map(function(p){return '<a href="#p-'+p.id+'">'+esc(p.common||p.name)+'<small>'+p.chs.length+'</small></a>'}).join('')}
Q.addEventListener('input',function(){list(Q.value.trim())});list('');
function person(id){var p=byp[id];if(!p)return;while(P.firstChild)P.removeChild(P.firstChild);var cx=380,cy=300,r1=150,r2=255,n=p.chs.length;
document.getElementById('gxrwh').innerHTML='<b>'+esc(p.common||p.name)+'</b>'+(p.common&&p.common!==p.name?'（'+esc(p.name)+'）':'')+' · '+esc(p.role||'')+' · 全书 '+n+' 章'+(p.card?' · <a href="'+p.card+'">人物卡：身份、出处、各章原文 ›</a>':'');
var co={};p.chs.forEach(function(c){D.rw.forEach(function(q){if(q.id!==id&&q.chs.indexOf(c)>=0)co[q.id]=(co[q.id]||0)+1})});
var top=Object.keys(co).sort(function(a,b){return co[b]-co[a]}).slice(0,12);
top.forEach(function(q,i){var a=-Math.PI/2+2*Math.PI*(i+.5)/top.length,x=cx+r2*Math.cos(a),y=cy+r2*Math.sin(a);
p.chs.forEach(function(c,j){if(byp[q].chs.indexOf(c)>=0){var b=-Math.PI/2+2*Math.PI*j/n;el('line',{x1:cx+r1*Math.cos(b),y1:cy+r1*Math.sin(b),x2:x,y2:y,'class':'gxe co'},P)}});
var g=el('a',{href:'#p-'+q},P);el('circle',{cx:x,cy:y,r:7+Math.min(co[q],8),'class':'gxpp'},g);var t=el('text',{x:x,y:y+(y>cy?30:-16),'text-anchor':'middle','class':'gxt'},g);t.textContent=(byp[q].common||byp[q].name)+' '+co[q]});
p.chs.forEach(function(c,j){var b=-Math.PI/2+2*Math.PI*j/n,x=cx+r1*Math.cos(b),y=cy+r1*Math.sin(b),ch=byc[c.split(':')[1]];el('line',{x1:cx,y1:cy,x2:x,y2:y,'class':'gxe sp'},P);
var g=el('a',{href:ch?ch[2]:'#'},P);el('circle',{cx:x,cy:y,r:n>40?5:9,'class':'gxn on'},g);if(n<=40){var t=el('text',{x:x,y:y+4,'text-anchor':'middle','class':'gxt s'},g);t.textContent=c.split(':')[1]}else{var tt=el('title',{},g);tt.textContent=c.split(':')[1]}});
el('circle',{cx:cx,cy:cy,r:34,'class':'gxme'},P);var t=el('text',{x:cx,y:cy+6,'text-anchor':'middle','class':'gxt b'},P);t.textContent=p.common||p.name;
document.getElementById('gxrwchs').innerHTML=p.chs.map(function(c){var k=c.split(':')[1],x=byc[k];return x?'<a href="'+x[2]+'">'+k+' '+esc(x[4])+'</a>':''}).join('')}
window.addEventListener('hashchange',tabs);tabs()})();
</script>"""


def build(L, G, write, page, P, href, short, PIAN, pub, DOMAIN):
    if not G or not L.code.startswith("zh"): return []
    d = G["raw"]
    order = sorted({_c(r["a"]) for r in d["rels"] if r["type"] == "年历"}, key=lambda c: tuple(int(x) for x in c.split(".")))
    pk = list(PIAN)
    ch = [[c, pk.index(c.split(".")[0]), href(c), 1 if c in pub else 0, short(c)] for c in order]
    hj = [[_c(r["a"]), _c(r["b"])] for r in d["rels"] if r["type"] == "互见"]
    wd = [{"id": g["id"], "q": g["q"], "items": [[_c(i["c"]), i["who"], i["a"]] for i in g["items"]]} for g in d["groups"]["wenda"]]
    rw = sorted([{"id": g["id"], "name": g["name"], "common": g.get("common") or "", "alias": g.get("alias") or "", "role": g.get("role") or "", "chs": g["chs"], "card": f"{P}renwu/{RWID[g['id']]}.html" if g["id"] in RWID else ""} for g in d["groups"]["renwu"]], key=lambda p: -len(p["chs"]))
    data = json.dumps({"ch": ch, "hj": hj, "wd": wd, "rw": rw, "pian": [PIAN[p][0].replace("第", "").rstrip("一二三四五六七八九十") for p in pk]}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    st = d.get("stats", {})
    wdh = ""
    for g in d["groups"]["wenda"]:  # 同问异答：服务端画好，不靠脚本也能看
        n = len(g["items"]); cx, cy, r = 300, 210, 150
        sv = f'<svg viewBox="0 0 600 420" class="gxwdsvg" role="img" aria-label="{esc(g["q"])}，全书 {n} 次">'
        for i, it in enumerate(g["items"]):
            import math
            a = -math.pi / 2 + 2 * math.pi * i / n; x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            sv += f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" class="gxe sp"/>'
            sv += (f'<a href="{href(_c(it["c"]))}"><circle cx="{x:.0f}" cy="{y:.0f}" r="22" class="gxn on"/><text x="{x:.0f}" y="{y + 5:.0f}" text-anchor="middle" class="gxt s">{_c(it["c"])}</text>'
                   f'<text x="{x:.0f}" y="{y + (40 if y >= cy else -30):.0f}" text-anchor="middle" class="gxt">{esc(it["who"])}</text></a>')
        sv += f'<circle cx="{cx}" cy="{cy}" r="40" class="gxme"/><text x="{cx}" y="{cy + 7}" text-anchor="middle" class="gxt b">{esc(g["q"])}</text></svg>'
        li = "".join(f'<li><a href="{href(_c(it["c"]))}">论语 {_c(it["c"])}</a> {esc(it["who"])}：{esc(it["a"])}{f"<small>{esc(it["note"])}</small>" if it.get("note") else ""}</li>' for it in g["items"])
        wdh += f'<section class="gxcard" id="{g["id"]}"><h3>{esc(g["q"])} · 全书 {n} 次</h3>{sv}<ol>{li}</ol></section>'
    body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a></p><h1><span class="no">全书 498 章 · 197 位人物</span>《论语》关系图</h1></div></div>
<main class="wrap guanxi"><p class="lead">《论语》二十篇四百九十八章，看着一章一章是散的，其实处处连着：同一句话在两处出现，同一个问题孔子答不同的人，同一个弟子在几十章里出场。全书共 {sum(v for k, v in st.items() if k != "年历"):,} 条关系，都记在《论语》智器重建本里，<a href="{P}duben.html">PDF 免费下载</a>。</p>
<div class="gxtab" role="tablist"><button type="button" data-v="all">全书一张网</button><button type="button" data-v="wd">同问异答</button><button type="button" data-v="rw">人物</button></div>
<section class="gxview" id="v-all"><p class="note">圆周上一个点是一章，按二十篇排一圈，深色的点是已经讲过的章。绿线是同一句话在书里出现两次（本书互见 {st.get("互见", 0)} 条），赭线连着同一个问题的几问几答（同问异答 {len(wd)} 组）。点一章看它连着哪几章。</p>
<div class="gxwrap"><svg id="gxall" viewBox="0 0 760 760" role="img" aria-label="《论语》全书 498 章关系图"></svg></div><p id="gxinfo" class="gxinfo">点圆周上任一章。</p></section>
<section class="gxview" id="v-wd" hidden><p class="note">同一个问题，孔子对不同的人答得不一样。这是读《论语》最要紧的一条线：答案跟着人走。</p>{wdh}</section>
<section class="gxview" id="v-rw" hidden><p class="note">《论语》里有名有姓的人共 {len(rw)} 位。点一个人，内圈是他出场的章，外圈是常和他同章出现的人，数字是同章几次。</p>
<p><input id="gxq" type="search" placeholder="搜人名，如：子路、颜回、管仲" aria-label="搜人名"></p><p id="gxrwlist" class="gxchips"></p>
<p id="gxrwh" class="gxinfo"></p><div class="gxwrap"><svg id="gxrw" viewBox="0 0 760 600" role="img" aria-label="人物与章的关系"></svg></div><p id="gxrwchs" class="gxchips s"></p></section>
<script type="application/json" id="gxdata">{data}</script>{GX_JS}</main>'''
    write("lunyu/guanxi/index.html", page(L, "《论语》关系图与人物：全书 498 章怎样连着｜一孔录", "同问异答、本书互见、197 位人物各在哪几章：智器把全书 498 章两两比对找线，人逐条核到原页。", "lunyu/guanxi/", body, codes=["zh-Hans", "zh-Hant"] + langs()))
    dst = f"/{L.prefix}lunyu/guanxi/"
    for old, tab in (("guanxi/index.html", ""), ("renwu/index.html", "#rw")):  # 旧网址跳过来，带上 #
        write(old, f'<!doctype html><meta charset="utf-8"><title>《论语》关系图｜一孔录</title><link rel="canonical" href="{DOMAIN}{dst}"><meta name="robots" content="noindex">'
                   f'<script>location.replace("{dst}"+(location.hash||"{tab}"))</script><meta http-equiv="refresh" content="0;url={dst}{tab}"><a href="{dst}{tab}">《论语》关系图</a>')
    return [f"{DOMAIN}{dst}"]

def rw_ids(G, R):
    """关系表人物 id → 人物卡 id（按本名对上）。"""
    if not G or not R: return {}
    by = {p["name"]: p["id"] for p in R}
    return {g["id"]: by[g["name"]] for g in G["raw"]["groups"]["renwu"] if g["name"] in by}

RWID = {}


# ———— 11-14 外文版：关系图页、章页“这一章连着”、人物卡（译文 i18n/gx-<语种>.json：S 页面文字、W 同问异答、X 关系注、p 人名身份；智器译）————
TR = {}
for _l in ("en", "ja", "ko", "fr", "es", "de", "vi", "id", "ru"):
    _f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", f"gx-{_l}.json")
    if os.path.exists(_f): TR[_l] = json.load(open(_f, encoding="utf-8"))


def has_lang(code): return bool((TR.get(code) or {}).get("S")) and bool((TR.get(code) or {}).get("p"))
def langs(): return [k for k in TR if has_lang(k)]


def pname(code, name, common=""):
    """外文人名：常称（如子路）优先，没有就本名。"""
    t = (TR.get(code) or {}).get("p", {}).get(name) or {}
    return (t.get("common") if common else "") or t.get("name") or common or name


def _bk_prefix(code, P, kind):  # 道德经、三字经外文页只有英日
    return P if code in ("en", "ja") else "/"


def section_f(G, c, P, href, short, L):
    T = TR[L.code]; S = T["S"]; X = T.get("X") or {}; WD = {w["id"]: w for w in T.get("W") or []}
    rs = G["by"].get(c) or []
    if not [r for r in rs if r["type"] not in ("年历", "场合")]: return ""
    K = collections.defaultdict(list)
    for r in rs: K[r["type"]].append(r)
    lbl = S.get("sh_lbl") or L.t("sh_lbl")
    row = []
    for g in dict.fromkeys(r["group"] for r in K["同问异答"]):
        w = G["wd"][g]; wt = WD.get(g) or {}; its = wt.get("items") or []
        li = "".join(f'<li{" class=on" if _c(it["c"]) == c else ""}><a href="{href(_c(it["c"]))}">{_c(it["c"])}</a> {esc((its[k].get("who") if k < len(its) else "") or pname(L.code, it["who"]))}: {esc((its[k].get("a") if k < len(its) else "") or it["a"])}</li>' for k, it in enumerate(w["items"]))
        row.append(("同问异答", f'<p>{esc(S["gx_wd_line"].replace("{q}", wt.get("q") or w["q"]).replace("{n}", str(len(w["items"]))))}</p><ol class="gxwd">{li}</ol><p class="gxmore"><a href="{P}lunyu/guanxi/#{g}">{esc(S["gx_in_map"])}</a></p>'))
    if K["互见"]:
        row.append(("互见", "<ul>" + "".join(f'<li><a href="{href(_c(r["b"]))}">{esc(lbl)} {_c(r["b"])}</a> <span lang="zh-Hans">{esc(short(_c(r["b"])))}</span></li>' for r in K["互见"]) + "</ul>"))
    if K["书外互见"]:
        KD = {"出处": S["gx_kind_cc"], "注家引": S["gx_kind_zj"], "相通": S["gx_kind_xt"]}
        li = ""
        for r in sorted(K["书外互见"], key=lambda r: (r.get("book", ""), int(re.sub(r"\D", "", r.get("b", "0")) or 0))):
            b = r.get("b", ""); x = X.get(r["_i"]) or {}; bk = x.get("book") or r.get("book", "")
            if b.startswith("ddj:"): where = f'<a href="{_bk_prefix(L.code, P, "ddj")}daodejing/{_c(b)}.html">{esc(bk)} {_c(b)}</a>'
            elif b.startswith("szj:"): where = f'<a href="{_bk_prefix(L.code, P, "szj")}sanzijing/{_c(b)}.html">{esc(bk)} {_c(b)}</a>'
            elif r.get("url"): where = f'<a href="{esc(r["url"])}" target="_blank" rel="noopener">{esc(bk)}</a>'
            else: where = esc(bk)
            li += f'<li><span class="gxk">{esc(KD.get(r.get("kind"), r.get("kind", "")))}</span>{where}: {esc(x.get("note") or r["note"])}</li>'
        row.append(("书外互见", f"<ul>{li}</ul>"))
    if K["人物"]:
        ch = []
        for r in K["人物"]:
            p = G["rw"].get(r.get("group")) or {}; n = len(p.get("chs") or [])
            nm = pname(L.code, p.get("name") or r["who"], p.get("common"))
            ch.append(f'<a href="{P}lunyu/guanxi/#p-{r.get("group")}">{esc(nm)}{f"<small>{esc(S["gx_nch"].replace("{n}", str(n)))}</small>" if n > 1 else ""}</a>')
        row.append(("人物", '<p class="gxchips">' + "".join(ch) + "</p>"))
    if K["争议"]:
        row.append(("争议", "<ul>" + "".join(f'<li>{esc(S["gx_zy_pick"].replace("{p}", (X.get(r["_i"]) or {}).get("pick") or re.sub(r"^[甲乙丙丁戊]\s*", "", r.get("pick", ""))))} <a href="#ykan">{esc(S["gx_zy_link"])}</a></li>' for r in K["争议"]) + "</ul>"))
    if K["异文"]:
        row.append(("异文", "<ul>" + "".join(f'<li>{esc((X.get(r["_i"]) or {}).get("note") or r["note"])}</li>' for r in K["异文"]) + "</ul>"))
    if not row: return ""
    row.sort(key=lambda x: ORDER.index(x[0]))
    HD = {"同问异答": S["gx_head_wd"], "互见": S["gx_head_hj"], "书外互见": S["gx_head_bw"], "人物": S["gx_head_rw"], "争议": S["gx_head_zy"], "异文": S["gx_head_yw"]}
    return (f'<section class="gx" id="lian"><h2>{esc(S["gx_sec_h"])}<small>{esc(S["gx_sec_sub"])}</small></h2><dl>'
            + "".join(f"<dt>{esc(HD[k])}</dt><dd>{v}</dd>" for k, v in row)
            + f'</dl><p class="gxmore"><a href="{P}lunyu/guanxi/">{esc(S["gx_more_map"])}</a> · <a href="{P}duben.html">{esc(S["gx_more_pdf"])}</a></p></section>')


def _js_f():
    j = GX_JS
    for a, b in (("'\">论语 '+c+'</a></b> '", "'\">'+D.s.lbl+' '+c+'</a></b> '"), ("'<br>连着：'", "'<br>'+esc(D.s.links)"),
                 ("'<br><small>这一章在图上没有连线，章页“这一章连着”里还有人物、别的书等</small>'", "'<br><small>'+esc(D.s.nolink)+'</small>'"),
                 ("'（'+esc(p.name)+'）'", "' ('+esc(p.name)+')'"), ("' · 全书 '+n+' 章'", "' · '+D.s.nch.replace('{n}',n)"),
                 ("'\">人物卡：身份、出处、各章原文 ›</a>'", "'\">'+esc(D.s.card)+'</a>'")):
        assert a in j, a
        j = j.replace(a, b)
    return j


def build_f(L, G, write, page, P, href, short, PIAN, pub, DOMAIN, codes):
    if not G or not has_lang(L.code): return []
    import math
    T = TR[L.code]; S = T["S"]; WD = {w["id"]: w for w in T.get("W") or []}
    d = G["raw"]
    order = sorted({_c(r["a"]) for r in d["rels"] if r["type"] == "年历"}, key=lambda c: tuple(int(x) for x in c.split(".")))
    pk = list(PIAN)
    ch = [[c, pk.index(c.split(".")[0]), href(c), 1 if c in pub else 0, short(c)] for c in order]
    hj = [[_c(r["a"]), _c(r["b"])] for r in d["rels"] if r["type"] == "互见"]
    def wdi(g):
        wt = WD.get(g["id"]) or {}; its = wt.get("items") or []
        return wt.get("q") or g["q"], [[_c(i["c"]), (its[k].get("who") if k < len(its) else "") or pname(L.code, i["who"]), (its[k].get("a") if k < len(its) else "") or i["a"], (its[k].get("note") if k < len(its) else "") or ""] for k, i in enumerate(g["items"])]
    wd = []
    for g in d["groups"]["wenda"]:
        q, its = wdi(g); wd.append({"id": g["id"], "q": q, "items": [x[:3] for x in its]})
    PT = T.get("p") or {}
    rw = sorted([{"id": g["id"], "name": (PT.get(g["name"]) or {}).get("name") or g["name"], "common": (PT.get(g["name"]) or {}).get("common") or "", "alias": (PT.get(g["name"]) or {}).get("alias") or "",
                  "role": (PT.get(g["name"]) or {}).get("role") or g.get("role") or "", "chs": g["chs"], "card": f"{P}renwu/{RWID[g['id']]}.html" if g["id"] in RWID else ""} for g in d["groups"]["renwu"]], key=lambda p: -len(p["chs"]))
    for p in rw: p["alias"] = p["alias"] + " " + next((g["name"] + (g.get("alias") or "") for g in d["groups"]["renwu"] if g["id"] == p["id"]), "")  # 搜中文名也搜得到
    lbl = S.get("sh_lbl") or L.t("sh_lbl")
    data = json.dumps({"ch": ch, "hj": hj, "wd": wd, "rw": rw, "pian": [str(i + 1) for i in range(len(pk))], "s": {"lbl": lbl, "links": S["gx_links"], "nolink": S["gx_nolink"], "nch": S["gx_nch"], "card": S["gx_card"]}}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    st = d.get("stats", {})
    wdh = ""
    for g in d["groups"]["wenda"]:
        q, its = wdi(g); n = len(its); cx, cy, r = 300, 210, 150
        sv = f'<svg viewBox="0 0 600 420" class="gxwdsvg" role="img" aria-label="{esc(q)}">'
        for i, it in enumerate(its):
            a = -math.pi / 2 + 2 * math.pi * i / n; x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            sv += f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" class="gxe sp"/>'
            sv += (f'<a href="{href(it[0])}"><circle cx="{x:.0f}" cy="{y:.0f}" r="22" class="gxn on"/><text x="{x:.0f}" y="{y + 5:.0f}" text-anchor="middle" class="gxt s">{it[0]}</text>'
                   f'<text x="{x:.0f}" y="{y + (40 if y >= cy else -30):.0f}" text-anchor="middle" class="gxt">{esc(it[1])}</text></a>')
        qs = q if len(q) <= 14 else q[:13] + "…"
        sv += f'<circle cx="{cx}" cy="{cy}" r="40" class="gxme"/><text x="{cx}" y="{cy + 7}" text-anchor="middle" class="gxt b">{esc(qs)}</text></svg>'
        li = "".join(f'<li><a href="{href(it[0])}">{esc(lbl)} {it[0]}</a> {esc(it[1])}: {esc(it[2])}{f"<small>{esc(it[3])}</small>" if it[3] else ""}</li>' for it in its)
        wdh += f'<section class="gxcard" id="{g["id"]}"><h3>{esc(q)} · {esc(S["gx_times"].replace("{n}", str(n)))}</h3>{sv}<ol>{li}</ol></section>'
    ntot = sum(v for k, v in st.items() if k != "年历")
    body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">{esc(L.t("lunyu"))}</a></p><h1><span class="no">{esc(S["gx_sub"])}</span>{esc(S["gx_h1"])}</h1></div></div>
<main class="wrap guanxi"><p class="lead">{esc(S["gx_lead"].replace("{n}", str(ntot)))}</p>
<div class="gxtab" role="tablist"><button type="button" data-v="all">{esc(S["gx_tab_all"])}</button><button type="button" data-v="wd">{esc(S["gx_tab_wd"])}</button><button type="button" data-v="rw">{esc(S["gx_tab_rw"])}</button></div>
<section class="gxview" id="v-all"><p class="note">{esc(S["gx_all_note"].replace("{hj}", str(st.get("互见", 0))).replace("{wd}", str(len(wd))))}</p>
<div class="gxwrap"><svg id="gxall" viewBox="0 0 760 760" role="img" aria-label="{esc(S["gx_all_aria"])}"></svg></div><p id="gxinfo" class="gxinfo">{esc(S["gx_pick"])}</p></section>
<section class="gxview" id="v-wd" hidden><p class="note">{esc(S["gx_wd_note"])}</p>{wdh}</section>
<section class="gxview" id="v-rw" hidden><p class="note">{esc(S["gx_rw_note"].replace("{n}", str(len(rw))))}</p>
<p><input id="gxq" type="search" placeholder="{esc(S["gx_q_ph"])}" aria-label="{esc(S["gx_q_aria"])}"></p><p id="gxrwlist" class="gxchips"></p>
<p id="gxrwh" class="gxinfo"></p><div class="gxwrap"><svg id="gxrw" viewBox="0 0 760 600" role="img" aria-label="{esc(S["gx_rw_aria"])}"></svg></div><p id="gxrwchs" class="gxchips s"></p></section>
<script type="application/json" id="gxdata">{data}</script>{_js_f()}</main>'''
    write("lunyu/guanxi/index.html", page(L, S["gx_title"], S["gx_desc"], "lunyu/guanxi/", body, codes=codes))
    return [f"{DOMAIN}/{L.prefix}lunyu/guanxi/"]
