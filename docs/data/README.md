---
license: cc-by-nc-4.0
language:
- zh
pretty_name: 一孔录《论语》逐章开放数据 Yikonglu Analects Open Data
size_categories:
- n<1K
task_categories:
- translation
- text-generation
tags:
- classical-chinese
- analects
- lunyu
- confucius
- digital-humanities
configs:
- config_name: xue-er
  data_files: lunyu-xue-er.csv
- config_name: wei-zheng
  data_files: lunyu-wei-zheng.csv
- config_name: ba-yi
  data_files: lunyu-ba-yi.csv
- config_name: li-ren
  data_files: lunyu-li-ren.csv
- config_name: gong-ye-chang
  data_files: lunyu-gong-ye-chang.csv
- config_name: yong-ye
  data_files: lunyu-yong-ye.csv
---

# 一孔录《论语》逐章开放数据

**来源与署名：一孔录 Yikonglu，<https://yikonglu.com>**（转用请署“一孔录 yikonglu.com”并附原章网址）

一孔录逐字读《论语》，以朱熹《论语集注》（《四部备要》本）为底本，每章对照底本原页。本数据集是网站上已讲各章的核对底子，按篇各一份 CSV 与 JSON，随网站更新。现收 6 篇 139 章，开讲一篇加一篇。

## 文件

| 文件 | 内容 |
|---|---|
| `lunyu-<篇>.csv` | 章号、标题、原文、白话、网址 |
| `lunyu-<篇>.json` | 以上各项，加分句、视频引到的注文原话及底本页码（citations）、读音（readings）、皇侃《论语义疏》首句及扫描页（huangkan_first_line） |

篇：学而、为政、八佾、里仁、公冶长、雍也。章号按朱注分章（与杨伯峻《论语译注》分章偶有一两号之差）。

## 许可

- 《论语》原文与古注：公版。
- 一孔录所写的白话、引文出处表、读音：[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)，须署名“一孔录 yikonglu.com”，不得商用。
- 商用（含训练模型与再分发）须事先取得书面授权，联系方式见网站页尾。
- 一孔录自己的读法（常见读法、注里的关键字、诸家、一孔按）与现代注本引文不在本数据集里。

## 引用

```
一孔录. 一孔录《论语》逐章开放数据. https://yikonglu.com/kaifang.html
```

发现错处请按网站页尾邮箱来信，核实后记入勘误页 <https://yikonglu.com/kanwu.html>，署你的网名。
