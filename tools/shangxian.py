"""写共享盘 数据/网站素材/_上线章页.json：有讲读的章数（chapters_live）与挂了视频的章数（chapters_video），论语；11-16 起分开报。build.py 末尾调用。"""
import glob, json, os, re, sys, datetime
out, sdir = sys.argv[1], sys.argv[2]
fs = [open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(out, "lunyu", "*", "*.html")) if re.fullmatch(r"\d+\.html", os.path.basename(f))]
n = sum(1 for t in fs if "<!--yk:jiang-->" in t)  # 11-16：有讲读（札记、讲稿）的章；视频另计
nv = sum(1 for t in fs if "<!--yk:vid-->" in t)  # 已挂视频的章（含定时公开、还没到点的）
if os.path.isdir(sdir):
    t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    json.dump({"updated": t.strftime("%m-%d %H:%M（北京）"), "chapters_live": n, "chapters_video": nv, "total": 498},
              open(os.path.join(sdir, "_上线章页.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"有讲读章页 {n}/498，挂了视频 {nv}")
