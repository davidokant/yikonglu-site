"""论语原页（四部备要本）找版框：横向找贯穿大半页宽的黑线定上下框，纵向在上下框之间找贯穿大半高的黑线定左右框。返回 [x0,y0,x1,y1]（含外边 M 像素）。"""
import numpy as np
from PIL import Image
M = 24
MBR = 0.048  # 底边留白＝切后宽×0.048（三本同一比例）：一行小字写在白边里，印骑在版框下沿
def mb(w): return round(MBR * w)
def frame_box(path, M=M):
    im = np.asarray(Image.open(path).convert("L")) < 110
    H, W = im.shape
    rows = np.where(im.sum(1) > 0.45 * W)[0]
    if len(rows) < 2: return None
    y0, y1 = rows.min(), rows.max()
    if y1 - y0 < 0.4 * H: return None
    cols = np.where(im[y0:y1 + 1].sum(0) > 0.8 * (y1 - y0))[0]
    if len(cols) < 2: return None
    x0, x1 = cols.min(), cols.max()
    if (x1 - x0) < 0.75 * W: return None
    return [max(0, int(x0) - M), max(0, int(y0) - M), min(W, int(x1) + 1 + M), min(H, int(y1) + 1 + mb(x1 - x0 + 1 + 2 * M))], (W, H)
def ink_box(path, M=M):
    """没有整圈版框的页（校平过的几页）：按墨迹取外接框。"""
    im = np.asarray(Image.open(path).convert("L")) < 110
    H, W = im.shape; E = 30
    im[:E] = False; im[-E:] = False; im[:, :E] = False; im[:, -E:] = False  # 扫描边上的黑边不算
    r = np.where(im.sum(1) > 0.03 * W)[0]; c = np.where(im.sum(0) > 0.03 * H)[0]
    return [max(0, int(c.min()) - M), max(0, int(r.min()) - M), min(W, int(c.max()) + 1 + M), min(H, int(r.max()) + 1 + mb(c.max() - c.min() + 1 + 2 * M))], (W, H)
def box(path):
    return frame_box(path) or ink_box(path)
if __name__ == "__main__":
    import sys, os
    for p in sys.argv[2:]:
        print(p, frame_box(os.path.join(sys.argv[1], p + ".jpg")))
