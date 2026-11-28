# 11-27 主人点卡先做“引用本页”：六本书章页底的引用格式只在这一处出（GB/T 7714 与 APA 各一行，一键复制），
# 书名、底本、版本从各书 书单.json 取，本章页码从本章逐句注（或讲读“字眼”）的出处取，不在各书生成函数里各写一份。
# 只出简繁两种中文页；外文页照旧。访问日期由读者打开页面时填。
import glob, html, json, os, re

W = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材"
# 网址第一段 → 书单目录
DIRS = {"lunyu": "_论语", "mengzi": "_孟子", "daxue": "_大学", "zhongyong": "_中庸", "daodejing": "_道德经", "sanzijing": "_三字经", "zhouyi": "_周易"}
ZY_ZHUAN = {"xici-shang": "xs", "xici-xia": "xx", "shuogua": "sg", "xugua": "xg", "zagua": "zg"}
_shudan, _pages, _raw = {}, {}, {}
CN = {c: i for i, c in enumerate("〇一二三四五六七八九")}
FT = str.maketrans({"經": "经", "傳": "传", "葉": "叶", "後": "后", "繫": "系", "辭": "辞", "説": "说", "說": "说", "雜": "杂", "卦": "卦"})


def esc(s): return html.escape(s, quote=True)


def shudan(top):
    if top not in _shudan:
        p = os.path.join(W, DIRS[top], "书单.json")
        _shudan[top] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    return _shudan[top]


def key_of(rel, pian):
    """站内路径 → (书目录名, 章号)。pian：论语篇号 → (篇名, 网址段, …)。不是章页就给 None。"""
    if rel == "lunyu/duyin/": return ("lunyu", "duyin")  # 11-27 易读错字速查页也出引用本页
    m = re.fullmatch(r"lunyu/([a-z-]+)/(\d+)\.html", rel)
    if m:
        p = next((k for k, v in pian.items() if v[1] == m.group(1)), None)
        return ("lunyu", f"{p}.{m.group(2)}") if p else None
    m = re.fullmatch(r"zhouyi/([a-z-]+)/(\d+)\.html", rel)
    if m and m.group(1) in ZY_ZHUAN: return ("zhouyi", f"{ZY_ZHUAN[m.group(1)]}-{m.group(2)}")
    m = re.fullmatch(r"(mengzi|daxue|zhongyong|daodejing|sanzijing|zhouyi)/([\d.]+)\.html", rel)
    return (m.group(1), m.group(2)) if m else None


def _cnum(s):
    n = cur = 0
    for c in s:
        if c == "十": n += (cur or 1) * 10; cur = 0
        elif c in CN: cur = cur * 10 + CN[c]
    return n + cur


