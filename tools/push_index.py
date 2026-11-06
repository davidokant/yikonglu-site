#!/usr/bin/env python3
"""新页推给搜索引擎（GitHub Actions 里跑，见 .github/workflows/push-index.yml）。
- IndexNow：必应、Yandex、Naver、Seznam 等共用，密钥文件在站点根目录（tools/root/<key>.txt）。
- 百度普通收录 API：仓库 Secret BAIDU_TOKEN 有值才推；新站每天额度很少，只推中文章节页，最多 BAIDU_MAX 条。
用法：push_index.py <改动的 docs/ 文件…>，或 push_index.py --all（推 sitemap 全部）。"""
import json, os, re, sys, glob, urllib.request

DOMAIN = "https://yikonglu.com"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def to_url(path):
    p = path.replace("\\", "/")
    if not p.startswith("docs/") or not p.endswith(".html") or p.endswith("404.html") or "baidu_verify" in p: return None
    p = p[len("docs/"):]
    if p.endswith("index.html"): p = p[: -len("index.html")]
    return f"{DOMAIN}/{p}"

def post(url, data, ctype):
    req = urllib.request.Request(url, data=data, headers={"Content-Type": ctype, "User-Agent": "yikonglu-site-indexer"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, r.read().decode("utf-8", "replace")[:300]
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e: return 0, str(e)

def main(args):
    if args == ["--all"]:
        urls = re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "docs", "sitemap.xml"), encoding="utf-8").read())
    else:
        urls = [u for u in (to_url(a) for a in args) if u]
    urls = list(dict.fromkeys(urls))
    print(f"要推 {len(urls)} 个地址")
    if not urls: return
    keys = [os.path.basename(f)[:-4] for f in glob.glob(os.path.join(HERE, "root", "*.txt")) if re.fullmatch(r"[0-9a-f]{32}", os.path.basename(f)[:-4])]
    if keys:
        body = {"host": "yikonglu.com", "key": keys[0], "keyLocation": f"{DOMAIN}/{keys[0]}.txt", "urlList": urls[:10000]}
        print("IndexNow:", *post("https://api.indexnow.org/indexnow", json.dumps(body).encode(), "application/json; charset=utf-8"))
    tok = os.environ.get("BAIDU_TOKEN", "").strip()
    if tok:
        zh = [u for u in urls if not re.search(r"/(en|ja|ko|fr|es|de|vi|id|ru)/", u)]
        zh.sort(key=lambda u: (0 if re.search(r"/lunyu/[^/]+/\d+\.html$", u) else 1, "/zh-hant/" in u))
        n = int(os.environ.get("BAIDU_MAX", "10"))
        api = f"http://data.zz.baidu.com/urls?site={DOMAIN}&token={tok}"
        while n >= 1:  # 新站额度很小，超额就减半再试，最少推 1 条
            code, msg = post(api, "\n".join(zh[:n]).encode(), "text/plain"); print(f"百度（{n} 条）:", code, msg)
            if "over quota" not in msg: break
            n //= 2
    else:
        print("百度：没有 BAIDU_TOKEN，跳过")

if __name__ == "__main__":
    main(sys.argv[1:])
