"""11-17 主人定“现在就瘦身”：各页内嵌的同一段脚本（分享卡、在读人数、原文框字等）每页一份，近万页撑到 670MB，
GitHub Pages 发布上限 1GB。这里在生成完之后把重复出现的内嵌脚本抽成 /assets/js/<内容哈希>.js，各页只留一行引用。
脚本内容、先后顺序都不变（同步外链脚本照原位置执行）；文件名带内容哈希，脚本一改换新名，浏览器和 sw.js 可以放心长缓存。"""
import os, re, sys, hashlib, collections

MIN_SIZE, MIN_PAGES = 800, 10
PAT = re.compile(r"<script>(.*?)</script>", re.S)  # 只抽不带任何属性的内嵌脚本；JSON、结构化数据、外链脚本都带属性，不动

def main(outdir):
    files = []
    for root, _, fs in os.walk(outdir):
        files += [os.path.join(root, f) for f in fs if f.endswith(".html")]
    cnt = collections.Counter()
    for f in files:
        for m in PAT.finditer(open(f, encoding="utf-8").read()):
            b = m.group(1)
            if len(b.encode()) >= MIN_SIZE and "currentScript" not in b: cnt[b] += 1
    keep = {b: hashlib.sha1(b.encode()).hexdigest()[:12] for b, n in cnt.items() if n >= MIN_PAGES}
    jd = os.path.join(outdir, "assets", "js"); os.makedirs(jd, exist_ok=True)
    for b, h in keep.items():
        open(os.path.join(jd, h + ".js"), "w", encoding="utf-8").write(b.strip() + "\n")
    before = after = 0
    for f in files:
        s = open(f, encoding="utf-8").read(); before += len(s.encode())
        t = PAT.sub(lambda m: f'<script src="/assets/js/{keep[m.group(1)]}.js"></script>' if m.group(1) in keep else m.group(0), s)
        after += len(t.encode())
        if t != s: open(f, "w", encoding="utf-8").write(t)
    print(f"抽出公用脚本 {len(keep)} 个；页面合计 {before/1e6:.0f}MB → {after/1e6:.0f}MB")

if __name__ == "__main__":
    main(sys.argv[1])
