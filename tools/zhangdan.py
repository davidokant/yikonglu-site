#!/usr/bin/env python3
"""通用章单生成器（2026-11-27 起，《孙子兵法》第一本）。

规矩见 规范/网站做书规范-一页.md：新书不写 build_X，数据不进代码。一本书只要在共享盘有
  数据/网站素材/_<书>/书单.json   书名、网址前缀、底本、篇章表、繁简护字表
  数据/网站素材/_<书>/章/<篇号>.json  篇、题、句（id yw bd bh 注 出处）、段（id 句区间 网址 yk）
  数据/网站素材/_<书>/读音.tsv     读音库（网站与配音共用）
  数据/网站素材/_<书>/争议.json    争议读法（可无）
再在 tools/zhangdan.json 登记一行，就出书页、篇页、段页（简繁，繁体 noindex）。

两个入口：
  build.py 的 build_lang 里一行：urls += ZD.build_all(sys.modules[__name__], L, write, P, search_idx)
  命令行：
    python3 tools/zhangdan.py zhuyin 孙子兵法          由读音库＋pypinyin 出 _<书>/_注音/<篇号-段号>.json 和 多音字核对表
    python3 tools/zhangdan.py yangzhang 孙子兵法 01 <出目录>   只出一篇的样张（不跑全站）
"""
import json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "zhangdan.json")  # {"孙子兵法": {"dir": "_孙子", "slug": "sunzi", "open": false, "img": ""}}
SRC = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材"
HAN = re.compile(r"[㐀-鿿\U00020000-\U0003134f]")
HANS_FIX = [("𬮱", "闉"), ("筭", "算"), ("彊", "强")]  # 𬮱：t2s 转出的罕用类推简化字，字库多半没有，简体栏保原字；筭、彊：书单“繁简护字表”定简体栏作算、强，繁体栏保原字
YITI = os.path.join(os.path.dirname(SRC), "..", "规范", "闸", "异体字.txt")  # 全项目一份：刻本异体 → 正字（Z3）
_yt = None
def zheng(s):
    """页面显示用：刻本异体换正字（录文与原页照旧）。"""
    global _yt
    if _yt is None:
        p = os.path.normpath(YITI); _yt = {}
        if os.path.exists(p):
            for ln in open(p, encoding="utf-8"):
                f = ln.rstrip("\n").split("\t")
                if len(f) == 2 and not ln.startswith("#"): _yt[f[0]] = f[1]
    return "".join(_yt.get(ch, ch) for ch in s)
HANT_MARK = '<i id="zdhant" hidden></i>'


def _j(p): return json.load(open(p, encoding="utf-8"))


def cfg():
    return _j(CFG) if os.path.exists(CFG) else {}


_cc = {}
def cc(k):
    if k not in _cc:
        import opencc
        _cc[k] = opencc.OpenCC(k).convert
    return _cc[k]


def t2s(s):
    s = cc("t2s")(zheng(s))
    for a, b in HANS_FIX: s = s.replace(a, b)
    return s


def load(name, c=None):
    """读一本书：返回 {meta, pian: [篇json], sent: {句id: 句}, duan: [(篇, 段)], zy: {句id: [...]}}。没有书单就 None。"""
    c = c or cfg()[name]; d = os.path.join(SRC, c["dir"])
    if not os.path.exists(os.path.join(d, "书单.json")): return None
    meta = _j(os.path.join(d, "书单.json"))
    pians = [_j(os.path.join(d, p["章单"])) for p in meta["篇章表"] if os.path.exists(os.path.join(d, p["章单"]))]
    sent = {s["id"]: s for p in pians for s in p["句"]}
    zy = _j(os.path.join(d, "争议.json")) if os.path.exists(os.path.join(d, "争议.json")) else {}
    for p in pians:  # 机检：bd 去标点必须与 yw 逐字相同（标点只加不改字）
        for s in p["句"]:
            if "".join(HAN.findall(s.get("bd", ""))) != "".join(HAN.findall(s["yw"])): raise SystemExit(f"{name} {s['id']} bd 与 yw 字不同")
    for sid, a, b in (meta.get("显示换字") or {}).get("条", []):  # 刻本“巳”义为已／己等：只换页面与注音用的 bd，录文不动
        if sid in sent and a in sent[sid]["bd"]: sent[sid] = dict(sent[sid], bd=sent[sid]["bd"].replace(a, b))
        else: print(f"  显示换字对不上：{sid} {a}→{b}")
    for p in pians: p["句"] = [sent[x["id"]] for x in p["句"]]
    return dict(name=name, c=c, dir=d, meta=meta, pian=pians, sent=sent, zy=zy)


