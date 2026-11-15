"""一字一页（十一项之 4，11-15 主人定）：/zi/字-拼音/（拼音去声调，同字同音节不同调时带调号数字）。
数据：tools/zidian.json（occ＝字|音→全书各章；per＝已讲章里每处的 [句序, 句内位置(含标点,从0起), 字|音, 朱注原话, 出处]）。
分批：先上出现章数最多、且有朱注的一百个（进站点地图）；两周后看收录再上其余带朱注的；没朱注的最后再定。只简繁。"""
import json, os, re, html, unicodedata, collections

esc = html.escape
FIRST = 100
TONE = {"̄": "1", "́": "2", "̌": "3", "̀": "4"}


def _plain(py):
    d = unicodedata.normalize("NFD", py)
    tone = next((TONE[c] for c in d if c in TONE), "5")
    base = "".join(c for c in d if unicodedata.category(c) != "Mn").replace("ü", "v")
    return base, tone


def plan(ZD):
    """返回 [(字|音, slug)]，按出现章数排，只取有朱注的前 FIRST 个。"""
    has_g = collections.defaultdict(list)
    for c, rows in ZD["per"].items():
        for s, i, key, g, src in rows:
            if g: has_g[key].append(c)
    keys = sorted([k for k in ZD["occ"] if has_g.get(k)], key=lambda k: (-len(ZD["occ"][k]), k))[:FIRST]
    slugs, seen = {}, collections.defaultdict(list)
    for k in ZD["occ"]:
        ch, py = k.split("|"); seen[(ch, _plain(py)[0])].append(k)
    for k in keys:
        ch, py = k.split("|"); base, tone = _plain(py)
        slugs[k] = f"{ch}-{base}" + (tone if len(seen[(ch, base)]) > 1 else "")
    return [(k, slugs[k]) for k in keys]


def urls_map(ZD, P):
    return {k: f"{P}zi/{s}/" for k, s in plan(ZD)}


def build(L, ZD, write, page, P, href, title_of, text_of, split_ju, DOMAIN):
    if not L.code.startswith("zh") or not ZD.get("occ"): return []
    pl = plan(ZD); urls = []
    by = collections.defaultdict(list)
    for c, rows in ZD["per"].items():
        for s, i, key, g, src in rows: by[key].append((c, s, i, g, src))
    cno = lambda c: tuple(int(x) for x in c.split("."))
    for key, slug in pl:
        ch, py = key.split("|")
        occ = sorted(ZD["occ"][key], key=cno)
        gl, seen = [], set()
        for c, s, i, g, src in sorted(by[key], key=lambda r: cno(r[0])):
            if g and g not in seen: seen.add(g); gl.append((g, src, c))
        pos = collections.defaultdict(list)
        for c, s, i, g, src in by[key]: pos[c].append((s, i))
        li = []
        for c in occ:
            t = text_of(c) or ""; sents = split_ju(t) if t else []
            snip = ""
            for s, i in sorted(pos.get(c, [])):
                if 0 < s <= len(sents) and i < len(sents[s - 1]) and sents[s - 1][i] == ch:
                    x = sents[s - 1]; snip = f"{esc(x[:i])}<b>{esc(ch)}</b>{esc(x[i + 1:])}"; break
            if not snip:
                x = next((x for x in sents if ch in x), "")
                snip = esc(x)
            li.append(f'<li><a href="{href(c)}"><em>论语 {c}</em> {esc(title_of(c))}</a>' + (f'<span lang="zh-Hans">{snip}</span>' if snip else "") + "</li>")
        gh = "".join(f'<li><q lang="zh-Hans">{esc(g)}</q><small>{esc(src)}（<a href="{href(c)}">论语 {c}</a>）</small></li>' for g, src, c in gl)
        n = len(occ)
        body = (f'<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a> › <a href="{P}zi/">难字一字一页</a></p>'
                f'<h1><span class="no">《论语》难字 · 全书 {n} 章</span>“{esc(ch)}”读 {esc(py)}</h1></div></div>'
                f'<main class="wrap narrow zizhuan"><div class="zihead"><b lang="zh-Hans">{esc(ch)}</b><span>{esc(py)}</span></div>'
                f'<p class="lead">《论语》里“{esc(ch)}”读 {esc(py)} 的，全书共 {n} 章。读音照朱熹《论语集注》定，和一孔录朗读一致。</p>'
                + (f'<h2 class="ph">朱熹怎么注</h2><ul class="zig">{gh}</ul><p class="note">注文照朱熹《论语集注》（《四部备要》本）原文，页码是本站底本页码，点章号可以看原页。</p>' if gh else "")
                + f'<h2 class="ph">全书 {n} 处</h2><ol class="zio">{"".join(li)}</ol>'
                f'<p class="note"><a href="{P}zi/">更多难字</a> · <a href="{P}kanwu.html">发现读音错了，告诉我们</a></p></main>')
        ttl = f"“{ch}”读 {py}：《论语》里的 {n} 处与朱熹注｜一孔录"
        desc = f"《论语》里“{ch}”读 {py}，全书 {n} 章。" + (f"朱熹注：{gl[0][0]}" if gl else "") + "各章原句与链接。"
        ld = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": f"{ch}（{py}）", "description": desc, "inDefinedTermSet": f"{DOMAIN}/{L.prefix}zi/"}
        write(f"zi/{slug}/index.html", page(L, ttl, desc, f"zi/{slug}/", body, ld, codes=["zh-Hans", "zh-Hant"]))
        urls.append(f"{DOMAIN}/{L.prefix}zi/{slug}/")
    chips = "".join(f'<a href="{P}zi/{s}/"><b lang="zh-Hans">{esc(k.split("|")[0])}</b><span>{esc(k.split("|")[1])}</span><small>{len(ZD["occ"][k])} 章</small></a>' for k, s in pl)
    body = (f'<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">《论语》</a></p><h1><span class="no">读音、朱熹注、全书出处</span>《论语》难字：一字一页</h1></div></div>'
            f'<main class="wrap narrow zizhuan"><p class="lead">《论语》里读音容易错的字，一个字一页：读什么音，朱熹怎么注，全书哪几章出现。读音和一孔录朗读同一张表。先收出现最多的 {len(pl)} 个。</p>'
            f'<div class="zichips">{chips}</div></main>')
    write("zi/index.html", page(L, "《论语》难字一字一页：读音、朱熹注与全书出处｜一孔录", f"《论语》里读音容易错的 {len(pl)} 个字，每字一页：读音、朱熹注原文与底本页码、全书各处出现。", "zi/", body, codes=["zh-Hans", "zh-Hant"]))
    urls.append(f"{DOMAIN}/{L.prefix}zi/")
    return urls
