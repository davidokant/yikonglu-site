# 11-26 主人点卡“开栏发首篇”：一孔札记栏目 /zhaji/ 与单篇 /zhaji/<编号>/，只出简体。
# 内容在 tools/zhaji.json（照定稿誊入），原页图在 tools/zhaji/<图名>.webp，建站时拷到 docs/zhaji/<编号>/。
import json, os, re, shutil, html

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "zhaji.json")


def esc(s): return html.escape(s, quote=True)


def load():
    if not os.path.exists(CFG): return {}
    return json.load(open(CFG, encoding="utf-8"))


CSS = """<style>
.zj-meta{font-size:14px;color:var(--muted,#666);line-height:1.9;margin:.4em 0 0}
.zj-meta b{font-weight:normal;color:var(--ink,#222)}
.zj-jl{border-left:4px solid var(--accent,#23503F);background:var(--card,#fff);padding:.8em 1em;margin:1.2em 0;font-size:1.08em;line-height:1.8}
.zj-fig{margin:1.2em 0;text-align:center}.zj-fig img{max-width:100%;height:auto;border:1px solid var(--line,#ddd)}
.zj-fig figcaption{font-size:14px;color:var(--muted,#666);text-align:left;margin-top:.5em;line-height:1.7}
.zj-body p{line-height:1.95;margin:0 0 1em}
.zj-sec{margin:2em 0 0}.zj-sec h2{font-size:1.15em;margin:0 0 .6em}
.zj-qr{list-style:none;padding:0;margin:0}.zj-qr li{padding:.55em 0;border-bottom:1px dashed var(--line,#ddd);line-height:1.8}
.zj-qr .who{font-weight:bold}.zj-qr .q{display:block}.zj-qr .n{display:block;font-size:14px;color:var(--muted,#666)}
.zj-cz dt{font-weight:bold;margin-top:.7em}.zj-cz dd{margin:.2em 0 0;line-height:1.85}
.zj-cite{background:var(--card,#fff);border:1px solid var(--line,#ddd);padding:.7em 1em;margin:.5em 0;font-size:14px;line-height:1.8;word-break:break-word}
.zj-cite button{margin-top:.4em}
.zj-list{list-style:none;padding:0}.zj-list li{border-bottom:1px solid var(--line,#ddd);padding:1em 0}
.zj-list a{text-decoration:none}.zj-list b{font-size:1.1em;display:block;margin:.2em 0}
.zj-list .jl{display:block;line-height:1.8;margin:.3em 0}.zj-list small{color:var(--muted,#666)}
</style>"""

COPY_JS = """<script>(function(){document.querySelectorAll('.zj-cite button').forEach(function(b){b.addEventListener('click',function(){var t=b.parentNode.querySelector('.ct').textContent;var ok=function(){var o=b.textContent;b.textContent='已复制';setTimeout(function(){b.textContent=o},1500)};if(navigator.clipboard)navigator.clipboard.writeText(t).then(ok,function(){});else{var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');ok()}catch(e){}document.body.removeChild(a)}})})})();</script>"""


def _link_ch(text, href, chs):
    """正文里的“5.9”这类章号链到章页；只链 chs 里有的章，免得把页码、通行本章号也链上。"""
    def rep(m):
        c = m.group(1)
        return f'<a href="{href(c)}">{c}</a>' if c in chs else c
    return re.sub(r"(?<![\d.])(\d{1,2}\.\d{1,2})(?![\d.])", rep, text)