def _cn(n):
    d = "〇一二三四五六七八九"
    if n < 10: return d[n]
    if n < 20: return "十" + (d[n % 10] if n % 10 else "")
    return d[n // 10] + "十" + (d[n % 10] if n % 10 else "")


YWPG = {"daxue": "_大学/_原文/大学原文-v1.json", "zhongyong": "_中庸/_原文/中庸原文-v1.json", "mengzi": "_孟子/_原文/孟子原文-v1.json",
        "lunyu": "_原文/论语原文-集注分章-v1.json", "daodejing": "_道德经/_原文/道德经原文-v*.json"}  # 11-27 主人点卡孟子、论语、道德经一起修
_jl = {}


def pages(top, cid):
    """本章用到的底本页码（或叶次），给人看的一小段字，如“第 65—66 页”“上经第八叶至第九叶”。查不到给空串。"""
    k = (top, cid)
    if k in _pages: return _pages[k]
    d = DIRS[top]; out = ""
    zj = os.path.join(W, "" if top == "lunyu" else d, "_逐句", f"{cid}.json")
    srcs = []
    if os.path.exists(zj):
        for s in json.load(open(zj, encoding="utf-8")).get("句", []):
            for z in s.get("zhu", []) or []:
                if len(z) > 1: srcs.append(z[1])
    ps = [int(x) for s in srcs for x in re.findall(r"(\d+)\s*(?=页|[—–-]\s*\d+\s*页)", s)]
    # 11-27 大学中庸修改单 X24：只有正文、没有朱注的页也要算进去，取原文书单里本章的 pages（与章页“底本第 N 页”同源）
    ywf = sorted(glob.glob(os.path.join(W, YWPG[top])))[-1:] if top in YWPG else []
    if ywf:
        _jl.setdefault(top, json.load(open(ywf[0], encoding="utf-8")))
        q = _jl[top].get(cid) if isinstance(_jl[top].get(cid), dict) else {}
        pg = q.get("pages") or ([q["pdf_page"]] if q.get("pdf_page") else [])
        if pg: ps += [int(x) for x in (json.loads(pg) if isinstance(pg, str) else pg)]
    ye = [(m.group(1), _cnum(m.group(2))) for s in srcs for m in re.finditer(r"([上下]經|[^\s，、；《》]{1,5}?傳|[^\s，、；《》]{1,3}卦)第([〇一二三四五六七八九十]+)葉", s)]
    if not ps and not ye:
        jd = os.path.join(W, d, "_讲读", f"{cid}.json")
        if os.path.exists(jd):
            zy = json.load(open(jd, encoding="utf-8")).get("字眼")
            if isinstance(zy, str): ps = [int(x) for x in re.findall(r"〔p(\d{1,4})〕", zy)]
    _raw[k] = ("p", min(ps), max(ps)) if ps else (("l", ye[0], ye[-1]) if ye else None)
    if ps:
        a, b = min(ps), max(ps); out = f"第 {a} 页" if a == b else f"第 {a}—{b} 页"
    elif ye:
        cn = _cn
        a, b = ye[0], ye[-1]
        out = (f"{a[0]}第{cn(a[1])}叶" + ("" if a == b else (f"至第{cn(b[1])}叶" if a[0] == b[0] else f"至{b[0]}第{cn(b[1])}叶"))).translate(FT)
    _pages[k] = out
    return out


def diben(top):
    s = shudan(top)
    return s["底本"] if s else None


def ld_extra(top, cid, date):
    """并进章页 Article 结构化数据：底本是哪本书哪一版、哪几页，本页何时改过。"""
    b = diben(top)
    if not b: return {}
    x = {"isBasedOn": {"@type": "Book", "name": b["书名"], "author": {"@type": "Person", "name": b["作者"]}, "bookEdition": b["版本"]}, "dateModified": date}
    pg = pages(top, cid)
    if pg: x["isBasedOn"]["description"] = pg
    return x


def title_cn(top, headline):
    s = shudan(top) or {}; bk = s.get("书名", ""); t = headline.strip()
    return f"《{bk}》{t[len(bk):].strip()}" if bk and t.startswith(bk) else t


def short_cn(t):
    """“《孟子》1.2 孟子见梁惠王”→“《孟子》1.2”；复制出处与原文句出处共用这一种写法（11-27 统一）。"""
    return t.split(" ")[0]


# 复制超过 20 字（白话、一孔之见、讲读、诸家等）自动在末尾附一行出处，不提示、不拦（11-27 主人：“带出处”不用提醒别人）。
# 原文句另有自己的复制处理（已带出处、已 preventDefault），这里跳过。
CP = ("<script>(function(){var S=document.querySelector('.citeit.yy');if(!S||!S.dataset.cp)return;"
      "document.addEventListener('copy',function(e){if(e.defaultPrevented||!e.clipboardData)return;var g=getSelection(),t=String(g);"
      "if(t.replace(/\\s+/g,'').length<=20||/yikonglu\\.com/i.test(t))return;var n=g.anchorNode;n=n&&(n.nodeType===1?n:n.parentNode);"
      "if(!n||!n.closest||!n.closest('main')||n.closest('.citeit,code,input,textarea,.jubar,#jubar'))return;"
      "e.clipboardData.setData('text/plain',t.replace(/\\s+$/,'')+'\\n'+S.dataset.cp);e.preventDefault()})})();</script>")


def wiki_pg(top, cid, en=False):
    """维基 cite book 的页码参数（11-28 对手外链调研，主人点卡“两件都做”）：单页 page=，跨页 pages=，周易叶次 at=。"""
    pages(top, cid); r = _raw.get((top, cid))
    if not r: return ""
    if r[0] == "p": return f" |page={r[1]}" if r[1] == r[2] else f" |pages={r[1]}\u2013{r[2]}"
    return " |at=" + (pages_en(top, cid) if en else pages(top, cid))


def block(top, cid, headline, url, kanwu_href, mail_html, report, date):
    """“引用本页”整块（简体字写，繁体页由建站统一转繁）。headline 形如“论语 5.10 · 公冶长 吾未见刚者”。"""
    s = shudan(top); b = s and s["底本"]
    if not b: return None
    bk = s["书名"]
    t = title_cn(top, headline)
    pg = pages(top, cid)
    src = f"据{b['作者']}《{b['书名']}》（{b['版本']}）" + (pg if pg else "")
    src_apa = f"据{b['作者']}《{b['书名']}》，{b['版本']}" + (f"，{pg}" if pg else "")
    acc = '<span class="yya">引用日期</span>'
    gb = f'一孔录. {esc(t)}：{esc(src)}[EB/OL]. ({date})[{acc}]. {esc(url)}.'
    apa = f'一孔录.（<span class="yyz">{date}</span>）. {esc(t)}（{esc(src_apa)}）. 检索于 <span class="yyb">引用日期</span>，{esc(url)}'
    cp = f"\u2014\u2014{short_cn(t)} \u00b7 一孔录 {url}"
    wk = ("{{cite book |author=" + b["作者"] + " |title=" + b["书名"] + " |edition=" + b["版本"].replace("《", "").replace("》", "") + wiki_pg(top, cid)
          + " |chapter=" + headline.replace(" · ", " ").strip() + " |url=" + url + " |via=一孔录 |access-date=" + acc + " |language=zh}}")
    return (f'<section class="citeit yy" data-d="{date}" data-cp="{esc(cp)}"><b>引用本页</b>'
            f'<p class="yyf"><span class="yyl">GB/T 7714</span><code>{gb}</code><button type="button">复制</button></p>'
            f'<p class="yyf"><span class="yyl">APA</span><code>{apa}</code><button type="button">复制</button></p>'
            f'<p class="yyf"><span class="yyl">维基百科</span><code>{wk.replace(acc, "@@A@@").replace("&", "&amp;").replace("<", "&lt;").replace("@@A@@", acc)}</code><button type="button">复制</button></p>'
            f'<p>本页更新于 {date}，改动都记在<a href="{kanwu_href}">勘误页</a>。本页以 CC BY 4.0 许可公开，转载、摘引请署“一孔录”并附本页网址。觉得有用？把本章链接贴到你常去的地方，就是对一孔录最大的帮助。</p>'
            f'<p class="mailp">{report} {mail_html}</p></section>' + JS + CP)


JS = ("<script>(function(){var S=document.querySelector('.citeit.yy');if(!S)return;var n=new Date(),p=function(x){return(x<10?'0':'')+x},"
      "a=n.getFullYear()+'-'+p(n.getMonth()+1)+'-'+p(n.getDate()),b=n.getFullYear()+'年'+(n.getMonth()+1)+'月'+n.getDate()+'日';"
      "S.querySelectorAll('.yya').forEach(function(e){e.textContent=a});S.querySelectorAll('.yyb').forEach(function(e){e.textContent=b});"
      "S.querySelectorAll('.yyz').forEach(function(e){var m=e.textContent.match(/(\\d{4})-(\\d{1,2})-(\\d{1,2})/);if(m)e.textContent=m[1]+'年'+(+m[2])+'月'+(+m[3])+'日'});"
      "S.querySelectorAll('.yyf button').forEach(function(btn){btn.onclick=function(){var t=btn.previousElementSibling.textContent,o=btn.textContent,"
      "ok=function(){btn.textContent='已复制';setTimeout(function(){btn.textContent=o},1500)};if(navigator.clipboard)navigator.clipboard.writeText(t).then(ok,function(){})}})})();</script>")


JUAN_EN = {"上經": "Shangjing", "下經": "Xiajing", "彖上傳": "Tuan I", "彖下傳": "Tuan II", "象上傳": "Xiang I", "象下傳": "Xiang II", "文言傳": "Wenyan",
           "繫辭上傳": "Xici I", "繫辭下傳": "Xici II", "説卦傳": "Shuogua", "說卦傳": "Shuogua", "序卦傳": "Xugua", "雜卦傳": "Zagua"}


def pages_en(top, cid):
    pages(top, cid); r = _raw.get((top, cid))
    if not r: return ""
    if r[0] == "p": return f"p. {r[1]}" if r[1] == r[2] else f"pp. {r[1]}\u2013{r[2]}"
    a, b = r[1], r[2]
    ja, jb = JUAN_EN.get(a[0], a[0]), JUAN_EN.get(b[0], b[0])
    return f"{ja}, leaf {a[1]}" if a == b else (f"{ja}, leaves {a[1]}\u2013{b[1]}" if a[0] == b[0] else f"{ja}, leaf {a[1]} to {jb}, leaf {b[1]}")


def block_en(top, cid, headline, url, kanwu_href, mail_html, report, date):
    """英文页：Chicago 一条、BibTeX 一条（11-27 攒引用线程要的，给图书馆和论文用）。"""
    s = shudan(top); e = s and s.get("英文")
    if not e: return None
    b = e["底本"]; pg = pages_en(top, cid)
    based = f"Based on {b['作者']}, <i>{esc(b['书名'])}</i> ({esc(b['版本'])})" + (f", {pg}" if pg else "")
    based_t = f"Based on {b['作者']}, {b['书名']} ({b['版本']})" + (f", {pg}" if pg else "")
    t = headline.strip()
    chi = (f'Yikonglu. \u201c{esc(t)}.\u201d {based}. Last modified <span class="yyz2">{date}</span>. '
           f'Accessed <span class="yyc2">today</span>. {esc(url)}.')
    key = "yikonglu_" + re.sub(r"[^a-z0-9]+", "_", f"{top}_{cid}".lower()).strip("_")
    bib = ("@misc{" + key + ",\n  author = {{Yikonglu}},\n  title = {" + esc(t) + "},\n  year = {" + (date[:4] if date[:1].isdigit() else date.replace("DATE", "DATEYR", 1)) + "},\n  url = {" + esc(url) + "},\n"
           "  note = {" + esc(based_t.replace("\u2013", "--")) + ". Last modified " + date + ". Accessed <span class=\"yya\">today</span>}\n}")
    cp = f"\u2014 Yikonglu, \u201c{t}\u201d, {url}"
    wk = ("{{cite book |author=" + b["作者"] + " |title=" + b["书名"] + " |edition=" + re.sub(r"\s*edition$", "", b["版本"]) + wiki_pg(top, cid, True)
          + " |chapter=" + t.replace(" \u00b7 ", " ") + " |url=" + url + ' |via=Yikonglu |access-date=<span class="yya">today</span> |language=zh}}')
    return (f'<section class="citeit yy" data-d="{date}" data-cp="{esc(cp)}"><b>Cite this page</b>'
            f'<p class="yyf"><span class="yyl">Chicago</span><code>{chi}</code><button type="button">Copy</button></p>'
            f'<p class="yyf"><span class="yyl">BibTeX</span><code style="white-space:pre-wrap">{bib}</code><button type="button">Copy</button></p>'
            f'<p class="yyf"><span class="yyl">Wikipedia</span><code>{wk.replace("&", "&amp;").replace("<span", "@@S@@").replace("</span>", "@@E@@").replace("<", "&lt;").replace("@@S@@", "<span").replace("@@E@@", "</span>")}</code><button type="button">Copy</button></p>'
            f'<p>Last modified {date}; every correction is logged on the <a href="{kanwu_href}">errata page</a>. Licensed CC BY 4.0: please credit \u201cYikonglu\u201d and link to this page. Found this useful? Linking to this chapter from your notes, course page or blog is the best way to help Yikonglu.</p>'
            f'<p class="mailp">{report} {mail_html}</p></section>' + JS_EN + CP)


JS_EN = ("<script>(function(){var S=document.querySelector('.citeit.yy');if(!S)return;var n=new Date(),M=['January','February','March','April','May','June','July','August','September','October','November','December'],"
         "p=function(x){return(x<10?'0':'')+x},iso=n.getFullYear()+'-'+p(n.getMonth()+1)+'-'+p(n.getDate()),lng=M[n.getMonth()]+' '+n.getDate()+', '+n.getFullYear();"
         "S.querySelectorAll('.yya').forEach(function(e){e.textContent=iso});S.querySelectorAll('.yyc2').forEach(function(e){e.textContent=lng});"
         "S.querySelectorAll('.yyz2').forEach(function(e){var m=e.textContent.match(/(\\d{4})-(\\d{1,2})-(\\d{1,2})/);if(m)e.textContent=M[+m[2]-1]+' '+(+m[3])+', '+m[1]});"
         "S.querySelectorAll('.yyf button').forEach(function(btn){btn.onclick=function(){var t=btn.previousElementSibling.textContent,o=btn.textContent,"
         "ok=function(){btn.textContent='Copied';setTimeout(function(){btn.textContent=o},1500)};if(navigator.clipboard)navigator.clipboard.writeText(t).then(ok,function(){})}})})();</script>")
