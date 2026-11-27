"""《论语》易读错字速查 A4 PDF（11-27）：照 tools/lunyu_duyin.json 排，页脚带网址与页码。
用法：python3 tools/lunyu_duyin_pdf.py  → tools/root/lunyu/duyin/yikonglu-lunyu-duyin.pdf（建站原样放到网站根）。
数据改了就重跑一次；字体用共享盘 _字体/NotoSerifSC.ttf，Chromium 用本机 Playwright。"""
import html, json, os, subprocess, tempfile, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "lunyu_duyin.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "root", "lunyu", "duyin", "yikonglu-lunyu-duyin.pdf")
FONT = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_字体/NotoSerifSC.ttf"
URL = "https://yikonglu.com/lunyu/duyin/"
esc = html.escape


def ju(e):
    s, i = e["ju"], e["i"]
    return esc(s[:i]) + f"<b>{esc(s[i])}</b>" + esc(s[i + 1:])


def row(e, fu=False):
    al = "、".join(e.get("also", []))
    tag = f'朱注 {esc(e["zhu_py"])}' if fu else f'不读 {esc(e["chang"])}'
    return (f'<tr><td class="z">{esc(e["zi"])}<i>{esc(e["py"])}</i><s>{tag}</s></td>'
            f'<td><p class="j">{ju(e)}（{e["c"]}）</p><p>朱注：“{esc(e["zhu"])}”（底本第 {e["page"]} 页）</p><p class="x">{esc(e["jie"])}</p>'
            + (f'<p class="a">全书还见于：{al}</p>' if al else "") + "</td></tr>")


def main():
    E, FU = D["entries"], D["fu"]
    today = datetime.date.today().isoformat()
    doc = f"""<!doctype html><html lang="zh-Hans"><meta charset="utf-8"><style>
@font-face{{font-family:NS;src:url("file://{FONT}")}}
@page{{size:A4;margin:16mm 14mm 18mm}}body{{font:10.5pt/1.55 NS,serif;color:#1d1d1d}}
h1{{font-size:20pt;margin:0 0 2mm;color:#23503F;font-weight:700}}.sub{{color:#8A5A2C;margin:0 0 4mm}}.lead{{margin:0 0 2mm}}.note{{color:#555;font-size:9.5pt;margin:0 0 4mm}}
table{{border-collapse:collapse;width:100%}}tr{{break-inside:avoid}}td{{border-top:.4pt solid #bdb9a8;padding:2.2mm 1.5mm;vertical-align:top}}
td.z{{width:22mm;font-size:22pt;line-height:1.1;color:#23503F}}td.z i{{display:block;font-style:normal;font-size:11pt;color:#1d1d1d}}td.z s{{display:block;text-decoration:none;font-size:8pt;color:#777}}
p{{margin:0 0 .8mm}}p.j b{{color:#8A5A2C;text-decoration:underline}}p.x{{color:#333}}p.a{{color:#666;font-size:9pt}}h2{{font-size:13pt;color:#23503F;margin:6mm 0 2mm}}
.end{{margin-top:5mm;font-size:9pt;color:#555}}</style>
<h1>《论语》易读错字速查</h1><p class="sub">朱熹集注本 · {len(E)} 字 · 一孔录 yikonglu.com</p>
<p class="lead">《论语》里有些字，今天习惯的读法跟书里的意思对不上，朱熹《论语集注》在原页上给它们注了音。这里收 {len(E)} 个，按书中先后排。每条有例句、朱注原话和底本页码，并把“反切”“去声”这类旧说法换成今天的话。读音和一孔录配音一致。</p>
<p class="note">同一个字、同一个读音只收一条，例句取朱注注出这个音的那一章。每条都对过底本原页（朱熹《论语集注》，《四部备要》本）；原页图在网页版点页码可看：{URL}</p>
<table>{"".join(row(e) for e in E)}</table>
<h2>朱注读法与本站配音不同的字</h2><p class="note">下面 {len(FU)} 个字，朱注注的音和一孔录配音读的不一样，两种都写明，不收进上面的速查。</p>
<table>{"".join(row(e, True) for e in FU)}</table>
<p class="end">一孔录《论语》易读错字速查，{today} 版。CC BY 4.0：可转载、改编、商用，请署“一孔录”并附 {URL}。勘误公开：https://yikonglu.com/kanwu.html</p></html>"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        h = os.path.join(td, "d.html"); open(h, "w", encoding="utf-8").write(doc)
        js = os.path.join(td, "p.js")
        foot = ('<div style="font:8px sans-serif;color:#777;width:100%;padding:0 14mm;display:flex;justify-content:space-between">'
                f'<span>一孔录《论语》易读错字速查 · {URL}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
        open(js, "w").write(f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://{h}');await p.waitForTimeout(800);await p.pdf({{path:{json.dumps(OUT)},format:'A4',printBackground:true,displayHeaderFooter:true,
headerTemplate:'<span></span>',footerTemplate:{json.dumps(foot)},margin:{{top:'16mm',bottom:'18mm',left:'14mm',right:'14mm'}}}});await b.close()}})();""")
        subprocess.run(["node", js], check=True)
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
