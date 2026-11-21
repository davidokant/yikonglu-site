#!/usr/bin/env python3
"""新页推给搜索引擎（GitHub Actions 里跑，见 .github/workflows/push-index.yml）。
- IndexNow：必应、Yandex、Naver、Seznam 等共用，密钥文件在站点根目录（tools/root/<key>.txt）。
- 百度普通收录 API：仓库 Secret BAIDU_TOKEN 有值才推；新站每天额度很少，只推中文章节页，最多 BAIDU_MAX 条。
用法：push_index.py --dates <旧 pagedates.json> <新 pagedates.json>（只推正文真改过或新加的页，11-21 起 Actions 用这个），
      push_index.py <改动的 docs/ 文件…>，或 push_index.py --all（推 sitemap 全部，只在接入时推一次）。"""
import json, os, re, sys, glob, urllib.request

DOMAIN = "https://yikonglu.com"
CAP = int(os.environ.get("INDEX_CAP", "200"))  # 一次最多推多少页
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
    def sitemap_urls():
        return [u for f in sorted(glob.glob(os.path.join(ROOT, "docs", "sitemap-*.xml"))) if not f.endswith("sitemap-images.xml")
                for u in re.findall(r"<loc>([^<]+)</loc>", open(f, encoding="utf-8").read())]
    if args and args[0] == "--dates":  # 11-21：每次重建几千个文件跟着脚本版本号变，按文件推等于不推；改看正文指纹日期变没变
        try: old = json.load(open(args[1], encoding="utf-8"))
        except Exception: old = {}
        new = json.load(open(args[2], encoding="utf-8"))
        inmap = set(sitemap_urls())  # 只推进站点地图的页（noindex 的外文杂页、跳转页不推）
        urls = [u for u in (to_url("docs/" + k) for k in new if old.get(k, [None, None])[1] != new[k][1]) if u and u in inmap]
        if len(urls) > 2000: print(f"正文改动 {len(urls)} 页，太多，像是指纹算法变了，不推"); urls = []
    elif args == ["--all"]:
        urls = sitemap_urls()  # 11-18 起站点地图分卷
    elif args and args[0] == "--added":  # 11-18：只推新加的页；改版式、改脚本会让几千页一起变，那种不推
        urls = [u for u in (to_url(a) for a in args[1:]) if u]
    else:
        urls = [u for u in (to_url(a) for a in args) if u]
        if len(urls) > CAP:  # 一次改动超过 CAP 页，多半是全站模板、版本戳变了，内容没变：不推（必应会把反复整站重推当滥用）
            print(f"改动 {len(urls)} 页超过 {CAP}，视为全站模板改动，不推"); urls = []
    urls = list(dict.fromkeys(urls))
    print(f"要推 {len(urls)} 个地址")
    if not urls: return
    keys = [k for k in (os.path.basename(f)[:-4] for f in sorted(glob.glob(os.path.join(HERE, "root", "*.txt"))))  # 文件内容等于文件名的才是 IndexNow 密钥（根目录还有别家的验证文件）
            if re.fullmatch(r"[0-9a-f]{32}", k) and open(os.path.join(HERE, "root", k + ".txt"), encoding="utf-8").read().strip() == k]
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
