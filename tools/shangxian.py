"""写共享盘 数据/网站素材/_上线章页.json：已讲、有完整章页的章数（论语）。build.py 末尾调用。"""
import glob, json, os, re, sys, datetime
out, sdir = sys.argv[1], sys.argv[2]
n = sum(1 for f in glob.glob(os.path.join(out, "lunyu", "*", "*.html"))
        if re.fullmatch(r"\d+\.html", os.path.basename(f)) and 'class="pg-chapter"' in open(f, encoding="utf-8").read())
if os.path.isdir(sdir):
    t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    json.dump({"updated": t.strftime("%m-%d %H:%M（北京）"), "chapters_live": n, "total": 498},
              open(os.path.join(sdir, "_上线章页.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"已讲章页 {n}/498")
