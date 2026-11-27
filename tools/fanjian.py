"""简体页繁转简（11-27）：OpenCC t2s 加 fanjian.json 的补充规则。各处一律用 fanjian.t2s（或 fanjian.convert），不要再直接 OpenCC("t2s")。"""
import json, os, re
_R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fanjian.json"), encoding="utf-8"))
_CC = __import__("opencc").OpenCC("t2s").convert
_KEEP = re.compile("|".join(f"(?:{p})" for p in _R["保留原字"]))
_X = ""  # 閒 的占位
_WL = re.compile("|".join(re.escape(w).replace("闲", f"[{_X}闲]") for w in _R["閒作闲"]))
_BU = _R["补转"]


def t2s(s):
    if not s: return s
    kept = []
    def put(m):
        kept.append(m.group(0)); return "".join(chr(0xF0000 + len(kept) - 1) for _ in m.group(0)) if len(m.group(0)) == 1 else chr(0xF0000 + len(kept) - 1)
    s = _KEEP.sub(put, s)
    if "閒" in s: s = s.replace("閒", _X)
    s = _CC(s)
    if _X in s:
        s = _WL.sub(lambda m: m.group(0).replace(_X, "闲"), s).replace(_X, "间")
    for a, b in _BU.items():
        if a in s: s = s.replace(a, b)
    if kept: s = re.sub("[\U000F0000-\U000FFFFD]", lambda m: kept[ord(m.group(0)) - 0xF0000], s)
    return s


convert = t2s