def duan_sents(B, dn):
    a, b = dn["句"][0], dn["句"][-1]
    ids = sorted(k for k in B["sent"] if a <= k <= b)
    return [B["sent"][k] for k in ids]


def dkey(dn): return dn["id"].replace(".", "-")  # 01.03 → 01-03（网址与注音文件名）


# ———————————————— 读音：读音库＋pypinyin → _注音/<段>.json ————————————————
SID = re.compile(r"^\d{2}\.\d{3}")


def duyin_rows(d):
    rows = []
    for ln in open(os.path.join(d, "读音.tsv"), encoding="utf-8").read().splitlines()[1:]:
        f = ln.split("\t")
        if len(f) >= 3 and f[0]: rows.append(f)
    return rows


_SY = None
def _syl(py):
    """把 jiāngjūn、wěi jī 这类读音切成音节（按 pypinyin 的音节表，回溯切分）。"""
    global _SY
    import unicodedata
    if _SY is None:
        from pypinyin.constants import PINYIN_DICT
        from pypinyin.style.tone import ToneConverter  # noqa: F401
        _SY = set()
        for v in PINYIN_DICT.values():
            for x in v.split(","):
                _SY.add("".join(ch for ch in unicodedata.normalize("NFD", x) if not unicodedata.combining(ch)).replace("ü", "v"))
    out = []
    for r in py.split():
        plain = "".join(ch for ch in unicodedata.normalize("NFD", r) if not unicodedata.combining(ch)).replace("ü", "v")
        if len(plain) != len(r): return None
        def go(i):
            if i == len(plain): return []
            for L in range(min(6, len(plain) - i), 0, -1):
                if plain[i:i + L] in _SY:
                    t = go(i + L)
                    if t is not None: return [r[i:i + L]] + t
            return None
        t = go(0)
        if t is None: return None
        out += t
    return out


def duyin_rules(d):
    """读音库 → [(字串, 读音音节列表, 适用句id集合或None, 上下文短语列表, 依据)]。读不懂的行打印出来交人改库，不猜。"""
    rules, bad = [], []
    for f in duyin_rows(d):
        zi, ctx, du = f[0], f[1], f[2]; yj = f[3] if len(f) > 3 else ""
        ctxs = [x.strip() for x in re.split(r"[；;]", ctx) if x.strip()]
        sids = {re.match(r"\d{2}\.\d{3}", x).group(0) for x in ctxs if SID.match(x)}
        phr = [x for x in ctxs if not SID.match(x)]
        parts = [x.strip() for x in re.split(r"[；;]", du) if x.strip()]
        for part in parts:
            m = re.match(r"^(?:(\d{2}\.\d{3})\s+|其余\s*|([㐀-鿿]+)(?:（[^）]*）)?\s*)?([a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü ]+)$", part)
            if not m: bad.append("\t".join(f[:3])); continue
            sid1, word, py = m.group(1), m.group(2), m.group(3).strip()
            syl = _syl(py)
            w = word or zi
            if syl is None: bad.append("\t".join(f[:3])); continue
            if word and len(word) != len(syl):  # 如“陳兵 chén”：只给词里的本字定音，词作上下文
                zc = [ch for ch in re.split(r"[/／]", zi) if ch in t2s(word) or ch in word]
                if len(syl) == 1 and zc: phr = [word]; w = zc[0]
                else: bad.append("\t".join(f[:3])); continue
            if not word and len(syl) != len(zi):  # 如 将 jiāngjūn：读音带了后字，只取本字那一节
                if len(zi) == 1 and len(syl) > 1: syl = syl[:1]
                else: bad.append("\t".join(f[:3])); continue
            only = {sid1} if sid1 else (sids or None)
            if part.startswith("其余"): only = sids or None
            whole = ctx.strip() == "全书"
            if whole: phr = []
            rules.append((t2s(w), syl, only, ["".join(HAN.findall(t2s(x))) for x in phr], yj, bool(sid1), part.startswith("其余") or whole))
            phr = [x for x in ctxs if not SID.match(x)]
    return rules, bad


