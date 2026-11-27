"""《论语》易读错字速查页（11-27 攒引用线程方案，主人点“照方案交网站线程做”）：/lunyu/duyin/（简、繁、英）＋ embed.html（给别人嵌入）。
数据只在 tools/lunyu_duyin.json；这里只管排版。A4 PDF 由 tools/lunyu_duyin_pdf.py 照同一份数据另出，放 root/lunyu/duyin/。"""
import json, os, re, html, unicodedata

esc = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "lunyu_duyin.json")
PDF = "lunyu/duyin/yikonglu-lunyu-duyin.pdf"
DATA = json.load(open(F, encoding="utf-8")) if os.path.exists(F) else None


def plain(py):
    return "".join(c for c in unicodedata.normalize("NFD", py) if unicodedata.category(c) != "Mn").replace("ü", "v")


def aid(e):
    return f'd{e["c"].replace(".", "-")}-{plain(e["py"])}'


def anchors(P):
    """难字卡用：字|音 → 速查页本条网址（只给简繁）。"""
    if not DATA: return {}
    return {f'{e["zi"]}|{e["py"]}': f"{P}lunyu/duyin/#{aid(e)}" for e in DATA["entries"]}


CSS = """<style>.dy-tools{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 6px}.dy-idx{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 22px;padding:0;list-style:none}
.dy-idx a{display:inline-flex;flex-direction:column;align-items:center;min-width:46px;padding:4px 6px;border:1px solid var(--line,#d9d6c8);border-radius:6px;text-decoration:none;color:inherit;line-height:1.2}
.dy-idx b{font-size:1.25em;font-weight:500}.dy-idx small{font-size:.72em;opacity:.75}
.dy{border-top:1px solid var(--line,#d9d6c8);padding:14px 0 12px;scroll-margin-top:70px}.dy:target{background:rgba(138,90,44,.07)}
.dy h3{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:0 0 6px;font-weight:400}.dy h3 .z{font-size:2em;line-height:1}.dy h3 .p{font-size:1.15em;color:#23503F}
.dy h3 .n{font-size:.85em;opacity:.75}.dy .ju b{color:#8A5A2C;border-bottom:2px solid #8A5A2C;font-weight:600}.dy p{margin:4px 0}.dy .k{display:inline-block;min-width:3.2em;opacity:.7;font-size:.9em}
.dy .al a{margin-right:2px;white-space:nowrap}.dy-emb textarea{width:100%;min-height:5.5em;font:13px/1.5 ui-monospace,monospace;box-sizing:border-box}
@media (prefers-color-scheme:dark){.dy h3 .p{color:#8fc2a8}.dy .ju b{color:#d9a36b;border-color:#d9a36b}}</style>"""

T = {
    "zh": dict(title="《论语》易读错字速查｜一孔录", h1="易读错字速查", sub="《论语》· 朱熹集注本",
               desc="《论语》里今天容易读错的字：读音、例句、朱熹集注音注原话、底本原页，反切、去声换成今天的说法。",
               lead="《论语》里有些字，今天习惯的读法跟书里的意思对不上，朱熹《论语集注》在原页上给它们注了音。这里收 {n} 个，按书中先后排。每条有例句、朱注原话和底本原页，并把“反切”“去声”这类旧说法换成今天的话。读音和一孔录配音一致。",
               how="收字办法：同一个字、同一个读音只收一条，例句取朱注注出这个音的那一章，书里其余读这个音的章列在“全书还见于”。每条都对过底本原页（朱熹《论语集注》，《四部备要》本），点页码看原页。",
               pdf="下载 A4 PDF", emb="嵌入代码", not_="不读", ju="例句", zhu="朱注", jie="怎么读", also="全书还见于", page="底本第 {p} 页",
               fu_h="朱注读法与本站配音不同的字", fu_p="下面 {n} 个字，朱注注的音和一孔录配音读的不一样，单列出来，两种都写明，不收进上面的速查。",
               emb_h="嵌入到你的网页", emb_p="把下面这段代码贴进你的网页或博客，就能显示这张速查表；表下自带出处链接，请保留。",
               lic="本页文字以 CC BY 4.0 许可公开，可转载、改编、商用，请署“一孔录”并附本页网址。"),
    "en": dict(title="Commonly Misread Characters in the Analects | Yikonglu", h1="Commonly Misread Characters", sub="The Analects · Zhu Xi's commentary",
               desc="Characters in the Analects that modern readers often mispronounce: reading, example, Zhu Xi's own sound gloss and the scanned page.",
               lead="Some characters in the Analects are read differently from their everyday modern pronunciation, and Zhu Xi's commentary (Lunyu jizhu) marks the sound on the page. This list has {n} of them in book order. Each entry gives an example sentence, Zhu Xi's gloss in his own words, and the scanned page, with the old fanqie and tone terms explained. Readings match Yikonglu's recordings.",
               how="One entry per character and reading; the example is the chapter where Zhu Xi glosses it, and the other chapters with the same reading follow. Every entry has been checked against the base text (Zhu Xi, Lunyu jizhu, Sibu beiyao edition); click the page number to see it.",
               pdf="A4 PDF (Chinese)", emb="Embed", not_="not", ju="Example", zhu="Zhu Xi", jie="How to read", also="Also in", page="p. {p}",
               fu_h="Where our recordings differ from Zhu Xi", fu_p="For these {n} characters our recordings do not follow Zhu Xi's gloss. Both readings are given; they are not part of the list above.",
               emb_h="Embed this list", emb_p="Paste this code into your page or blog to show the list; please keep the source link below it.",
               lic="Text licensed CC BY 4.0: please credit “Yikonglu” and link to this page."),
}


