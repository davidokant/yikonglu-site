"""每月全站正文存档包（11-27 主人点“先做每月存档拿时间戳”）：把 docs/ 里简体、繁体、英文页面 <main> 的正文抽成纯文本，
连同每页 HTML 与正文的 SHA-256 清单、站点提交号打成一个 zip，供每月 1 日存 Zenodo（第三方时间戳与 DOI）。
用法：python3 tools/yuedu_cundang.py [输出目录]；默认 /mnt/project-files/一孔学-内-自媒体/数据/存档/<年-月>/"""
import os, re, sys, json, hashlib, zipfile, html, subprocess, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DOCS = os.path.join(ROOT, "docs")
SKIP = ("assets/", "og/", "data/")
LANGS = ("", "zh-hant/", "en/")  # 正文只收简体、繁体、英文三套；其余语种是同一内容的译本
def text_of(t):
    m = re.search(r"<main\b.*?</main>", t, re.S); t = m.group(0) if m else t
    t = re.sub(r"<(script|style|template|button|nav)\b.*?</\1>", " ", t, flags=re.S)
    t = re.sub(r"<(br|/p|/li|/h[1-6]|/div|/blockquote|/dd|/dt|/tr)\b[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return "\n".join(x.strip() for x in t.splitlines() if x.strip()) + "\n"
def main():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ym = now.strftime("%Y-%m"); out = sys.argv[1] if len(sys.argv) > 1 else f"/mnt/project-files/一孔学-内-自媒体/数据/存档/{ym}"
    os.makedirs(out, exist_ok=True)
    commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    rows = []; zp = os.path.join(out, f"yikonglu-quanzhan-{ym}.zip")
    with zipfile.ZipFile(zp + ".part", "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(DOCS):
            for f in sorted(fs):
                if not f.endswith(".html"): continue
                rel = os.path.relpath(os.path.join(dp, f), DOCS).replace(os.sep, "/")
                if rel.startswith(SKIP): continue
                lang = "zh-hant/" if rel.startswith("zh-hant/") else "en/" if rel.startswith("en/") else ""
                if not lang and re.match(r"^(ja|ko|fr|es|de|ru|vi|id)/", rel): continue
                b = open(os.path.join(DOCS, rel), "rb").read(); tx = text_of(b.decode("utf-8", "replace"))
                if len(tx) < 20: continue
                z.writestr("text/" + rel[:-5] + ".txt", tx)
                rows.append((rel, hashlib.sha256(b).hexdigest(), hashlib.sha256(tx.encode()).hexdigest(), len(tx)))
        rows.sort()
        man = "path\thtml_sha256\ttext_sha256\ttext_chars\n" + "".join("\t".join(map(str, r)) + "\n" for r in rows)
        z.writestr("MANIFEST.tsv", man)
        z.writestr("README.txt", f"一孔录 yikonglu.com 全站正文存档 {ym}\n生成时间 {now.isoformat(timespec='seconds')}\n站点仓库 davidokant/yikonglu-site 提交 {commit}\n"
                   f"收页 {len(rows)} 个（简体、繁体、英文页的 <main> 正文）；MANIFEST.tsv 列每页 HTML 与正文的 SHA-256。\n许可 CC BY 4.0（原文与古注为公版；视频、配音、原创角色与插图不在许可内）。\n")
    os.replace(zp + ".part", zp)
    h = hashlib.sha256(open(zp, "rb").read()).hexdigest()
    json.dump({"month": ym, "zip": zp, "sha256": h, "pages": len(rows), "commit": commit, "made": now.isoformat(timespec="seconds")},
              open(os.path.join(out, "存档说明.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(zp, os.path.getsize(zp), h, len(rows))
if __name__ == "__main__": main()
