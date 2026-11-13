# 道德经原页逐句框（11-13）

四库本《老子道德经》原页（图片仓库 ddj/pNNN.jpg，已校平）每页 8 列×21 行。经文顶格、王弼注低一格、章题列“N章 案河上公注本…”低两格。

流程：scan.py 量每页每列每格有无字（geo.py 找版框与界行，grid.py 定格）→ seg.py 按章题列切章、挑出顶格的经文列 → local.py 每章动态规划把经文字数配到各列（允许 ±2 字误差）→ export.py 按网站的分句（split_ju）写 tools/ddj_julie.json：{章: [[[页, x0, y0, x1, y1], …] 每句一组]}。viz2.py 出核对图。

81 章全部对上，74 章误差 ≤4（其余 7 章 6—9，边界可能差一个字）。build.py 的 build_ddj 读 ddj_julie.json 画 rect.hl。
