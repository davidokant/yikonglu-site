import glob, os, json, re
import numpy as np
from PIL import Image
G = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材"
def png_index():
    idx = {}
    for f in glob.glob(G + "/*/p*.png"):
        b = os.path.basename(f)[:-4]
        if re.fullmatch(r"p\d{3}", b): idx.setdefault(b, f)
    return idx
def load(p, idx):
    f = idx.get(p)
    if f: return np.array(Image.open(f).convert("L"))
    j = f"/home/user/yikonglu-site/tools/yuanye/{p}.jpg"
    if os.path.exists(j): return np.array(Image.open(j).convert("L"))
    return None
def julie():
    out = {}
    for f in glob.glob(G + "/_句列/*.json"):
        c = os.path.basename(f)[:-5]
        if c.startswith("_"): continue
        d = json.load(open(f, encoding="utf-8"))
        chars = d.get("chars") or [ch for s in d.get("sentences", []) for ch in s.get("chars", [])]
        out[c] = (d, chars)
    return out
