"""视频逐字稿上章页（十一项之 6，11-15）：各期讲稿按章拆开，折进章页“细读与核对”。
只取每期最新版稿；只要旁白，不要角色对白；原文段（页面上已有）、开场、片尾、下集引子等串场段不要；
【语气…】之类配音提示去掉；带【待核】【请复核】的整段不上（成片里那句可能已删，留半段会接不上）；“上一集”之类照成片保留。
只上已公开的集（有 YouTube、公开时间已过），由 build.py 判断。"""
import glob, os, re, html

esc = html.escape
NUM = "一二三四五六七八九十"
DROP_KIND = ("全集的问", "下集引子", "下篇引子", "全集收尾", "接回全集")


def _ver(p):
    return [int(x) for x in re.findall(r"v(\d+(?:\.\d+)*)", os.path.basename(p))[-1].split(".")]


def _latest(d):
    fs = [p for p in glob.glob(os.path.join(d, "*-稿-v*.md")) if re.search(r"v\d", os.path.basename(p))]
    return max(fs, key=_ver) if fs else None


def _clean(t):
    if re.search(r"待核|请复核", t): return ""
    return re.sub(r"\s*【[^】]*】\s*", "", re.sub(r"\s+", " ", t.replace("‖", ""))).strip()


def load(root, eps):
    """返回 {章号: [段, …]}；eps 是 episodes.json（期名 → chapters）。"""
    out = {}
    for name, e in eps.items():
        ds = glob.glob(os.path.join(root, f"论语-*-{name}"))
        f = _latest(ds[0]) if ds else None
        if not f: continue
        s = open(f, encoding="utf-8").read().split("## 引文取处")[0]
        s = re.split(r"\n### 片尾", s)[0]
        chs = re.split(rf"\n### 第[{NUM}]+章 ", s)[1:]
        if len(chs) != len(e["chapters"]):
            print("逐字稿：章数对不上，整期不上", name, os.path.basename(f)); continue
        for c, body in zip(e["chapters"], chs):
            ps = []
            for tag, kind, txt in re.findall(r"\*\*([KX]\d+) ?([^*]*)\*\*\n(.*?)(?=\n\*\*[KX]\d+|\n---|\n### |\Z)", body, re.S):
                if tag[0] == "X" or not kind.startswith("旁白"): continue  # 原文段页面上已有
                if any(d in kind for d in DROP_KIND) and "照今" not in kind: continue
                lines = [l for l in txt.strip().split("\n") if l.strip() and not l.lstrip().startswith(">")]
                t = _clean(" ".join(lines))
                if len(t) < 12 or t.startswith("先读原文"): continue
                ps.append(t)
            if ps: out[c] = ps
    return out


def section(c, ps, epname, yt, st, quotes):
    if not ps: return ""
    link = f'https://www.youtube.com/watch?v={yt}' + (f"&amp;t={st}s" if st else "")
    body = "".join(f"<p>{quotes(p)}</p>" for p in ps)
    return (f'<section class="sec gaoben" id="gaoben"><h2><i>讲</i>视频里怎么讲：本章旁白全文</h2>'
            f'<p class="note">《{esc(epname)}》视频里讲本章的旁白，照成片原话；角色对白和片头片尾的串场话略去。<a href="{link}">去看视频</a></p>'
            f'{body}<p class="note">（一孔录 yikonglu.com/lunyu/{c}）</p></section>')