def build(L, write, page, P, href, DOMAIN, MAIL, outdir, all_ch):
    """返回进站点地图的网址列表。L 只接简体。"""
    D = load()
    if not D or L.code != "zh-Hans": return []
    items = [x for x in D.get("篇", []) if x.get("pub")]
    if not items: return []
    urls = []
    for x in items:
        no = x["no"]; rel = f"zhaji/{no}/"
        os.makedirs(os.path.join(outdir, "zhaji", no), exist_ok=True)
        for fn in [f'{x["img"]}.webp', f'{x["img"]}-s.webp'] + ([x["pdf"]] if x.get("pdf") else []):
            src = os.path.join(HERE, "zhaji", fn)
            if os.path.exists(src): shutil.copy(src, os.path.join(outdir, "zhaji", no, fn))
        date = x.get("date") or ""; doi = x.get("doi") or ""
        date_s = date or "首发日待定"; doi_s = (f'<a href="https://doi.org/{esc(doi)}">{esc(doi)}</a>' if doi else "存档后补")
        url = f"{DOMAIN}/{rel}"
        body_p = "".join(f"<p>{_link_ch(esc(p), href, all_ch)}</p>" for p in x["zhengwen"])
        qr = "".join(f'<li><span class="who">{esc(a)}</span>' + (f'<span class="q">“{esc(q)}”</span>' if q else "") + f'<span class="n">{esc(n)}</span></li>' for a, q, n in x["qianren"])
        cz = "".join(f"<dt>{esc(a)}</dt><dd>{esc(t)}</dd>" for a, t in x["chazheng"])
        doi_cn = doi or "存档后补"
        cite_cn = x.get("cite_cn") or f'一孔录. 一孔札记 {no}：{x["title"].split("：")[0]}[EB/OL]. {url}，{date or "首发日待定"}. DOI：{doi_cn}.'
        cite_en = x.get("cite_en") or f'Yikonglu. {x["title_en"]}. {url}, {date or "forthcoming"}. DOI: {doi or "pending"}.'
        kw = x.get("kanwu") or []
        kw_html = ("<ul>" + "".join(f"<li>{esc(k[0])}：{esc(k[1])}（{esc(k[2])}）</li>" for k in kw) + "</ul>") if kw else "<p>暂无。</p>"
        pdf_html = (f'<p class="note">存档 PDF（与 Zenodo 存档同一份）：<a href="{esc(x["pdf"])}" download>{esc(x["pdf"])}</a><br>文件指纹 SHA-256：<code style="word-break:break-all">{esc(x["sha256"])}</code></p>') if x.get("pdf") else ""
        sf = x.get("shoufa") or []
        sf_html = (f'<section class="zj-sec"><h2>首发记录</h2><ul>' + "".join(f"<li>{esc(a)}：{esc(b)}</li>" for a, b in sf) + "</ul></section>") if sf else ""
        chs = "、".join(f'<a href="{href(c)}">{c}</a>' for c in x.get("chapters", []))
        body = f'''{CSS}<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}zhaji/">一孔札记</a> › {esc(x["id"])}</p>
<h1><span class="no">一孔札记 {esc(x["id"])}</span>{esc(x["title"])}</h1>
<p class="zj-meta">编号 <b>{esc(x["id"])}</b> · 发表 <b>{esc(date_s)}</b> · 版本 <b>{esc(x["ver"])}</b> · DOI <b>{doi_s}</b> · 署名 <b>一孔录</b> · 本章 {chs}</p></div></div>
<main class="wrap narrow zhaji">
<p class="zj-jl"><b>一句话：</b>{_link_ch(esc(x["jielun"]), href, all_ch)}</p>
<figure class="zj-fig"><a href="{x["img"]}.webp" target="_blank" rel="noopener"><img src="{x["img"]}-s.webp" width="900" height="1295" alt="{esc(x["img_cap"])}" loading="lazy"></a><figcaption>{esc(x["img_cap"])}点图看大图。</figcaption></figure>
<p class="note">{esc(x["dibennote"])}</p>
<section class="zj-sec zj-body"><h2>正文</h2>{body_p}</section>
<section class="zj-sec"><h2>前人怎么说</h2><ul class="zj-qr">{qr}</ul></section>
<section class="zj-sec"><h2>查证范围（截至 {esc(x["chazheng_date"])}）</h2><dl class="zj-cz">{cz}</dl></section>
<section class="zj-sec"><h2>什么情况下这条要改</h2><p>{esc(x["tuifan"])}</p></section>
<section class="zj-sec"><h2>引用本文</h2><div class="zj-cite"><span class="ct">{esc(cite_cn)}</span><br><button type="button" class="btn ghost">复制引用</button></div><div class="zj-cite"><span class="ct">{esc(cite_en)}</span><br><button type="button" class="btn ghost">Copy citation</button></div>{pdf_html}</section>
<section class="zj-sec"><h2>勘误记录</h2>{kw_html}</section>{sf_html}
<section class="zj-sec"><p class="note">本文采用 <a href="https://creativecommons.org/licenses/by/4.0/deed.zh-hans" rel="license noopener" target="_blank">CC BY 4.0</a> 许可，转载请署名“一孔录”并附本页网址。发现错处或前人已经说过，请<a href="{P}wen.html">来信</a>，核实后记入勘误，署你的网名。</p></section>
</main>{COPY_JS}'''
        ld = {"@context": "https://schema.org", "@type": "ScholarlyArticle", "headline": x["title"], "inLanguage": "zh-Hans", "url": url,
              "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN}, "publisher": {"@type": "Organization", "name": "一孔录", "url": DOMAIN},
              "license": "https://creativecommons.org/licenses/by/4.0/", "version": x["ver"], "identifier": x["id"], "abstract": x["jielun"],
              "about": {"@type": "Book", "name": "论语"}, "image": f"{url}{x['img']}-s.webp"}
        if date: ld["datePublished"] = date
        if doi: ld["sameAs"] = f"https://doi.org/{doi}"
        write(rel + "index.html", page(L, f'{x["title"]}｜一孔札记 {x["id"]}｜一孔录', x["jielun"], rel, body, jsonld=ld, codes=["zh-Hans"]))
        urls.append(url)
    lis = "".join(f'<li><a href="{P}zhaji/{x["no"]}/"><small>{esc(x["id"])} · {esc(x.get("date") or "首发日待定")} · {esc(x.get("status", "已发"))}</small><b>{esc(x["title"])}</b></a><span class="jl">{esc(x["jielun"])}</span></li>'
                  for x in sorted(items, key=lambda y: y["no"], reverse=True))
    body = f'''{CSS}<div class="chhead"><div class="wrap"><h1><span class="no">栏目</span>一孔札记</h1></div></div>
<main class="wrap narrow"><p class="lead">{esc(D.get("列表说明", ""))}</p>
<ul class="zj-list">{lis}</ul>
<p class="note">每条都写明查过哪些书、哪些没查；查到前人已经说过，就改署“前人已发，一孔录补证”，记入勘误。来信请到<a href="{P}wen.html">来信：勘误与荐书</a>。</p></main>'''
    write("zhaji/index.html", page(L, "一孔札记：一孔录在古籍原页里读出的新东西｜一孔录", D.get("列表说明", ""), "zhaji/", body, codes=["zh-Hans"]))
    urls.append(f"{DOMAIN}/zhaji/")
    return urls