def zhuyin_text(text_s, sid, rules):
    """一句（简体，带标点）→ [[字, 拼音, 注音符号, 多音字1, 依据]]。"""
    from pypinyin import pinyin, Style
    from pypinyin.style.bopomofo import BopomofoConverter
    to_bopomofo = BopomofoConverter().to_bopomofo
    hz = HAN.findall(text_s); plain = "".join(hz)
    py = [x[0] for x in pinyin(plain, style=Style.TONE, errors=lambda s_: ["?"] * len(s_))]
    hetero = [len(set(x)) > 1 for x in pinyin(plain, style=Style.TONE, heteronym=True, errors=lambda s_: [["?"]] * len(s_))]
    src = [""] * len(hz)
    # 先排“其余”，再排一般，最后排指名句 id 的：后写的盖前面
    order = sorted(rules, key=lambda r: (0 if r[6] else 1 if not r[5] else 2))
    for w, syl, only, phr, yj, exact, rest in order:
        if only is not None and sid not in only: continue
        i = plain.find(w)
        hit = []
        while i >= 0:
            ok = (only is not None and not phr) or (rest and not phr)
            if not ok and phr:  # 上下文短语里含本字：只在短语覆盖处生效
                for p in phr:
                    k = plain.find(p)
                    while k >= 0:
                        if k <= i < k + len(p): ok = True; break
                        k = plain.find(p, k + 1)
                    if ok: break
            if ok: hit.append(i)
            i = plain.find(w, i + 1)
        for i in hit:
            for k, s_ in enumerate(syl): py[i + k] = s_; src[i + k] = "读音库：" + (yj or "照库")
    out = []
    for k, ch in enumerate(hz):
        try: bp = to_bopomofo(py[k])
        except Exception: bp = "?"
        out.append([ch, py[k], bp, 1 if (hetero[k] or src[k]) else 0, src[k]])
    return out


