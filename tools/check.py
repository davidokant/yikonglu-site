#!/usr/bin/env python3
"""发版前检查：python3 tools/check.py docs。有问题打印出来并以非零退出，别推。"""
import os, re, sys, glob, subprocess
out = sys.argv[1] if len(sys.argv) > 1 else "docs"
bad = []
css = open(os.path.join(out, "style.css"), encoding="utf-8").read()
css_nc = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
if css_nc.count("{") != css_nc.count("}"): bad.append(f"style.css 花括号不配对：{{ {css_nc.count('{')} 对 }} {css_nc.count('}')}")
WORDS = ["一孔按", "Codex", "标题问", "封面问", "片头问", "短片问", "标题候选", "本集只上", "外参", "工坊", "定版稿", "插科", "特别期", "发布线程", "主人选定", "待主人", "主人選定", "主人定", "主人看片", "主人在", "", "", ""]
n = 0
for f in glob.glob(os.path.join(out, "**", "*.*"), recursive=True):
    if not f.endswith((".html", ".json", ".xml", ".js", ".css", ".txt")): continue
    n += f.endswith(".html")
    t = open(f, encoding="utf-8").read()
    t = re.sub(r"[木铁石陶织绣]工坊", "", t)  # 讲稿今例里的“木工坊”等是普通词，不是内部说法
    for w in WORDS:
        if w in t: bad.append(f"{f} 含内部字样或占位符 {w!r}")
    if re.search(r"(?<!开始 · )(?<!开始，)(?<!開始 · )(?<!開始，)逐字[读讀]經?经?典原文", t): bad.append(f"{f} 有旧标语“逐字读经典原文”，没带“从《论语》开始”")  # 11-16 标语统一
    if re.search(r"主人\s*\d{1,2}-\d{1,2}", t): bad.append(f"{f} 含内部定稿记录（主人+日期）")
    if f.endswith(".html") and (m := re.search(r">([a-z]{2,6}_[a-z0-9_]+)<", t)): bad.append(f"{f} 有没翻出的界面字键 {m.group(1)!r}")
    if f.endswith(".html") and t.count("<main") != t.count("</main>"): bad.append(f"{f} <main> 不配对")
try:
    def _sm_old():  # 11-18 起站点地图分卷：总目录 sitemap.xml＋sitemap-*.xml；旧版是单个 sitemap.xml
        ls = subprocess.run(["git", "ls-tree", "--name-only", "HEAD", out + "/"], capture_output=True, text=True).stdout.split()
        fs = [x for x in ls if re.fullmatch(r".*/sitemap(-[a-z-]+)?\.xml", x) and not x.endswith("sitemap-images.xml")]
        return sum(subprocess.run(["git", "show", "HEAD:" + x], capture_output=True, text=True).stdout.count("<url>") for x in fs)
    old = _sm_old()
    new = sum(open(f, encoding="utf-8").read().count("<url>") for f in glob.glob(os.path.join(out, "sitemap*.xml")) if not f.endswith("sitemap-images.xml"))
    if old and new < old * 0.97: bad.append(f"sitemap 页数从 {old} 掉到 {new}（构建依赖缺了？）")
except Exception as e:
    pass
for b in bad[:50]: print("✗", b)
print(f"检查 {n} 个页面：" + ("通过" if not bad else f"{len(bad)} 处问题"))
sys.exit(1 if bad else 0)
