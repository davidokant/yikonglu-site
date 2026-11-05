#!/usr/bin/env python3
"""发版前检查：python3 tools/check.py docs。有问题打印出来并以非零退出，别推。"""
import os, re, sys, glob, subprocess
out = sys.argv[1] if len(sys.argv) > 1 else "docs"
bad = []
css = open(os.path.join(out, "style.css"), encoding="utf-8").read()
css_nc = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
if css_nc.count("{") != css_nc.count("}"): bad.append(f"style.css 花括号不配对：{{ {css_nc.count('{')} 对 }} {css_nc.count('}')}")
WORDS = ["Codex", "外参", "工坊", "定版稿", "插科", "特别期", "发布线程", "", "", ""]
n = 0
for f in glob.glob(os.path.join(out, "**", "*.*"), recursive=True):
    if not f.endswith((".html", ".json", ".xml")): continue
    n += f.endswith(".html")
    t = open(f, encoding="utf-8").read()
    for w in WORDS:
        if w in t: bad.append(f"{f} 含内部字样或占位符 {w!r}")
    if re.search(r"主人\s*\d{1,2}-\d{1,2}", t): bad.append(f"{f} 含内部定稿记录（主人+日期）")
    if f.endswith(".html") and t.count("<main") != t.count("</main>"): bad.append(f"{f} <main> 不配对")
try:
    old = subprocess.run(["git", "show", "HEAD:" + os.path.join(out, "sitemap.xml")], capture_output=True, text=True).stdout.count("<url>")
    new = open(os.path.join(out, "sitemap.xml"), encoding="utf-8").read().count("<url>")
    if old and new < old * 0.97: bad.append(f"sitemap 页数从 {old} 掉到 {new}（构建依赖缺了？）")
except Exception as e:
    pass
for b in bad[:50]: print("✗", b)
print(f"检查 {n} 个页面：" + ("通过" if not bad else f"{len(bad)} 处问题"))
sys.exit(1 if bad else 0)
