"""一孔书院 · 题名（11-16 主人点卡定“先开题名”，改动单 评审/2026-11-16-书院题名开卖/网站改动单-题名-v1.md）。
数据只读：数据/网站素材/_题名/题名.json，[{date:"01-01", lesson, chapter, name, note, tier:"日"|"篇", pian?}]，由书院题名线程维护，网站不写。
年历页每天显示已题、查生日给一行；章页（这一天的主章）抬头下一行小字；题一篇的篇页一行；支持页题名录满 20 位才出。"""
import html, json, os, re

SRC = os.environ.get("YK_TIMING") or "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_题名/题名.json"  # 样张可用 YK_TIMING 指假数据
RUYUAN = "shuyuan/ruyuan.html"
AFDIAN = "https://afdian.com/item/d667fd6ae19d11f1a65c5254001e7c00"
MIN_LU = 20  # 题名录满 20 位才公开（未满整块不显示）
_D = None


def esc(s): return html.escape(s or "", quote=True)


def _md(d):
    m = re.match(r"^\s*(\d{1,2})\D+(\d{1,2})\s*$", str(d or ""))
    return f"{int(m.group(1))}-{int(m.group(2))}" if m else ""


def load():
    """{"day": {"1-1": 条目}, "pian": {"1" 或篇名: 条目}, "all": [...]}；文件没有或坏了就当空。"""
    global _D
    if _D is not None: return _D
    rows = []
    try: rows = json.load(open(SRC, encoding="utf-8")) or []
    except Exception: rows = []
    day, pian = {}, {}
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or not (r.get("name") or "").strip(): continue
        if r.get("tier") == "篇":
            k = str(r.get("pian") or "").strip()
            if k: pian.setdefault(k, r)
        else:
            md = _md(r.get("date"))
            if md: day.setdefault(md, r)  # 一天只收一位：先写进表的算
    _D = {"day": day, "pian": pian, "all": [r for r in rows if isinstance(r, dict) and (r.get("name") or "").strip()]}
    return _D


def _say(r):
    n = (r.get("note") or "").strip()
    return f'{esc(r["name"].strip())}题' + (f'：{esc(n)}' if n else "")


def nl_attr(md):
    """年历 li 的属性：已题的带 data-tm（查生日脚本用）。"""
    r = load()["day"].get(md)
    return f' data-tm="{esc(r["name"].strip())}"' if r else ""


def nl_line(md):
    r = load()["day"].get(md)
    return f'<small class="tmn">{_say(r)}</small>' if r else ""


def chapter_line(c, nl_rows):
    """这一章是某天的主章且那天已题：抬头下一行小字“2027 年 1 月 1 日 · 青山题：……”。"""
    D = load()["day"]
    if not D: return ""
    for r in nl_rows or []:
        if r.get("cs") and r["cs"][0] == c and r["md"] in D:
            m, d = r["md"].split("-")
            return f'<p class="tmline">2027 年 {m} 月 {d} 日 · {_say(D[r["md"]])}</p>'
    return ""


def pian_line(p, pname):
    P = load()["pian"]
    r = P.get(str(p)) or P.get(pname) or P.get(f"{pname}第{p}")
    return f'<p class="tmline">本篇由{esc(r["name"].strip())}题名</p>' if r else ""


def lu_block():
    """支持页“2027 首轮题名录”：满 20 位才出，列网名与日子，不显示题记。"""
    A = load()["all"]
    if len(A) < MIN_LU: return ""
    def when(r):
        if r.get("tier") == "篇": return f'题《{esc(str(r.get("pian") or ""))}》篇'
        md = _md(r.get("date")); return f'{md.replace("-", " 月 ")} 日' if md else ""
    li = "".join(f'<li><b>{esc(r["name"].strip())}</b><span>{when(r)}</span></li>' for r in A)
    return f'<h2>2027 首轮题名录</h2><p class="note">共 {len(A)} 位书友。</p><ul class="tmlu">{li}</ul>'