def zhuyin(name):
    c = cfg()[name]; B = load(name, c); d = B["dir"]
    rules, bad = duyin_rules(d)
    od = os.path.join(d, "_注音"); os.makedirs(od, exist_ok=True)
    rep = ["段\t句id\t字\t读音\t来源"]
    for p in B["pian"]:
        for dn in p["段"]:
            zi = []
            for s in duan_sents(B, dn):
                rows = zhuyin_text(t2s(s["bd"]), s["id"], rules)
                zi += rows
                rep += [f"{dn['id']}\t{s['id']}\t{r[0]}\t{r[1]}\t{r[4] or '默认（pypinyin）'}" for r in rows if r[3]]
            json.dump({"x": "".join(t2s(s["bd"]) for s in duan_sents(B, dn)), "段": dn["id"], "zi": zi}, open(os.path.join(od, dkey(dn) + ".json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(od, "多音字核对表.tsv"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print(f"{name} 注音：{sum(len(p['段']) for p in B['pian'])} 段；多音字处 {len(rep) - 1}；读音库读不懂 {len(bad)} 行")
    for b in bad: print("  读不懂：", b)


# ———————————————— 页面 ————————————————
ZHUJIA = ["曹操", "孟氏", "李筌", "杜牧", "陳皥", "賈林", "杜佑", "梅堯臣", "王晳", "何氏", "張預"]


def chuchu(o, short=False):
    if not o: return ""
    a, b = o["起"], o["止"]
    f = lambda x: f'第 {x["PDF页"]} 页{"右" if x["半叶"] == "R" else "左"}半叶第 {x["行"]} 行'
    s = f'第 {a["册"]} 册' + f(a) + ("" if a == b else "至" + (f'第 {b["册"]} 册' if b["册"] != a["册"] else "") + f(b))
    return s


def build_all(BM, L, write, P, S_IDX=None):
    urls = []
    for name, c in cfg().items():
        if not L.code.startswith("zh"): continue
        B = load(name, c)
        if B: urls += build_book(BM, B, L, write, P, S_IDX)
    return urls


def build_book(BM, B, L, write, P, S_IDX=None):
    esc, page, fold, quotes = BM.esc, BM.page, BM.fold, BM.quotes
    c = B["c"]; meta = B["meta"]; slug = c["slug"]; bk = meta["书名"]
    hant = L.code == "zh-Hant"
    is_open = bool(c.get("open")); img = c.get("img", "")
    NOIDX = "" if is_open else '<meta name="robots" content="noindex,follow">'
    CODES = ["zh-Hans", "zh-Hant"]
    Y = (lambda s: "\ue010" + zheng(s) + "\ue011") if hant else t2s  # 繁体页底本字形（异体换正字）原样，整页转繁时不再碰
    if hant:
        _w = write
        def write(rel, text): _w(rel, text.replace("</main>", HANT_MARK + "</main>", 1))
    urls = []
    src = c.get("src") or meta["底本"]["名"].split("，")[0]
    pians = B["pian"]; allduan = [(p, dn) for p in pians for dn in p["段"]]
    pnm = lambda p: t2s(p["篇"]) if not hant else p["篇"]
    rel_d = lambda dn: f"{slug}/{dkey(dn)}/"
    rel_p = lambda p: f"{slug}/{p['篇号']}/"
    def ttl(dn):
        t = "".join(t2s(s["bd"]) for s in duan_sents(B, dn))
        return BM.seo_head(t, 16).rstrip("，、；：")
    cover = BM.mcv(P, "", True, slug, bk); cover_s = BM.mcv(P, "", False, slug, bk)
    jnote = lambda: '<p class="note">原文据' + esc(src) + "；简体栏转简体，繁体栏照底本字形。标点为一孔录所加。</p>"

    # 篇页：段目录＋全篇白话（逐句白话连成）
    def pian_body(p):
        toc = '<ol class="toc">' + "".join(
            f'<li><a href="{P}{rel_d(dn)}"><em>{dn["id"]}</em><b>{esc(ttl(dn))}</b><span><span lang="zh-Hans">{esc(Y("".join(s["bd"] for s in duan_sents(B, dn)))[:0])}{esc(t2s("".join(s["bd"] for s in duan_sents(B, dn)))[:40])}…</span></span></a></li>'
            for dn in p["段"]) + "</ol>"
        bh = "".join(f'<p><a class="pgref" href="{P}{rel_d(dn)}">{dn["id"]}</a> {esc("".join(s.get("bh", "") for s in duan_sents(B, dn)))}</p>' for dn in p["段"])
        tz = p.get("题") or {}
        note = ""
        if tz.get("注"):
            note = '<details class="sec fold"><summary><h2>篇题下诸家注</h2></summary>' + "".join(
                f'<p><span lang="zh-Hant">{esc(Y(z.get("bd") or z["原话"]))}</span></p>' for z in tz["注"]) + f'<p class="note">见底本{chuchu(tz.get("出处"))}。</p></details>'
        return toc + f'<section class="sec sec-白"><h2><i>白</i>全篇白话</h2>{bh}<p class="note">由各段逐句白话连成，{esc(meta["白话依据"]["值"])}。</p></section>' + note
    items = [(p["篇号"], pnm(p), f'{len(p["段"])} 段 · {len(p["句"])} 句', pian_body(p), "") for p in pians]
    def bk_page(sl, nm, body):
        write(f"{slug}/{sl}/index.html", page(L, f"《{t2s(bk)}·{nm}》原文、白话与十一家注｜一孔录", f"《{bk}·{nm}》分段原文、白话、一孔之见与宋本十一家注。", f"{slug}/{sl}/", body, None, "pg-book", head_extra=NOIDX, codes=CODES))
        if is_open: urls.append(f"{BM.DOMAIN}/{L.prefix}{slug}/{sl}/")
    groups = BM.pian_layer(L, P, write, urls, slug, bk, items, f"{P}{rel_d(allduan[0][1])}", bk_page, cover)
    nsent = sum(len(p["句"]) for p in pians)
    lead = (f"《{bk}》十三篇，一段一页：原文带拼音，逐句白话，一孔之见，再附宋本十一家注。"
            f"原文、注文照{esc(src)}录出，白话{esc(meta['白话依据']['值'])}。")
    body = f"""<div class="chhead bk"><div class="wrap">{cover}<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a></p>
<h1><span class="no">《{bk}》 · {len(pians)} 篇 {len(allduan)} 段 {nsent} 句</span>{bk}</h1></div></div>
<main class="wrap narrow"><p class="lead">{lead}</p>{groups}</main>"""
    write(f"{slug}/index.html", page(L, f"《{bk}》原文、白话与十一家注｜一孔录", f"《{bk}》十三篇分段原文、白话、一孔之见，附宋刻十一家注与原页。", f"{slug}/", body, None, "pg-book", head_extra=NOIDX, codes=CODES))
    if is_open: urls.append(f"{BM.DOMAIN}/{L.prefix}{slug}/")

    # 段页
    for k, (p, dn) in enumerate(allduan):
        ss = duan_sents(B, dn); key = f"sz.{dn['id']}"; rel = rel_d(dn); url = f"{BM.DOMAIN}/{L.prefix}{rel}"
        sents = [t2s(s["bd"]) for s in ss]
        zy_ = BM.ZJ.zhuyin_book(c["dir"][1:], dkey(dn), sents)
        rows = [{"zhu": [[Y(z.get("bd") or z["原话"]), chuchu(z.get("出处"))] for z in s.get("注", [])], "hj": []} for s in ss]
        text_s = "".join(sents)
        bq = f'<blockquote lang="{"zh-Hant" if hant else "zh-Hans"}" data-src="{esc(bk + " " + dn["id"] + " · 一孔录")}" data-url="{url}" data-short="" data-sep="，" data-reads="[]" data-rl="" data-hj="{{}}">'
        ju = "".join(f'<span class="ju" id="s{j}" data-n="{j}" data-id="{s["id"]}" tabindex="0">{esc(Y(s["bd"]) if hant else sents[j - 1])}</span>' for j, s in enumerate(ss, 1))
        cc_ = {"起": ss[0]["出处"]["起"], "止": ss[-1]["出处"]["止"]}
        cap = f"原文据{src}，底本{chuchu(cc_)}。点一句，下面看这一句的十一家注。"
        pane = ""  # 原页图：img 配好、裁图传到图片仓库后再出（见 zhangdan.json）
        fig = (f'<figure class="yuanwen dz{"" if pane else " nopane"}"><div class="dztools"><span class="prog">{esc(pnm(p))} · 第 {int(dn["id"][3:])} 段</span></div>'
               f'<div class="dzgrid"><div>{bq}{ju}</blockquote><figcaption>{esc(cap)}</figcaption></div>' + (f'<div class="yypane">{pane}</div>' if pane else "") + '</div>'
               f'<script type="application/json" class="zjdata">{json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")}</script>{BM.zy_tag(zy_)}</figure>')
        bh = "".join(s.get("bh", "") for s in ss)
        bh_html = f'<section class="sec sec-白"><h2><i>白</i>{L.t("baihua")}：“{esc(re.sub(r"[“”‘’…]", "", ttl(dn)).rstrip("，、；：。"))}”是什么意思</h2><p lang="zh-Hans">{esc(bh)}</p><p class="note">逐句直译，{esc(meta["白话依据"]["值"])}。</p></section>' if bh else ""
        yk = dn.get("yk", "")
        yk_html = f'<section class="gist ykan" id="ykan"><h2>这一段讲什么</h2><p><b class="anlab">一孔之见：</b>{quotes(yk)}</p></section>' if yk else ""
        # 争议读法：本段句子上的
        zyl = [z for z in (B["zy"].get(p["篇号"]) or []) if z.get("句") in {s["id"] for s in ss}]
        zy_html = ""
        if zyl:
            zy_html = '<section class="sec sec-议"><h2><i>议</i>这一段的争议读法</h2>' + "".join(
                f'<div class="zyi"><h3>{esc(z["t"])}</h3>' + "".join(f'<p><b>{esc(r["k"])}</b>（{esc(r["who"])}）：{esc(r["t"])}</p>' for r in z["r"])
                + (f'<p class="note">本站取{esc(z["定"].split("（")[0])}。</p>' if z.get("定") else "") + "</div>" for z in zyl) + "</section>"
        deep = BM.ZJ.zy_section(dkey(dn), sents, zy_, [{"bh": s.get("bh", "")} for s in ss], esc, "读音照今音为准，注家音注与今字典不合的按今音。") if zy_ else ""
        zhu_all = ""
        for s, t in zip(ss, sents):
            if not s.get("注"): continue
            zhu_all += f'<div class="zj1"><h3 lang="zh-Hans">{esc(Y(s["bd"]) if hant else t)}</h3>' + "".join(
                f'<p><span lang="zh-Hant">{esc(Y(z.get("bd") or z["原话"]))}</span> <small class="pgref">（{chuchu(z.get("出处"))}）</small></p>' for z in s["注"]) + "</div>"
        if zhu_all: deep += f'<section class="sec sec-注"><h2><i>注</i>十一家注（宋本全录）</h2>{zhu_all}<p class="note">注文照底本录出，标点为一孔录所加，有疑处请对照原页。</p></section>'
        deep += f'<section class="sec sec-出"><h2><i>出</i>出处</h2>' + "".join(f'<p>{s["id"]}　底本{chuchu(s["出处"])}</p>' for s in ss) + jnote() + "</section>"
        prv = allduan[k - 1][1] if k else None; nxt = allduan[k + 1][1] if k + 1 < len(allduan) else None
        pn = "".join(f'<a class="pncard {cl}" href="{P}{rel_d(x)}"><small>{L.t(lb)}</small><b>{x["id"]}　{esc(ttl(x))}</b></a>' if x else "<span></span>" for x, lb, cl in ((prv, "prev", "prev"), (nxt, "next", "next")))
        side = "".join(f'<li class="{"cur" if x is dn else ""}"><a href="{P}{rel_d(x)}"><em>{x["id"][3:]}</em>{esc(ttl(x))}</a></li>' for x in p["段"])
        body = f"""<div class="chhead bk"><div class="wrap">{cover_s}
<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}{slug}/">{bk}</a> › <a href="{P}{rel_p(p)}">{esc(pnm(p))}</a></p>
<h1><span class="no">{bk} {dn["id"]} · {esc(pnm(p))}第 {int(dn["id"][3:])} 段</span>{esc(ttl(dn))}</h1>
</div></div>
<main class="wrap chapter">
<article>
{fig}
{yk_html}
{bh_html}
{zy_html}
<div class="chacts">{BM.done_html(L, key)}</div>
{"" if not nxt else f'<a class="nextread" href="{P}{rel_d(nxt)}">接着读下一段：{nxt["id"]}　{esc(ttl(nxt))} ›</a>'}
<div class="deep"><div class="deephead"><h2>{L.t("ch_deep")}</h2><button type="button" class="foldall" data-o="{L.t("ch_open_all")}" data-c="{L.t("ch_close_all")}">{L.t("ch_open_all")}</button></div><p class="note">{L.t("ch_deep_note")}</p>{fold(deep)}</div>
<section class="citeit"><p class="mailp">{L.t("report")} {BM.MAIL}</p></section>
<nav class="pn">{pn}</nav>
</article>
<aside><h3>{esc(pnm(p))}</h3><ol>{side}</ol></aside>
</main><i id="rc" data-c="{key}" hidden></i>"""
        js = BM.FOLD_JS + BM.ZJ.ZJ_JS.replace('<button data-a="img">@IMG@</button>', "").replace("@TABS@", json.dumps([["zhu", "十一家注"]], ensure_ascii=False)).replace("@NONE@", "这一句下面宋本没有注。").replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied")) + (BM.ZJ.KJ_JS if zy_ else "")
        hd = ttl(dn)
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": f"{bk} {dn['id']} {hd}", "inLanguage": L.hreflang, "url": url,
              "author": {"@type": "Organization", "name": "一孔录", "url": BM.DOMAIN}, "about": {"@type": "Book", "name": bk}, "isBasedOn": {"@type": "Book", "name": "十一家注孙子"}}
        write(rel + "index.html", page(L, f"{hd}｜《{bk}·{pnm(p)}》原文与白话｜一孔录", f"{text_s[:60]}……《{bk}·{t2s(p['篇'])}》第 {int(dn['id'][3:])} 段原文、白话、一孔之见与宋本十一家注。", rel, body + js, ld, "pg-chapter pg-wj", head_extra=NOIDX, codes=CODES))
        if is_open: urls.append(url)
        if is_open and S_IDX is not None: S_IDX.append({"c": f"{bk} {dn['id']}", "t": hd, "u": P + rel, "y": text_s, "x": bh})
    return urls


# ———————————————— 样张：只出一篇，不跑全站 ————————————————
def yangzhang(name, pno, out):
    sys.path.insert(0, HERE)
    import build as BM
    import shutil
    c = dict(cfg()[name]); B = load(name, c)
    B["pian"] = [p for p in B["pian"] if p["篇号"] == pno]
    n = 0
    for code, prefix in (("zh-Hans", ""), ("zh-Hant", "zh-hant")):
        L = BM.Lang(code, BM.ZH_UI)
        def write(rel, text, prefix=prefix):
            nonlocal n
            if prefix:  # 样张的繁体：整页 s2twp，底本字形段原样（全站构建由 build.py 的 to_hant 做）
                keep = []
                text = re.sub("(.*?)", lambda m: keep.append(m.group(1)) or f"{len(keep) - 1}", text, flags=re.S)
                text = cc("s2twp")(text)
                text = re.sub("(\\d+)", lambda m: keep[int(m.group(1))], text).replace(HANT_MARK, "")
                text = re.sub(r'(href|src)="/(?!zh-hant/|assets/|style\.css)([^"]*)"', r'\1="/zh-hant/\2"', text)
            pth = os.path.join(out, prefix, rel)
            os.makedirs(os.path.dirname(pth), exist_ok=True)
            open(pth, "w", encoding="utf-8").write(text.replace(BM.DATE_TOK, "2026-11-27")); n += 1
        build_book(BM, B, L, write, "/" + L.prefix)
    shutil.copy(os.path.join(HERE, "style.css"), os.path.join(out, "style.css"))
    print(f"样张 {name} 篇 {pno}：{n} 页 → {out}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["zhuyin"]: zhuyin(a[1])
    elif a[:1] == ["yangzhang"]: yangzhang(a[1], a[2], a[3])
    else: print(__doc__)