def build(L, write, page, P, DOMAIN, ch_url, pian_name):
    """L：语种；ch_url(c)→本语种章页网址；pian_name(c)→篇名（中文）。只出简、繁、英。"""
    if not DATA or L.code not in ("zh-Hans", "zh-Hant", "en"): return []
    zh = L.code.startswith("zh"); hant = L.code == "zh-Hant"; t = T["zh" if zh else "en"]
    Z = X = (lambda s: s)  # 繁体页由建站整页 to_hant 转，这里不先转
    E = DATA["entries"]; FU = DATA["fu"]
    def zz(e, s):  # 字头、例句里的南宫适保持原字
        if hant and e["zi"] == "适" and e["py"] == "kuò": return s.replace("适", "\ue010适\ue011")  # 南宫适（kuò）繁体仍作“适”，不转“適”（to_hant 原样留 \ue010…\ue011）
        return s
    def ju(e):
        s = Z(e["ju"]); i = e["i"]
        return esc(zz(e, s[:i])) + f"<b>{esc(zz(e, s[i]))}</b>" + esc(zz(e, s[i + 1:]))
    def chl(c):
        return f'<a href="{ch_url(c)}">{("《论语》" if zh else "Analects ")}{c}</a>' if c else ""
    def entry(e, fu=False):
        pg = f'<a class="pg" href="/yuanye/p{e["page"]:03d}.jpg" target="_blank">{X(t["page"].format(p=e["page"]))}</a>'
        zi = zz(e, Z(e["zi"]))
        head = (f'<h3><span class="z" lang="zh">{esc(zi)}</span><span class="p">{esc(e["py"])}</span>'
                + (f'<span class="n">{X(t["not_"])} {esc(e["chang"])}</span>' if not fu and e.get("chang") else "")
                + (f'<span class="n">{("朱注" if zh else "Zhu Xi")} {esc(e["zhu_py"])}</span>' if fu else "") + "</h3>")
        al = " ".join(f'<a href="{ch_url(c)}">{c}</a>' for c in e.get("also", []))
        return (f'<section class="dy" id="{aid(e) if not fu else "f" + aid(e)}">{head}'
                f'<p class="ju"><span class="k">{X(t["ju"])}</span><span lang="zh">{ju(e)}</span>（{chl(e["c"])}）</p>'
                f'<p><span class="k">{X(t["zhu"])}</span><span lang="zh">“{esc(zz(e, Z(e["zhu"])))}”</span> {pg}</p>'
                f'<p><span class="k">{X(t["jie"])}</span>{esc(X(e["jie"] if zh else e["jie_en"]))}</p>'
                + (f'<p class="al"><span class="k">{X(t["also"])}</span>{al}</p>' if al else "") + "</section>")
    idx = "".join(f'<li><a href="#{aid(e)}"><b lang="zh">{esc(zz(e, Z(e["zi"])))}</b><small>{esc(e["py"])}</small></a></li>' for e in E)
    url = f"{DOMAIN}/{L.prefix}lunyu/duyin/"
    emb_code = (f'<iframe src="{DOMAIN}/lunyu/duyin/embed.html" width="100%" height="560" style="border:1px solid #d9d6c8;border-radius:6px" loading="lazy" '
                f'title="《论语》易读错字速查（一孔录）"></iframe>\n<p style="font-size:13px">来源：<a href="{DOMAIN}/lunyu/duyin/">一孔录《论语》易读错字速查</a>（CC BY 4.0）</p>')
    body = (f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}lunyu/">{L.t("lunyu")}</a></p><h1><span class="no">{X(t["sub"])}</span>{X(t["h1"])}</h1></div></div>
<main class="wrap narrow prose">{CSS}<p class="lead">{esc(X(t["lead"].format(n=len(E))))}</p><p class="note">{esc(X(t["how"]))}</p>
<p class="dy-tools"><a class="btn" href="/{PDF}" download>{X(t["pdf"])}</a><a class="btn ghost" href="#emb">{X(t["emb"])}</a></p>
<ul class="dy-idx">{idx}</ul>{"".join(entry(e) for e in E)}
<h2 class="ph" id="fu">{X(t["fu_h"])}</h2><p class="note">{esc(X(t["fu_p"].format(n=len(FU))))}</p>{"".join(entry(e, True) for e in FU)}
<section class="dy-emb" id="emb"><h2 class="ph">{X(t["emb_h"])}</h2><p>{esc(X(t["emb_p"]))}</p><textarea readonly onclick="this.select()">{esc(emb_code)}</textarea></section>
<section class="citeit"><p class="mailp">{L.t("report")}</p></section></main>''')
    ld = {"@context": "https://schema.org", "@graph": [{"@type": "Article", "headline": ("论语 易读错字速查" if zh else "Analects: Commonly Misread Characters"),
          "inLanguage": L.code if zh else "en", "url": url, "about": {"@type": "Book", "name": "论语"}}]}
    write("lunyu/duyin/index.html", page(L, X(t["title"]), X(t["desc"]), "lunyu/duyin/", body, jsonld=ld, codes=["zh-Hans", "zh-Hant", "en"]))
    urls = [url]
    if L.code == "zh-Hans":  # 嵌入用的精简页：只有字表，不进收录，canonical 指正页
        rows = "".join(f'<tr><td class="z"><a href="{DOMAIN}/lunyu/duyin/#{aid(e)}" target="_blank">{esc(e["zi"])}</a></td><td>{esc(e["py"])}</td><td class="c">不读 {esc(e["chang"])}</td>'
                       f'<td>{ju(e)}<small>（{e["c"]}）</small></td></tr>' for e in E)
        write("lunyu/duyin/embed.html", f'''<!doctype html><html lang="zh-Hans"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>《论语》易读错字速查｜一孔录</title>
<link rel="canonical" href="{DOMAIN}/lunyu/duyin/"><meta name="robots" content="noindex,follow">
<style>body{{margin:0;font:15px/1.6 -apple-system,"PingFang SC","Noto Sans SC",sans-serif;color:#222;background:#F2F1EA}}h1{{font-size:16px;margin:10px 12px}}table{{border-collapse:collapse;width:100%}}td{{border-top:1px solid #d9d6c8;padding:5px 8px;vertical-align:top}}td.z{{font-size:22px;white-space:nowrap}}td.z a{{color:#23503F;text-decoration:none}}td.c{{color:#777;white-space:nowrap;font-size:13px}}td b{{color:#8A5A2C}}small{{color:#777}}p{{margin:8px 12px;font-size:13px}}a{{color:#23503F}}
@media (prefers-color-scheme:dark){{body{{background:#1b1d1b;color:#ddd}}td.z a,a{{color:#8fc2a8}}td b{{color:#d9a36b}}}}</style>
<h1>《论语》易读错字速查（{len(E)} 字）</h1><table>{rows}</table>
<p>来源：<a href="{DOMAIN}/lunyu/duyin/" target="_blank">一孔录 yikonglu.com/lunyu/duyin/</a>。每条都对过朱熹《论语集注》（《四部备要》本）原页。CC BY 4.0。</p></html>''')
    return urls
