#!/usr/bin/env python3
"""一孔录 yikonglu.com 静态站生成器（多语种）。
输入：读法札记/*.md（只取“片里的读法”，丢“书里可走处”“观众疑问”和待核内容）、
      yuanwen.json（章号→原文）、episodes.json（集名→章号与平台 ID，只列已公开的集）、assets/（横幅、印章）、
      共享盘 数据/网站素材/<期名>/（各期稿：引文取处、读音表；原页 png）、数据/网站勘误.md、
      i18n/<lang>.json（界面与各章译文；缺的章回落到中文并标注）。
语种：zh-Hans（根目录）、zh-Hant（/zh-hant/，OpenCC 自动转台湾用字）、en（/en/）。
用法：python3 tools/build.py <读法札记目录> docs
"""
import json, re, sys, html, os, shutil, datetime, glob, csv, io, contextlib
import og as OG
import gushi as GS
import renwu as RW
import zhuju as ZJ
import shuyuan as SY
import lunyu_extra as LX  # 11-14 只为《论语》做的：年历、场合用句、课本带读
import guanxi as GX  # 11-14 《论语》智器重建本的关系：章页“这一章连着”、关系图页 /guanxi/

DOMAIN = "https://yikonglu.com"
# 图片另放 davidokant/yikonglu-img（Pages：img.yikonglu.com，11-08 主人定）：原页、分享图、故事图建好后挪到图片仓库，页面里改用绝对地址。
# 回退：YK_IMG= （设空）再建站，图片就留在本站 docs 里。建站要有图片仓库的克隆（默认与本仓库同级 ../yikonglu-img），没有就停，免得图片又进本仓库。
IMG = os.environ.get("YK_IMG", "https://img.yikonglu.com").rstrip("/")
IMG_DIR = os.environ.get("YK_IMG_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "yikonglu-img")
IMG_SUBS = ("yuanye/", "og/", "gushi/img/")
HERE = os.path.dirname(os.path.abspath(__file__))
PIAN = {"1": ("学而", "xue-er", "学而第一", 16), "2": ("为政", "wei-zheng", "为政第二", 24),
        "3": ("八佾", "ba-yi", "八佾第三", 26), "4": ("里仁", "li-ren", "里仁第四", 26),
        "5": ("公冶长", "gong-ye-chang", "公冶长第五", 27), "6": ("雍也", "yong-ye", "雍也第六", 28),
        "7": ("述而", "shu-er", "述而第七", 37), "8": ("泰伯", "tai-bo", "泰伯第八", 21),
        "9": ("子罕", "zi-han", "子罕第九", 30), "10": ("乡党", "xiang-dang", "乡党第十", 17),
        "11": ("先进", "xian-jin", "先进第十一", 25), "12": ("颜渊", "yan-yuan", "颜渊第十二", 24),
        "13": ("子路", "zi-lu", "子路第十三", 30), "14": ("宪问", "xian-wen", "宪问第十四", 47),
        "15": ("卫灵公", "wei-ling-gong", "卫灵公第十五", 41), "16": ("季氏", "ji-shi", "季氏第十六", 14),
        "17": ("阳货", "yang-huo", "阳货第十七", 26), "18": ("微子", "wei-zi", "微子第十八", 11),
        "19": ("子张", "zi-zhang", "子张第十九", 25), "20": ("尧曰", "yao-yue", "尧曰第二十", 3)}  # 章数按朱注分章（乡党 17 节）
YW_DIR = os.path.join("/mnt/project-files/一孔学-内-自媒体/数据/网站素材", "_原文")  # 全书原文（朱注分章 498 章）、分章对照、异文表
FIELDS = [("常见读法", "f_common", "常"), ("字眼", "f_keys", "注"), ("诸家", "f_others", "说"), ("片里落点", "f_ours", "读")]
SOURCE = "朱熹《论语集注》（《四部备要》本）"
# 语文课本里的《论语》（统编教材；章号＝朱注分章，11-08 逐章对过 _原文 集注分章原文）。台湾高中论孟选读篇目未核准，先不列
KEBEN = [("chu7", "七年级上册《〈论语〉十二章》", "初中第一次读《论语》：学习、修身、志向。", ["1.1", "1.4", "2.4", "2.11", "2.15", "6.9", "6.18", "7.15", "7.21", "9.16", "9.25", "19.6"]),
         ("bixiu", "高中必修下册《子路、曾皙、冉有、公西华侍坐》", "孔子让四个学生各言其志，最后说“吾与点也”。课本按杨伯峻本是《先进》第 26 章，朱注本是第 25 章。", ["11.25"]),
         ("xuanbi", "高中选择性必修上册《〈论语〉十二章》", "从学而、八佾、里仁、雍也、泰伯、子罕、颜渊、卫灵公、阳货九篇选出，讲仁、礼、义与君子。", ["1.14", "3.3", "4.8", "4.16", "4.17", "6.16", "8.7", "9.18", "9.28", "12.1", "15.23", "17.9"])]
TAGLINE = "逐字读经典原文"
GAO_DIR = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材"  # 各期稿只在共享盘读取，不进公开仓库
GUSHI_DIR = os.environ.get("YK_GUSHI_DIR") or os.path.join(GAO_DIR, "_故事")  # “故事”栏资料；没有人物表就整栏不出
GUSHI_ON = False
RENWU_DIR = os.environ.get("YK_RENWU_DIR") or os.path.join(GAO_DIR, "_人物")  # 论语真实人物表；没有就整栏不出
RENWU_ON = False
BH_DIR = os.path.join(GAO_DIR, "_白话")  # 白话直译：每行“- 1.1：……”，跟各期稿走
ZB_DIR = os.path.join(GAO_DIR, "_注本")  # 注本索引（皇疏、杨伯峻、钱穆逐章 CSV）
HUANG_WK = "https://commons.wikimedia.org/w/index.php?title=File:WUL-ro12_00916_%E8%AB%96%E8%AA%9E%E9%9B%86%E8%A7%A3%E7%BE%A9%E7%96%8F_{ce}.pdf&page={n}"  # 早稻田大学图书馆藏 1750 年和刻本，册2—5
HUANG_SCAN = "https://commons.wikimedia.org/w/index.php?title=File:SSID-13146346_%E7%9F%A5%E4%B8%8D%E8%B6%B3%E9%BD%8B_%E7%AC%AC7%E9%9B%86_%E8%AB%96%E8%AA%9E%E7%BE%A9%E7%96%8F%E6%95%98_%E5%8D%B71-2.pdf&page={n}"
SUPPORT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "support.json"))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "support.json")) else {}
ANALYTICS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics.json"))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics.json")) else {}
KANWU_DEFAULT = "/mnt/project-files/一孔学-内-自媒体/数据/网站勘误.md"
INTERNAL = re.compile(r"（[^（）]*(只|转述|不上屏|不念|常识|核不到|见注|今读)[^（）]*）")

HANT_FIX = {"余力": "餘力", "余，": "餘，", "余者": "餘者", "托看": "託看", "诗云": "詩云", "子云": "子云", "干禄": "干祿"}  # 护住后手工给的繁体
# 繁体转换后再改的经文与人名（OpenCC 按今语词转错的），左为转出的错形，右为底本字形
HANT_POST = [("通道不篤", "信道不篤"), ("相維闢公", "相維辟公"), ("師也闢", "師也辟"), ("趨而闢之", "趨而辟之"), ("甯戚", "寧戚"),
    ("鬱郁", "郁郁"), ("愛之慾其生", "愛之欲其生"), ("惡之慾其死", "惡之欲其死"), ("門人慾厚葬", "門人欲厚葬"), ("無慾速", "無欲速"),
    ("禮雲禮", "禮云禮"), ("禮云禮雲", "禮云禮云"), ("樂雲樂", "樂云樂"), ("禮雲禮雲", "禮云禮云"), ("樂雲樂雲", "樂云樂云"), ("書雲", "書云"), ("不佔而已", "不占而已"), ("先嚐之", "先嘗之"), ("寢不屍", "寢不尸"),
    ("亞飯幹", "亞飯干"), ("難與併為仁", "難與並為仁"), ("可以托六尺", "可以託六尺"), ("不捨晝夜", "不舍晝夜"), ("舊谷既沒", "舊穀既沒"),
    ("新谷既升", "新穀既升"), ("不至於谷", "不至於穀"), ("邦有道，谷", "邦有道，穀"), ("邦無道，谷", "邦無道，穀"), ("必覆命", "必復命"),
    ("寧媚於灶", "寧媚於竈"), ("媚於灶", "媚於竈"), ("冠不以吊", "冠不以弔"), ("不撤姜食", "不撤薑食"), ("李鬱", "李郁")]
HANT_PROTECT = ["范祖禹", "范氏", "游酢", "游氏", "坐如尸", "尸", "咸", "丑", "干禄", "云：", "云，", "子云", "诗云", "余力", "余，", "余者", "托看"]
_HANT_CC = []
def hant_plain(text):  # 经文转繁（与繁体站同一套护字与改字），给分享卡用：卡上经文一律繁体（11-14 主人）
    if not text: return text
    if not _HANT_CC: _HANT_CC.append(__import__("opencc").OpenCC("s2twp"))
    for i, w in enumerate(HANT_PROTECT): text = text.replace(w, f"\ue000{i}\ue001")
    t = _HANT_CC[0].convert(text)
    for i, w in enumerate(HANT_PROTECT): t = t.replace(f"\ue000{i}\ue001", HANT_FIX.get(w, w))
    for a_, b_ in HANT_POST: t = t.replace(a_, b_)
    return t
_HS_RE = [re.compile(r'(<blockquote lang="zh-Hans"[^>]*>)(.*?)(</blockquote>)', re.S), re.compile(r'(<p class="zy" lang="zh-Hans"[^>]*>)(.*?)(</p>)', re.S)]
def hant_scripture(html):  # 外文页上的经文原句用繁体（11-14 主人选“分享卡全用繁体，外文页也改”）：只改原文块（章页原文、首页引句、人物卡经文），白话（span.yi）和注不动
    def _blk(m):
        head = m.group(1).replace('lang="zh-Hans"', 'lang="zh-Hant"')
        head = re.sub(r'data-reads="([^"]*)"', lambda a: 'data-reads="' + hant_plain(a.group(1)) + '"', head)
        out, skip = [], 0
        for x in re.split(r"(<[^>]+>)", m.group(2)):
            if x.startswith("<"):
                if skip: skip += 1 if (x.startswith("<span") and not x.endswith("/>")) else -1 if x == "</span>" else 0
                elif x.startswith('<span class="yi"'): skip = 1
                out.append(x)
            else: out.append(x if skip else hant_plain(x))
        return head + "".join(out) + m.group(3)
    for R in _HS_RE: html = R.sub(_blk, html)
    return html
LANGS = {  # code: (路径前缀, 自称, hreflang)
    "zh-Hans": ("", "简体中文", "zh-Hans"),
    "zh-Hant": ("zh-hant/", "繁體中文", "zh-Hant"),
    "en": ("en/", "English", "en"),
    "ja": ("ja/", "日本語", "ja"),
    "ko": ("ko/", "한국어", "ko"),
    "fr": ("fr/", "Français", "fr"),
    "es": ("es/", "Español", "es"),
    "de": ("de/", "Deutsch", "de"),
    "vi": ("vi/", "Tiếng Việt", "vi"),
    "id": ("id/", "Bahasa Indonesia", "id"),
    "ru": ("ru/", "Русский", "ru"),
}
for _k in [k for k in LANGS if not k.startswith("zh")]:  # 译文文件还没有的语种先不出页、不进互指
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", _k + ".json")): del LANGS[_k]

ZH_UI = {
 "tagline": TAGLINE, "nav_books": "书架", "nav_search": "检索", "nav_errata": "勘误", "nav_about": "关于",
 "motto": "一孔录讲过的每一句，都能在这里核。",
 "intro": "原文、底本页码、注家原话、读音、我们的读法、公开勘误，按书按章排好。视频在各平台看，核对来这里。",
 "search_ph": "搜原文、注家原话，如：鸟数飞", "btn_books": "按书目找", "btn_errata": "看勘误",
 "p1t": "底本可查", "p1": "原文和注都据各家底本原页，每条引文标出底本页，原页图可放大看。",
 "p2t": "注家原话", "p2": "引到谁就写谁，朱熹、程子、谢氏分开标；转述和原话分开，核不到出处的不放。",
 "p3t": "勘误公开", "p3": "讲错的地方改了就记：哪集哪句、原来怎么说、改成什么、依据是什么。",
 "books": "书架", "recent": "最近收录", "lunyu": "论语", "lunyu_sub": "二十篇 · 持续更新",
 "by_chapter": f"按篇按章排。底本：{SOURCE}。",
 "book_lead": "每章有原文、注里的关键字、诸家说法和一孔录的读法，附视频。", "covered": "已讲 {done} / {total} 章",
 "f_common": "常见的理解", "f_keys": "注里的关键字", "f_others": "诸家怎么说", "f_ours": "一孔录这样读",
 "cites": "本章引文逐条核对", "cites_note": "视频里引到的每一句注：原话、出自谁、在底本哪一页。标“转述”的是我们概括的意思，不是原话。",
 "th_quote": "引文原话", "th_src": "出自", "th_page": "底本页", "para": "转述", "pg": "原页 {n}", "other_ed": "另本",
 "reads": "读音", "th_zi": "字", "th_pos": "位置", "th_du": "读", "shots": "底本原页",
 "kw": "本章勘误", "kw_note": "", "cite": "引用本页", "copy": "复制", "copied": "已复制",
 "checked": "本页最后核对：{d}。改动记在", "errata_page": "勘误页",
 "video": "看这一章的视频", "wj_vid": "这一章的视频正在制作，上线后就放在这里。先关注一孔录，出片第一时间看到：", "ddj_lead": "王弼本八十一章：道经第 1—37 章，德经第 38—81 章。视频还在制作，网站先放原文、原页、白话和注，开讲后逐章补全。", "bk_prog_wj": "原文全 · 视频制作中", "wj_pane": "原页", "video_in": "这一章在一孔录《{ep}》里讲：", "cn_note": "（大陆请点哔哩哔哩）",
 "prev": "上一章", "next": "下一章", "chapter_no": "{book} · 第 {n} 章", "book_no": "《论语》第 {n} 篇 · 已讲 {done} / {total} 章",
 "source_line": f"原文与注据{SOURCE}", "rendering": "",
 "errata_title": "公开勘误", "errata_sub": "原文·引文·出处·读音·读法",
 "errata_p1": "一孔录讲错或说满的地方，改了就记在这里，按时间倒排，旧记录不删。画面上的小问题不记，只记内容。",
 "errata_p2": "发现错误，请写邮件到下面这个邮箱，写明哪集哪句、依据是什么，再写上你想署的网名。核实后记入此页，勘误者一栏署你的网名。也可以在任一平台「一孔录」视频下留言。", "mail_note": "邮箱做成了图片防垃圾邮件，请手动输入。", "report": "本章有错？写信告诉我们，核实后署你的网名记入勘误：", "errata_empty": "目前没有勘误。",
 "search_title": "检索", "search_sub": "原文 · 注家原话 · 读法", "search_ph2": "输入几个字，如：鸟数飞、主一无适、孝弟",
 "search_n": "找到 {n} 章", "search_none": "没有找到。未讲各章只收原文和白话。",
 "about_def": "一孔录（Yikonglu）是一个逐字逐章讲读中国经典原文的中文项目，2026 年起以视频、播客和本网站逐章讲读《论语》；原文与注据朱熹《论语集注》（《四部备要》本），每条引文标出底本页码，原页可查；一孔录自己的读法称“一孔按”。独立编纂，无机构或基金资助。", "about_title": "关于一孔录", "about_p": "一孔录是一个逐字逐章读中国经典原文的频道，用讲书动画和几位固定的人物，把一句原文落到具体的人和处境上。默认你没读过原书，也不用看过前几期。",
 "about_h1": "这个网站做什么", "about_site": "平台上的视频面向大众，这里面向想核对的人：一孔录讲过的每一句，原文、底本页码、注家原话、读音、我们的读法，都能在这里查到，讲错的地方在<a href=\"kanwu.html\">勘误页</a>公开记录。",
 "about_h2": "我们的承诺", "about_c1": "原文和注家的话都据各家底本原页，页面写明底本。", "about_c2": "先讲注家怎么说，再讲我们怎么读；我们自己的看法明说是一孔录的读法，不冒充古人。", "about_c3": "核不到出处的话不放。发现错误请告诉我们，勘误公开。",
 "about_h3": "在哪里看", "about_where": "YouTube、哔哩哔哩、视频号「一孔录」，播客「一孔录」（Spotify、Apple 播客、小宇宙、喜马拉雅），公众号「一孔录」。",
 "follow_h": "关注一孔录，轻松读经典", "follow_wx": "有问题想问一孔录？关注公众号「一孔录」留言，每周选答，进片署你的网名。", "follow_yt": "在 YouTube 订阅", "foot_src": "引文据各家底本原页，各页注明底本。发现错误请告诉我们，勘误公开。", "foot_where": "YouTube · 哔哩哔哩 · 视频号 · 公众号 · 播客：搜「一孔录」",
 "lang_bar": "", "lang_go": "", "lang_close": "", "translated_note": "",
 "cite_fmt": "一孔录《论语·{book}》{c}“{title}”，{url}，{d} 版。",
 "hant_note": "繁體頁面由簡體自動轉換，用字按台灣習慣；原文以底本原頁為準。",
}

# 11-03 第一批新增界面字（各语种；缺的回落简体）
EXTRA_UI = {
 "zh-Hans": {"db_k_cj": "《论语》智器重建本", "db_k_cj_who": "想把整部《论语》连起来读的人：这一章连着哪几章，同一个问题孔子怎样答不同的人。", "db_k_cj_how": "《论语》智器重建本：498 章、931 条关系、条条对得上原页，免费、可转载（署名即可）。手机上看，点章号就跳过去；也可以打印。", "db_cj": "《论语》智器重建本", "db_cj_meta": "498 章 · 292 页 · 约 12 MB", "db_link": "免费读本", "db_title": "免费读本", "db_k_adult": "成人逐字读本", "db_k_adult_who": "想自己读懂原文的成年人，从头读或者查某一章都行。", "db_k_adult_how": "每篇一本，原文、读音、朱注读法、白话、一孔按、注家原页都在里面。可以配着视频一章一章读，也可以打印出来，一天读一章。", "db_k_kids": "亲子讲读本", "db_k_kids_who": "十岁以前孩子的家长，主要是父亲。", "db_k_kids_how": "每周一讲，一年读完。父亲每周讲一堂，三十到四十分钟：讲典故、讲道理、答孩子的问题；平日跟读交给孩子自己，或家人陪读。每讲附孩子填的学习单和生字栏。", "db_szj": "《三字经》父亲讲义", "db_szj_meta": "六卷三十九讲 · 137 页 · 约 13 MB", "db_who": "给谁：", "db_how": "怎么用：", "db_xueer_full": "《论语》学而篇", "db_sub": "免费 PDF，能在手机上看，也能打印", "db_p": "一孔录的读本永远免费。最新一本是《论语》智器重建本，全书 498 章连成一张网，另有英文、日文版；还有家长带孩子用的亲子讲读本。每种都写明给谁用、怎么用。", "db_xueer": "学而篇", "db_meta": "十六章 · 60 页 · 约 6 MB", "db_hans": "简体版", "db_hant": "繁體版", "db_note": "发现错处请告诉我们，勘误公开，署你的网名。", "db_wx": "国内读者也可以在公众号「一孔录」回复“读本”领取链接。", "zt_sub": "按一个字、一个概念读各书", "zt_p": "每个专题按书分段，列出原文里说到它的各章：已讲的章带一孔录的读法，没讲的标“未讲”，只放原文。", "zt_all": "《{b}》全部章节", "zt_routes": "跟着一个人读", "zt_routes_p": "跟着一孔录原创角色，按一个问题读：每条路线串起几章，导语是角色说的，读法以章节页为准。", "zt_nb": "{n} 本书 · {m} 章", "zt_n": "已收 {n} 章", "gzi": "子部", "gmeng": "蒙学", "bk_sanzijing": "三字经", "bk_sub_sanzijing": "三字一句", "gshi": "史部", "gbing": "兵家", "bk_tanjing": "六祖坛经", "bk_shiji": "史记", "bk_zizhi": "资治通鉴", "bk_sunzi": "孙子兵法", "bk_sub_tanjing": "十品", "bk_liezi": "列子", "bk_sub_liezi": "八篇", "bk_huainanzi": "淮南子", "bk_sub_huainanzi": "二十一篇", "bk_yinfujing": "黄帝阴符经", "bk_sub_yinfujing": "三四百字", "bk_qingjingjing": "清静经", "bk_sub_qingjingjing": "约四百字", "bk_baopuzi": "抱朴子", "bk_sub_baopuzi": "内篇二十卷", "bk_ganyingpian": "太上感应篇", "bk_sub_ganyingpian": "约一千二百字", "bk_jingang": "金刚经", "bk_sub_jingang": "三十二分", "bk_sishierzhang": "四十二章经", "bk_sub_sishierzhang": "四十二章", "bk_baiyu": "百喻经", "bk_sub_baiyu": "九十八喻", "bk_weimojie": "维摩诘经", "bk_sub_weimojie": "十四品", "bk_fahua": "法华经", "bk_sub_fahua": "二十八品", "bk_amituo": "阿弥陀经", "bk_sub_amituo": "一卷", "bk_dizang": "地藏经", "bk_sub_dizang": "十三品", "bk_lengyan": "楞严经", "bk_sub_lengyan": "十卷", "bk_guoyu": "国语", "bk_sub_guoyu": "二十一卷", "bk_zhanguoce": "战国策", "bk_sub_zhanguoce": "三十三篇", "bk_hanshu": "汉书", "bk_sub_hanshu": "一百篇", "bk_houhanshu": "后汉书", "bk_sub_houhanshu": "一百二十卷", "bk_sanguozhi": "三国志", "bk_sub_sanguozhi": "六十五卷", "bk_zhenguan": "贞观政要", "bk_sub_zhenguan": "十卷", "bk_xunzi": "荀子", "bk_sub_xunzi": "三十二篇", "bk_jinsilu": "近思录", "bk_sub_jinsilu": "十四卷", "bk_hanfeizi": "韩非子", "bk_sub_hanfeizi": "五十五篇", "bk_mozi": "墨子", "bk_sub_mozi": "五十三篇", "bk_lvshi": "吕氏春秋", "bk_sub_lvshi": "二十六卷", "bk_yanshi": "颜氏家训", "bk_sub_yanshi": "二十篇", "bk_shishuo": "世说新语", "bk_sub_shishuo": "三十六门", "bk_caigentan": "菜根谭", "bk_sub_caigentan": "三百多则", "bk_sub_shiji": "一百三十卷", "bk_sub_zizhi": "二百九十四卷", "bk_sub_sunzi": "十三篇", "g13": "十三经", "gdao": "道家", "gfo": "佛典", "bk_sub_daxue": "《礼记》篇 · 四书之一", "bk_sub_zhongyong": "《礼记》篇 · 四书之一", "grp_main": "主线", "grp_13": "十三经", "grp_13_p": "《周易》《论语》《孟子》见上。", "bk_shijing": "诗经", "bk_shangshu": "尚书", "bk_zhouli": "周礼", "bk_yili": "仪礼", "bk_liji": "礼记", "bk_zuozhuan": "春秋左传", "bk_gongyang": "春秋公羊传", "bk_guliang": "春秋谷梁传", "bk_xiaojing": "孝经", "bk_erya": "尔雅", "bk_sub_shijing": "三百〇五篇", "bk_sub_shangshu": "五十八篇", "bk_sub_zhouli": "六官", "bk_sub_yili": "十七篇", "bk_sub_liji": "四十九篇", "bk_sub_zuozhuan": "编年二百五十五年", "bk_sub_gongyang": "春秋三传之一", "bk_sub_guliang": "春秋三传之一", "bk_sub_xiaojing": "十八章", "bk_sub_erya": "十九篇", "shumu_title": "书架", "shumu_sub": "一生一本《论语》，其余放在书架上", "shumu_p": "一本一本读，逐字读原文。", "soon": "筹备中", "soon_line": "《道德经》等 {n} 部筹备中 · 完整书目 ›", "bk_prog": "已讲 {done} / {total} 章", "bk_lunyu": "论语", "bk_daodejing": "道德经", "bk_xinjing": "心经", "bk_zhouyi": "周易", "bk_zhuangzi": "庄子", "bk_mengzi": "孟子", "bk_chuanxilu": "传习录", "bk_daxue": "大学", "bk_zhongyong": "中庸", "bk_sub_lunyu": "二十篇 · 朱熹集注本", "bk_sub_daodejing": "八十一章", "bk_sub_xinjing": "二百六十字", "bk_sub_zhouyi": "六十四卦与易传", "bk_sub_zhuangzi": "内七篇与名篇", "bk_sub_mengzi": "七篇十四卷", "bk_sub_chuanxilu": "王阳明语录", "off_t": "离线", "off_h": "现在没有网络", "off_p": "看过的页面已经存在这台设备上，离线也能打开。下面是存着的章节；有网后自动更新。", "off_none": "还没有存下的章节。联网时打开几章，下次离线就能看。", "off_home": "回首页", "zb_huang_meta2": "梁 · 1750 年日本和刻本 · 卷{j}", "zb_scan2": "和刻本扫描 第 {ce} 册第 {n} 页", "wj": "未讲", "wj_tag": "未讲", "wj_lead": "这一章的视频还在制作。网站先放原文、原页、白话和注，视频上线后补全讲解。", "wj_bh_note": "白话为初稿，按朱注直译；开讲时再核。", "wj_src": "原文据{src}，底本第 {n} 页。", "wj_yang": "杨伯峻《论语译注》分章作 {y}。", "yiwen": "异文", "yiwen_note": "底本与通行本用字不同处，原文照底本。", "th_di": "底本", "th_tong": "通行本", "th_shuo": "说明", "toc_wj": "未讲", "wj_title": "{head}｜原文与白话｜论语·{book} {c}｜一孔录", "foot_org": "一孔录 · 独立编纂，无机构或基金资助", "nav_topics": "专题", "nav_more": "更多", "grp_read": "读", "grp_check": "核", "grp_use": "用", "tools_h": "查与用", "t_zt": "按仁、孝、礼等十个字读全书", "t_zi": "配音照读的每个字音", "t_bb": "每家注本用的哪个本子", "t_dt": "按篇下载，CC BY 4.0", "zc_usdt": "加密货币（USDT）", "zc_usdt_net": "网络：{n}。只能用这个网络转 USDT，转错网络或别的币会丢失，无法找回。", "zc_link": "支持一孔录", "zc_title": "支持一孔录", "zc_sub": "内容全部免费，自愿赞助", "zc_p": "一孔录的原文、注、读法、勘误和开放数据永远免费，不会因为赞助多少而锁住任何一页。如果这里帮到了你，可以请我们喝杯茶，钱用在底本、扫描和配音上。", "zc_kofi": "海外读者：在 Ko-fi 赞助", "zc_wx": "国内读者：在公众号「一孔录」任一篇原创文章末尾点“赞赏”。", "zc_soon": "海外赞助页即将开通。", "cp_entry": "复制此条（带出处）", "cp_link": "复制此条链接", "bb_link": "版本说明", "hj_h": "本句互见", "hj_zb": "本章各家注", "hj_cites": "引文逐条核对", "hj_video": "视频里讲本章：{t} 起", "hj_book": "本书互见", "hj_other": "他书出处", "hj_note": "注", "bb_title": "版本与许可", "bb_sub": "每家注本用的哪个本子、页码怎么算、能不能转用", "bb_p": "一孔录引到的每一家注，都在这里说明底本、影像来源、页码算法和许可。章节页每条注旁的“版本说明”链到这里。", "bb_base": "底本", "bb_img": "影像来源", "bb_page": "页码", "bb_lic": "许可", "bb_use": "本站怎么用", "zt_title": "专题", "zt_link": "专题", "zt_none": "已讲章节里还没有。", "dt_title": "开放数据", "dt_sub": "按篇下载原文、白话、引文出处与读音", "dt_p": "本站数据按篇出 JSON 和 CSV，随网站每周更新。原文与古注是公版，照公版使用；一孔录写的白话、一孔按、引文出处表、读音表等文字，按 CC BY 4.0 许可：可以转载、改编，也可以商用，只须署名“一孔录 yikonglu.com”并附原页链接。数据包里暂时只有核对用的内容；现代注本（杨伯峻、钱穆）的引文不在许可内。", "dt_file": "文件", "dt_rows": "章数", "dt_lic": "许可：CC BY 4.0（公版部分照公版）", "dt_link": "开放数据", "feed": "订阅更新（RSS）", "zi_title": "读音索引", "zi_sub": "各章配音照读的字音", "zi_p": "一孔录配音时照这里的读音读。点章号看那一章。", "th_ch": "章", "zi_link": "读音索引", "ju_reads": "本句读音：", "kw_stats": "已记 {n} 处勘误（{cats}），其中读者指出 {m} 处。", "thanks_h": "致谢", "thanks_p": "以下读者指出过一孔录的错误，按首次来信先后排：", "thanks_none": "还没有读者来信勘误。第一位指出错误的读者，网名会记在这里。", "baihua": "白话", "baihua_note": "按一孔录的读法直译，和视频一致；别家读法见下。", "ju_copy": "复制本句（带出处）", "ju_link": "复制本句链接", "ju_tip": "点原文任一句，可复制带出处的引文。",
   "zb_h": "各家注本", "zb_note": "本站底本是朱熹《论语集注》，见上文。这里并列别家：古注录疏文第一句，附原刻本扫描页；现代注本只短引一句译文，作通行读法对照。“与朱注异同”是一孔录写的说明，不是注本原文。",
   "zb_huang": "皇侃《论语义疏》", "zb_huang_meta": "梁 · 知不足斋丛书本 · 卷{j}", "zb_scan": "原刻本扫描第 {n} 页",
   "zb_yang": "杨伯峻《论语译注》", "zb_yang_meta": "中华书局 · 现代通行本，短引", "zb_qian": "钱穆《论语新解》", "zb_qian_meta": "现代通行本，短引",
   "zb_diff": "与朱注异同", "th_zb": "注本", "th_key": "关键处", "th_kind": "异同", "th_say": "说明",
   "th_sure": "把握", "s_ding": "定", "s_wen": "较稳", "s_yi": "存疑", "k_same": "同解", "k_diff": "异读", "k_add": "补充", "k_shade": "轻重不同", "k_word": "字义不同",
   "nf_h": "这一页不在了", "nf_p": "链接可能拼错，或这一页改过地址。可以搜原文，或按书目找。"},
 "en": {"about_def": "Yikonglu (一孔录) is a Chinese-language project that reads the Chinese classics word by word and chapter by chapter. Since 2026 it has been working through the Analects in videos, podcasts and this website; the text and commentary follow Zhu Xi's Collected Commentaries on the Analects (Sibu Beiyao edition), with every citation keyed to a page of the base edition. Its own reading is labelled “一孔按” (Yikonglu's reading). Independently compiled, with no institutional or foundation funding.", "db_k_cj": "The Analects, Rebuilt with AI", "db_k_cj_who": "Readers who want the whole Analects as one connected book: which chapters link to which, and how Confucius answered the same question for different people.", "db_k_cj_how": "Free · 498 chapters · 931 connections between chapters, people, books and occasions, each checked against the page · CC BY 4.0. Chapter numbers are clickable; it also prints.", "db_cj": "The Analects, Rebuilt with AI", "db_cj_meta": "498 chapters · 345 pages · about 9 MB · English (Chinese editions too)", "db_link": "Free reader (PDF)", "db_title": "Free readers", "db_k_adult": "Word-by-word readers (adults)", "db_k_adult_who": "Adults who want to read the original text themselves.", "db_k_adult_how": "One PDF per book: original, pronunciations, Zhu Xi\u2019s reading, plain Chinese, our notes and facsimile pages. Read along with the videos, or print it and read a chapter a day.", "db_k_kids": "Parent-and-child readers", "db_k_kids_who": "Parents of children under ten, especially fathers.", "db_k_kids_how": "One lesson a week for a year: a 30–40 minute talk with stories, reasons and the child\u2019s questions; daily recitation with the child. Each lesson has a worksheet with new characters.", "db_szj": "Three-Character Classic · a father\u2019s handbook", "db_szj_meta": "6 parts, 39 lessons · A4 · Chinese", "db_who": "For: ", "db_how": "How to use: ", "db_xueer_full": "Analects · Xue Er", "db_sub": "Free PDFs, readable on a phone and printable", "db_p": "Our readers are always free. The newest is The Analects, Rebuilt with AI: all 498 chapters as one connected book, in English, Japanese and Chinese. There is also a parent-and-child reader in Chinese. Each says who it is for and how to use it.", "db_xueer": "Book 1 · Xue Er", "db_meta": "16 chapters · 60 pages · about 6 MB", "db_hans": "Simplified Chinese", "db_hant": "Traditional Chinese", "db_note": "Some readers are in Chinese only. If you find a mistake, please tell us; corrections are public and credited.", "db_wx": "", "zt_sub": "Read across the books by one word or idea", "zt_p": "Each topic is divided by book and lists the chapters whose original text mentions it: chapters we have covered include our reading; others show the original only.", "zt_all": "All chapters of {b}", "zt_routes": "Routes", "zt_routes_p": "Follow one of our characters through one question.", "zt_nb": "{n} books · {m} chapters", "gzi": "Masters (zibu)", "gmeng": "Primers", "bk_sanzijing": "Three-Character Classic", "bk_sub_sanzijing": "Three characters a line", "gshi": "Histories", "gbing": "Military", "bk_tanjing": "Platform Sutra", "bk_shiji": "Records of the Grand Historian", "bk_zizhi": "Zizhi Tongjian", "bk_sunzi": "The Art of War", "bk_sub_tanjing": "10 chapters", "bk_liezi": "Liezi", "bk_sub_liezi": "8 books", "bk_huainanzi": "Huainanzi", "bk_sub_huainanzi": "21 chapters", "bk_yinfujing": "Yinfu Jing", "bk_sub_yinfujing": "about 400 characters", "bk_qingjingjing": "Qingjing Jing", "bk_sub_qingjingjing": "about 400 characters", "bk_baopuzi": "Baopuzi", "bk_sub_baopuzi": "Inner Chapters, 20 scrolls", "bk_ganyingpian": "Treatise on Response and Retribution", "bk_sub_ganyingpian": "about 1,200 characters", "bk_jingang": "Diamond Sutra", "bk_sub_jingang": "32 sections", "bk_sishierzhang": "Sutra in Forty-two Sections", "bk_sub_sishierzhang": "42 sections", "bk_baiyu": "Sutra of a Hundred Parables", "bk_sub_baiyu": "98 parables", "bk_weimojie": "Vimalakirti Sutra", "bk_sub_weimojie": "14 chapters", "bk_fahua": "Lotus Sutra", "bk_sub_fahua": "28 chapters", "bk_amituo": "Amitabha Sutra", "bk_sub_amituo": "1 scroll", "bk_dizang": "Ksitigarbha Sutra", "bk_sub_dizang": "13 chapters", "bk_lengyan": "Shurangama Sutra", "bk_sub_lengyan": "10 scrolls", "bk_guoyu": "Discourses of the States", "bk_sub_guoyu": "21 scrolls", "bk_zhanguoce": "Strategies of the Warring States", "bk_sub_zhanguoce": "33 books", "bk_hanshu": "Book of Han", "bk_sub_hanshu": "100 chapters", "bk_houhanshu": "Book of the Later Han", "bk_sub_houhanshu": "120 scrolls", "bk_sanguozhi": "Records of the Three Kingdoms", "bk_sub_sanguozhi": "65 scrolls", "bk_zhenguan": "Essentials of Governance of the Zhenguan Era", "bk_sub_zhenguan": "10 scrolls", "bk_xunzi": "Xunzi", "bk_sub_xunzi": "32 chapters", "bk_jinsilu": "Reflections on Things at Hand", "bk_sub_jinsilu": "14 scrolls", "bk_hanfeizi": "Han Feizi", "bk_sub_hanfeizi": "55 chapters", "bk_mozi": "Mozi", "bk_sub_mozi": "53 chapters", "bk_lvshi": "Annals of Lü Buwei", "bk_sub_lvshi": "26 scrolls", "bk_yanshi": "Family Instructions of the Yan Clan", "bk_sub_yanshi": "20 chapters", "bk_shishuo": "A New Account of the Tales of the World", "bk_sub_shishuo": "36 sections", "bk_caigentan": "Vegetable Roots Discourse", "bk_sub_caigentan": "300+ maxims", "bk_sub_shiji": "130 scrolls", "bk_sub_zizhi": "294 scrolls", "bk_sub_sunzi": "13 chapters", "g13": "The Thirteen Classics", "gdao": "Daoist", "gfo": "Buddhist", "bk_sub_daxue": "A Liji chapter · one of the Four Books", "bk_sub_zhongyong": "A Liji chapter · one of the Four Books", "grp_main": "Main line", "grp_13": "The Thirteen Classics", "grp_13_p": "The Changes, the Analects and Mencius are listed above.", "bk_shijing": "Book of Odes", "bk_shangshu": "Book of Documents", "bk_zhouli": "Rites of Zhou", "bk_yili": "Ceremonies and Rites", "bk_liji": "Book of Rites", "bk_zuozhuan": "Zuo Tradition", "bk_gongyang": "Gongyang Commentary", "bk_guliang": "Guliang Commentary", "bk_xiaojing": "Classic of Filial Piety", "bk_erya": "Erya", "bk_sub_shijing": "305 poems", "bk_sub_shangshu": "58 chapters", "bk_sub_zhouli": "Six offices", "bk_sub_yili": "17 chapters", "bk_sub_liji": "49 chapters", "bk_sub_zuozhuan": "Annals of 255 years", "bk_sub_gongyang": "Commentary on the Spring and Autumn", "bk_sub_guliang": "Commentary on the Spring and Autumn", "bk_sub_xiaojing": "18 chapters", "bk_sub_erya": "19 chapters", "shumu_title": "Books", "shumu_sub": "Reading the classics word by word", "shumu_p": "One book at a time, word by word.", "soon": "coming", "soon_line": "Daodejing and {n} more in preparation · full list ›", "bk_prog": "{done} / {total} chapters", "bk_lunyu": "The Analects", "bk_daodejing": "Daodejing", "bk_xinjing": "Heart Sutra", "bk_zhouyi": "Book of Changes", "bk_zhuangzi": "Zhuangzi", "bk_mengzi": "Mencius", "bk_chuanxilu": "Chuanxilu (Wang Yangming)", "bk_daxue": "Great Learning", "bk_zhongyong": "Doctrine of the Mean", "bk_sub_lunyu": "20 books · Zhu Xi's edition", "bk_sub_daodejing": "81 chapters", "bk_sub_xinjing": "260 characters", "bk_sub_zhouyi": "64 hexagrams and the Ten Wings", "bk_sub_zhuangzi": "Inner chapters and selections", "bk_sub_mengzi": "7 books", "bk_sub_chuanxilu": "Recorded sayings", "off_t": "Offline", "off_h": "You are offline", "off_p": "Pages you have visited are saved on this device and open offline. Saved chapters are listed below; they update when you are back online.", "off_none": "No chapters saved yet. Open a few while online and they will be here next time.", "off_home": "Home", "zb_huang_meta2": "Liang dynasty · 1750 Japanese woodblock edition · juan {j}", "zb_scan2": "woodblock scan vol. {ce} p. {n}", "toc_wj": "not yet covered", "yiwen": "Textual variants", "yiwen_note": "Where the base edition differs from the common text; the original follows the base edition.", "th_di": "Base edition", "th_tong": "Common text", "th_shuo": "Note", "foot_org": "Yikonglu (一孔录) · independently compiled, with no institutional or foundation funding", "nav_topics": "Topics", "nav_more": "More", "grp_read": "Read", "grp_check": "Check", "grp_use": "Use", "tools_h": "Tools", "t_zt": "Ten key words across the book", "t_zi": "Every reading our narration follows", "t_bb": "Which edition each commentary uses", "t_dt": "Download by book, CC BY 4.0", "zc_usdt": "Crypto (USDT)", "zc_usdt_net": "Network: {n}. Send USDT on this network only; other networks or tokens will be lost and cannot be recovered.", "zc_link": "Support us", "zc_title": "Support Yikonglu", "zc_sub": "Everything stays free; support is voluntary", "zc_p": "The text, commentaries, readings, corrections and open data on this site will always be free; no page will ever be locked behind support. If this site helps you, you can buy us a tea — it pays for editions, scans and narration.", "zc_kofi": "Support on Ko-fi", "zc_wx": "Readers in mainland China: use “appreciate” at the end of any original article on our WeChat account “一孔录”.", "zc_soon": "Our Ko-fi page is coming soon.", "cp_entry": "Copy with source", "cp_link": "Copy link", "bb_link": "About this edition", "hj_h": "Cross-references", "hj_zb": "Commentaries on this chapter", "hj_cites": "Citation check", "hj_video": "In the video from {t}", "hj_book": "Elsewhere in the Analects", "hj_other": "Other sources", "hj_note": "Commentary", "bb_title": "Editions & licenses", "bb_sub": "Which edition each commentary comes from, how pages are counted, and how it may be reused", "bb_p": "For every commentary we cite, this page states the base edition, image source, page numbering and license. The “about this edition” links on chapter pages lead here.", "bb_base": "Base edition", "bb_img": "Images", "bb_page": "Pages", "bb_lic": "License", "bb_use": "How we use it", "zt_title": "Topics", "zt_n": "{n} chapters", "zt_link": "Topics", "zt_none": "None among covered chapters yet.", "dt_title": "Open data", "dt_sub": "Download text, plain renderings, citation sources and pronunciations by book", "dt_p": "Data is published per book as JSON and CSV and updated weekly. The original text and old commentaries are public domain. Plain renderings, our readings, citation tables and pronunciation tables are licensed CC BY 4.0: credit “一孔录 Yikonglu yikonglu.com” with a link; commercial use is allowed. Quotations from modern commentaries are not covered.", "dt_file": "File", "dt_rows": "Chapters", "dt_lic": "License: CC BY 4.0 (public-domain parts remain public domain)", "dt_link": "Open data", "feed": "Subscribe (RSS)", "zi_title": "Pronunciation index", "zi_sub": "Readings used in our narration", "zi_p": "These are the readings our narration follows. Click a chapter number to open it.", "th_ch": "Chapter", "zi_link": "Pronunciation index", "ju_reads": "Readings: ", "kw_stats": "{n} corrections recorded ({cats}); {m} reported by readers.", "thanks_h": "Thanks", "thanks_p": "These readers have pointed out our mistakes, in order of first report:", "thanks_none": "No reader corrections yet. The first reader to catch a mistake will be credited here.", "baihua": "Plain Chinese", "baihua_note": "A plain modern-Chinese rendering following Yikonglu's reading.", "ju_copy": "Copy this line with source", "ju_link": "Copy link to this line", "ju_tip": "Tap any sentence of the original to copy it with its source.",
   "zb_h": "Other commentaries", "zb_note": "Our base text is Zhu Xi's Collected Commentaries (above). Here are other commentaries side by side: for old commentaries, the first line of the sub-commentary with a link to the woodblock scan; for modern editions, one short quoted translation for comparison. The “compared with Zhu Xi” notes are written by Yikonglu, not quoted.",
   "zb_huang_meta": "Liang dynasty · Zhibuzu Zhai edition · juan {j}", "zb_scan": "woodblock scan p. {n}", "zb_yang_meta": "Zhonghua Book Co. · modern, short quote", "zb_qian_meta": "modern, short quote",
   "zb_diff": "Compared with Zhu Xi", "th_zb": "Commentary", "th_key": "Point", "th_kind": "Relation", "th_say": "Note",
   "th_sure": "Confidence", "s_ding": "settled", "s_wen": "fairly sure", "s_yi": "uncertain", "k_same": "same", "k_diff": "differs", "k_add": "adds", "k_shade": "nuance", "k_word": "word sense",
   "nf_h": "Page not found", "nf_p": "The link may be mistyped or the page has moved. Search the original text or browse by book."},
 "ja": {"db_k_cj": "『論語』AI再構築版", "db_k_cj_who": "『論語』を一冊のつながった本として読みたい人へ。この章がどの章とつながるか、同じ問いに孔子が相手ごとにどう答えたか。", "db_k_cj_how": "無料・全498章・章・人物・書物・場面をつなぐ931本のつながり、すべて原本の頁で確認・CC BY 4.0。章番号はタップで飛べます。印刷もできます。", "db_cj": "『論語』AI再構築版", "db_cj_meta": "全498章・311頁・約12 MB・日本語（中国語版もあり）", "about_def": "一孔録（Yikonglu）は、中国古典の原文を一字一章ずつ読む中国語のプロジェクトです。2026 年から動画・ポッドキャスト・本サイトで『論語』を章ごとに講読しています。原文と注は朱熹『論語集注』（四部備要本）に拠り、引用にはすべて底本の頁を示します。一孔録自身の読みは「一孔按」と記します。独立編纂で、機関や基金の助成は受けていません。", "zt_sub": "一つの字・概念で各書を読む", "zt_p": "専題は書ごとに分け、原文にその語が出る章を列挙します。既講の章は一孔録の読みつき、未講の章は原文のみ。", "zt_all": "『{b}』全章", "zt_routes": "ルート", "zt_routes_p": "作中の人物とともに、一つの問いで読む。", "zt_nb": "{n}書 · {m}章", "gzi": "子部", "gmeng": "蒙学", "bk_sanzijing": "三字経", "bk_sub_sanzijing": "三字一句", "gshi": "史部", "gbing": "兵家", "bk_tanjing": "六祖壇経", "bk_shiji": "史記", "bk_zizhi": "資治通鑑", "bk_sunzi": "孫子", "bk_sub_tanjing": "十品", "bk_liezi": "列子", "bk_sub_liezi": "八篇", "bk_huainanzi": "淮南子", "bk_sub_huainanzi": "二十一篇", "bk_yinfujing": "黄帝陰符経", "bk_sub_yinfujing": "三、四百字", "bk_qingjingjing": "清静経", "bk_sub_qingjingjing": "約四百字", "bk_baopuzi": "抱朴子", "bk_sub_baopuzi": "内篇二十巻", "bk_ganyingpian": "太上感応篇", "bk_sub_ganyingpian": "約千二百字", "bk_jingang": "金剛経", "bk_sub_jingang": "三十二分", "bk_sishierzhang": "四十二章経", "bk_sub_sishierzhang": "四十二章", "bk_baiyu": "百喩経", "bk_sub_baiyu": "九十八喩", "bk_weimojie": "維摩経", "bk_sub_weimojie": "十四品", "bk_fahua": "法華経", "bk_sub_fahua": "二十八品", "bk_amituo": "阿弥陀経", "bk_sub_amituo": "一巻", "bk_dizang": "地蔵経", "bk_sub_dizang": "十三品", "bk_lengyan": "楞厳経", "bk_sub_lengyan": "十巻", "bk_guoyu": "国語", "bk_sub_guoyu": "二十一巻", "bk_zhanguoce": "戦国策", "bk_sub_zhanguoce": "三十三篇", "bk_hanshu": "漢書", "bk_sub_hanshu": "百篇", "bk_houhanshu": "後漢書", "bk_sub_houhanshu": "百二十巻", "bk_sanguozhi": "三国志", "bk_sub_sanguozhi": "六十五巻", "bk_zhenguan": "貞観政要", "bk_sub_zhenguan": "十巻", "bk_xunzi": "荀子", "bk_sub_xunzi": "三十二篇", "bk_jinsilu": "近思録", "bk_sub_jinsilu": "十四巻", "bk_hanfeizi": "韓非子", "bk_sub_hanfeizi": "五十五篇", "bk_mozi": "墨子", "bk_sub_mozi": "五十三篇", "bk_lvshi": "呂氏春秋", "bk_sub_lvshi": "二十六巻", "bk_yanshi": "顔氏家訓", "bk_sub_yanshi": "二十篇", "bk_shishuo": "世説新語", "bk_sub_shishuo": "三十六門", "bk_caigentan": "菜根譚", "bk_sub_caigentan": "三百余則", "bk_sub_shiji": "百三十巻", "bk_sub_zizhi": "二百九十四巻", "bk_sub_sunzi": "十三篇", "g13": "十三経", "gdao": "道家", "gfo": "仏典", "bk_sub_daxue": "『礼記』の篇 · 四書の一", "bk_sub_zhongyong": "『礼記』の篇 · 四書の一", "grp_main": "主線", "grp_13": "十三経", "grp_13_p": "周易・論語・孟子は上に。", "bk_shijing": "詩経", "bk_shangshu": "尚書", "bk_zhouli": "周礼", "bk_yili": "儀礼", "bk_liji": "礼記", "bk_zuozhuan": "春秋左氏伝", "bk_gongyang": "春秋公羊伝", "bk_guliang": "春秋穀梁伝", "bk_xiaojing": "孝経", "bk_erya": "爾雅", "bk_sub_shijing": "三百五篇", "bk_sub_shangshu": "五十八篇", "bk_sub_zhouli": "六官", "bk_sub_yili": "十七篇", "bk_sub_liji": "四十九篇", "bk_sub_zuozhuan": "編年二百五十五年", "bk_sub_gongyang": "春秋三伝の一", "bk_sub_guliang": "春秋三伝の一", "bk_sub_xiaojing": "十八章", "bk_sub_erya": "十九篇", "shumu_title": "書目", "shumu_sub": "古典の原文を一字ずつ", "shumu_p": "一冊ずつ、原文を一字ずつ読みます。", "soon": "準備中", "soon_line": "『道徳経』など {n} 部を準備中 · 書目 ›", "bk_prog": "既講 {done} / {total} 章", "bk_lunyu": "論語", "bk_daodejing": "道徳経", "bk_xinjing": "般若心経", "bk_zhouyi": "周易", "bk_zhuangzi": "荘子", "bk_mengzi": "孟子", "bk_chuanxilu": "伝習録", "bk_daxue": "大学", "bk_zhongyong": "中庸", "bk_sub_lunyu": "二十篇 · 朱熹集注本", "bk_sub_daodejing": "八十一章", "bk_sub_xinjing": "二百六十字", "bk_sub_zhouyi": "六十四卦と易伝", "bk_sub_zhuangzi": "内篇と名篇", "bk_sub_mengzi": "七篇十四巻", "bk_sub_chuanxilu": "王陽明の語録", "off_t": "オフライン", "off_h": "ネットワークに接続されていません", "off_p": "一度開いたページはこの端末に保存され、オフラインでも開けます。保存済みの章は下のとおりです。接続が戻ると自動で更新されます。", "off_none": "保存済みの章はまだありません。オンラインの時に何章か開くと、次からここに出ます。", "off_home": "トップへ", "zb_huang_meta2": "梁 · 1750年和刻本 · 巻{j}", "zb_scan2": "和刻本スキャン 第{ce}冊 {n} 頁", "toc_wj": "未講", "yiwen": "異文", "yiwen_note": "底本と通行本で字が異なる箇所。原文は底本に従います。", "th_di": "底本", "th_tong": "通行本", "th_shuo": "説明", "foot_org": "一孔録 · 独立編纂、機関・財団の助成なし", "feed": "更新を購読（RSS）", "zi_title": "読音索引", "zi_sub": "ナレーションで用いた字音", "zi_p": "一孔録のナレーションはこの読音に従います。章番号をクリックすると開きます。", "th_ch": "章", "zi_link": "読音索引", "ju_reads": "この句の読音：", "kw_stats": "勘誤 {n} 件（{cats}）、うち読者の指摘 {m} 件。", "thanks_h": "謝辞", "thanks_p": "一孔録の誤りを指摘してくださった読者（初回の順）：", "thanks_none": "まだ読者からの勘誤はありません。最初に誤りを指摘された方のお名前をここに記します。", "baihua": "現代中国語訳", "baihua_note": "一孔録の読みに沿った現代中国語の直訳です。", "zb_huang": "皇侃『論語義疏』", "zb_yang": "楊伯峻『論語訳注』", "zb_qian": "銭穆『論語新解』", "ju_copy": "この句を出典付きでコピー", "ju_link": "この句へのリンクをコピー", "ju_tip": "原文の句をタップすると、出典付きでコピーできます。",
   "zb_h": "諸家の注釈", "zb_note": "底本は朱熹『論語集注』（上記）。ここでは他の注釈を並べます。古注は疏の最初の一句と原刻本スキャンへのリンク、現代の注釈は訳文一句のみを短く引用します。「朱注との異同」は一孔録による説明です。",
   "zb_huang_meta": "梁 · 知不足斎叢書本 · 巻{j}", "zb_scan": "原刻本スキャン {n} 頁", "zb_yang_meta": "中華書局 · 現代の通行本、短い引用", "zb_qian_meta": "現代の通行本、短い引用",
   "zb_diff": "朱注との異同", "th_zb": "注釈", "th_key": "要点", "th_kind": "異同", "th_say": "説明",
   "th_sure": "確度", "s_ding": "確定", "s_wen": "ほぼ確実", "s_yi": "存疑", "k_same": "同じ", "k_diff": "異なる読み", "k_add": "補足", "k_shade": "軽重の差", "k_word": "字義の違い",
   "nf_h": "ページが見つかりません", "nf_p": "リンクの誤りか、ページが移動しました。原文を検索するか、書目からお探しください。"},
 "ko": {"about_def": "일공록(一孔录, Yikonglu)은 중국 고전 원문을 한 글자, 한 장씩 읽는 중국어 프로젝트입니다. 2026년부터 영상·팟캐스트·이 웹사이트에서 『논어』를 장마다 강독하고 있습니다. 원문과 주석은 주희 『논어집주』(사부비요본)를 따르며, 모든 인용에 저본의 쪽수를 밝힙니다. 일공록 자신의 읽기는 ‘일공안(一孔按)’이라 표시합니다. 독립 편찬이며 기관이나 재단의 지원을 받지 않습니다.", "zt_sub": "한 글자·한 개념으로 여러 책 읽기", "zt_p": "전제는 책별로 나누어 원문에 그 말이 나오는 장을 나열합니다. 강독한 장은 일공록의 해석이 붙고, 미강독 장은 원문만.", "zt_all": "『{b}』 전체 장", "zt_routes": "경로", "zt_routes_p": "작중 인물 한 사람을 따라 한 가지 물음으로 읽기.", "zt_nb": "{n}책 · {m}장", "gzi": "자부", "gmeng": "몽학", "bk_sanzijing": "삼자경", "bk_sub_sanzijing": "세 글자 한 구", "gshi": "사부", "gbing": "병가", "bk_tanjing": "육조단경", "bk_shiji": "사기", "bk_zizhi": "자치통감", "bk_sunzi": "손자병법", "bk_sub_tanjing": "10품", "bk_liezi": "열자", "bk_sub_liezi": "8편", "bk_huainanzi": "회남자", "bk_sub_huainanzi": "21편", "bk_yinfujing": "황제음부경", "bk_sub_yinfujing": "삼사백 자", "bk_qingjingjing": "청정경", "bk_sub_qingjingjing": "약 사백 자", "bk_baopuzi": "포박자", "bk_sub_baopuzi": "내편 20권", "bk_ganyingpian": "태상감응편", "bk_sub_ganyingpian": "약 천이백 자", "bk_jingang": "금강경", "bk_sub_jingang": "32분", "bk_sishierzhang": "사십이장경", "bk_sub_sishierzhang": "42장", "bk_baiyu": "백유경", "bk_sub_baiyu": "98유", "bk_weimojie": "유마경", "bk_sub_weimojie": "14품", "bk_fahua": "법화경", "bk_sub_fahua": "28품", "bk_amituo": "아미타경", "bk_sub_amituo": "1권", "bk_dizang": "지장경", "bk_sub_dizang": "13품", "bk_lengyan": "능엄경", "bk_sub_lengyan": "10권", "bk_guoyu": "국어", "bk_sub_guoyu": "21권", "bk_zhanguoce": "전국책", "bk_sub_zhanguoce": "33편", "bk_hanshu": "한서", "bk_sub_hanshu": "100편", "bk_houhanshu": "후한서", "bk_sub_houhanshu": "120권", "bk_sanguozhi": "삼국지", "bk_sub_sanguozhi": "65권", "bk_zhenguan": "정관정요", "bk_sub_zhenguan": "10권", "bk_xunzi": "순자", "bk_sub_xunzi": "32편", "bk_jinsilu": "근사록", "bk_sub_jinsilu": "14권", "bk_hanfeizi": "한비자", "bk_sub_hanfeizi": "55편", "bk_mozi": "묵자", "bk_sub_mozi": "53편", "bk_lvshi": "여씨춘추", "bk_sub_lvshi": "26권", "bk_yanshi": "안씨가훈", "bk_sub_yanshi": "20편", "bk_shishuo": "세설신어", "bk_sub_shishuo": "36문", "bk_caigentan": "채근담", "bk_sub_caigentan": "300여 칙", "bk_sub_shiji": "130권", "bk_sub_zizhi": "294권", "bk_sub_sunzi": "13편", "g13": "십삼경", "gdao": "도가", "gfo": "불전", "bk_sub_daxue": "『예기』의 편 · 사서 중 하나", "bk_sub_zhongyong": "『예기』의 편 · 사서 중 하나", "grp_main": "주선", "grp_13": "십삼경", "grp_13_p": "주역·논어·맹자는 위에 있습니다.", "bk_shijing": "시경", "bk_shangshu": "서경", "bk_zhouli": "주례", "bk_yili": "의례", "bk_liji": "예기", "bk_zuozhuan": "춘추좌전", "bk_gongyang": "춘추공양전", "bk_guliang": "춘추곡량전", "bk_xiaojing": "효경", "bk_erya": "이아", "bk_sub_shijing": "305편", "bk_sub_shangshu": "58편", "bk_sub_zhouli": "육관", "bk_sub_yili": "17편", "bk_sub_liji": "49편", "bk_sub_zuozhuan": "편년 255년", "bk_sub_gongyang": "춘추삼전의 하나", "bk_sub_guliang": "춘추삼전의 하나", "bk_sub_xiaojing": "18장", "bk_sub_erya": "19편", "shumu_title": "서목", "shumu_sub": "고전 원문을 한 글자씩", "shumu_p": "한 권씩, 원문을 한 글자씩 읽습니다.", "soon": "준비 중", "soon_line": "『도덕경』 등 {n}부 준비 중 · 전체 목록 ›", "bk_prog": "강독 {done} / {total} 장", "bk_lunyu": "논어", "bk_daodejing": "도덕경", "bk_xinjing": "반야심경", "bk_zhouyi": "주역", "bk_zhuangzi": "장자", "bk_mengzi": "맹자", "bk_chuanxilu": "전습록", "bk_daxue": "대학", "bk_zhongyong": "중용", "bk_sub_lunyu": "스무 편 · 주희 집주본", "bk_sub_daodejing": "81장", "bk_sub_xinjing": "260자", "bk_sub_zhouyi": "64괘와 역전", "bk_sub_zhuangzi": "내편과 명편", "bk_sub_mengzi": "7편 14권", "bk_sub_chuanxilu": "왕양명 어록", "off_t": "오프라인", "off_h": "네트워크에 연결되어 있지 않습니다", "off_p": "한 번 연 페이지는 이 기기에 저장되어 오프라인에서도 열립니다. 저장된 장은 아래와 같고, 연결되면 자동으로 갱신됩니다.", "off_none": "아직 저장된 장이 없습니다. 온라인일 때 몇 장을 열어 두면 다음부터 여기에 나옵니다.", "off_home": "홈", "zb_huang_meta2": "양나라 · 1750년 일본 화각본 · 권{j}", "zb_scan2": "화각본 스캔 제{ce}책 {n}쪽", "toc_wj": "아직 다루지 않음", "yiwen": "이문", "yiwen_note": "저본과 통행본의 글자가 다른 곳. 원문은 저본을 따릅니다.", "th_di": "저본", "th_tong": "통행본", "th_shuo": "설명", "foot_org": "일공록(一孔录) · 독립 편찬, 기관·재단 후원 없음", "feed": "업데이트 구독(RSS)", "zi_title": "독음 색인", "zi_sub": "내레이션에서 읽은 글자 음", "zi_p": "일공록 내레이션은 이 독음을 따릅니다. 장 번호를 누르면 열립니다.", "th_ch": "장", "zi_link": "독음 색인", "ju_reads": "이 구절의 독음: ", "kw_stats": "감오 {n}건({cats}), 그중 독자 지적 {m}건.", "thanks_h": "감사", "thanks_p": "일공록의 오류를 지적해 주신 독자(첫 제보 순):", "thanks_none": "아직 독자 감오가 없습니다. 처음 오류를 지적한 분의 이름을 여기에 적습니다.", "baihua": "현대 중국어 풀이", "baihua_note": "일공록의 해석에 따른 현대 중국어 직역입니다.", "zb_huang": "皇侃《論語義疏》", "zb_yang": "楊伯峻《論語譯注》", "zb_qian": "錢穆《論語新解》", "ju_copy": "이 구절을 출처와 함께 복사", "ju_link": "이 구절 링크 복사", "ju_tip": "원문의 구절을 누르면 출처와 함께 복사할 수 있습니다.",
   "zb_h": "여러 주석서", "zb_note": "저본은 주희 『논어집주』(위)입니다. 여기에는 다른 주석을 나란히 둡니다. 고주는 소(疏)의 첫 구절과 원각본 스캔 링크, 현대 주석은 번역 한 구절만 짧게 인용합니다. '주희 주석과의 이동'은 일공록의 설명입니다.",
   "zb_huang_meta": "양나라 · 지부족재총서본 · 권{j}", "zb_scan": "원각본 스캔 {n}쪽", "zb_yang_meta": "중화서국 · 현대 통행본, 짧은 인용", "zb_qian_meta": "현대 통행본, 짧은 인용",
   "zb_diff": "주희 주석과의 이동", "th_zb": "주석", "th_key": "요점", "th_kind": "이동", "th_say": "설명",
   "th_sure": "확실성", "s_ding": "확정", "s_wen": "비교적 확실", "s_yi": "의문", "k_same": "같음", "k_diff": "다른 해석", "k_add": "보충", "k_shade": "경중 차이", "k_word": "자의 차이",
   "nf_h": "페이지를 찾을 수 없습니다", "nf_p": "링크가 잘못되었거나 주소가 바뀌었습니다. 원문을 검색하거나 서목에서 찾아보세요."},
 "fr": {"about_def": "Yikonglu (一孔录) est un projet en chinois qui lit les classiques chinois mot à mot, chapitre par chapitre. Depuis 2026, il parcourt les Entretiens de Confucius en vidéos, en podcasts et sur ce site ; le texte et le commentaire suivent les Commentaires réunis de Zhu Xi (édition Sibu Beiyao), chaque citation renvoyant à une page de l'édition de base. Sa propre lecture est signalée « 一孔按 ». Compilation indépendante, sans financement d'institution ni de fondation.", "zt_sub": "Lire les livres par un mot ou une idée", "zt_p": "Chaque thème est divisé par livre et liste les chapitres dont le texte original le mentionne : les chapitres traités portent notre lecture, les autres ne montrent que l'original.", "zt_all": "Tous les chapitres de {b}", "zt_routes": "Parcours", "zt_routes_p": "Suivre un personnage à travers une question.", "zt_nb": "{n} livres · {m} chapitres", "gzi": "Maîtres (zibu)", "gmeng": "Abécédaires", "bk_sanzijing": "Classique des trois caractères", "bk_sub_sanzijing": "Trois caractères par vers", "gshi": "Histoires", "gbing": "Art militaire", "bk_tanjing": "Sūtra de l'Estrade", "bk_shiji": "Mémoires historiques", "bk_zizhi": "Zizhi Tongjian", "bk_sunzi": "L'Art de la guerre", "bk_sub_tanjing": "10 chapitres", "bk_liezi": "Liezi", "bk_sub_liezi": "8 livres", "bk_huainanzi": "Huainanzi", "bk_sub_huainanzi": "21 chapitres", "bk_yinfujing": "Yinfu jing", "bk_sub_yinfujing": "env. 400 caractères", "bk_qingjingjing": "Qingjing jing", "bk_sub_qingjingjing": "env. 400 caractères", "bk_baopuzi": "Baopuzi", "bk_sub_baopuzi": "chapitres intérieurs, 20 rouleaux", "bk_ganyingpian": "Traité des actions et rétributions", "bk_sub_ganyingpian": "env. 1 200 caractères", "bk_jingang": "Sūtra du Diamant", "bk_sub_jingang": "32 sections", "bk_sishierzhang": "Sūtra en quarante-deux articles", "bk_sub_sishierzhang": "42 articles", "bk_baiyu": "Sūtra des cent paraboles", "bk_sub_baiyu": "98 paraboles", "bk_weimojie": "Sūtra de Vimalakīrti", "bk_sub_weimojie": "14 chapitres", "bk_fahua": "Sūtra du Lotus", "bk_sub_fahua": "28 chapitres", "bk_amituo": "Sūtra d'Amitābha", "bk_sub_amituo": "1 rouleau", "bk_dizang": "Sūtra de Kṣitigarbha", "bk_sub_dizang": "13 chapitres", "bk_lengyan": "Sūtra de Śūraṅgama", "bk_sub_lengyan": "10 rouleaux", "bk_guoyu": "Discours des royaumes", "bk_sub_guoyu": "21 rouleaux", "bk_zhanguoce": "Stratagèmes des Royaumes combattants", "bk_sub_zhanguoce": "33 livres", "bk_hanshu": "Livre des Han", "bk_sub_hanshu": "100 chapitres", "bk_houhanshu": "Livre des Han postérieurs", "bk_sub_houhanshu": "120 rouleaux", "bk_sanguozhi": "Chroniques des Trois Royaumes", "bk_sub_sanguozhi": "65 rouleaux", "bk_zhenguan": "L'Essentiel du gouvernement de l'ère Zhenguan", "bk_sub_zhenguan": "10 rouleaux", "bk_xunzi": "Xunzi", "bk_sub_xunzi": "32 chapitres", "bk_jinsilu": "Réflexions sur les choses proches", "bk_sub_jinsilu": "14 rouleaux", "bk_hanfeizi": "Han Feizi", "bk_sub_hanfeizi": "55 chapitres", "bk_mozi": "Mozi", "bk_sub_mozi": "53 chapitres", "bk_lvshi": "Printemps et automnes de Lü", "bk_sub_lvshi": "26 rouleaux", "bk_yanshi": "Instructions familiales des Yan", "bk_sub_yanshi": "20 chapitres", "bk_shishuo": "Nouveaux propos du monde", "bk_sub_shishuo": "36 sections", "bk_caigentan": "Propos sur la racine des légumes", "bk_sub_caigentan": "plus de 300 maximes", "bk_sub_shiji": "130 rouleaux", "bk_sub_zizhi": "294 rouleaux", "bk_sub_sunzi": "13 chapitres", "g13": "Les Treize Classiques", "gdao": "Taoïsme", "gfo": "Bouddhisme", "bk_sub_daxue": "Chapitre du Liji · un des Quatre Livres", "bk_sub_zhongyong": "Chapitre du Liji · un des Quatre Livres", "grp_main": "Ligne principale", "grp_13": "Les Treize Classiques", "grp_13_p": "Les Mutations, les Entretiens et Mencius figurent ci-dessus.", "bk_shijing": "Livre des Odes", "bk_shangshu": "Livre des Documents", "bk_zhouli": "Rites des Zhou", "bk_yili": "Cérémonial", "bk_liji": "Livre des Rites", "bk_zuozhuan": "Tradition de Zuo", "bk_gongyang": "Commentaire de Gongyang", "bk_guliang": "Commentaire de Guliang", "bk_xiaojing": "Classique de la piété filiale", "bk_erya": "Erya", "bk_sub_shijing": "305 poèmes", "bk_sub_shangshu": "58 chapitres", "bk_sub_zhouli": "Six ministères", "bk_sub_yili": "17 chapitres", "bk_sub_liji": "49 chapitres", "bk_sub_zuozhuan": "Annales de 255 ans", "bk_sub_gongyang": "Commentaire des Printemps et Automnes", "bk_sub_guliang": "Commentaire des Printemps et Automnes", "bk_sub_xiaojing": "18 chapitres", "bk_sub_erya": "19 chapitres", "shumu_title": "Livres", "shumu_sub": "Les classiques mot à mot", "shumu_p": "Un livre à la fois, mot à mot.", "soon": "à venir", "soon_line": "Daodejing et {n} autres en préparation · liste complète ›", "bk_prog": "{done} / {total} chapitres", "bk_lunyu": "Les Entretiens", "bk_daodejing": "Daodejing", "bk_xinjing": "Sūtra du Cœur", "bk_zhouyi": "Livre des Mutations", "bk_zhuangzi": "Zhuangzi", "bk_mengzi": "Mencius", "bk_chuanxilu": "Chuanxilu (Wang Yangming)", "bk_daxue": "La Grande Étude", "bk_zhongyong": "L'Invariable Milieu", "bk_sub_lunyu": "20 livres · édition de Zhu Xi", "bk_sub_daodejing": "81 chapitres", "bk_sub_xinjing": "260 caractères", "bk_sub_zhouyi": "64 hexagrammes et les Dix Ailes", "bk_sub_zhuangzi": "Chapitres intérieurs et morceaux choisis", "bk_sub_mengzi": "7 livres", "bk_sub_chuanxilu": "Propos recueillis", "off_t": "Hors ligne", "off_h": "Vous êtes hors ligne", "off_p": "Les pages déjà consultées sont gardées sur cet appareil et s'ouvrent hors ligne. Les chapitres gardés sont listés ci-dessous ; ils se mettent à jour au retour du réseau.", "off_none": "Aucun chapitre gardé pour l'instant. Ouvrez-en quelques-uns en ligne et ils apparaîtront ici.", "off_home": "Accueil", "zb_huang_meta2": "dynastie Liang · éd. japonaise de 1750 · juan {j}", "zb_scan2": "xylographie vol. {ce} p. {n}", "toc_wj": "pas encore traité", "yiwen": "Variantes", "yiwen_note": "Là où l'édition de base diffère du texte courant ; l'original suit l'édition de base.", "th_di": "Édition de base", "th_tong": "Texte courant", "th_shuo": "Note", "foot_org": "Yikonglu (一孔录) · compilé de façon indépendante, sans financement institutionnel ni de fondation", "feed": "S'abonner (RSS)", "zi_title": "Index des prononciations", "zi_sub": "Lectures suivies par notre narration", "zi_p": "Notre narration suit ces lectures. Cliquez sur un numéro de chapitre pour l'ouvrir.", "th_ch": "Chapitre", "zi_link": "Index des prononciations", "ju_reads": "Lectures : ", "kw_stats": "{n} corrections enregistrées ({cats}), dont {m} signalées par des lecteurs.", "thanks_h": "Remerciements", "thanks_p": "Ces lecteurs ont relevé nos erreurs, par ordre de premier signalement :", "thanks_none": "Aucune correction de lecteur pour l'instant. Le premier à relever une erreur sera crédité ici.", "baihua": "Chinois moderne", "baihua_note": "Rendu en chinois moderne selon la lecture de Yikonglu.", "ju_copy": "Copier la phrase avec la source", "ju_link": "Copier le lien de la phrase", "ju_tip": "Touchez une phrase du texte original pour la copier avec sa source.",
   "zb_h": "Autres commentaires", "zb_note": "Notre texte de base est le commentaire de Zhu Xi (ci-dessus). Voici d'autres commentaires en regard : pour les anciens, la première phrase du sous-commentaire et un lien vers la xylographie ; pour les modernes, une seule phrase de traduction, citée brièvement. Les notes « par rapport à Zhu Xi » sont de Yikonglu.",
   "zb_huang_meta": "dynastie Liang · éd. Zhibuzu Zhai · juan {j}", "zb_scan": "xylographie p. {n}", "zb_yang_meta": "Zhonghua · moderne, citation brève", "zb_qian_meta": "moderne, citation brève",
   "zb_diff": "Par rapport à Zhu Xi", "th_zb": "Commentaire", "th_key": "Point", "th_kind": "Relation", "th_say": "Note",
   "th_sure": "Certitude", "s_ding": "établi", "s_wen": "assez sûr", "s_yi": "incertain", "k_same": "identique", "k_diff": "diverge", "k_add": "complète", "k_shade": "nuance", "k_word": "sens du mot",
   "nf_h": "Page introuvable", "nf_p": "Le lien est peut-être erroné ou la page a changé d'adresse. Cherchez dans le texte original ou parcourez par livre."},
 "es": {"about_def": "Yikonglu (一孔录) es un proyecto en chino que lee los clásicos chinos palabra por palabra y capítulo por capítulo. Desde 2026 recorre las Analectas en vídeos, pódcast y este sitio; el texto y el comentario siguen los Comentarios reunidos de Zhu Xi (edición Sibu Beiyao), y cada cita remite a una página de la edición base. Su propia lectura se marca «一孔按». Compilación independiente, sin financiación de instituciones ni fundaciones.", "zt_sub": "Leer los libros por una palabra o una idea", "zt_p": "Cada tema se divide por libro y lista los capítulos cuyo texto original lo menciona: los capítulos tratados llevan nuestra lectura; los demás solo muestran el original.", "zt_all": "Todos los capítulos de {b}", "zt_routes": "Rutas", "zt_routes_p": "Seguir a un personaje a través de una pregunta.", "zt_nb": "{n} libros · {m} capítulos", "gzi": "Maestros (zibu)", "gmeng": "Primeras letras", "bk_sanzijing": "Clásico de los tres caracteres", "bk_sub_sanzijing": "Tres caracteres por verso", "gshi": "Historias", "gbing": "Arte militar", "bk_tanjing": "Sutra del Estrado", "bk_shiji": "Memorias históricas", "bk_zizhi": "Zizhi Tongjian", "bk_sunzi": "El arte de la guerra", "bk_sub_tanjing": "10 capítulos", "bk_liezi": "Liezi", "bk_sub_liezi": "8 libros", "bk_huainanzi": "Huainanzi", "bk_sub_huainanzi": "21 capítulos", "bk_yinfujing": "Yinfu jing", "bk_sub_yinfujing": "unos 400 caracteres", "bk_qingjingjing": "Qingjing jing", "bk_sub_qingjingjing": "unos 400 caracteres", "bk_baopuzi": "Baopuzi", "bk_sub_baopuzi": "capítulos interiores, 20 rollos", "bk_ganyingpian": "Tratado de la respuesta y la retribución", "bk_sub_ganyingpian": "unos 1.200 caracteres", "bk_jingang": "Sutra del Diamante", "bk_sub_jingang": "32 secciones", "bk_sishierzhang": "Sutra de los cuarenta y dos capítulos", "bk_sub_sishierzhang": "42 capítulos", "bk_baiyu": "Sutra de las cien parábolas", "bk_sub_baiyu": "98 parábolas", "bk_weimojie": "Sutra de Vimalakirti", "bk_sub_weimojie": "14 capítulos", "bk_fahua": "Sutra del Loto", "bk_sub_fahua": "28 capítulos", "bk_amituo": "Sutra de Amitabha", "bk_sub_amituo": "1 rollo", "bk_dizang": "Sutra de Ksitigarbha", "bk_sub_dizang": "13 capítulos", "bk_lengyan": "Sutra Shurangama", "bk_sub_lengyan": "10 rollos", "bk_guoyu": "Discursos de los Estados", "bk_sub_guoyu": "21 rollos", "bk_zhanguoce": "Estratagemas de los Reinos Combatientes", "bk_sub_zhanguoce": "33 libros", "bk_hanshu": "Libro de Han", "bk_sub_hanshu": "100 capítulos", "bk_houhanshu": "Libro de los Han Posteriores", "bk_sub_houhanshu": "120 rollos", "bk_sanguozhi": "Crónicas de los Tres Reinos", "bk_sub_sanguozhi": "65 rollos", "bk_zhenguan": "Lo esencial del gobierno de la era Zhenguan", "bk_sub_zhenguan": "10 rollos", "bk_xunzi": "Xunzi", "bk_sub_xunzi": "32 capítulos", "bk_jinsilu": "Reflexiones sobre lo cercano", "bk_sub_jinsilu": "14 rollos", "bk_hanfeizi": "Han Feizi", "bk_sub_hanfeizi": "55 capítulos", "bk_mozi": "Mozi", "bk_sub_mozi": "53 capítulos", "bk_lvshi": "Primaveras y otoños de Lü", "bk_sub_lvshi": "26 rollos", "bk_yanshi": "Instrucciones familiares de los Yan", "bk_sub_yanshi": "20 capítulos", "bk_shishuo": "Nuevos relatos del mundo", "bk_sub_shishuo": "36 secciones", "bk_caigentan": "Discurso de las raíces de verduras", "bk_sub_caigentan": "más de 300 máximas", "bk_sub_shiji": "130 rollos", "bk_sub_zizhi": "294 rollos", "bk_sub_sunzi": "13 capítulos", "g13": "Los Trece Clásicos", "gdao": "Taoísmo", "gfo": "Budismo", "bk_sub_daxue": "Capítulo del Liji · uno de los Cuatro Libros", "bk_sub_zhongyong": "Capítulo del Liji · uno de los Cuatro Libros", "grp_main": "Línea principal", "grp_13": "Los Trece Clásicos", "grp_13_p": "Los Cambios, las Analectas y Mencio figuran arriba.", "bk_shijing": "Libro de las Odas", "bk_shangshu": "Libro de los Documentos", "bk_zhouli": "Ritos de Zhou", "bk_yili": "Ceremonial", "bk_liji": "Libro de los Ritos", "bk_zuozhuan": "Tradición de Zuo", "bk_gongyang": "Comentario de Gongyang", "bk_guliang": "Comentario de Guliang", "bk_xiaojing": "Clásico de la piedad filial", "bk_erya": "Erya", "bk_sub_shijing": "305 poemas", "bk_sub_shangshu": "58 capítulos", "bk_sub_zhouli": "Seis ministerios", "bk_sub_yili": "17 capítulos", "bk_sub_liji": "49 capítulos", "bk_sub_zuozhuan": "Anales de 255 años", "bk_sub_gongyang": "Comentario de Primaveras y Otoños", "bk_sub_guliang": "Comentario de Primaveras y Otoños", "bk_sub_xiaojing": "18 capítulos", "bk_sub_erya": "19 capítulos", "shumu_title": "Libros", "shumu_sub": "Los clásicos palabra por palabra", "shumu_p": "Un libro cada vez, palabra por palabra.", "soon": "próximamente", "soon_line": "Daodejing y {n} más en preparación · lista completa ›", "bk_prog": "{done} / {total} capítulos", "bk_lunyu": "Las Analectas", "bk_daodejing": "Daodejing", "bk_xinjing": "Sutra del Corazón", "bk_zhouyi": "Libro de los Cambios", "bk_zhuangzi": "Zhuangzi", "bk_mengzi": "Mencio", "bk_chuanxilu": "Chuanxilu (Wang Yangming)", "bk_daxue": "El Gran Saber", "bk_zhongyong": "El Justo Medio", "bk_sub_lunyu": "20 libros · edición de Zhu Xi", "bk_sub_daodejing": "81 capítulos", "bk_sub_xinjing": "260 caracteres", "bk_sub_zhouyi": "64 hexagramas y las Diez Alas", "bk_sub_zhuangzi": "Capítulos interiores y selección", "bk_sub_mengzi": "7 libros", "bk_sub_chuanxilu": "Dichos recogidos", "off_t": "Sin conexión", "off_h": "Estás sin conexión", "off_p": "Las páginas que ya abriste se guardan en este dispositivo y se abren sin conexión. Abajo están los capítulos guardados; se actualizan al volver la red.", "off_none": "Aún no hay capítulos guardados. Abre algunos con conexión y aparecerán aquí.", "off_home": "Inicio", "zb_huang_meta2": "dinastía Liang · ed. japonesa de 1750 · juan {j}", "zb_scan2": "xilografía vol. {ce} p. {n}", "toc_wj": "aún no tratado", "yiwen": "Variantes", "yiwen_note": "Donde la edición base difiere del texto común; el original sigue la edición base.", "th_di": "Edición base", "th_tong": "Texto común", "th_shuo": "Nota", "foot_org": "Yikonglu (一孔录) · compilado de forma independiente, sin financiación institucional ni de fundaciones", "feed": "Suscribirse (RSS)", "zi_title": "Índice de pronunciación", "zi_sub": "Lecturas que sigue nuestra narración", "zi_p": "Nuestra narración sigue estas lecturas. Haz clic en un número de capítulo para abrirlo.", "th_ch": "Capítulo", "zi_link": "Índice de pronunciación", "ju_reads": "Lecturas: ", "kw_stats": "{n} correcciones registradas ({cats}); {m} señaladas por lectores.", "thanks_h": "Agradecimientos", "thanks_p": "Estos lectores han señalado nuestros errores, por orden del primer aviso:", "thanks_none": "Aún no hay correcciones de lectores. El primero en señalar un error figurará aquí.", "baihua": "Chino moderno", "baihua_note": "Versión en chino moderno según la lectura de Yikonglu.", "ju_copy": "Copiar la frase con la fuente", "ju_link": "Copiar el enlace de la frase", "ju_tip": "Toca una frase del original para copiarla con su fuente.",
   "zb_h": "Otros comentarios", "zb_note": "Nuestro texto base es el comentario de Zhu Xi (arriba). Aquí van otros comentarios en paralelo: de los antiguos, la primera frase del subcomentario y un enlace a la xilografía; de los modernos, una sola frase de traducción citada brevemente. Las notas «frente a Zhu Xi» son de Yikonglu.",
   "zb_huang_meta": "dinastía Liang · ed. Zhibuzu Zhai · juan {j}", "zb_scan": "xilografía p. {n}", "zb_yang_meta": "Zhonghua · moderno, cita breve", "zb_qian_meta": "moderno, cita breve",
   "zb_diff": "Frente a Zhu Xi", "th_zb": "Comentario", "th_key": "Punto", "th_kind": "Relación", "th_say": "Nota",
   "th_sure": "Certeza", "s_ding": "firme", "s_wen": "bastante firme", "s_yi": "dudoso", "k_same": "igual", "k_diff": "difiere", "k_add": "añade", "k_shade": "matiz", "k_word": "sentido de la palabra",
   "nf_h": "Página no encontrada", "nf_p": "Puede que el enlace esté mal escrito o que la página haya cambiado. Busca en el texto original o explora por libro."},
}
# 转载声明与出处标记（页底另起一行；关于页“转载与引用”一节）
REUSE_UI = {
 "zh-Hans": {"foot_reuse": "原文与古注为公版；一孔录写的白话、一孔按、引文核对等文字按 <a href=\"https://creativecommons.org/licenses/by/4.0/deed.zh-hans\" rel=\"license noopener\" target=\"_blank\">CC BY 4.0</a> 许可：可以转载、改编，也可以商用，只须署名“一孔录 yikonglu.com”并附原链接。<a href=\"{p}about.html#zhuanzai\">转载说明</a>",
  "about_h4": "转载与引用",
  "about_r1": "原文和古注（朱熹集注、皇侃义疏等古刻本）是公版，谁都可以用。",
  "about_r2": "一孔录写的文字，包括白话、一孔按和读法、引文核对表、读音表、专题编排和译文，按 CC BY 4.0 许可：谁都可以转载、改编，也可以商用，只须署名“一孔录 yikonglu.com”、附原页链接、注明有没有改动。",
  "about_r3": "现代注本（杨伯峻、钱穆等）的引文版权归原作者和出版方，不在这个许可之内，本站只作短引。",
  "about_r4": "视频、配音、原创角色形象和插图不在这个许可之内，转用请先来信。",
  "about_r5": "引一句时，点原文任一句，复制出来就带着章号和网址，例如“——论语 2.1 · 一孔录 yikonglu.com/lunyu/2.1”，照这样贴出去就算署了名。原页图角上印着“一孔录”和卷页，转用时请保留。要成批转载，可以直接用<a href=\"{p}kaifang.html\">开放数据</a>。看到没署名的转载，或者照搬全站的网站，也请告诉我们：",
  "mirror_bar": "本页原载一孔录 yikonglu.com，最新版本和勘误请看原站", "mirror_go": "去原站"},
 "en": {"foot_reuse": "Original texts and old commentaries are public domain. Everything Yikonglu writes (plain renderings, our readings, citation checks) is licensed <a href=\"https://creativecommons.org/licenses/by/4.0/deed.en\" rel=\"license noopener\" target=\"_blank\">CC BY 4.0</a>: share, adapt and use it commercially, as long as you credit “Yikonglu yikonglu.com” with a link to the original page. <a href=\"{p}about.html#zhuanzai\">Reuse guide</a>",
  "about_h4": "Reuse and citation",
  "about_r1": "The original texts and old commentaries (Zhu Xi, Huang Kan and other early printed editions) are public domain and free for anyone to use.",
  "about_r2": "Everything Yikonglu writes, including plain renderings, our own readings, citation tables, pronunciation tables, topic arrangements and translations, is licensed CC BY 4.0: anyone may share and adapt it, commercially too, as long as they credit “Yikonglu yikonglu.com”, link to the original page and say whether they changed it.",
  "about_r3": "Quotations from modern commentaries (Yang Bojun, Qian Mu and others) belong to their authors and publishers, are not covered by this license, and appear here only as short quotations.",
  "about_r4": "Videos, narration, our characters and illustrations are not covered by this license; please write to us before reusing them.",
  "about_r5": "To quote a line, tap any sentence of the original: the copy carries its chapter number and address, and pasting it as is counts as credit. Page images carry “Yikonglu” and the volume and page in the corner; please keep that mark. For bulk reuse, use our <a href=\"{p}kaifang.html\">open data</a>. If you see an uncredited copy or a mirror of this site, please let us know:",
  "mirror_bar": "This page was first published on Yikonglu (yikonglu.com). See the original for the latest version and corrections.", "mirror_go": "Go to original"},
 "ja": {"foot_reuse": "原文と古注はパブリックドメインです。一孔録が書いた文章（現代語訳・一孔按・引用照合）は <a href=\"https://creativecommons.org/licenses/by/4.0/deed.ja\" rel=\"license noopener\" target=\"_blank\">CC BY 4.0</a> で公開しています。「一孔録 yikonglu.com」と元ページへのリンクを明記すれば、転載・改変・商用利用ができます。<a href=\"{p}about.html#zhuanzai\">転載について</a>",
  "about_h4": "転載と引用",
  "about_r1": "原文と古注（朱熹集注、皇侃義疏などの古版本）はパブリックドメインで、どなたでも使えます。",
  "about_r2": "一孔録が書いた文章、すなわち現代語訳、一孔按と読み方、引用照合表、読音表、専題の編成、翻訳は CC BY 4.0 です。「一孔録 yikonglu.com」の表示、元ページへのリンク、改変の有無の明記を条件に、どなたでも転載・改変でき、商用利用もできます。",
  "about_r3": "現代の注釈書（楊伯峻、銭穆など）からの引用の権利は著者と出版社にあり、このライセンスの対象外です。本サイトでは短い引用にとどめています。",
  "about_r4": "動画、ナレーション、作中の人物と挿絵はこのライセンスの対象外です。転用の前にご連絡ください。",
  "about_r5": "一文を引くときは、原文のどの文でもタップすればコピーに章番号とアドレスが付きます。そのまま貼れば出典表示になります。原頁画像の隅にある「一孔録」と巻・頁はそのまま残してください。まとめて転載するなら<a href=\"{p}kaifang.html\">オープンデータ</a>をお使いください。出典のない転載やサイト丸ごとのミラーを見つけたら、お知らせください：",
  "mirror_bar": "このページの初出は一孔録 yikonglu.com です。最新版と訂正は元サイトでご覧ください。", "mirror_go": "元サイトへ"},
 "ko": {"foot_reuse": "원문과 옛 주석은 퍼블릭 도메인입니다. 일공록이 쓴 글(번역·일공안·인용 대조)은 <a href=\"https://creativecommons.org/licenses/by/4.0/deed.ko\" rel=\"license noopener\" target=\"_blank\">CC BY 4.0</a> 라이선스입니다. “일공록 yikonglu.com”과 원래 페이지 링크만 밝히면 옮겨 싣고 고치고 상업적으로 써도 됩니다. <a href=\"{p}about.html#zhuanzai\">전재 안내</a>",
  "about_h4": "전재와 인용",
  "about_r1": "원문과 옛 주석(주희 집주, 황간 의소 등 옛 판본)은 퍼블릭 도메인이라 누구나 쓸 수 있습니다.",
  "about_r2": "일공록이 쓴 글, 곧 번역, 일공안과 읽기, 인용 대조표, 독음표, 전제 편성, 번역문은 CC BY 4.0 라이선스입니다. “일공록 yikonglu.com” 표기, 원래 페이지 링크, 수정 여부 표시만 지키면 누구나 옮겨 싣고 고칠 수 있으며 상업적 이용도 됩니다.",
  "about_r3": "현대 주석서(양보쥔, 첸무 등) 인용문의 권리는 저자와 출판사에 있어 이 라이선스에 포함되지 않으며, 이 사이트에서는 짧게 인용할 뿐입니다.",
  "about_r4": "영상, 내레이션, 작품 속 인물과 삽화는 이 라이선스에 포함되지 않습니다. 쓰시려면 먼저 연락해 주십시오.",
  "about_r5": "한 구절을 인용할 때는 원문의 아무 문장이나 누르면 장 번호와 주소가 붙어 복사됩니다. 그대로 붙이면 출처 표시가 됩니다. 원문 쪽 이미지 모서리의 “일공록”과 권·쪽은 지우지 말아 주십시오. 한꺼번에 옮기려면 <a href=\"{p}kaifang.html\">공개 데이터</a>를 쓰십시오. 출처 없는 전재나 사이트 전체를 베낀 미러를 보시면 알려 주십시오:",
  "mirror_bar": "이 페이지는 일공록 yikonglu.com에 처음 실렸습니다. 최신판과 정정은 원래 사이트에서 보십시오.", "mirror_go": "원래 사이트로"},
 "fr": {"foot_reuse": "Les textes originaux et les commentaires anciens sont dans le domaine public. Tout ce qu’écrit Yikonglu (traductions, nos lectures, vérifications de citations) est sous licence <a href=\"https://creativecommons.org/licenses/by/4.0/deed.fr\" rel=\"license noopener\" target=\"_blank\">CC BY 4.0</a> : reprise, adaptation et usage commercial permis, à condition de citer « Yikonglu yikonglu.com » avec un lien vers la page d’origine. <a href=\"{p}about.html#zhuanzai\">Conditions de reprise</a>",
  "about_h4": "Reprise et citation",
  "about_r1": "Les textes originaux et les commentaires anciens (Zhu Xi, Huang Kan et autres éditions anciennes) sont dans le domaine public : chacun peut les utiliser.",
  "about_r2": "Tout ce qu’écrit Yikonglu, traductions, nos propres lectures, tableaux de citations, tables de prononciation, organisation des thèmes, est sous licence CC BY 4.0 : chacun peut le reprendre et l’adapter, y compris à des fins commerciales, en citant « Yikonglu yikonglu.com », avec un lien vers la page d’origine et en indiquant les modifications.",
  "about_r3": "Les citations de commentaires modernes (Yang Bojun, Qian Mu, etc.) appartiennent à leurs auteurs et éditeurs, ne sont pas couvertes par cette licence et ne figurent ici qu’en courts extraits.",
  "about_r4": "Les vidéos, la narration, nos personnages et les illustrations ne sont pas couverts par cette licence ; écrivez-nous avant de les réutiliser.",
  "about_r5": "Pour citer une phrase, touchez-la dans le texte original : la copie porte le numéro du chapitre et l’adresse, et la coller telle quelle vaut mention de source. Les images de pages portent « Yikonglu » et le volume et la page dans le coin ; merci de garder cette marque. Pour une reprise en nombre, utilisez nos <a href=\"{p}kaifang.html\">données ouvertes</a>. Si vous voyez une copie sans mention de source ou un miroir de ce site, dites-le-nous :",
  "mirror_bar": "Cette page a d’abord été publiée sur Yikonglu (yikonglu.com). Voir l’original pour la dernière version et les corrections.", "mirror_go": "Voir l’original"},
 "es": {"foot_reuse": "Los textos originales y los comentarios antiguos son de dominio público. Todo lo que escribe Yikonglu (traducciones, nuestras lecturas, verificaciones de citas) tiene licencia <a href=\"https://creativecommons.org/licenses/by/4.0/deed.es\" rel=\"license noopener\" target=\"_blank\">CC BY 4.0</a>: puede compartirlo, adaptarlo y usarlo comercialmente citando «Yikonglu yikonglu.com» con un enlace a la página original. <a href=\"{p}about.html#zhuanzai\">Cómo reutilizar</a>",
  "about_h4": "Reutilización y cita",
  "about_r1": "Los textos originales y los comentarios antiguos (Zhu Xi, Huang Kan y otras ediciones antiguas) son de dominio público y cualquiera puede usarlos.",
  "about_r2": "Todo lo que escribe Yikonglu, incluidas traducciones, nuestras propias lecturas, tablas de citas, tablas de pronunciación, organización de los temas y versiones, tiene licencia CC BY 4.0: cualquiera puede compartirlo y adaptarlo, también con fines comerciales, citando «Yikonglu yikonglu.com», con enlace a la página original e indicando si hizo cambios.",
  "about_r3": "Las citas de comentarios modernos (Yang Bojun, Qian Mu y otros) pertenecen a sus autores y editoriales, no están cubiertas por esta licencia y aquí solo aparecen como citas breves.",
  "about_r4": "Los vídeos, la narración, nuestros personajes y las ilustraciones no están cubiertos por esta licencia; escríbanos antes de reutilizarlos.",
  "about_r5": "Para citar una frase, toque cualquier frase del original: la copia lleva el número de capítulo y la dirección, y pegarla tal cual ya cuenta como atribución. Las imágenes de página llevan «Yikonglu» y el volumen y la página en la esquina; por favor, conserve esa marca. Para reutilizar en bloque, use nuestros <a href=\"{p}kaifang.html\">datos abiertos</a>. Si ve una copia sin atribución o un espejo de este sitio, avísenos:",
  "mirror_bar": "Esta página se publicó primero en Yikonglu (yikonglu.com). Vea el original para la versión más reciente y las correcciones.", "mirror_go": "Ir al original"},
}
for _c, _d in REUSE_UI.items(): EXTRA_UI.setdefault(_c, {}).update(_d)
LC_UI = {  # 一页两层：上半给普通读者，下半给细读核对的读者
 "zh-Hans": {"ch_gist": "这一章讲什么", "ch_deep": "细读与核对", "ch_deep_note": "给想细读、要核对的读者：注里的关键字、诸家说法、异文、各家注本原话与底本原页、读音和勘误。点标题展开。", "ch_open_all": "全部展开", "ch_close_all": "全部收起",
   "cta_db_p": "新出《论语》智器重建本：498 章连成一张网，条条对得上原页。PDF，手机能看，也能打印。", "cta_wen_p": "读到不懂的地方？写信问一孔录，每周选答，进片署你的网名。",
   "h_motto": "一章一章，把经典原文读明白。", "h_intro": "每章先给原文、白话和一句话读懂，配一段视频；想细读的，往下有注家原话、底本原页和公开勘误，句句可核。",
   "h_start": "今日共读一章", "h_latest": "最新一章", "h_read": "读这一章", "h_recent": "最近讲的", "h_deep_h": "给细读的人", "h_deep_p": "一孔录讲过的每一句，都能在这里核。"},
 "en": {"ch_gist": "What this chapter says", "ch_deep": "Close reading and checking", "ch_deep_note": "For readers who want to go deeper or check our work: key words in the commentary, what other commentators say, textual variants, the commentaries in their own words with facsimile pages, pronunciation and corrections. Tap a heading to open it.", "ch_open_all": "Open all", "ch_close_all": "Close all",
   "cta_db_p": "New: the whole Analects as one connected book, 498 chapters and 931 checked links. PDF in English, Japanese or Chinese.", "cta_wen_p": "Something you don't understand? Write to us; each week we answer a question or two and credit you by name.",
   "h_motto": "Reading the classics, one chapter at a time.", "h_intro": "Each chapter starts with the original, a plain rendering and a one-line summary, with a short video. Further down, for close readers: the commentators' own words, facsimile pages and a public errata log.",
   "h_start": "Today’s shared chapter", "h_latest": "Latest chapter", "h_read": "Read this chapter", "h_recent": "Recently read", "h_deep_h": "For close readers", "h_deep_p": "Every line Yikonglu has read aloud can be checked here."},
 "ja": {"ch_gist": "この章の要点", "ch_deep": "精読と確認", "ch_deep_note": "じっくり読みたい方、確かめたい方へ：注の要となる語、諸家の説、異文、各注釈の原文と底本の頁、読み方、正誤。見出しを押すと開きます。", "ch_open_all": "すべて開く", "ch_close_all": "すべて閉じる",
   "cta_db_p": "新刊『論語』AI再構築版：全498章を一つの網につなぎ、一つずつ原本の頁で確かめました。日本語版 PDF。", "cta_wen_p": "分からないところは？一孔録に質問を。毎週いくつか選んでお答えし、お名前（ハンドル）を記します。",
   "h_motto": "一章ずつ、古典の原文を読み解く。", "h_intro": "各章はまず原文、現代語訳、一行の要点と短い動画から。その下に、精読する方のための注釈者の原文、底本の頁、公開の正誤表があります。",
   "h_start": "今日の共読の章", "h_latest": "最新の章", "h_read": "この章を読む", "h_recent": "最近読んだ章", "h_deep_h": "精読する方へ", "h_deep_p": "一孔録が読み上げた一句一句を、ここで確かめられます。"},
 "ko": {"ch_gist": "이 장의 요지", "ch_deep": "깊이 읽기와 확인", "ch_deep_note": "더 깊이 읽거나 확인하려는 분께: 주석의 핵심어, 여러 주석가의 설, 이문, 각 주석의 원문과 저본 쪽, 독음, 정오. 제목을 누르면 펼쳐집니다.", "ch_open_all": "모두 펼치기", "ch_close_all": "모두 접기",
   "cta_db_p": "새로 나온 《논어》 AI 재구성판: 498장을 하나의 그물로 잇고 하나하나 원본 쪽과 대조했습니다. PDF(중국어·영어·일본어).", "cta_wen_p": "모르는 대목이 있나요? 일공록에 질문하세요. 매주 한두 개를 골라 답하고 닉네임을 밝힙니다.",
   "h_motto": "한 장씩, 고전 원문을 읽어 냅니다.", "h_intro": "각 장은 원문, 풀이, 한 줄 요지와 짧은 영상으로 시작합니다. 그 아래에는 깊이 읽는 분을 위한 주석가의 원문, 저본 쪽, 공개 정오표가 있습니다.",
   "h_start": "오늘 함께 읽는 장", "h_latest": "최신 장", "h_read": "이 장 읽기", "h_recent": "최근 읽은 장", "h_deep_h": "깊이 읽는 분께", "h_deep_p": "일공록이 읽은 모든 구절은 여기서 확인할 수 있습니다."},
 "fr": {"ch_gist": "Ce que dit ce chapitre", "ch_deep": "Lecture approfondie et vérification", "ch_deep_note": "Pour qui veut lire de près ou vérifier : mots clés du commentaire, avis des autres commentateurs, variantes, commentaires dans leurs propres mots avec les pages de l'édition, prononciation et errata. Touchez un titre pour l'ouvrir.", "ch_open_all": "Tout ouvrir", "ch_close_all": "Tout fermer",
   "cta_db_p": "Nouveau : les Entretiens entiers comme un seul livre relié, 498 chapitres et 931 liens vérifiés. PDF en chinois, anglais ou japonais.", "cta_wen_p": "Un passage obscur ? Écrivez-nous ; chaque semaine nous répondons à une ou deux questions en citant votre pseudo.",
   "h_motto": "Lire les classiques, un chapitre à la fois.", "h_intro": "Chaque chapitre commence par l'original, une traduction et un résumé en une ligne, avec une courte vidéo. Plus bas, pour les lecteurs attentifs : les mots mêmes des commentateurs, les pages de l'édition et un registre public d'errata.",
   "h_start": "Le chapitre du jour, ensemble", "h_latest": "Dernier chapitre", "h_read": "Lire ce chapitre", "h_recent": "Lus récemment", "h_deep_h": "Pour les lecteurs attentifs", "h_deep_p": "Chaque phrase lue par Yikonglu peut être vérifiée ici."},
 "es": {"ch_gist": "Qué dice este capítulo", "ch_deep": "Lectura detenida y comprobación", "ch_deep_note": "Para quien quiera leer a fondo o comprobar: palabras clave del comentario, otros comentaristas, variantes, los comentarios con sus propias palabras y las páginas de la edición, pronunciación y erratas. Toque un título para abrirlo.", "ch_open_all": "Abrir todo", "ch_close_all": "Cerrar todo",
   "cta_db_p": "Nuevo: las Analectas completas como un solo libro conectado, 498 capítulos y 931 vínculos verificados. PDF en chino, inglés o japonés.", "cta_wen_p": "¿Algo que no entiende? Escríbanos; cada semana respondemos una o dos preguntas y citamos su nombre.",
   "h_motto": "Leer los clásicos, capítulo a capítulo.", "h_intro": "Cada capítulo empieza con el original, una traducción y un resumen de una línea, con un vídeo breve. Más abajo, para lectores atentos: las palabras exactas de los comentaristas, las páginas de la edición y un registro público de erratas.",
   "h_start": "Capítulo compartido de hoy", "h_latest": "Último capítulo", "h_read": "Leer este capítulo", "h_recent": "Leídos recientemente", "h_deep_h": "Para lectores atentos", "h_deep_p": "Cada frase que Yikonglu ha leído se puede comprobar aquí."},
}
for _c, _d in LC_UI.items(): EXTRA_UI.setdefault(_c, {}).update(_d)
ZH_UI.update(EXTRA_UI["zh-Hans"])

# 第三批：版本说明（/banben/）。内容是中文底账，外文页照中文显示。
BANBEN = [
 ("zhuxi", "朱熹《论语集注》（宋）", [
   ("bb_base", "《四部备要》本《论语集注》。本站原文与注的底本，视频里的朱注原页也用这一本。"),
   ("bb_img", "Wikimedia Commons 上的公版影印扫描；本站“底本原页”是同一扫描压缩后的图。"),
   ("bb_page", "“原页 N”是扫描文件的第 N 页（从 1 起算），不是原书叶码。"),
   ("bb_lic", "原书是公版。原页图只作核对展示。"),
   ("bb_use", "每章原文、注里的关键字、引文逐条核对表都据此本；转述和原话分开标。")]),
 ("huangkan", "皇侃《论语义疏》（梁）", [
   ("bb_base", "卷一、二（学而至里仁）：知不足斋丛书第七集本《论语集解义疏》（题魏何晏集解、梁皇侃义疏）。书目著录的乾隆五十三年（1788）是序年，扫描的具体印次未定。卷三至卷十（公冶长至尧曰）：日本宽延三年（1750）根本逊志校正和刻本，早稻田大学图书馆藏，第 2 至 5 册。"),
   ("bb_img", '<a href="https://commons.wikimedia.org/wiki/File:SSID-13146346_%E7%9F%A5%E4%B8%8D%E8%B6%B3%E9%BD%8B_%E7%AC%AC7%E9%9B%86_%E8%AB%96%E8%AA%9E%E7%BE%A9%E7%96%8F%E6%95%98_%E5%8D%B71-2.pdf" target="_blank" rel="noopener">Wikimedia Commons 影印扫描</a>（共 164 页）；卷三起的和刻本是 <a href="https://commons.wikimedia.org/wiki/File:WUL-ro12_00916_%E8%AB%96%E8%AA%9E%E9%9B%86%E8%A7%A3%E7%BE%A9%E7%96%8F_2.pdf" target="_blank" rel="noopener">Wikimedia Commons 早稻田大学图书馆影印</a>（第 2 至 5 册各一个文件）。'),
   ("bb_page", "“原刻本扫描第 N 页”是该扫描文件的第 N 页（从 1 起算）；卷一第一叶正面是第 29 页，背面第 30 页，以下按版心正背推。和刻本写“第 M 册第 N 页”，是该册扫描文件的第 N 页（含封面，从 1 起算）。"),
   ("bb_lic", "公版。"),
   ("bb_use", "每章录疏文第一个完整释义单元，句读是一孔录加的；全文请点扫描页看原刻。还没对过扫描或把握“存疑”的章先不放。")]),
 ("heyan", "何晏《论语集解》（三国魏）", [
   ("bb_base", "清光绪十八年（1892）湖南宝庆务本书局重镌阮元本《论语注疏》所收《集解》。"),
   ("bb_img", "Wikimedia Commons 上的公版影印扫描，视频里“别家原页”用这一本。"),
   ("bb_page", "按扫描文件页（从 1 起算）。"),
   ("bb_lic", "公版。"),
   ("bb_use", "视频里讲到魏晋旧说时上原页；网站引文表里标“集解”的条目据此本。")]),
 ("yangbojun", "杨伯峻《论语译注》", [
   ("bb_base", "中华书局。"),
   ("bb_img", "不放书影。"),
   ("bb_page", "页码待核后补上。"),
   ("bb_lic", "在版权期。本站每章只短引一句译文，作“通行读法”对照，属适当引用；不收进开放数据。"),
   ("bb_use", "“各家注本”里的一句译文和“与朱注异同”表；异同说明是一孔录写的，不是原书文字。")]),
 ("qianmu", "钱穆《论语新解》", [
   ("bb_base", "通行本（版本信息待核后补）。"),
   ("bb_img", "不放书影。"),
   ("bb_page", "页码待按正版核过后补上。"),
   ("bb_lic", "在版权期。本站每章只短引一句，作通行读法对照，属适当引用；不收进开放数据。"),
   ("bb_use", "同上。")]),
 ("yikonglu", "一孔录自己的内容", [
   ("bb_base", "白话直译、“一孔录这样读”、引文逐条核对表、读音表、勘误记录。"),
   ("bb_img", "—"),
   ("bb_page", "—"),
   ("bb_lic", '<a href="https://creativecommons.org/licenses/by/4.0/deed.zh-hans" target="_blank" rel="license noopener">CC BY 4.0</a>：可以转载、改编，也可以商用，只须署名“一孔录 yikonglu.com”并附原页链接。'),
   ("bb_use", '可在<a href="/kaifang.html">开放数据</a>按篇下载。')]),
]
# 书目：按传统类目分组、各类目内按传统次序排，不按我们开讲的顺序；已开讲的 live=True，其余暗着
BOOK_GROUPS = [
 ("g13", [("zhouyi", "周易"), ("shangshu", "尚书"), ("shijing", "诗经"), ("zhouli", "周礼"), ("yili", "仪礼"), ("liji", "礼记"), ("zuozhuan", "春秋左传"),
          ("gongyang", "春秋公羊传"), ("guliang", "春秋谷梁传"), ("lunyu", "论语"), ("xiaojing", "孝经"), ("erya", "尔雅"), ("mengzi", "孟子")]),
 ("gdao", [("daodejing", "道德经"), ("zhuangzi", "庄子"), ("liezi", "列子"), ("huainanzi", "淮南子"), ("yinfujing", "黄帝阴符经"), ("qingjingjing", "清静经"), ("baopuzi", "抱朴子"), ("ganyingpian", "太上感应篇")]),  # 11-13 主人定佛道两格补全
 ("gfo", [("xinjing", "心经"), ("jingang", "金刚经"), ("tanjing", "六祖坛经"), ("sishierzhang", "四十二章经"), ("baiyu", "百喻经"), ("weimojie", "维摩诘经"), ("fahua", "法华经"), ("amituo", "阿弥陀经"), ("dizang", "地藏经"), ("lengyan", "楞严经")]),
 ("gshi", [("guoyu", "国语"), ("zhanguoce", "战国策"), ("shiji", "史记"), ("hanshu", "汉书"), ("houhanshu", "后汉书"), ("sanguozhi", "三国志"), ("zizhi", "资治通鉴"), ("zhenguan", "贞观政要")]),  # 11-13 主人定史部、子部补全
 ("gzi", [("xunzi", "荀子"), ("jinsilu", "近思录"), ("chuanxilu", "传习录"), ("sunzi", "孙子兵法"), ("hanfeizi", "韩非子"), ("mozi", "墨子"), ("lvshi", "吕氏春秋"), ("yanshi", "颜氏家训"), ("shishuo", "世说新语"), ("caigentan", "菜根谭")]),
 ("gmeng", [("sanzijing", "三字经")]),  # 11-08 主人定《三字经》进一期（论语之后、道德经之前，约 30 集）；底本副本 数据/网站素材/_三字经/  # 子部：不好归类的书先收这里，按四库子部次序 儒家→兵家
]
BOOK_SUB = {"liji": [("daxue", "大学"), ("zhongyong", "中庸")]}  # 挂在某书底下的篇
LIVE_BOOKS = {"lunyu"}
# 专题闯关的页面脚本（关卡图、专题页进度条、跟着一个人读的进度）；读本机 yk_xd 里读过的章
QUEST_JS = """<script>(function(){var T=@QT@;
var seen=[];try{seen=((JSON.parse(localStorage.getItem("yk_xd")||"{}").b||{}).lunyu||{}).seen||[]}catch(e){}
var S={};seen.forEach(function(c){S[c]=1});function cs(el){try{return JSON.parse(el.getAttribute("data-cs"))}catch(e){return[]}}
function f(t,o){return t.replace(/\\{(\\w+)\\}/g,function(_,k){return o[k]})}
var a=0,b=0,u={},nx=null;document.querySelectorAll(".qn").forEach(function(li){var C=cs(li),x=C.filter(function(c){return S[c]}).length,p=C.length?x/C.length:0;
 li.style.setProperty("--p",(p*100).toFixed(1)+"%");if(x){li.classList.add("lit");a++;C.forEach(function(c){if(S[c])u[c]=1})}if(x&&x==C.length){li.classList.add("done");b++}else if(!nx)nx=li;
 var q=li.querySelector(".qc");if(q&&x)q.textContent=x+" / "+C.length});
if(nx){nx.classList.add("next");var tg=document.createElement("em");tg.className="qtag";tg.textContent=T.nx;nx.querySelector("a").appendChild(tg)}
var st=document.getElementById("qstat");if(st&&a)st.textContent=f(T.st,{a:a,b:b,c:Object.keys(u).length});
document.querySelectorAll(".qbar").forEach(function(qb){var C=cs(qb),x=C.filter(function(c){return S[c]}).length,n=C.length;qb.querySelector(".bar i").style.width=(n?x*100/n:0)+"%";
 if(x)qb.classList.add("lit");if(x==n&&n)qb.classList.add("done");var s=qb.querySelector(".qbs");if(x&&s)s.textContent=f(T.rd,{x:x,n:n})+(x==n?" · "+T.ok:"");
 var g=qb.querySelector(".qgo"),c0=null;document.querySelectorAll(".ztl li[data-c]").forEach(function(li){var c=li.getAttribute("data-c");if(S[c])li.classList.add("rd");else if(!c0&&!li.classList.contains("wj"))c0=li});
 if(!c0)c0=[].filter.call(document.querySelectorAll(".ztl li[data-c]"),function(li){return !S[li.getAttribute("data-c")]})[0];
 if(c0){var A=c0.querySelector("a");g.innerHTML='<a class="btn" href="'+A.getAttribute("href")+'">'+T.go+A.querySelector("em").textContent+" "+A.querySelector("b").textContent+" →</a>"}else g.textContent=T.all});
document.querySelectorAll(".gsroute[data-cs]").forEach(function(r){var C=cs(r),x=C.filter(function(c){return S[c]}).length;if(!x)return;var d=r.querySelector("div"),e=document.createElement("small");e.className="qr";e.textContent=f(T.rd,{x:x,n:C.length});d.appendChild(e);if(x==C.length)r.classList.add("done")})
})();</script>"""

# 闯关各语种界面字（11-13 主人：各语言功能尽量一致）。js：页面脚本用；lv 第几关、bar 本关说明、nx 下一关、ch 章数、intro 关卡图说明、note 进度说明
QUEST_TXT = {
 "zh-Hans": {"js": {"st": "已点亮 {a} 关 · 通关 {b} 关 · 读过其中 {c} 章", "nx": "下一关", "ok": "通关", "go": "接着闯：", "all": "本关已通。再读一遍，也算温故。", "rd": "已读 {x} / {n} 章", "st0": "从第一关开始"},
             "lv": "第 {k} 关", "bar": "本关 {n} 章：读过一章点亮，章章读过通关", "nx": "下一关", "ch": "{n} 章", "intro": "{n} 关，一关一个字。读过本关一章就点亮，章章读过就通关；从第一关“{f}”开始。", "note": "进度只记在这台设备上，一孔录无需登录，不取隐私。"},
 "zh-Hant": {"js": {"st": "已點亮 {a} 關 · 通關 {b} 關 · 讀過其中 {c} 章", "nx": "下一關", "ok": "通關", "go": "接著闖：", "all": "本關已通。再讀一遍，也算溫故。", "rd": "已讀 {x} / {n} 章", "st0": "從第一關開始"},
             "lv": "第 {k} 關", "bar": "本關 {n} 章：讀過一章點亮，章章讀過通關", "nx": "下一關", "ch": "{n} 章", "intro": "{n} 關，一關一個字。讀過本關一章就點亮，章章讀過就通關；從第一關「{f}」開始。", "note": "進度只記在這台裝置上，一孔錄無需登入，不取隱私。"},
 "en": {"js": {"st": "{a} levels lit · {b} cleared · {c} chapters read", "nx": "Next", "ok": "cleared", "go": "Continue: ", "all": "Level cleared. Reading it again still counts as review.", "rd": "{x} / {n} chapters read", "st0": "Start from level 1"},
        "lv": "Level {k}", "bar": "{n} chapters: read one to light it up, read them all to clear it", "nx": "Next level", "ch": "{n} ch.", "intro": "{n} levels, one character each. Read one chapter of a level to light it up; read every chapter to clear it. Start with level 1, “{f}”.", "note": "Progress is kept on this device only. No sign-in, no personal data."},
 "ja": {"js": {"st": "{a} 関点灯 · {b} 関突破 · うち {c} 章読了", "nx": "次の関", "ok": "突破", "go": "続きから：", "all": "この関は突破済み。もう一度読むのも温故です。", "rd": "{x} / {n} 章読了", "st0": "第一関から"},
        "lv": "第 {k} 関", "bar": "この関は {n} 章：一章読めば点灯、全章読めば突破", "nx": "次の関", "ch": "{n} 章", "intro": "全 {n} 関、一関一字。その関の章を一つ読めば点灯、全部読めば突破。第一関「{f}」から始めましょう。", "note": "進み具合はこの端末だけに保存されます。ログイン不要、個人情報は取りません。"},
 "ko": {"js": {"st": "{a}관 점등 · {b}관 통과 · 그중 {c}장 읽음", "nx": "다음 관", "ok": "통과", "go": "이어서: ", "all": "이 관은 통과했습니다. 다시 읽는 것도 온고입니다.", "rd": "{n}장 중 {x}장 읽음", "st0": "제1관부터"},
        "lv": "제{k}관", "bar": "이 관은 {n}장: 한 장 읽으면 점등, 모두 읽으면 통과", "nx": "다음 관", "ch": "{n}장", "intro": "{n}관, 한 관에 한 글자. 한 장을 읽으면 점등, 모든 장을 읽으면 통과. 제1관 “{f}”부터 시작하세요.", "note": "진행 상황은 이 기기에만 저장됩니다. 로그인도 개인정보도 필요 없습니다."},
 "fr": {"js": {"st": "{a} niveaux allumés · {b} réussis · {c} chapitres lus", "nx": "Suivant", "ok": "réussi", "go": "Continuer : ", "all": "Niveau réussi. Relire compte aussi comme révision.", "rd": "{x} / {n} chapitres lus", "st0": "Commencer au niveau 1"},
        "lv": "Niveau {k}", "bar": "{n} chapitres : lisez-en un pour l’allumer, tous pour le réussir", "nx": "Niveau suivant", "ch": "{n} ch.", "intro": "{n} niveaux, un caractère chacun. Un chapitre lu allume le niveau ; tous lus, il est réussi. Commencez par le niveau 1, « {f} ».", "note": "La progression reste sur cet appareil. Sans compte, sans données personnelles."},
 "es": {"js": {"st": "{a} niveles encendidos · {b} superados · {c} capítulos leídos", "nx": "Siguiente", "ok": "superado", "go": "Continuar: ", "all": "Nivel superado. Releer también cuenta como repaso.", "rd": "{x} / {n} capítulos leídos", "st0": "Empezar por el nivel 1"},
        "lv": "Nivel {k}", "bar": "{n} capítulos: lee uno para encenderlo, todos para superarlo", "nx": "Siguiente nivel", "ch": "{n} cap.", "intro": "{n} niveles, un carácter cada uno. Un capítulo leído enciende el nivel; todos leídos, lo superas. Empieza por el nivel 1, «{f}».", "note": "El progreso se guarda solo en este dispositivo. Sin registro, sin datos personales."},
 "de": {"js": {"st": "{a} Stufen erleuchtet · {b} geschafft · {c} Kapitel gelesen", "nx": "Weiter", "ok": "geschafft", "go": "Weiter mit: ", "all": "Stufe geschafft. Nochmals lesen ist Wiederholung.", "rd": "{x} / {n} Kapitel gelesen", "st0": "Mit Stufe 1 beginnen"},
        "lv": "Stufe {k}", "bar": "{n} Kapitel: eines lesen erleuchtet die Stufe, alle lesen schafft sie", "nx": "Nächste Stufe", "ch": "{n} Kap.", "intro": "{n} Stufen, je ein Schriftzeichen. Ein gelesenes Kapitel erleuchtet die Stufe, alle gelesen heißt geschafft. Beginne mit Stufe 1, „{f}“.", "note": "Der Fortschritt bleibt auf diesem Gerät. Keine Anmeldung, keine persönlichen Daten."},
 "vi": {"js": {"st": "Đã sáng {a} cửa · qua {b} cửa · đọc {c} chương", "nx": "Cửa tiếp", "ok": "đã qua", "go": "Đọc tiếp: ", "all": "Đã qua cửa này. Đọc lại cũng là ôn cố.", "rd": "Đã đọc {x} / {n} chương", "st0": "Bắt đầu từ cửa 1"},
        "lv": "Cửa {k}", "bar": "{n} chương: đọc một chương là sáng, đọc hết là qua cửa", "nx": "Cửa tiếp theo", "ch": "{n} chương", "intro": "{n} cửa, mỗi cửa một chữ. Đọc một chương là sáng cửa, đọc hết là qua cửa. Bắt đầu từ cửa 1, “{f}”.", "note": "Tiến độ chỉ lưu trên thiết bị này. Không cần đăng nhập, không lấy dữ liệu cá nhân."},
 "id": {"js": {"st": "{a} level menyala · {b} tuntas · {c} bab dibaca", "nx": "Berikutnya", "ok": "tuntas", "go": "Lanjut: ", "all": "Level tuntas. Membaca ulang juga terhitung mengulang.", "rd": "{x} / {n} bab dibaca", "st0": "Mulai dari level 1"},
        "lv": "Level {k}", "bar": "{n} bab: baca satu untuk menyalakan, baca semua untuk menuntaskan", "nx": "Level berikutnya", "ch": "{n} bab", "intro": "{n} level, satu aksara tiap level. Baca satu bab untuk menyalakan level, baca semua untuk menuntaskannya. Mulai dari level 1, “{f}”.", "note": "Progres hanya tersimpan di perangkat ini. Tanpa login, tanpa data pribadi."},
 "ru": {"js": {"st": "Зажжено уровней: {a} · пройдено: {b} · прочитано глав: {c}", "nx": "Дальше", "ok": "пройден", "go": "Продолжить: ", "all": "Уровень пройден. Перечитать — тоже повторение.", "rd": "Прочитано {x} из {n}", "st0": "Начните с уровня 1"},
        "lv": "Уровень {k}", "bar": "Глав: {n}. Прочтите одну — уровень зажжётся, все — пройден", "nx": "Следующий уровень", "ch": "гл.: {n}", "intro": "Уровней: {n}, по одному иероглифу. Прочитайте одну главу уровня — он зажжётся, все — пройден. Начните с уровня 1, «{f}».", "note": "Прогресс хранится только на этом устройстве. Без входа и личных данных."},
}
def quest_js(code):
    return QUEST_JS.replace("@QT@", json.dumps(QUEST_TXT.get(code, QUEST_TXT["en"])["js"], ensure_ascii=False))

SHOW_DRAFT = True  # “初稿改动”比例：首页小字与方法页
DRAFT_FILE = "/mnt/project-files/一孔学-内-自媒体/数据/搜索位次/初稿改动.json"
YXL_FILE = "/mnt/project-files/一孔学-内-自媒体/数据/搜索位次/影响力.json"  # 一孔影响力（找到分），每天自动更新
YXL_WEEK_FILE = "/mnt/project-files/一孔学-内-自媒体/数据/搜索位次/最新.json"  # 本周日采（含没测完的平台）

def yxl_merge(y, w):
    """主人 11-12 定：日采结果上网站。影响力.json 只收测完的平台，本周没测完的（如 YouTube）从 最新.json 补上，注明已测几章；本周找到分按已有平台重算。"""
    if not y or not w or w.get("week") != (y.get("history") or [{}])[-1].get("week"): return y
    y = json.loads(json.dumps(y)); P = w.get("platforms", {}); n = w.get("chapters")
    have = {p["key"] for p in y.get("platforms", [])}
    for k, v in P.items():
        if "." in k: continue
        subs = [x for kk, x in P.items() if kk.startswith(k + ".")]
        meas = max((x.get("measured") or 0) for x in subs) if subs else None
        done = all(x.get("complete", True) for x in subs)
        if k in have:
            for p in y["platforms"]:
                if p["key"] == k: p["measured"] = meas
            continue
        if v.get("score") is None: continue
        y["platforms"].append({"key": k, "name": v["name"], "score": v["score"], "share": v.get("share"), "measured": meas, "partial": not done})
    sc = [p["score"] for p in y["platforms"] if p.get("score") is not None]
    if sc:
        y["score"] = round(sum(sc) / len(sc), 1)
        y["history"][-1]["score"] = y["score"]
        shs = [p["share"] for p in y["platforms"] if p.get("share") is not None]
        y["share"] = round(sum(shs) / len(shs), 2) if shs else None
        y["history"][-1]["share"] = y["share"]
    y["chapters"] = n or y.get("chapters")
    try:  # 日采每天写 最新.json，更新日期取它（北京日期）
        t = datetime.datetime.fromtimestamp(os.path.getmtime(YXL_WEEK_FILE), datetime.timezone(datetime.timedelta(hours=8)))
        y["updated"] = max(y.get("updated") or "", t.date().isoformat())
    except OSError: pass
    return y
FANGFA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fangfa.json"), encoding="utf-8"))  # 核验方法页七语文字
KAIFANG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kaifang.json"), encoding="utf-8"))  # 开放数据页：开放与不开放的分界（七语）
WEN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wen.json"), encoding="utf-8"))  # 问一孔页（七语）
EPIS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "episodes.json"), encoding="utf-8"))
ZT_DIR = os.path.join("/mnt/project-files/一孔学-内-自媒体/数据/网站素材", "_专题")  # 专题表.json：一专题一页、页内按书分段
def load_zhuanti():
    f = os.path.join(ZT_DIR, "专题表.json")
    if os.path.exists(f): return json.load(open(f, encoding="utf-8"))["topics"]
    return [{"slug": a, "name": b, "intro": "", "books": {"lunyu": {"terms": c, "intro": d}}} for a, b, c, d in ZHUANTI]
# 旧专题表（只论语）；现在只在 专题表.json 缺席时用
ZHUANTI = [
 ("ren", "仁", ["仁"], "“仁”是《论语》里分量最重的一个字。孔子从不给它下一句定义，总是对不同的人、在不同的处境里说怎么做。朱熹说“仁者，爱之理，心之德也”。"),
 ("xiao", "孝", ["孝"], "《论语》里问孝的人很多，孔子按各人的毛病答，所以同一个问题有好几种答法。朱熹注“善事父母为孝”。"),
 ("li", "礼", ["礼"], "“礼”在《论语》里既是祭祀、朝聘这些具体仪节，也是待人处事的分寸。朱熹说礼是“天理之节文，人事之仪则”。"),
 ("junzi", "君子", ["君子"], "“君子”本来指有位的人，孔子多用来说有德的人，常和“小人”对着讲。朱熹注“君子，成德之名”。"),
 ("xue", "学", ["学"], "《论语》开篇就是“学而时习之”。朱熹说“学之为言效也”：学是照着做，不只是读书。"),
 ("xin", "信", ["信"], "“信”有说话算数和取信于人两层。朱熹注“以实之谓信”，又说“信，约信也”。"),
 ("zheng", "政", ["政"], "孔子论政，常把政令刑罚和德礼对着讲，落点在治理者自己。朱熹注“政之为言正也”。"),
 ("le", "乐", ["乐"], "“乐”有两个读音：读 yuè 是礼乐的乐，读 lè 是快乐的乐。这里两种都收，各章怎么读见该章读音表。"),
 ("you", "友", ["友", "朋"], "交友在《论语》里是修身的一部分：曾子每天问自己“与朋友交而不信乎”，孔子说“无友不如己者”。这里收“友”“朋”两个字。"),
 ("ming", "命", ["命"], "“命”有天命、命令、寿命几层意思。孔子自述“五十而知天命”，朱熹解天命为“天道之流行而赋于物者”。"),
]

def seo_head(text, n=22):
    """给标题用的首句：去掉“子曰：”“子贡问曰：”一类引导语，按句末标点取句，不够 8 字就再取一句，最长 n 字（主人 11-07 定：标题写读者会搜的话）。"""
    t = re.sub(r"^[^：，。]{1,12}[曰云]：", "", text.strip())
    s = ""
    for m in re.finditer(r"[^。？！]+[。？！]?", t):
        s += m.group(0)
        if len(s) >= 8: break
    s = s.strip() or t
    return s if len(s) <= n else s[:n - 1] + "…"

YKCITE = '<p class="ykcite"><button type="button" onclick="var s=this.closest(\'.ykan\'),t=s.querySelector(\'p\').textContent,u=location.origin+location.pathname+\'#ykan\',b=this,d=function(){b.textContent=\'已复制\';setTimeout(function(){b.textContent=\'引用这段一孔按\'},1200)};var q=document.querySelector(\'blockquote[data-short]\');t=q&&q.dataset.short?t+\'——\'+q.dataset.src+\' \'+q.dataset.short:t+\'——\'+document.querySelector(\'h1\').textContent+\'，一孔录 \'+u;navigator.clipboard?navigator.clipboard.writeText(t).then(d):prompt(\'\',t)">引用这段一孔按</button></p>'
# 书页观感（11-13 主人：从书架点进去，章页跟着书的逻辑）：书目录、篇目录、章页头部放一册小书封；本篇章节读过的打勾；篇卡显示“你读过几章”
def mcv(P, qian="", big=False, book="lunyu", name="论语"):
    return f'<a class="mcv{" big" if big else ""}" href="{P}{book}/" aria-label="{name}"><span class="qian{" l5" if len(qian) >= 5 else ""}">{qian or name}</span></a>'
BOOK_JS = """<script>(function(){var s=[];try{s=((JSON.parse(localStorage.getItem("yk_xd")||"{}").b||{}).lunyu||{}).seen||[]}catch(e){return}if(!s.length)return;
var S={},P={};s.forEach(function(c){S[c]=1;var p=String(c).split(".")[0];P[p]=(P[p]||0)+1});
document.querySelectorAll("aside li[data-c]").forEach(function(li){if(S[li.getAttribute("data-c")])li.classList.add("rd")});
var H=/Hant/.test(document.documentElement.lang),Z=/^zh/.test(document.documentElement.lang);
document.querySelectorAll(".pcard[data-p]").forEach(function(a){var n=P[a.getAttribute("data-p")];if(!n)return;a.classList.add("rd");if(!Z)return;var e=document.createElement("em");e.className="mine";e.textContent=(H?"你讀過 ":"你读过 ")+n+" 章";a.appendChild(e)})})();</script>"""
FROM_JS = """<script>(function(){var q=new URLSearchParams(location.search),f=(q.get('from')||'').toLowerCase();if(!f)return;
var V={yt:'YouTube',bili:'哔哩哔哩',dy:'抖音',ks:'快手',sph:'视频号'},T={xhs:'小红书',pod:'播客',gzh:'公众号',zhihu:'知乎',bjh:'百家号',tt:'头条'},nm=V[f]||T[f];
try{q.delete('from');history.replaceState(null,'',location.pathname+(q.toString()?'?'+q:'')+location.hash)}catch(e){}
if(!nm)return;try{if(sessionStorage.getItem('yk_from'))return;sessionStorage.setItem('yk_from',f)}catch(e){}
var H=document.querySelector('.chhead .wrap');if(!H)return;var d=document.createElement('p');d.className='fromtip';var m,go=null;
if(V[f]){m='从'+nm+'过来的？片里讲的原文都在下面，点任何一句，原页上那几列就框出来；朱注和各家说法在“细读与核对”。'}
else if(f==='xhs'){m='从小红书过来的？这一章可以一键做成带原文底纹的分享图，存下来就能发。';go=['生成分享图',function(){var p=document.querySelector('.shpanel');if(!p)return;if(p.hidden)p.previousElementSibling.click();var b=p.querySelector('[data-p=card]');if(b)b.click()}]}
else if(f==='pod'){m='从播客过来的？按原文上方的“音”，可以边听原文朗读边看原页。';go=['听原文',function(){var b=document.querySelector('.ldbtn');if(b){b.scrollIntoView({block:'center',behavior:'smooth'});b.click()}}]}
else{m='从'+nm+'过来的？这里有原文、原页和一孔按，每条引文都标了底本页码，点句就能核。'}
d.textContent=m;if(go){var a=document.createElement('button');a.type='button';a.textContent=go[0];a.onclick=go[1];d.appendChild(a)}
var x=document.createElement('button');x.type='button';x.className='fx';x.setAttribute('aria-label','关闭');x.textContent='×';x.onclick=function(){d.remove()};d.appendChild(x);H.appendChild(d)})();</script>"""
def seo_q(text):  # 问句用的短首句：第一个分句，≤12 字
    return re.split(r"[，。？！；：]", seo_head(text, 40))[0][:12]

def split_ju(text):
    """原文按句切：句末是 。？！ 或其后紧跟的引号。"""
    out = re.findall(r"[^。？！]+[。？！]+[”’」』]*|[^。？！]+$", text)
    return [x for x in out if x.strip()]

def parse_zhuben(d):
    """读注本索引 CSV，返回 {章号: {"huang": {...}, "yang": {...}, "qian": {...}}}。"""
    out = {}
    if not os.path.isdir(d): return out
    def rows(prefix):
        """同一家的多份 CSV（分篇交、v1/v2）合起来：版本号小的先读，大的覆盖；同版本按文件名。空行（暂停未核）不覆盖。"""
        ver = lambda f: (int((re.search(r"-v(\d+)", f) or [0, 0])[1]), f)
        out_ = {}
        for f in sorted((x for x in glob.glob(os.path.join(d, prefix + "-*逐章*.csv")) if "映射" not in x), key=ver):
            for r in csv.DictReader(open(f, encoding="utf-8-sig")):
                if r.get("章号"): out_[r["章号"].strip()] = r
        return list(out_.values())
    CN = "一二三四五六七八九十"
    for r in rows("皇疏"):
        t = (r.get("义疏首句") or "").strip().replace("其其孝悌者也", "其，其孝悌者也")  # 11-03 核收意见：疏先单释“其”字
        sure = (r.get("把握") or "").strip()
        if not t or not r.get("义疏首句PDF页") or sure == "存疑" or re.search(r"待(核|复核|二次|校字|补)|暂停", r.get("状态") or ""): continue  # 宁缺：存疑、待复核的不上
        p = int(r["章号"].split(".")[0]); j = (r.get("卷") or "").strip()
        if j.isdigit(): j = CN[int(j) - 1] if int(j) <= 10 else j
        ed = "zbz" if p <= 4 else "wk"  # 知不足斋本只有卷一二（学而至里仁）；公冶长起用 1750 年和刻本
        ce = {5: 2, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3, 12: 3, 13: 4, 14: 4, 15: 4, 16: 4}.get(p, 5)
        out.setdefault(r["章号"], {})["huang"] = {"text": t, "juan": j, "page": r["义疏首句PDF页"].strip(), "leaf": r.get("章首叶面", ""), "ed": ed, "ce": ce}
    pageref = re.compile(r"[^。；]*书\s*\d+(?:[—-]\d+)?页（PDF[^）]*）[。；]?|（PDF[^）]*）")
    for key, prefix in (("yang", "杨伯峻"), ("qian", "钱穆")):
        for r in rows(prefix):
            cmp_ = pageref.sub("", r["与朱注比较"]).replace("。；", "；").strip().rstrip("；")
            mm = re.match(r"^[杨钱]\d+\.\d+：", cmp_)  # 朱注一章并杨本多章：“杨5.1：同解：……；杨5.2：……”，按第一段判类，说明保留全文
            pre = cmp_[mm.end():] if mm else None
            m = re.match(r"^([^：]{1,8})：(.*)$", pre if pre is not None else cmp_)
            head, body = (m.group(1), m.group(2)) if m else ("", cmp_)
            if pre is not None: body = cmp_
            META = {"同解": "k_same", "同旨": "k_same", "同解为主": "k_same", "主旨相近": "k_same", "同一方向": "k_same", "同属至、正之解": "k_same",
                    "异读": "k_diff", "异读（人物）": "k_diff", "名物异读": "k_diff", "数量差异": "k_diff",
                    "补充阐释": "k_add", "补充": "k_add", "同解而有扩展": "k_add",
                    "有轻重差别": "k_shade", "主取不同": "k_shade", "解释重心不同": "k_shade", "解法有别": "k_shade", "同旨而申说不同": "k_shade", "字义范围不同": "k_word0"}
            kind = META.get(head)
            mx = re.match(r"^(.*?)(字|的)?(主取|主训|读义|解释重心|解释|重心|侧重|方向|指向|句法取向|所责|所承|所问|所叹焦点|名物|身份|事迹|范围|语气与章旨|语气|指涉|句读|句义|义|器具解释|历史指称|章旨|经文选择|文字句读|取义)?(不同|有别|相反|相异|略异|异解|有异读|有异)$", head) if head and not kind else None
            if mx:  # 钱本元判断如“怨的方向不同”“里字主取不同”：关键字取前面的字，类别按轻重
                kind = "k_shade" if (mx.group(4) == "略异" or (mx.group(3) or "") in ("侧重", "重心", "解释重心")) else "k_diff"
                head_is_word = True; head = mx.group(1) if 0 < len(mx.group(1)) <= 6 else ""
                if not head: head_is_word = False
            if mx: pass
            elif kind == "k_word0": kind, head_is_word = "k_word", False
            else: head_is_word = bool(head and not kind)
            if head and not kind: kind = "k_word"
            if not head: kind = "k_same" if "同" in cmp_[:4] else "k_diff"
            if not r.get("译文一句", "").strip(): continue  # 重出省译的章不放
            src_ch = (r.get("引句实际来源章") or "").strip()
            if src_ch and src_ch != r["章号"].strip(): continue  # 重出章借用别章译句的不放，免得张冠李戴
            out.setdefault(r["章号"], {})[key] = {"text": r["译文一句"].strip(), "key": head if head_is_word else "", "kind": kind, "say": body if head else cmp_, "sure": {"定": "s_ding", "较稳": "s_wen", "存疑": "s_yi"}.get((r.get("把握") or "").strip(), "")}
    return out

_WJP = {}
def wj_pages():  # 原页 jpg 尺寸（未讲章原页同屏用）；只读文件头
    if not _WJP and getattr(ZJ, "YDIR", None):
        from PIL import Image
        for f in os.listdir(ZJ.YDIR):
            if f.endswith(".jpg"):
                w, h = Image.open(os.path.join(ZJ.YDIR, f)).size; _WJP[f[:-4]] = {"w": w, "h": h}
    return _WJP

def esc(s): return html.escape(s, quote=True)

def wj_title(text, n=1):
    """未讲章没有标题：取原文开头一句（去掉“子曰：”之类），最多 14 字。开头的说话人（“曾子曰”）同“子曰”一样省掉；n 为再多接几句。"""
    t = re.sub(r"^(子|孔子)曰[：；]", "", text)
    seg = [x for x in re.split(r"[，。？！；：]", t) if x]
    while len(seg) > 1 and seg[0].endswith("曰"): seg = seg[1:]  # “曾子曰”这类说话人和“子曰”一样省掉
    k = 1
    while k < len(seg) and len("".join(seg[:k])) < 2: k += 1
    e = min(len(seg), k + n - 1)
    while e < len(seg) and seg[e - 1].endswith("曰"): e += 1
    return "".join(seg[:e])[:14]

_WJT = {}
def wj_titles(qw):
    """全书未讲章标题：同一篇里撞名的，逐句往后接到分得开为止。"""
    if id(qw) in _WJT: return _WJT[id(qw)]
    out = {c: wj_title(v["text"]) for c, v in qw.items()}
    for n in range(2, 6):
        seen = {}
        for c, t in out.items(): seen.setdefault((c.split(".")[0], t), []).append(c)
        dup = [c for v in seen.values() if len(v) > 1 for c in v]
        if not dup: break
        for c in dup: out[c] = wj_title(qw[c]["text"], n)
    _WJT[id(qw)] = out
    return out

def cpbtn(L, text, link, link_only=False):
    """复制按钮：data-t 是要复制的引文（空则只复制链接）。"""
    sep = "，" if L.code.startswith("zh") else ", "
    b = "" if link_only else f'<button class="cp" data-t="{esc(text + sep + link)}">{L.t("cp_entry")}</button>'
    return b + f'<button class="cp" data-t="{esc(link)}">{L.t("cp_link")}</button>'

def clean(text):
    text = re.sub(r"[^。；]*【[^】]*待核[^】]*】[。；]?", "", text)  # 整句带【待核】的不上
    text = re.sub(r"（[^（）]*(待核|书里)[^（）]*）", "", text)
    parts = [p for p in re.split(r"(?<=[，；])", text) if "待核" not in p]
    text = "".join(parts).strip()
    text = re.sub(r"^（标题问）", "", text)
    text = text.replace("照今：", "放到今天：").replace("片里", "这里")
    text = re.sub(r"【[^】]*】", "", text)
    return text.rstrip("；，").strip()

NEIBU_DING = re.compile(r"主人\s*\d{1,2}-\d{1,2}\s*定")  # 内部“谁哪天定的”不上页面，只留定下的结论

def parse_zhaji(path):
    out, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = NEIBU_DING.sub("", line.rstrip("\n"))
        m = re.match(r"^### \S+ (\d+\.\d+) (.+)$", line)
        if m:
            cur = {"no": m.group(1), "title": re.sub(r"（[^）]*(?:章号|底本|为准|待核|待定)[^）]*）", "", m.group(2)).strip(), "fields": {}, "tags": []}  # 11-13 主人：编辑注记（如“朱注本章号以底本为准”）不进对外章名
            out[cur["no"]] = cur
            continue
        if not cur: continue
        if line.startswith("集："):
            t = re.search(r"标签：(.*)$", line)
            if t: cur["tags"] = [x.lstrip("#") for x in t.group(1).split() if x.startswith("#")]
            continue
        m = re.match(r"^- ([^：]+)：(.*)$", line)
        if m and m.group(1) in {f[0] for f in FIELDS}:
            v = clean(m.group(2))
            if v and not v.startswith("这里只取"): cur["fields"][m.group(1)] = v
    return out

def quotes(s):
    return re.sub(r"“([^”]+)”", r'<span class="q">“\1”</span>', esc(s).replace("&quot;", '"'))

def md_tables(lines, start_pat):
    rows, on, intable = [], False, False
    for l in lines:
        if re.match(r"^## ", l):
            if on and rows: break
            on = bool(re.match(start_pat, l)); continue
        if not on: continue
        if l.startswith("|"):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells): intable = True; continue
            if intable: rows.append(cells)
        elif intable and rows and not l.strip(): break
    return rows

CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
def cn2int(t):
    t = t.strip()
    if t.isdigit(): return int(t)
    if "十" in t:
        a, b = t.split("十", 1)
        return (CN[a] if a else 1) * 10 + (CN[b] if b else 0)
    return CN[t]

def cn_chs(s):  # 稿里节题的章号：“三十八至四十”“三十、三十一”“一、二” → [38, 39, 40] 等
    out = []
    for part in s.split("、"):
        if "至" in part:
            a, b = part.split("至", 1); out += list(range(cn2int(a), cn2int(b) + 1))
        else: out.append(cn2int(part))
    return out
PIAN_NUM = {v[0]: k for k, v in PIAN.items()}

def pdf_pages(page):  # “PDF084—085”这类跨页范围展开成各页
    out = []
    for a, b in re.findall(r"PDF0*(\d+)(?:\s*[—–-]\s*(?:PDF)?0*(\d+))?", page):
        a = int(a); b = int(b) if b else a
        out += [str(n) for n in range(a, b + 1)] if a <= b <= a + 3 else [str(a)]
    return out

def parse_gao(path, yw):
    L = NEIBU_DING.sub("", open(path, encoding="utf-8").read().replace("\r", "")).split("\n")
    kmap, cur = {}, None
    for l in L:
        m = re.match(r"^### (?:篇题；)?第(.+?)章", l)
        if m: cur = m.group(0)
        if re.match(r"^### (开场|片尾)", l): cur = None
        k = re.match(r"^\*\*(K\d+)", l)
        if k and cur and "引子" not in l: kmap[k.group(1)] = cur  # 下篇引子不算本章
    pnum = next((v for k2, v in PIAN_NUM.items() if k2 in os.path.basename(path)), None)
    out = {}
    sec2ch = {sec: [f"{pnum}.{n}" for n in cn_chs(re.match(r'^### (?:篇题；)?第(.+?)章', sec).group(1))] for sec in set(kmap.values())} if pnum else {}
    HAN = lambda t: set(re.sub(r"[^\u3400-\u9fff]", "", t)) - set("之也者而其不以为于曰子乎矣焉则所")
    def pick(cs, text):  # 合讲一节：引文挂到字面最贴的那一章（数相同字），并列取前一章
        if len(cs) == 1: return cs[0]
        h = HAN(text)
        return max(cs, key=lambda c: (len(h & HAN(yw.get(c, ""))), -cs.index(c)))
    for row in md_tables(L, r"^## 引文取处"):
        if len(row) < 4: continue
        k, text, src, page = row[:4]
        km = re.match(r"\s*(K\d+)", k); cs = sec2ch.get(kmap.get(km.group(1) if km else k))
        if not cs or "待核" in page or "待核" in text: continue
        if src == "经文":
            for c in cs: out.setdefault(c, {"cites": [], "reads": []}).setdefault("qw_pages", []).extend(pdf_pages(page))
            continue
        c = pick(cs, text)
        para = bool(re.search(r"（[^（）]*(转述)[^（）]*）", text)) and not re.search(r"只原样念|前半转述|前后转述", text)
        text = INTERNAL.sub("", text).strip("；; ")
        if not text: continue
        pages = pdf_pages(page)
        other = ""
        if not pages:
            m = re.search(r"核到（([^（）]*)", page)
            other = m.group(1).split("，")[0].split("；")[0] if m else ""
        out.setdefault(c, {"cites": [], "reads": []})["cites"].append({"text": text, "src": re.sub(r"（Codex[^（）]*）", "", src.replace("**", "")), "pages": pages, "para": para, "other": other})
    for row in md_tables(L, r"^## 读音"):
        if len(row) < 3: continue
        zi, pos, du = row[:3]
        if "见注" in du: continue
        for c in dict.fromkeys(c for cs in sec2ch.values() for c in cs):
            if c in yw and pos and any(x and x in yw[c] for x in pos.split("、")):
                r = out.setdefault(c, {"cites": [], "reads": []})["reads"]
                if (zi, pos) not in [(a["zi"], a["pos"]) for a in r]:
                    r.append({"zi": zi, "pos": pos, "du": du})
    return out

def parse_kanwu(path):
    rows = []
    if not os.path.exists(path): return rows
    for l in open(path, encoding="utf-8"):
        if l.startswith("|") and not l.startswith("| 日期") and not re.match(r"^\|[-| ]+\|$", l.strip()):
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            if len(c) >= 7 and re.match(r"\d{4}-\d{2}-\d{2}", c[0]):
                r = [x.replace("线程", "") for x in c[:8]] + [""] * (8 - len(c[:8]))
                if not r[7] or r[7] in ("—", "-", "自查", "一孔录"): r[7] = "一孔录自查"
                rows.append(r)
    return rows

HEAD_FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;900&family=Noto+Serif+JP:wght@400;600;900&family=Noto+Serif+KR:wght@400;600;900&family=Noto+Serif:wght@400;600;900&display=swap" rel="stylesheet" media="print" onload="this.media=\'all\'">'
MAIL = '<picture class="mail"><source srcset="/assets/mail-dark.png" media="(prefers-color-scheme:dark)"><img src="/assets/mail.png" alt="email (image)" width="211" height="26"></picture>'
SAME_AS = ["https://www.youtube.com/@yikonglu", "https://x.com/yikonglu", "https://ko-fi.com/yikonglu"]  # 各平台账号另由 PLAT_LINKS 补进（见 main 里的首页 Organization）
# 一孔按署名短答（智器引用，主人 11-08 定）：落点（片里落点）作首句结论，第二句说与通行读法差在哪；素材只取札记里已有的“片里落点”“常见读法”“字眼”，不另编。
YKAN = {  # 主人 11-09 晚：署名只写“一孔按”，不带括号解释（解释在方法页、关于页）。语种: (署名开头, 常见读法是陈述时, 常见读法里自带引号时, 常见读法是问句时, 朱注依据句开头)
 "zh": ("一孔按：", "通行说法多是“{c}”，一孔录的落点不在这里。", "通行说法多是：{c}；一孔录的落点不在这里。", "常有人问“{c}”，上面是一孔录的回答。", "朱注原话："),
 "en": ("Yikonglu's reading: ", "The common view is “{c}”; Yikonglu's reading puts the weight elsewhere.", "The common view: {c}. Yikonglu's reading puts the weight elsewhere.", "A common question is “{c}” — the line above is Yikonglu's answer.", "Zhu Xi's commentary: "),
 "ja": ("一孔按：", "よくある読みは「{c}」。一孔録の読みの重心はそこにない。", "よくある読み：{c}。一孔録の読みの重心はそこにない。", "よく出る問いは「{c}」。上がその一孔録の答え。", "朱注の原文："),
 "ko": ("일공안: ", "흔한 읽기는 “{c}”이지만, 일공록의 읽기는 무게를 다른 데 둔다.", "흔한 읽기: {c}. 일공록의 읽기는 무게를 다른 데 둔다.", "흔히 “{c}”라고 묻는데, 위가 일공록의 답이다.", "주희 주석 원문: "),
 "fr": ("Lecture de Yikonglu : ", "La lecture courante dit « {c} » ; Yikonglu place l'accent ailleurs.", "Lecture courante : {c}. Yikonglu place l'accent ailleurs.", "On demande souvent « {c} » ; ce qui précède est la réponse de Yikonglu.", "Commentaire de Zhu Xi : "),
 "es": ("Lectura de Yikonglu: ", "La lectura habitual dice «{c}»; Yikonglu pone el peso en otro lugar.", "Lectura habitual: {c}. Yikonglu pone el peso en otro lugar.", "Se pregunta a menudo «{c}»; lo anterior es la respuesta de Yikonglu.", "Comentario de Zhu Xi: "),
 "de": ("Yikonglus Lesart: ", "Die übliche Lesart sagt „{c}“; Yikonglu legt das Gewicht anderswohin.", "Übliche Lesart: {c}. Yikonglu legt das Gewicht anderswohin.", "Oft wird gefragt: „{c}“ – oben steht Yikonglus Antwort.", "Zhu Xis Kommentar: "),
 "vi": ("Cách đọc của Yikonglu: ", "Cách hiểu thường gặp là “{c}”; Yikonglu đặt trọng tâm ở chỗ khác.", "Cách hiểu thường gặp: {c}. Yikonglu đặt trọng tâm ở chỗ khác.", "Người ta hay hỏi “{c}”; câu trên là câu trả lời của Yikonglu.", "Lời chú của Chu Hi: "),
 "id": ("Bacaan Yikonglu: ", "Bacaan umum mengatakan “{c}”; Yikonglu menaruh bobotnya di tempat lain.", "Bacaan umum: {c}. Yikonglu menaruh bobotnya di tempat lain.", "Orang sering bertanya “{c}”; kalimat di atas adalah jawaban Yikonglu.", "Komentar Zhu Xi: "),
 "ru": ("Прочтение Yikonglu: ", "Обычное прочтение — «{c}»; Yikonglu ставит акцент иначе.", "Обычное прочтение: {c}. Yikonglu ставит акцент иначе.", "Часто спрашивают: «{c}»; выше — ответ Yikonglu.", "Комментарий Чжу Си: "),
}
YKAN_LEN = {"zh": (60, 120), "ja": (60, 130), "ko": (70, 160)}  # 其他语种按 (150, 330) 字母算
def ykan(code, ours, common, keys, basis=None):
    """返回 (署名开头, 正文)。正文＝落点（首句结论）＋一句与通行读法的差别；太短再补朱注原话（取札记“字眼”，按分号截）。"""
    k = "zh" if code.startswith("zh") or code not in YKAN else code
    lab, st, st2, qt, bs = YKAN[k]
    if basis: bs = basis  # 别的书：依据不是朱注（道德经用王弼注等）
    zh = k == "zh"; cjk = k in ("zh", "ja")
    lo, hi = YKAN_LEN.get(k, (150, 330))
    sp = "" if cjk else " "
    o = (ours or "").strip()
    if zh and len(o) > 90:  # 太长截到 90 字内最后一个句读
        cut = max(o.rfind(x, 0, 90) for x in "。；")
        if cut > 30: o = o[:cut]
    if o and o[-1] not in "。！？.!?": o += "。" if cjk else "."
    c = (common or "").strip(); second = ""
    if c:
        isq = c[-1] in "？?"
        c = c.rstrip("。.？?！!；; ")
        if len(c) > ((40 if isq else 24) if cjk else 90):  # 常见读法太长：陈述只取第一分句；问句（40 字内整句留）取最后一个分句，问的是哪件事在句末
            for sep in ("；", "; ", "，", ", "):
                if sep in c: c = (c.split(sep)[-1] if isq else c.split(sep)[0]); break
        inner = any(q in c for q in "“”「」«»„\"")
        if isq and len(c) < (9 if cjk else 24): second = ""  # “为什么？”这类离了上下文看不懂的短问句不放，改由朱注原话补足
        elif isq and inner and zh: second = f"常有人问：{c}？上面是一孔录的回答。"  # 问句里已有引号，不再外套一层
        else: second = (qt if isq else (st2 if inner else st)).format(c=c)
    out = (o + sp + second).strip()
    if len(out) < lo and keys:  # 太短：补朱注原话，按分号一段段加，不超上限
        segs = [x.strip(" ；;") for x in re.split(r"；|; ", keys) if x.strip(" ；;")]
        add = ""
        for g in segs:
            t = (add + ("；" if cjk else "; ") + g) if add else g
            if len(out) + len(bs) + len(t) + 2 > hi: break
            add = t
        if add: out += sp + bs + add + ("" if add[-1] in "。.」”）)" else ("。" if cjk else "."))
    return lab, out
CSSV = __import__("hashlib").md5(open(os.path.join(HERE, "style.css"), "rb").read()).hexdigest()[:8]
A2V = __import__("hashlib").md5(open(os.path.join(HERE, "assets", "a2hs.js"), "rb").read()).hexdigest()[:8]
XDV = __import__("hashlib").md5(open(os.path.join(HERE, "assets", "xudu.js"), "rb").read()).hexdigest()[:8]  # 接着读（11-09 主人“过”）

# 页面被整站搬到别的域名时，顶上提示原站（不挡阅读；翻译代理、网页存档不提示）
MIRROR_JS = """<script>(function(){var h=location.hostname;if(!h||/(^|\\.)yikonglu\\.com$|^localhost$|^127\\.|\\.translate\\.goog$|archive\\.(org|ph|today|is)$|googleusercontent\\.com$|bingj\\.com$/.test(h))return;
var b=document.createElement('div');b.className='langbar';b.innerHTML='<span>@BAR@</span><a href="https://yikonglu.com'+location.pathname+'">@GO@ →</a>';document.body.insertBefore(b,document.body.firstChild)})();</script>"""

LANG_JS = """<script>
(function(){var D=function(){return document.querySelectorAll('details.lang[open]')};
document.addEventListener('click',function(e){D().forEach(function(d){if(!d.contains(e.target))d.removeAttribute('open')})});
document.addEventListener('keydown',function(e){if(e.key==='Escape')D().forEach(function(d){d.removeAttribute('open')})});
document.querySelectorAll('details.lang').forEach(function(d){d.addEventListener('toggle',function(){if(d.open)D().forEach(function(x){if(x!==d)x.removeAttribute('open')})})})})();
(function(){var P=document.documentElement.lang,K='yk_lang';try{var s=localStorage.getItem(K)}catch(e){var s=null}
document.querySelectorAll('[data-lang]').forEach(function(a){a.addEventListener('click',function(){try{localStorage.setItem(K,a.dataset.lang)}catch(e){}})});
if(s)return;var n=(navigator.language||'').toLowerCase(),w=null;
var c2=n.slice(0,2);if(c2=='in')c2='id';if(['en','ja','ko','fr','es','de','vi','id','ru'].indexOf(c2)>=0)w=c2;else if(n.startsWith('zh')&&/tw|hk|mo|hant/.test(n))w='zh-Hant';else if(n.startsWith('zh'))w='zh-Hans';
if(!w||w===P)return;var a=document.querySelector('link[hreflang="'+w+'"]');if(!a)return;
var t={en:['This page is available in English.','Switch to English'],ja:['このページには日本語版があります。','日本語に切り替える'],ko:['이 페이지는 한국어판이 있습니다.','한국어로 전환'],fr:['Cette page existe en français.','Passer au français'],es:['Esta página está disponible en español.','Cambiar a español'],de:['Diese Seite gibt es auf Deutsch.','Auf Deutsch lesen'],vi:['Trang này có bản tiếng Việt.','Chuyển sang tiếng Việt'],id:['Halaman ini tersedia dalam bahasa Indonesia.','Baca dalam bahasa Indonesia'],ru:['Эта страница есть на русском.','Читать по-русски'],'zh-Hant':['本頁有繁體中文版。','切換到繁體'],'zh-Hans':['本页有简体中文版。','切换到简体']}[w];
var b=document.createElement('div');b.className='langbar';b.innerHTML='<span>'+t[0]+'</span><a href="'+a.href+'">'+t[1]+' →</a><button aria-label="close">×</button>';
b.querySelector('a').onclick=function(){try{localStorage.setItem(K,w)}catch(e){}};b.querySelector('button').onclick=function(){try{localStorage.setItem(K,P)}catch(e){}b.remove()};
document.body.prepend(b)})();
</script>"""

SHARE_JS = """<script>
(function(){var B=document.querySelector('.sharebox');if(!B)return;var D=JSON.parse(B.querySelector('.shdata').textContent),T=D.t,P=B.querySelector('.shpanel'),btn=B.querySelector('.shbtn');
var HT=document.documentElement.lang==='zh-Hant';function QQ(t){return HT?String(t).replace(/“/g,'「').replace(/”/g,'」').replace(/‘/g,'『').replace(/’/g,'』'):t}  // 繁体页卡片与分享文字引号用「」『』（11-09 主人）
var txt=D.h+'「'+QQ(D.y.length>40?D.y.slice(0,40)+'……':D.y)+'」';
var SY=P.querySelector('[data-p=sys]');if(SY&&navigator.share&&/Mobi|Android|iPhone|iPad/.test(navigator.userAgent))SY.hidden=false;var MS=P.querySelector('[data-p=ms]');if(MS&&!/Mobi|Android|iPhone|iPad/.test(navigator.userAgent))MS.hidden=true;btn.addEventListener('click',function(){P.hidden=!P.hidden});document.addEventListener('click',function(e){if(!P.hidden&&!B.contains(e.target))P.hidden=true});document.addEventListener('keydown',function(e){if(e.key==='Escape')P.hidden=true});
var E=encodeURIComponent,U={weibo:'https://service.weibo.com/share/share.php?url='+E(D.u)+'&title='+E(txt+' — 一孔录'),x:'https://x.com/intent/post?url='+E(D.u)+'&text='+E(txt),fb:'https://www.facebook.com/sharer/sharer.php?u='+E(D.u),tg:'https://t.me/share/url?url='+E(D.u)+'&text='+E(txt),wa:'https://wa.me/?text='+E(txt+' '+D.u),line:'https://social-plugins.line.me/lineit/share?url='+E(D.u),threads:'https://www.threads.net/intent/post?text='+E(txt+' '+D.u),reddit:'https://www.reddit.com/submit?url='+E(D.u)+'&title='+E(txt),vk:'https://vk.com/share.php?url='+E(D.u)+'&title='+E(txt),ms:'fb-messenger://share/?link='+E(D.u)};
P.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var k=b.dataset.p;if(window.yklReset)window.yklReset();
if(k==='copy'){var done=function(){var o=b.textContent;b.textContent=T.ok;setTimeout(function(){b.textContent=o},1400)};if(navigator.clipboard)navigator.clipboard.writeText(txt+' '+D.u).then(done,function(){prompt('',D.u)});else prompt('',D.u);return}
if(k==='card'||k==='wx'){P.hidden=true;if(window.ykPick)window.ykPick('yy');else card();return}if(k==='sys'){P.hidden=true;navigator.share({title:D.h+' · 一孔录',text:txt,url:D.u}).catch(function(){});return}if(k==='ms'){location.href=U.ms;return}if(U[k])window.open(U[k],'_blank','noopener,width=640,height=560')});
function qr(cb){if(window.qrcode){cb();return}var s=document.createElement('script');s.src='/assets/qrcode.js';s.onload=cb;document.head.appendChild(s)}
function wrap(c,t,w){t=QQ(t);var L=[],cur='';for(var i=0;i<t.length;i++){var ch=t[i];if(c.measureText(cur+ch).width>w&&cur){if('，。；：？！、”’」』）,.;:?!'.indexOf(ch)>=0){cur+=ch;L.push(cur);cur='';continue}L.push(cur);cur=ch}else cur+=ch}if(cur)L.push(cur);return L}
function wrapW(c,t,w){var ws=t.split(/(\\s+)/),L=[],cur='';ws.forEach(function(x){if(c.measureText(cur+x).width>w&&cur.trim()){L.push(cur.trim());cur=x.trim()}else cur+=x});if(cur.trim())L.push(cur.trim());return L}
function rili(){try{var R=X3.rl,now=new Date(),y=now.getFullYear(),m=now.getMonth()+1,d=now.getDate();
function dd(Y,i){var s=R.jt[Y];return s?s.charCodeAt(i)-48:0}
var idx=-1,sy=y,sm,sd;for(var i=23;i>=0;i--){var mo=1+(i>>1),dy=dd(y,i);if(!dy)return null;if(mo<m||(mo===m&&dy<=d)){idx=i;sm=mo;sd=dy;break}}
if(idx<0){sy=y-1;idx=23;sm=12;sd=dd(sy,23);if(!sd)return null}
var k=Math.round((new Date(y,m-1,d)-new Date(sy,sm-1,sd))/864e5),h=Math.min(2,Math.floor(k/5));
var lp='';try{var o={};new Intl.DateTimeFormat('zh-CN-u-ca-chinese',{year:'numeric',month:'numeric',day:'numeric'}).formatToParts(now).forEach(function(p){o[p.type]=p.value});var ms=(o.month||'').replace(/^闰|bis$/g,'').replace(/月$/,''),CM=['正','二','三','四','五','六','七','八','九','十','十一','十二'],lm=/^\\d+$/.test(ms)?parseInt(ms,10):CM.indexOf(ms)+1,ry=parseInt(o.relatedYear||o.year,10),ld=parseInt((o.day||'').replace(/\\D/g,''),10),N='一二三四五六七八九十';
if(lm&&ld){var yn=(o.yearName||'').replace(/年$/,'')||(ry>0?'甲乙丙丁戊己庚辛壬癸'[(ry-4)%10]+'子丑寅卯辰巳午未申酉戌亥'[(ry-4)%12]:''),MN=['正','二','三','四','五','六','七','八','九','十','冬','腊'][lm-1]+'月',DN=ld<=10?'初'+N[ld-1]:ld<20?'十'+N[ld-11]:ld===20?'二十':ld<30?'廿'+N[ld-21]:'三十';lp='农历'+(/^[一-鿿]{2}$/.test(yn)?yn+'年':'')+(/闰|bis/.test(o.month)?'闰':'')+MN+DN}}catch(e){}
return{big:m+'月'+d+'日',wk:y+'年 · 星期'+'日一二三四五六'[now.getDay()]+(lp?' · '+lp:''),jq:(k===0?'今日'+R.jn[idx]:R.jn[idx]+'后第'+k+'天')+' · '+R.hou[idx*3+h]}}catch(e){return null}}
var X3=JSON.parse(B.querySelector('.shtri').textContent);
var O0={y:X3.y,en:X3.en,ja:X3.ja,u:D.u};window.yklReset=function(){X3.y=O0.y;X3.en=O0.en;X3.ja=O0.ja;D.u=O0.u;X3.n=0};window.yklCard=function(o){if(o.y){X3.y=o.y;X3.en='';X3.ja=''}if(o.u)D.u=o.u;X3.n=o.n||0;card()};
function card(){var F='"Noto Serif SC","Noto Serif JP","Noto Serif",serif',RL=rili(),all=X3.h+X3.y+X3.en+X3.ja+'一孔录逐字读经典原文扫码读懂这一章'+(RL?RL.big+RL.wk+RL.jq:'');
Promise.all(['900 72px '+F,'700 60px '+F,'400 30px '+F].map(function(f){return document.fonts?document.fonts.load(f,all).catch(function(){}):0})).then(function(){qr(draw)})
var MAXH=1400,AR=888/1400;function segs(n){var R=[];document.querySelectorAll('.yuanwen.dz .yyp').forEach(function(a){var sv=a.querySelector('svg'),im=a.querySelector('image');if(!sv||!im)return;var rs=[].slice.call(a.querySelectorAll('rect.hl')).filter(function(r){return !n||r.dataset.s==n});if(!rs.length)return;
var vb=sv.getAttribute('viewBox').split(' ').map(Number),pw=+im.getAttribute('width'),x0=1e9,x1=0,cw=0;rs.forEach(function(r){var x=+r.getAttribute('x'),w=+r.getAttribute('width');x0=Math.min(x0,x);x1=Math.max(x1,x+w);cw=Math.max(cw,w)});
var pad=cw*0.55,minw=cw*4.2;x0-=pad;x1+=pad;if(x1-x0<minw){var m=(x0+x1)/2;x0=m-minw/2;x1=m+minw/2}x0=Math.max(0,x0);x1=Math.min(pw,x1);
R.push({src:im.getAttribute('href'),pw:pw,x0:x0,x1:x1,y0:vb[1],y1:vb[1]+vb[3],p:+a.dataset.p.slice(1),hl:rs.map(function(r){return['x','y','width','height'].map(function(k){return +r.getAttribute(k)})})})});
var th=0,tw=0;R.forEach(function(g){th=Math.max(th,g.y1-g.y0);tw+=g.x1-g.x0});var need=th*AR-tw;if(R.length&&need>0){R.forEach(function(g){var e=need/R.length/2,a=g.x0-e,b=g.x1+e;if(a<0){b-=a;a=0}if(b>g.pw){a-=b-g.pw;b=g.pw}g.x0=Math.max(0,a);g.x1=b})}return R}  // 原页左右多带几列，铺满卡宽（11-09 主人）
function draw(){var W=1080,SG=segs(X3.n),ims=SG.map(function(g){return new Promise(function(ok){var m=new Image();m.crossOrigin='anonymous';m.onload=function(){g.im=m;ok()};m.onerror=function(){ok()};m.src=g.src})});Promise.all(ims).then(function(){SG=SG.filter(function(g){return g.im});draw2(W,SG)})}
function draw2(W,SG){var M0=document.createElement('canvas').getContext('2d'),RL=rili();
var top=RL?286:250,y0=top+58+30,CF=[[60,30,28],[54,28,26],[50,27,25],[46,26,24],[42,25,23],[38,23,22],[34,21,20]],cf,L1,L2,L3;
function H3(cf,a,b,j){return a.length*cf[0]*1.45+34+(b.length?b.length*cf[1]*1.5+18:0)+j.length*cf[2]*1.6}
for(var i=0;i<CF.length;i++){cf=CF[i];M0.font='700 '+cf[0]+'px '+F;L1=wrap(M0,X3.y,W-192);M0.font='400 '+cf[1]+'px '+F;L2=X3.en?wrapW(M0,X3.en,W-192):[];M0.font='400 '+cf[2]+'px '+F;L3=X3.ja?wrap(M0,X3.ja,W-192):[];if(H3(cf,L1,L2,L3)<=900)break}
var yT=y0+H3(cf,L1,L2,L3),sc=0,sw=0,sh=0,GAP=14;
if(SG.length){var tw=0,th=0;SG.forEach(function(g){tw+=g.x1-g.x0;th=Math.max(th,g.y1-g.y0)});tw+=GAP*(SG.length-1);sc=Math.min((W-192)/tw,MAXH/th);sw=tw*sc;sh=th*sc}
var yS=yT+36,H=Math.round((SG.length?yS+sh+64:yT)+330);
var cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');
c.fillStyle='#F2F1EA';c.fillRect(0,0,W,H);c.strokeStyle='#23503F';c.lineWidth=3;c.strokeRect(40,40,W-80,H-80);c.strokeStyle='rgba(35,80,63,.25)';c.lineWidth=1;c.strokeRect(52,52,W-104,H-104);if(window.ykTex)window.ykTex(c,W,H);
var seal=new Image();seal.onload=function(){c.drawImage(seal,96,100,72,72);rest()};seal.onerror=rest;seal.src='/assets/seal-180.png';
function rest(){c.textBaseline='middle';c.fillStyle='#1E2A25';c.font='900 44px '+F;c.fillText('一孔录',186,126);c.fillStyle='#6E6A60';c.font='400 24px '+F;c.fillText('逐字读经典原文',188,164);
c.textBaseline='alphabetic';
if(RL){c.textAlign='right';c.fillStyle='#23503F';c.font='900 76px '+F;c.fillText(RL.big,W-96,160);c.fillStyle='#6E6A60';c.font='400 24px '+F;c.fillText(RL.wk,W-96,202);c.fillStyle='#8A5A2C';c.font='700 30px '+F;c.fillText(RL.jq,W-96,246);c.textAlign='left'}
c.fillStyle='rgba(35,80,63,.3)';c.fillRect(96,top,W-192,1);
c.fillStyle='#8A5A2C';c.font='400 28px '+F;c.fillText(X3.h,96,top+58);
var y=y0;c.fillStyle='#1E2A25';c.font='700 '+cf[0]+'px '+F;L1.forEach(function(l){c.fillText(l,96,y+cf[0]*0.95);y+=cf[0]*1.45});
y+=8;c.fillStyle='#23503F';c.fillRect(96,y,64,4);y+=26;
c.fillStyle='#4A4840';c.font='400 '+cf[1]+'px '+F;L2.forEach(function(l){c.fillText(l,96,y+cf[1]*0.95);y+=cf[1]*1.5});if(L2.length)y+=18;
c.font='400 '+cf[2]+'px '+F;L3.forEach(function(l){c.fillText(l,96,y+cf[2]*0.95);y+=cf[2]*1.6});
if(SG.length){var x=(W+sw)/2;c.fillStyle='#fff';c.fillRect((W-sw)/2-10,yS-10,sw+20,sh+20);
SG.forEach(function(g,k){var k2=g.im.naturalWidth/g.pw,gw=(g.x1-g.x0)*sc,gh=(g.y1-g.y0)*sc;x-=gw;c.drawImage(g.im,g.x0*k2,g.y0*k2,(g.x1-g.x0)*k2,(g.y1-g.y0)*k2,x,yS,gw,gh);
c.strokeStyle='rgba(176,58,46,.85)';c.lineWidth=3;g.hl.forEach(function(r){c.strokeRect(x+(r[0]-g.x0)*sc,yS+(r[1]-g.y0)*sc,r[2]*sc,r[3]*sc)});
if(k<SG.length-1){x-=GAP*sc;c.fillStyle='#F2F1EA';c.fillRect(x,yS-10,GAP*sc,sh+20)}});
c.strokeStyle='rgba(35,80,63,.35)';c.lineWidth=1;c.strokeRect((W-sw)/2-10,yS-10,sw+20,sh+20);
var ps=SG.map(function(g){return g.p}),pl=ps[0]+(ps.length>1?'—'+ps[ps.length-1]:'');c.fillStyle='#6E6A60';c.font='400 22px '+F;c.textAlign='center';c.fillText((D.src2||'朱熹《论语集注》（四部备要本）')+'原页 '+pl+(ps.length>1?' · 自右向左接读':''),W/2,yS+sh+44);c.textAlign='left'}
var q=qrcode(0,'M');q.addData(D.u);q.make();var n=q.getModuleCount(),cs=Math.floor(190/n),qs=cs*n,qx=W-96-qs,qy=H-96-qs;c.fillStyle='#fff';c.fillRect(qx-12,qy-12,qs+24,qs+24);c.fillStyle='#1E2A25';for(var r=0;r<n;r++)for(var k=0;k<n;k++)if(q.isDark(r,k))c.fillRect(qx+k*cs,qy+r*cs,cs,cs);
c.fillStyle='#23503F';c.font='700 30px '+F;c.fillText('扫码读懂这一章',96,H-150);c.fillStyle='#6E6A60';c.font='400 24px '+F;c.fillText(D.u.replace(/^https:\\/\\//,'').replace(/\\.html$/,''),96,H-108);
show(cv)}}}
function show(cv){var M=document.createElement('div');M.className='shmodal';var url=cv.toDataURL('image/png');var fn='yikonglu-'+location.pathname.replace(/[\\/]+/g,'-').replace(/^-|\\.html$/g,'')+'.png';
M.innerHTML='<div class="shm"><img alt=""><p class="note"></p><div class="shmb"><a class="btn" download></a><button type="button" class="btn ghost snd" hidden></button><button type="button" class="btn ghost cls"></button></div></div>';
M.querySelector('img').src=url;M.querySelector('.note').textContent=T.tip;var a=M.querySelector('a');a.href=url;a.download=fn;a.textContent=T.save;M.querySelector('.cls').textContent=T.close;
var sb=M.querySelector('.snd');sb.textContent=T.send;var ua=navigator.userAgent,ios=/iPhone|iPad|iPod/.test(ua)||(/Macintosh/.test(ua)&&navigator.maxTouchPoints>1),inapp=/MicroMessenger|Weibo|QQ\\/|xhs|discover|Line\\/|FBAN|FBAV|Instagram|DingTalk|AlipayClient/i.test(ua),nt=M.querySelector('.note');
cv.toBlob(function(bl){var f=null;try{f=new File([bl],fn,{type:'image/png'})}catch(e){}var cs=!!(f&&navigator.canShare&&navigator.canShare({files:[f]}));try{a.href=URL.createObjectURL(bl)}catch(e){}
if(cs){sb.hidden=false;sb.onclick=function(){navigator.share({files:[f],text:txt+' '+D.u}).catch(function(){})}}
a.onclick=function(e){if(inapp||(ios&&!cs)){e.preventDefault();nt.textContent=T.hold;nt.classList.add('hl');return}if(ios&&cs){e.preventDefault();navigator.share({files:[f]}).catch(function(){})}}});
M.addEventListener('click',function(e){if(e.target===M||e.target.closest('.cls'))M.remove()});document.body.appendChild(M)}
@CARDS@
if(location.hash==='#ka'){history.replaceState(null,'',location.pathname+location.search);setTimeout(function(){if(window.ykPick)window.ykPick('yy');else card()},400)}
})();
</script>"""
SHARE_JS = SHARE_JS.replace("@CARDS@", open(os.path.join(HERE, "share_cards.js"), encoding="utf-8").read() if os.environ.get("YK_CARDS", "1") != "0" else "")  # 新分享卡（11-08 主人“过”）；回退设 YK_CARDS=0
JU_JS = """<div id="jubar" class="jubar" hidden><button data-a="q">@COPY@</button><button data-a="l">@LINK@</button><span class="jr" hidden></span><div class="hj"><b>@HJH@</b><ul class="hjd"></ul>@HJ@</div></div>
<script>
(function(){var B=document.getElementById('jubar'),Q=document.querySelector('.yuanwen blockquote'),cur=null;if(!Q)return;
function put(t,btn){var done=function(){var o=btn.textContent;btn.textContent='@DONE@';setTimeout(function(){btn.textContent=o;B.hidden=true},1200)};
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,function(){prompt('',t)})}else{prompt('',t)}}
function show(s){cur=s;document.querySelectorAll('.ju.on').forEach(function(x){x.classList.remove('on')});s.classList.add('on');
var J=B.querySelector('.jr'),R=[];try{R=JSON.parse(Q.dataset.reads||'[]')}catch(e){}
var t=s.textContent,hit=R.filter(function(x){return x[1].split('\u3001').some(function(p){return p&&t.indexOf(p)>=0})});
J.hidden=!hit.length;J.textContent=hit.length?Q.dataset.rl+hit.map(function(x){return x[0]+' '+x[2]}).join(' \u00b7 '):'';
var U=B.querySelector('.hjd'),H=[];try{H=JSON.parse(Q.dataset.hj||'{}')[s.id.slice(1)]||[]}catch(e){}
U.innerHTML='';H.forEach(function(x){var li=document.createElement('li');li.innerHTML='<i></i> ';li.firstChild.textContent=x[0];var a=document.createElement(x[3]?'a':'span');a.textContent=x[1]+(x[2]?'（'+x[2]+'）':'');if(x[3])a.href=x[3];li.appendChild(a);U.appendChild(li)});
var r=s.getBoundingClientRect();B.hidden=false;B.style.top=(window.scrollY+r.bottom+6)+'px';B.style.left=Math.max(8,Math.min(window.scrollX+r.left,document.documentElement.clientWidth-B.offsetWidth-8))+'px'}
Q.addEventListener('click',function(e){var s=e.target.closest('.ju');if(s)show(s)});
Q.addEventListener('keydown',function(e){if(e.key==='Enter'){var s=e.target.closest('.ju');if(s)show(s)}});
document.addEventListener('click',function(e){var c=e.target.closest('.cp');if(c){put(c.dataset.t,c);return}if(!e.target.closest('.ju')&&!e.target.closest('#jubar')){B.hidden=true;if(cur)cur.classList.remove('on')}});
B.addEventListener('click',function(e){var b=e.target.closest('button');if(!b||!cur)return;var u=Q.dataset.url+'#'+cur.id;
put(b.dataset.a==='q'?'\u201c'+cur.textContent+'\u201d\u2014\u2014'+Q.dataset.src+(Q.dataset.short?' '+Q.dataset.short:Q.dataset.sep+u):u,b);if(window.yklCopy)window.yklCopy(cur.id)});
var h=location.hash.slice(1);if(/^s\\d+$/.test(h)){var t=document.getElementById(h);if(t)t.classList.add('on')}})();
</script>"""

def lang_tab(tab, code):  # 按语种取内容表；外语缺译时用英文，不用中文
    return tab.get(code) or tab["zh-Hans" if code.startswith("zh") else "en"]

class Lang:
    def __init__(self, code, ui, tr=None):
        self.code = code; self.prefix, self.name, self.hreflang = LANGS[code]
        self.ui = ui; self.tr = tr or {}
    def t(self, k, **kw):
        s = self.ui.get(k)
        if s is None and not self.code.startswith("zh"): s = EXTRA_UI["en"].get(k)
        if s is None: s = ZH_UI.get(k, k)
        return s.format(**kw) if kw else s
    def ch(self, c): return self.tr.get("chapters", {}).get(c, {})
    def src(self, s): return self.tr.get("src", {}).get(s, s)
    def book(self, p):
        return self.tr.get("books", {}).get(p, PIAN[p][2])

def analytics(L):
    """访问统计：tools/analytics.json 里填了才加。cloudflare＝Web Analytics token；baidu＝百度统计 hm.js 的 id（只加在简体页）。"""
    a = ""
    if ANALYTICS.get("cloudflare"):
        a += f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{ANALYTICS['cloudflare']}\"}}'></script>"
    if ANALYTICS.get("baidu") and L.code == "zh-Hans":
        a += f'<script>var _hmt=_hmt||[];(function(){{var hm=document.createElement("script");hm.src="https://hm.baidu.com/hm.js?{ANALYTICS["baidu"]}";var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(hm,s)}})();</script>'
    if ANALYTICS.get("live"):  # 在线与累计读者：worker/ 部署的计数服务；首页有 #live 才显示，其他页只发心跳
        tpl = LIVE_TXT.get(L.code, LIVE_TXT["en"]); sp = LIVE_PILL.get(L.code, LIVE_PILL["en"])
        a += ("<script>(function(){var U=" + json.dumps(ANALYTICS["live"].rstrip("/")) + ",EP=function(x){return [U,x].join(String.fromCharCode(47))},T=" + json.dumps(tpl, ensure_ascii=False) + ",S=" + json.dumps(sp, ensure_ascii=False)
              + ';function RUN(){var DB=document.querySelector(".donebox"),RC=document.getElementById("rc"),CC=DB?DB.getAttribute("data-c"):(RC?RC.getAttribute("data-c"):"");var id,f=false;try{id=localStorage.getItem("ykl_id");if(!id){id=Math.random().toString(36).slice(2)+Date.now().toString(36);localStorage.setItem("ykl_id",id);f=true}}catch(e){id="x"+Math.random().toString(36).slice(2)}'
              + 'function n(x){try{return x.toLocaleString(document.documentElement.lang||undefined)}catch(e){return x}}'
              + 'function h(first){if(document.hidden&&!first)return;fetch(EP("hit"),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:id,first:first&&f,c:first?CC:""})}).then(function(r){return r.json()}).then(function(d){if(!d)return;window.yklTotal=d.total;var e=document.getElementById("live"),q=document.getElementById("livep");if(e){e.innerHTML=T.replace("{o}","<b>"+n(d.online)+"</b>").replace("{t}","<b>"+n(d.total)+"</b>");e.hidden=false}if(q){var kk="";q.textContent=S.replace("{o}",n(d.online)).replace("{t}",n(d.total))+kk;q.title=T.replace("{o}",n(d.online)).replace("{t}",n(d.total))+kk;q.hidden=false}}).catch(function(){})}'
              + 'function wk(){try{var d=new Date(Date.now()+288e5),t=d.toISOString().slice(0,10),m=new Date(d-((d.getUTCDay()+6)%7)*864e5).toISOString().slice(0,10),o=JSON.parse(localStorage.getItem("ykl_wk")||"{}"),b={};if(o.m!==m)o={m:m,a:[],l:[]};if(o.a.indexOf(t)<0){o.a.push(t);b.a=o.a.length}if(/^[0-9]+[.][0-9]+$/.test(CC)&&o.l.indexOf(t)<0){o.l.push(t);b.l=o.l.length}if(b.a||b.l){localStorage.setItem("ykl_wk",JSON.stringify(o));'
              + ('fetch(EP("wk"),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).catch(function(){})' if ANALYTICS.get("week") else '') + '}}catch(e){}}'  # 匿名周读（北极星）：章页停满一分钟算读了一天，只在本机记哪几天，本周第 n 天发一个 n；tools/analytics.json 设 "week": true 才开（计数服务 /wk 部署后）
              + 'h(true);setInterval(function(){h(false);if(CC&&!document.hidden)wk()},60000);'
              + 'var X=' + json.dumps(DONE_TXT.get(L.code, DONE_TXT["en"]), ensure_ascii=False) + ';'
              + 'function cnt(c,el){fetch(EP("done")+"?c="+encodeURIComponent(c)).then(function(r){return r.json()}).then(function(d){if(!d||!d.total){el.hidden=true;return}el.textContent=X.n.replace("{d}",n(d.today)).replace("{t}",n(d.total));el.hidden=false}).catch(function(){})}'
              + 'window.yklDone=cnt;'
              + 'document.querySelectorAll(".donebox").forEach(function(bx){var c=bx.getAttribute("data-c"),b=bx.querySelector("button"),p=bx.querySelector(".donecnt"),k="ykl_done_"+c,was=false;try{was=!!localStorage.getItem(k)}catch(e){}'
              + 'function mark(){b.textContent=X.ok;b.disabled=true;b.classList.add("on")}if(was)mark();bx.hidden=false;cnt(c,p);'
              + 'b.addEventListener("click",function(){if(b.disabled)return;mark();if(window.ykBing)setTimeout(window.ykBing,300);try{localStorage.setItem(k,"1")}catch(e){}fetch(EP("done"),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({c:c})}).then(function(r){return r.json()}).then(function(d){p.textContent=X.n.replace("{d}",n(d.today)).replace("{t}",n(d.total));p.hidden=false}).catch(function(){})})});'
              + 'window.yklCopy=function(sid){if(!CC||!DB)return;fetch(EP("copy"),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({c:CC,s:sid})}).catch(function(){})};'
              + 'var LJ=null;function lj(cb){if(LJ){cb(LJ);return}fetch(["","data","live"].join("/")+"-"+document.documentElement.lang+".json").then(function(r){return r.json()}).then(function(j){LJ=j;cb(j)}).catch(function(){})}'
              + 'var RM=document.getElementById("remen"),ST=document.getElementById("steps"),TJ=document.getElementById("topju"),HL=document.querySelectorAll(".toc li[data-c]"),GD=document.getElementById("rcta")||document.getElementById("meiri");'
              + 'function lk(j,c){var a=document.createElement("a");a.href=j.p+j.c[c][1];a.textContent=j.c[c][0];return a}'
              + 'if(RM||ST||TJ||HL.length)fetch(EP("top")).then(function(r){return r.json()}).then(function(t){if(!t)return;'
              + 'if(HL.length){var mx=0;HL.forEach(function(li){mx=Math.max(mx,t.heat[li.getAttribute("data-c")]||0)});if(mx)HL.forEach(function(li){var v=t.heat[li.getAttribute("data-c")]||0,i=li.querySelector("i.heat");if(i&&v){i.querySelector("s").style.width=Math.max(8,Math.round(v*140/mx))+"px";i.querySelector("small").textContent=X.hn.replace("{n}",n(v));i.hidden=false}})}'
              + 'if(RM&&t.heat)lj(function(j){var hs=Object.keys(t.heat).filter(function(c){return j.c[c]}).sort(function(a,b){return t.heat[b]-t.heat[a]}).slice(0,5);if(!hs.length)return;var ol=RM.querySelector("ol.toc");if(!ol)return;var old=[].slice.call(ol.querySelectorAll("li[data-c]")).map(function(li){return li.getAttribute("data-c")}).filter(function(c){return j.c[c]&&hs.indexOf(c)<0}),cs=hs.concat(old).slice(0,5),mx=t.heat[hs[0]];ol.textContent="";'
              + 'cs.forEach(function(c){var v=t.heat[c]||0,li=document.createElement("li"),a=document.createElement("a"),e=function(tg,tx){var x=document.createElement(tg);if(tx!=null)x.textContent=tx;return x};li.setAttribute("data-c",c);a.href=j.p+j.c[c][1];a.appendChild(e("em",c));a.appendChild(e("b",j.c[c][0]));var sp=e("span",(j.c[c][2]||[])[0]||"");sp.lang="zh-Hans";a.appendChild(sp);if(v){var i=e("i");i.className="heat";var sb=e("s");sb.style.width=Math.max(8,Math.round(v*140/mx))+"px";i.appendChild(sb);i.appendChild(e("small",X.hn.replace("{n}",n(v))));a.appendChild(i)}li.appendChild(a);ol.appendChild(li)})});'
              + 'if(ST&&t.recent&&t.recent.length)lj(function(j){var A=j.a||j.c,rc=t.recent.filter(function(c){return A[c]});if(!rc.length)return;var nall=Math.max(t.rn||0,rc.length);rc=rc.slice(0,12);ST.textContent="";var lb=document.createElement("b");lb.textContent=X.steps.replace("{n}",n(nall));ST.appendChild(lb);var sc=document.createElement("span");sc.className="stc";rc.forEach(function(c){var a=document.createElement("a");a.href=j.p+A[c][1];a.textContent=A[c][0];sc.appendChild(a)});ST.appendChild(sc);ST.hidden=false});'
              + 'if(TJ&&t.top&&t.top.length)lj(function(j){var k=t.top[0][0].split("#"),c=k[0],si=parseInt(k[1].slice(1),10)-1;if(!j.c[c]||!j.c[c][2][si])return;TJ.querySelector("blockquote").textContent=j.c[c][2][si];var a=TJ.querySelector("a");a.href=j.p+j.c[c][1]+"#"+k[1];a.textContent=j.c[c][0];TJ.hidden=false})'
              + '}).catch(function(){});'
              + 'function gdc(){if(!GD||!GD.getAttribute("data-c")||GD.querySelector(".gdn"))return;fetch(EP("reads")+"?c="+encodeURIComponent(GD.getAttribute("data-c"))).then(function(r){return r.json()}).then(function(d){if(d&&d.today&&!GD.querySelector(".gdn")){var sp=document.createElement("span");sp.className="gdn";sp.textContent=" · "+X.gdn.replace("{d}",n(d.today));(GD.querySelector(".md")||GD).appendChild(sp)}}).catch(function(){})}gdc();document.addEventListener("ykmeiri",gdc);'
              + '}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",RUN);else RUN()})();</script>')
    return a

DONE_TXT = {"zh-Hans": {"b": "读完了", "ok": "已读完 ✓", "n": "今天 {d} 人读完 · 共 {t} 人", "h": "今日共读", "p": "全站今天一起读这一章，明天换一章。", "steps": "今天大家一共读了 {n} 章", "topju": "近 7 天被抄走最多的一句", "gd": "今日共读一章", "gdn": "今天 {d} 人共读", "hn": "近 7 天 {n} 人读过"}, "zh-Hant": {"b": "讀完了", "ok": "已讀完 ✓", "n": "今天 {d} 人讀完 · 共 {t} 人", "h": "今日共讀", "p": "全站今天一起讀這一章，明天換一章。", "steps": "今天大家一共讀了 {n} 章", "topju": "近 7 天被抄走最多的一句", "gd": "今日共讀一章", "gdn": "今天 {d} 人共讀", "hn": "近 7 天 {n} 人讀過"}, "en": {"b": "I’ve read it", "ok": "Read ✓", "n": "{d} finished today · {t} in all", "h": "Today’s shared reading", "p": "Everyone on the site reads this chapter today; a new one tomorrow.", "steps": "Read today · {n}", "topju": "Most-copied line, last 7 days", "gd": "Today’s shared chapter", "gdn": "{d} read it today", "hn": "{n} read in the last 7 days"}, "ja": {"b": "読み終えた", "ok": "読了 ✓", "n": "今日 {d} 人が読了 · 累計 {t} 人", "h": "今日の共読", "p": "今日はサイトのみんなでこの章を読みます。明日は別の章です。", "steps": "今日読まれた章 · {n}", "topju": "直近7日でいちばん写された一句", "gd": "今日の共読の章", "gdn": "今日 {d} 人が共読", "hn": "直近7日 {n} 人が読了"}, "ko": {"b": "다 읽었어요", "ok": "읽음 ✓", "n": "오늘 {d}명 완독 · 누적 {t}명", "h": "오늘 함께 읽기", "p": "오늘은 모두 이 장을 함께 읽습니다. 내일은 다른 장입니다.", "steps": "오늘 읽힌 장 · {n}", "topju": "최근 7일 가장 많이 옮겨 적은 구절", "gd": "오늘 함께 읽는 장", "gdn": "오늘 {d}명 함께 읽음", "hn": "최근 7일 {n}명 읽음"}, "fr": {"b": "Je l’ai lu", "ok": "Lu ✓", "n": "{d} l’ont lu aujourd’hui · {t} en tout", "h": "Lecture commune du jour", "p": "Aujourd’hui, tout le site lit ce chapitre ; demain, un autre.", "steps": "Lus aujourd’hui · {n}", "topju": "La phrase la plus copiée ces 7 derniers jours", "gd": "Le chapitre du jour, ensemble", "gdn": "{d} l’ont lu aujourd’hui", "hn": "{n} lectures ces 7 derniers jours"}, "es": {"b": "Lo he leído", "ok": "Leído ✓", "n": "{d} lo leyeron hoy · {t} en total", "h": "Lectura compartida de hoy", "p": "Hoy todo el sitio lee este capítulo; mañana, otro.", "steps": "Leídos hoy · {n}", "topju": "La frase más copiada en los últimos 7 días", "gd": "Capítulo compartido de hoy", "gdn": "{d} lo leyeron hoy", "hn": "{n} lecturas en los últimos 7 días"}, "de": {"b": "Gelesen", "ok": "Gelesen ✓", "n": "heute {d} gelesen · insgesamt {t}", "h": "Gemeinsame Lektüre heute", "p": "Heute liest die ganze Seite dieses Kapitel, morgen ein anderes.", "steps": "Heute gelesen · {n}", "topju": "Meistkopierter Satz der letzten 7 Tage", "gd": "Gemeinsames Kapitel heute", "gdn": "heute {d} gelesen", "hn": "{n} in den letzten 7 Tagen gelesen"}, "vi": {"b": "Đã đọc xong", "ok": "Đã đọc ✓", "n": "hôm nay {d} người đọc xong · tổng {t}", "h": "Cùng đọc hôm nay", "p": "Hôm nay cả trang cùng đọc chương này; mai đổi chương khác.", "steps": "Hôm nay có người đọc · {n}", "topju": "Câu được chép nhiều nhất 7 ngày qua", "gd": "Chương cùng đọc hôm nay", "gdn": "hôm nay {d} người cùng đọc", "hn": "{n} lượt đọc 7 ngày qua"}, "id": {"b": "Sudah selesai", "ok": "Selesai ✓", "n": "{d} selesai hari ini · total {t}", "h": "Baca bersama hari ini", "p": "Hari ini semua pembaca membaca bab ini; besok bab lain.", "steps": "Dibaca hari ini · {n}", "topju": "Kalimat paling banyak disalin 7 hari terakhir", "gd": "Bab baca bersama hari ini", "gdn": "{d} membaca hari ini", "hn": "{n} dibaca 7 hari terakhir"}, "ru": {"b": "Прочитано", "ok": "Прочитано ✓", "n": "сегодня прочитали: {d} · всего: {t}", "h": "Читаем вместе сегодня", "p": "Сегодня весь сайт читает эту главу, завтра — другую.", "steps": "Сегодня читали · {n}", "topju": "Самая переписываемая строка за 7 дней", "gd": "Глава дня — читаем вместе", "gdn": "сегодня читали: {d}", "hn": "прочитали за 7 дней: {n}"}}
# 主人 11-08：计数单位一律“儒者”（同 LIVE_PILL）；外文写成“X：数”避开单复数
for _k, _v in {"zh-Hans": ("今天 {d} 位儒者读完 · 累计 {t} 位", "今天 {d} 位儒者共读", "近 7 天被读 {n} 次"),
               "zh-Hant": ("今天 {d} 位儒者讀完 · 累計 {t} 位", "今天 {d} 位儒者共讀", "近 7 天被讀 {n} 次"),
               "en": ("Confucians finished today: {d} · in all: {t}", "Confucians reading it today: {d}", "Read {n} times in the last 7 days"),
               "ja": ("今日 {d} 人の儒者が読了 · 累計 {t} 人", "今日 {d} 人の儒者が共読", "直近7日で {n} 回読まれた"),
               "ko": ("오늘 유학자 {d}명 완독 · 누적 {t}명", "오늘 유학자 {d}명이 함께 읽음", "최근 7일 {n}회 읽힘"),
               "fr": ("Lettrés l’ayant lu aujourd’hui : {d} · en tout : {t}", "Lettrés aujourd’hui : {d}", "Lu {n} fois ces 7 derniers jours"),
               "es": ("Letrados que lo leyeron hoy: {d} · en total: {t}", "Letrados hoy: {d}", "Leído {n} veces en los últimos 7 días"),
               "de": ("Gelehrte heute fertig: {d} · insgesamt: {t}", "Gelehrte heute: {d}", "In den letzten 7 Tagen {n}-mal gelesen"),
               "vi": ("hôm nay {d} nhà nho đọc xong · tổng {t}", "hôm nay {d} nhà nho cùng đọc", "7 ngày qua được đọc {n} lần"),
               "id": ("Cendekiawan selesai hari ini: {d} · total: {t}", "Cendekiawan hari ini: {d}", "Dibaca {n} kali dalam 7 hari terakhir"),
               "ru": ("Книжники прочитали сегодня: {d} · всего: {t}", "Книжники сегодня: {d}", "Прочитано за 7 дней: {n}")}.items():
    if _k in DONE_TXT: DONE_TXT[_k].update(n=_v[0], gdn=_v[1], hn=_v[2])
HOT_TXT = {"zh-Hans": "热门章节", "zh-Hant": "熱門章節", "en": "Most-read chapters", "ja": "よく読まれている章", "ko": "많이 읽은 장", "fr": "Chapitres les plus lus", "es": "Capítulos más leídos", "de": "Meistgelesene Kapitel", "vi": "Chương được đọc nhiều", "id": "Bab paling banyak dibaca", "ru": "Самые читаемые главы"}  # 首页“热门章节”（11-11 主人：替换“最近讲的”，近 7 天阅读最多的五章）
for _k in DONE_TXT: DONE_TXT[_k]["hot"] = HOT_TXT.get(_k, HOT_TXT["en"])
def done_html(L, c):
    if not ANALYTICS.get("live"): return ""
    return f'<section class="donebox" data-c="{c}" hidden><button type="button" class="btn ghost">{DONE_TXT.get(L.code, DONE_TXT["en"])["b"]}</button><p class="donecnt" hidden></p></section>'
SHARE_TXT = {"zh-Hans": {"sh": "分享", "cp": "复制链接", "ok": "已复制", "card": "生成分享图", "save": "保存图片", "send": "发送图片", "tip": "微信、小红书、朋友圈：保存图片再发（手机上也可以长按图片保存），图上有二维码。", "scan": "扫码读懂这一章", "close": "关闭", "plats": [["微博", "weibo"], ["X", "x"], ["Telegram", "tg"]]}, "zh-Hant": {"sh": "分享", "cp": "複製連結", "ok": "已複製", "card": "生成分享圖", "save": "儲存圖片", "send": "傳送圖片", "tip": "IG、小紅書、微信：儲存圖片再發（手機上也可以長按圖片儲存），圖上有 QR 碼。", "scan": "掃碼讀懂這一章", "close": "關閉", "plats": [["LINE", "line"], ["WhatsApp", "wa"], ["Facebook", "fb"], ["Messenger", "ms"], ["Threads", "threads"], ["X", "x"], ["微信", "wx"]]}, "en": {"sh": "Share", "cp": "Copy link", "ok": "Copied", "card": "Make a share image", "save": "Save image", "send": "Send image", "tip": "For Instagram and similar apps, save the image and post it; the QR code leads back here.", "scan": "Scan to understand this chapter", "close": "Close", "plats": [["X", "x"], ["Facebook", "fb"], ["WhatsApp", "wa"], ["Reddit", "reddit"]]}, "ja": {"sh": "共有", "cp": "リンクをコピー", "ok": "コピーしました", "card": "シェア画像を作る", "save": "画像を保存", "send": "画像を送る", "tip": "Instagram などは画像を保存して投稿してください。QR コードからこの章に戻れます。", "scan": "読み取って、この章を読み解く", "close": "閉じる", "plats": [["LINE", "line"], ["X", "x"], ["Facebook", "fb"]]}, "ko": {"sh": "공유", "cp": "링크 복사", "ok": "복사됨", "card": "공유 이미지 만들기", "save": "이미지 저장", "send": "이미지 보내기", "tip": "인스타그램 등은 이미지를 저장해 올려 주세요. QR 코드로 이 장에 돌아올 수 있습니다.", "scan": "스캔해서 이 장 제대로 이해하기", "close": "닫기", "plats": [["X", "x"], ["Facebook", "fb"], ["LINE", "line"]]}, "fr": {"sh": "Partager", "cp": "Copier le lien", "ok": "Copié", "card": "Créer une image", "save": "Enregistrer l’image", "send": "Envoyer l’image", "tip": "Pour Instagram et autres, enregistrez l’image puis publiez-la ; le QR code ramène ici.", "scan": "Scannez pour comprendre ce chapitre", "close": "Fermer", "plats": [["X", "x"], ["Facebook", "fb"], ["WhatsApp", "wa"]]}, "es": {"sh": "Compartir", "cp": "Copiar enlace", "ok": "Copiado", "card": "Crear imagen", "save": "Guardar imagen", "send": "Enviar imagen", "tip": "Para Instagram y similares, guarde la imagen y publíquela; el código QR lleva de vuelta aquí.", "scan": "Escanee para entender este capítulo", "close": "Cerrar", "plats": [["WhatsApp", "wa"], ["X", "x"], ["Facebook", "fb"]]}, "de": {"sh": "Teilen", "cp": "Link kopieren", "ok": "Kopiert", "card": "Bild zum Teilen", "save": "Bild speichern", "send": "Bild senden", "tip": "Für Instagram u. Ä. das Bild speichern und posten; der QR-Code führt hierher zurück.", "scan": "Scannen und dieses Kapitel verstehen", "close": "Schließen", "plats": [["WhatsApp", "wa"], ["X", "x"], ["Facebook", "fb"]]}, "vi": {"sh": "Chia sẻ", "cp": "Sao chép liên kết", "ok": "Đã sao chép", "card": "Tạo ảnh chia sẻ", "save": "Lưu ảnh", "send": "Gửi ảnh", "tip": "Với Instagram, Zalo…: lưu ảnh rồi đăng; mã QR dẫn về chương này.", "scan": "Quét để hiểu chương này", "close": "Đóng", "plats": [["Facebook", "fb"], ["X", "x"], ["Telegram", "tg"]]}, "id": {"sh": "Bagikan", "cp": "Salin tautan", "ok": "Tersalin", "card": "Buat gambar", "save": "Simpan gambar", "send": "Kirim gambar", "tip": "Untuk Instagram dan sejenisnya, simpan gambar lalu unggah; kode QR membawa kembali ke sini.", "scan": "Pindai untuk memahami bab ini", "close": "Tutup", "plats": [["WhatsApp", "wa"], ["Facebook", "fb"], ["X", "x"]]}, "ru": {"sh": "Поделиться", "cp": "Скопировать ссылку", "ok": "Скопировано", "card": "Сделать картинку", "save": "Сохранить", "send": "Отправить картинку", "tip": "Для Instagram и похожих приложений сохраните картинку и опубликуйте; QR-код ведёт сюда.", "scan": "Сканируйте, чтобы понять главу", "close": "Закрыть", "plats": [["Telegram", "tg"], ["VK", "vk"], ["WhatsApp", "wa"]]}}
# 分享图上的“日课”栏：节气日（北京时间，由 ephem 按太阳视黄经算出，2025—2040；每年 24 个字符＝小寒起各节气的日子，chr(48+日)）、节气名、七十二候
JIEQI_DAYS = {"2025": "5D3B5D4D5E5E7F7G7G8G7F7E", "2026": "5D4B5D5D5E5E7G7G7G8G7F7F", "2027": "5D4C6E5D6E6E7G8G8G8G7F7F", "2028": "6D4C5D4C5D5E6F7F7F8G7F6E", "2029": "5D3B5D4D5E5E7F7G7G8G7F7E", "2030": "5D4B5D5D5E5E7G7G7G8G7F7F", "2031": "5D4C6E5D6E6E7G8G8G8G7F7F", "2032": "6D4C5D4C5D5E6F7F7F8G7F6E", "2033": "5D3B5D4D5E5E7F7G7G8G7F7E", "2034": "5D4B5D5D5E5E7G7G7G8G7F7F", "2035": "5D4C6E5D5E6E7G7G8G8G7F7F", "2036": "6D4C5D4C5D5E6F7F7F8G7F6E", "2037": "5D3B5D4D5E5E7F7G7G8G7F7E", "2038": "5D4B5D5D5E5E7G7G7G8G7F7F", "2039": "5D4C6E5D5E6E7G7G8G8G7F7F", "2040": "6D4C5D4C5D5E6F7F7F8G7F6E"}
JIEQI_NAMES = {
 "zh": "小寒 大寒 立春 雨水 惊蛰 春分 清明 谷雨 立夏 小满 芒种 夏至 小暑 大暑 立秋 处暑 白露 秋分 寒露 霜降 立冬 小雪 大雪 冬至".split(),
 "ja": "小寒 大寒 立春 雨水 啓蟄 春分 清明 穀雨 立夏 小満 芒種 夏至 小暑 大暑 立秋 処暑 白露 秋分 寒露 霜降 立冬 小雪 大雪 冬至".split(),
 "ko": "소한 대한 입춘 우수 경칩 춘분 청명 곡우 입하 소만 망종 하지 소서 대서 입추 처서 백로 추분 한로 상강 입동 소설 대설 동지".split(),
 "vi": ["Tiểu hàn", "Đại hàn", "Lập xuân", "Vũ thủy", "Kinh trập", "Xuân phân", "Thanh minh", "Cốc vũ", "Lập hạ", "Tiểu mãn", "Mang chủng", "Hạ chí", "Tiểu thử", "Đại thử", "Lập thu", "Xử thử", "Bạch lộ", "Thu phân", "Hàn lộ", "Sương giáng", "Lập đông", "Tiểu tuyết", "Đại tuyết", "Đông chí"],
 "en": ["Minor Cold", "Major Cold", "Start of Spring", "Rain Water", "Awakening of Insects", "Spring Equinox", "Pure Brightness", "Grain Rain", "Start of Summer", "Grain Buds", "Grain in Ear", "Summer Solstice", "Minor Heat", "Major Heat", "Start of Autumn", "End of Heat", "White Dew", "Autumn Equinox", "Cold Dew", "Frost’s Descent", "Start of Winter", "Minor Snow", "Major Snow", "Winter Solstice"],
 "py": "Xiǎohán Dàhán Lìchūn Yǔshuǐ Jīngzhé Chūnfēn Qīngmíng Gǔyǔ Lìxià Xiǎomǎn Mángzhòng Xiàzhì Xiǎoshǔ Dàshǔ Lìqiū Chǔshǔ Báilù Qiūfēn Hánlù Shuāngjiàng Lìdōng Xiǎoxuě Dàxuě Dōngzhì".split(),
}
QISHIER_HOU = ("雁北乡 鹊始巢 雉始雊 鸡始乳 征鸟厉疾 水泽腹坚 东风解冻 蛰虫始振 鱼陟负冰 獭祭鱼 候雁北 草木萌动 桃始华 仓庚鸣 鹰化为鸠 玄鸟至 雷乃发声 始电 "
               "桐始华 田鼠化为鴽 虹始见 萍始生 鸣鸠拂其羽 戴胜降于桑 蝼蝈鸣 蚯蚓出 王瓜生 苦菜秀 靡草死 麦秋至 螳螂生 鵙始鸣 反舌无声 鹿角解 蜩始鸣 半夏生 "
               "温风至 蟋蟀居壁 鹰始挚 腐草为萤 土润溽暑 大雨时行 凉风至 白露降 寒蝉鸣 鹰乃祭鸟 天地始肃 禾乃登 鸿雁来 玄鸟归 群鸟养羞 雷始收声 蛰虫坯户 水始涸 "
               "鸿雁来宾 雀入大水为蛤 菊有黄华 豺乃祭兽 草木黄落 蛰虫咸俯 水始冰 地始冻 雉入大水为蜃 虹藏不见 天气上升地气下降 闭塞而成冬 鹖鴠不鸣 虎始交 荔挺出 蚯蚓结 麋角解 水泉动").split()
RW_LINE = {  # 人物卡上的一句台词（11-14 改：不用身份介绍，用一句见性格、说的是《论语》这部书的话；[台词, 出自哪一集（新写的留空）]）
    "youli": ["《论语》我读了三遍，每一遍都发现上一遍读错了。", ""],
    "zhaojin": ["读《论语》像写生，一句一句看下去，那个人就站起来了。", ""],
    "shouzhuo": ["一本《论语》，我装订过几百回，这回想翻开读读。", ""],
    "luchuan": ["一本《论语》，两千五百年没降过价。", ""],
    "liuqi": ["《论语》里的礼，我是用脚跳懂的。", ""],
    "shahela": ["我从西边来，《论语》是我学的第一本中文书。", ""],
}
LEAD_WEEK = [["youli", "上官有理", ""], ["zhaojin", "孔照今", ""], ["shouzhuo", "林守拙", ""], ["luchuan", "陆川", ""], ["liuqi", "阮流绮", ""], ["shahela", "莎赫拉", ""],
             ["lisa", "Lisa", "汪！——守拙家的柯基，戴青色头巾。人到齐了，它才肯睡。"]]  # 首页今日《论语》一周七位领读人，星期一到星期日（11-14 主人：六人＋一狗）
def wk_js_only(h):  # wk_html 里“本周读了几天”的那段脚本
    i = h.find("<script>")
    return h[i:] if i >= 0 else ""
def share_x(D):
    """四种分享卡的每章数据（只《论语》）：七语译文（英日另在 TRI_TXT）、年历第几课与日期、出场的原创角色。"""
    tr = {}
    for lg in ("ko", "fr", "es", "de", "vi", "id", "ru"):
        f = os.path.join(HERE, "i18n", f"{lg}.json")
        if os.path.exists(f):
            for c, v in (json.load(open(f, encoding="utf-8")).get("chapters") or {}).items():
                if v.get("yw"): tr.setdefault(c, {})[lg] = v["yw"]
    for c, v in WJ_TR.items():  # 未讲章：韩法西俄四语只给分享卡用（11-14 主人：多语卡要备齐），在 tri-weijiang.json
        for lg in ("ko", "fr", "es", "ru"):
            if v.get(lg): tr.setdefault(c, {}).setdefault(lg, v[lg])
    nl = {}
    for r in (D.get("lx") or {}).get("nl") or []:
        for c in r["cs"]: nl.setdefault(c, [r["n"], r["m"], r["d"], r["q"] if c == r["c"] else ""])
    G = os.path.join(GAO_DIR, "_故事"); who, ppl = {}, {}
    try:
        for r in csv.DictReader(open(os.path.join(G, "人物.csv"), encoding="utf-8-sig")): ppl[r["名"]] = [r["id"], r["名"], r["一句关系"]] + RW_LINE.get(r["id"], [])
        for r in csv.DictReader(open(os.path.join(G, "出场.csv"), encoding="utf-8-sig")):
            ws = [ppl[n] for n in re.split(r"[、，,\s]+", r["人物"]) if n in ppl]
            if ws: who.setdefault(r["章号"], ws)
    except OSError: pass
    order = list(ppl.values())
    for c in set(D.get("qw") or {}) | set(D.get("pub") or []):
        x = {}
        if c in tr: x["tr"] = tr[c]
        if c in nl: x["nl"] = nl[c]
        if order:
            p, n = (int(v) for v in c.split("."))
            x["who"] = who.get(c) or [order[(p * 7 + n) % len(order)]]
        SHARE_X[c] = x

def rili_data():
    return {"jt": JIEQI_DAYS, "jn": JIEQI_NAMES["zh"], "hou": QISHIER_HOU}
SHARE_MORE = {"zh-Hans": "发给朋友…", "zh-Hant": "傳給朋友…", "en": "Send via…", "ja": "ほかのアプリで送る…", "ko": "다른 앱으로 보내기…", "fr": "Envoyer via…", "es": "Enviar con…", "de": "Senden über…", "vi": "Gửi qua…", "id": "Kirim lewat…", "ru": "Отправить через…"}
SHARE_HOLD = {"zh-Hans": "这个浏览器存不了，请长按上面的图片，选“保存图片”。", "zh-Hant": "這個瀏覽器存不了，請長按上面的圖片，選「儲存圖片」。", "en": "This browser can’t save it directly. Press and hold the image above to save it.", "ja": "このブラウザでは直接保存できません。上の画像を長押しして保存してください。", "ko": "이 브라우저에서는 바로 저장할 수 없습니다. 위 이미지를 길게 눌러 저장해 주세요.", "fr": "Ce navigateur ne peut pas l’enregistrer directement. Appuyez longuement sur l’image pour l’enregistrer.", "es": "Este navegador no puede guardarla directamente. Mantenga pulsada la imagen para guardarla.", "de": "Dieser Browser kann es nicht direkt speichern. Bild lange drücken, um es zu speichern.", "vi": "Trình duyệt này không lưu trực tiếp được. Hãy nhấn giữ ảnh phía trên để lưu.", "id": "Browser ini tidak bisa menyimpan langsung. Tekan lama gambar di atas untuk menyimpannya.", "ru": "Этот браузер не сохраняет напрямую. Нажмите и удерживайте картинку, чтобы сохранить её."}
def share_html(L, c, url, head, title, yw_text, gist, rend, bk=None):  # bk：别的书（道德经等）{"bk": 书名, "tot": 章数, "src": 底本, "src2": 底本（括注式）, "pf": 读过记录前缀}
    t = dict(SHARE_TXT.get(L.code, SHARE_TXT["en"]), hold=SHARE_HOLD.get(L.code, SHARE_HOLD["en"]))
    plats = "".join(f'<button type="button" data-p="{k}">{esc(n)}</button>' for n, k in t["plats"])
    yt = hant_plain(yw_text) if L.code in HANT_CARD and (bk is None or L.code == "zh-Hans") else ""  # 分享卡上的经文用繁体（古书字），页面正文不动
    d = json.dumps(dict({"c": c, "kn": SHARE_KEYS.get(c), "u": url, "h": head, "ti": title, "y": yw_text, "g": gist or "", "r": rend or "", "t": t, "tag": TAGLINE_L.get(L.code, "")}, **(dict(yt=yt) if yt and yt != yw_text else {}), **(bk or {})), ensure_ascii=False)
    tri = dict(TRI_TXT.get(c, {}), rl=rili_data(), tr=SHARE_X.get(c, {}).get("tr", {}))
    if yt: tri.update({k_: hant_plain(tri[k_]) for k_ in ("h", "y") if tri.get(k_)})
    return (f'<section class="sharebox"><button type="button" class="btn ghost shbtn"><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 13v6h14v-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>{t["sh"]}</button>'
            f'<div class="shpanel" hidden><button type="button" data-p="card" class="on">{t["card"]}</button><button type="button" data-p="sys" hidden>{SHARE_MORE.get(L.code, SHARE_MORE["en"])}</button><button type="button" data-p="copy">{t["cp"]}</button>{plats}</div>'
            f'<script type="application/json" class="shdata">{d.replace("</", "<\\/")}</script>'
            f'<script type="application/json" class="shtri">{json.dumps(tri)}</script>'
            f'<script type="application/json" class="shx">{json.dumps({k: v for k, v in SHARE_X.get(c, {}).items() if k != "tr"}, ensure_ascii=False).replace("</", "<\\/")}</script>{shi_tag(L)}</section>')
SHI_CACHE = {}
HANT_CARD = {"zh-Hans", "en", "ja", "ko", "fr", "es", "de", "vi", "id", "ru"}  # 11-14 主人：分享卡经文一律繁体；只改外文时去掉 zh-Hans
def shi_tag(L):  # 11-14 外文页四种分享卡的本语种文字（智器译，fill-<语种>.json）
    if L.code.startswith("zh") or not (FILL.get(L.code) or {}).get("c"): return ""
    if L.code not in SHI_CACHE:
        F = FILL[L.code]; C = F["c"]
        o = {k[3:]: v for k, v in C.items() if k.startswith("sh_")}
        o.update({k: C[k] for k in ("rec_note", "rec_ex", "rec_copied", "rec_code", "rec_im", "rec_paste", "rec_bad")})
        o.update(on=1, lg=L.code, sl=1 if L.code in WJ_FL else 0, tag=L.t("tagline"), lmd=C["lunar_md"], leap=C["lunar_leap"], after=C["cal_after"], today=C["cal_today"], lunar=C["cal_lunar"], zod=C["zodiac"],
                 fe={k[3:]: v for k, v in C.items() if k.startswith("fe_")}, jn=F.get("jq") or JIEQI_NAMES.get(L.code) or JIEQI_NAMES["en"], hou=F.get("hou") or [],
                 rw={k: [v["name"], v["line"]] for k, v in (F.get("lead") or {}).items()})
        SHI_CACHE[L.code] = f'<script type="application/json" class="shi">{json.dumps(o, ensure_ascii=False).replace("</", "<\\/")}</script>'
    return SHI_CACHE[L.code]
SHARE_X = {}  # 11-14 四种分享卡（原页、人物、多语、年历）用的每章附加数据：tr 七语译文、nl 年历课、who 原创角色
SHARE_KEYS = {}  # 章 → 分享图关键句（句号或句中字），章节起点.json 各集可写 "keys": {"1.16": 1}；缺省取首句
LANGDU = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "langdu.json"), encoding="utf-8"))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "langdu.json")) else set()  # 原文朗读（孔照今，11-11 主人定）：有音频的章，文件在 img.yikonglu.com/langdu/lunyu/<章>.mp3
LANGDU_TXT = {"zh-Hans": "音", "zh-Hant": "音", "en": "Audio", "ja": "音", "ko": "음성", "fr": "Audio", "es": "Audio", "de": "Audio", "vi": "Nghe", "id": "Audio", "ru": "Аудио"}  # 11-11 主人：按钮跟“译”一样大小并排，一个译一个音，不写谁的声音
LANGDU_TITLE = {"zh-Hans": "朗读原文", "zh-Hant": "朗讀原文"}
LANGDU_JS = ('<script>(function(){var B=document.currentScript.previousElementSibling,A=null;function st(p){B.setAttribute("aria-pressed",p?"true":"false")}'
             'B.addEventListener("click",function(){if(!A){A=new Audio(B.getAttribute("data-src"));A.addEventListener("ended",function(){st(false)});A.addEventListener("pause",function(){st(false)});A.addEventListener("play",function(){st(true)})}if(A.paused)A.play().catch(function(){});else A.pause()})})();</script>')
LANGDU_DDJ = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "langdu-ddj.json"), encoding="utf-8"))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "langdu-ddj.json")) else set()  # 道德经原文朗读（11-13 主人要上），文件在 langdu/daodejing/<章>.mp3
def langdu_btn(code, c, book="lunyu"):
    if c not in {"daodejing": LANGDU_DDJ, "sanzijing": globals().get("LANGDU_SZJ", set())}.get(book, LANGDU): return ""
    t = LANGDU_TITLE.get(code, LANGDU_TXT.get(code, "Audio"))
    return f'<button type="button" class="ldbtn" data-src="https://img.yikonglu.com/langdu/{book}/{c}.mp3" aria-pressed="false" title="{esc(t)}">{esc(LANGDU_TXT.get(code, "Audio"))}</button>' + LANGDU_JS
def langdu_html(code, c, book="lunyu"):  # 没有“译”按钮的页（外文章页）：单独一行放同样的小按钮
    b = langdu_btn(code, c, book)
    return f'<div class="dztools ldonly">{b}</div>' if b else ""
ZD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zidian.json")  # 论语难字字典（11-11 主人要提前做）：点字看读音、朱注训诂、全书出处；读音与原文朗读同一张表
ZD = json.load(open(ZD_FILE, encoding="utf-8")) if os.path.exists(ZD_FILE) else {"occ": {}, "per": {}}
ZD_ON = os.environ.get("YK_ZIDIAN", "1") != "0"
def zx(code, c, j, x):  # 句里难字加点线，点了弹小卡（只在中文页）
    if not (ZD_ON and code.startswith("zh")): return esc(x)
    m = {o: k for jj, o, k, g, s in ZD["per"].get(c, []) if jj == j}
    if not m: return esc(x)
    return "".join(f'<b class="nz" data-o="{j}.{o}">{esc(ch)}</b>' if o in m else esc(ch) for o, ch in enumerate(x))
ZI_JS = """<div id="zipop" class="zipop" hidden role="dialog"><div class="zh"><b class="zz"></b><span class="zp"></span><button type="button" class="zx" aria-label="关闭">×</button></div><p class="zg"></p><p class="zo"></p></div>
<script>(function(){var D=JSON.parse(document.getElementById('zidata').textContent),P=document.getElementById('zipop'),cur=null;
function off(){P.hidden=true;if(cur)cur.classList.remove('on');cur=null}
function show(z){var it=D.i[z.dataset.o];if(!it)return;if(cur)cur.classList.remove('on');cur=z;z.classList.add('on');
P.querySelector('.zz').textContent=it[0];P.querySelector('.zp').textContent=it[1];
var g=P.querySelector('.zg');g.textContent='';if(it[2]){g.appendChild(document.createTextNode(it[2]));var s=document.createElement('small');s.textContent='（'+it[3]+'）';g.appendChild(s)}g.hidden=!it[2];
var o=P.querySelector('.zo'),L=D.o[it[0]+'|'+it[1]]||[];o.textContent='全书读 '+it[1]+' 的「'+it[0]+'」共 '+L.length+' 章：';
L.forEach(function(x,i){if(i)o.appendChild(document.createTextNode(' '));var a=document.createElement(x[0]===D.c?'b':'a');a.textContent=x[0];if(x[0]!==D.c)a.href=x[1];o.appendChild(a)});
var r=z.getBoundingClientRect();P.hidden=false;P.style.top=(window.scrollY+r.bottom+6)+'px';P.style.left=Math.max(8,Math.min(window.scrollX+r.left-12,document.documentElement.clientWidth-P.offsetWidth-8))+'px';var pr=P.getBoundingClientRect();if(pr.bottom>innerHeight)window.scrollBy({top:pr.bottom-innerHeight+12,behavior:'smooth'})}
document.addEventListener('click',function(e){var z=e.target.closest&&e.target.closest('.nz');if(z){e.stopPropagation();e.preventDefault();if(cur===z)off();else show(z);return}
if(!P.hidden&&!P.contains(e.target))off();else if(e.target.closest&&e.target.closest('.zx'))off()},true);
document.addEventListener('keydown',function(e){if(e.key==='Escape')off()})})();</script>"""
def zi_tail(code, c, P):
    if not (ZD_ON and code.startswith("zh")) or c not in ZD["per"]: return ""
    items = {f"{j}.{o}": [k.split("|")[0], k.split("|")[1], g, s] for j, o, k, g, s in ZD["per"][c]}
    occ = {k: [[x, f"{P}lunyu/{PIAN[x.split('.')[0]][1]}/{x.split('.')[1]}.html"] for x in ZD["occ"].get(k, [])] for k in {r[2] for r in ZD["per"][c]}}
    d = json.dumps({"i": items, "o": occ, "c": c}, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/json" id="zidata">{d}</script>' + ZI_JS
WJ_TR = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "tri-weijiang.json"), encoding="utf-8")) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "tri-weijiang.json")) else {}  # 未讲章原文英日译（分享图用）
# 11-14 外文补译（智器译，见 tools/i18n/fill-<语种>.json）：界面漏译、首页日历与领读人、四种分享卡、关系图页框；nianli-tr.json 是年历 365 课“今日一句”九种外文
FILL = {}
for _l in ("en", "ja", "ko", "fr", "es", "de", "vi", "id", "ru"):
    _f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", f"fill-{_l}.json")
    if os.path.exists(_f): FILL[_l] = json.load(open(_f, encoding="utf-8"))
NLTR = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "nianli-tr.json"), encoding="utf-8")) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "nianli-tr.json")) else {}
WJ_FL = ("en", "ja")  # 未讲章出页的外文（11-13：译文现成 tri-weijiang.json；其余七语没有译文，先不出空壳页，外文页未讲章仍链简体）
def wj_tr_title(code, c):
    """外文未讲章标题：取译文首句（去掉“The Master said:”“先生が言われた。”一类引导语），英文最长 64 字母，日文 24 字。"""
    t = (WJ_TR.get(c, {}).get(code) or "").strip()
    if not t: return ""
    if code == "ja":
        t = re.sub(r"^[^、。「」]{1,6}(?:が言われた|が言った|が問うた)。", "", t)
        s = ""
        for m in re.finditer(r"[^。？！]+[。？！]?", t):
            s += m.group(0)
            if len(s) >= 8: break
        s = (s or t).rstrip("。").lstrip("「『")
        if "「" not in s: s = s.replace("」", "")
        return s if len(s) <= 24 else s[:23] + "…"
    t = re.sub(r"^(?:The Master|Confucius|[A-Z][a-z]+(?: [A-Z][a-z]+)?) (?:said|asked)(?: to [A-Z][a-z]+(?: [A-Z][a-z]+)?)?:\s+", "", t)
    s = ""
    for m in re.finditer(r"[^.?!;]+[.?!;]?", t):
        s += m.group(0)
        if len(s) >= 24: break
    s = (s or t).strip().rstrip(".;").lstrip("'\"‘“")
    if len(s) > 64:
        s = s[:64]
        s = (s.rsplit(" ", 1)[0] if " " in s[32:] else s).rstrip(" ,;:") + "…"
    return s[:1].upper() + s[1:]
WJ_UI = {  # 外文未讲章与闯关、检索新功能的界面字（11-13 主人：各语言功能尽量一致）
 "en": {"wj_tag": "not yet covered", "wj": "not yet covered", "wj_lead": "The video for this chapter is still in production. For now this page gives the original text, the facsimile page, a working translation and the commentary; the full reading follows when the video is out.",
        "wj_bh_note": "Draft plain-Chinese rendering following Zhu Xi; it will be checked when the chapter is covered.", "wj_src": "Text: Zhu Xi's Collected Commentaries on the Analects (Sibu Beiyao edition), page {n} of the base edition.",
        "wj_yang": "Yang Bojun's Lunyu yizhu numbers this chapter {y}.", "wj_pane": "Facsimile", "wj_vid": "The video for this chapter is in production and will appear here. Follow Yikonglu to see it first:",
        "wj_an_note": "Yikonglu's reading of this chapter is in Chinese for now; the English version comes with the video.", "wj_deep_zx": "Zhu Xi's commentary, line by line", "wj_deep_zx_p": "Zhu Xi's own words on each line of this chapter, each checked against the base-edition page. Other commentators are added when the chapter is covered.",
        "th_ju": "Line", "wj_cd_none": "",
        "search_none": "Nothing found. Covered chapters are indexed in full; other chapters by original text and translation.",
        "s_new": "Recently covered", "s_feed": "Subscribe", "s_last": "Last read"},
 "ja": {"wj_tag": "未講", "wj": "未講", "wj_lead": "この章の動画は制作中です。サイトでは先に原文・原頁・作業訳と注を載せ、動画の公開後に講読を補います。",
        "wj_bh_note": "現代中国語訳は朱注に沿った初稿です。講読時に見直します。", "wj_src": "原文は朱熹『論語集注』（四部備要本）、底本第 {n} 頁による。",
        "wj_yang": "楊伯峻『論語訳注』ではこの章を {y} とする。", "wj_pane": "原頁", "wj_vid": "この章の動画は制作中で、公開されたらここに載せます。一孔録をフォローすると、いち早く見られます：",
        "wj_an_note": "この章の一孔按は今のところ中国語のみです。日本語版は動画とともに出します。", "wj_deep_zx": "朱熹集注・句ごとの原文", "wj_deep_zx_p": "この章の各句についての朱注の原文。いずれも底本の頁と照合済みです。諸家の説は講読時に補います。",
        "th_ju": "句", "hj_h": "本句の互見", "hj_note": "注", "hj_book": "論語の他の箇所", "hj_other": "他書の出典", "hj_zb": "この章の諸注", "bb_link": "版本について", "zt_none": "既講の章にはまだありません。",
        "search_none": "見つかりませんでした。既講の章は全文、未講の章は原文と訳で検索できます。",
        "s_new": "最近講じた章", "s_feed": "更新を購読", "s_last": "前回の続き"},
 "ko": {"s_new": "최근 강독한 장", "s_feed": "구독", "s_last": "마지막으로 읽은 곳"},
 "fr": {"s_new": "Derniers chapitres lus", "s_feed": "S’abonner", "s_last": "Dernière lecture"},
 "es": {"s_new": "Capítulos recientes", "s_feed": "Suscribirse", "s_last": "Última lectura"},
 "de": {"s_new": "Zuletzt besprochen", "s_feed": "Abonnieren", "s_last": "Zuletzt gelesen"},
 "vi": {"s_new": "Chương mới giảng", "s_feed": "Theo dõi", "s_last": "Lần trước đọc đến"},
 "id": {"s_new": "Bab terbaru", "s_feed": "Langganan", "s_last": "Terakhir dibaca"},
 "ru": {"s_new": "Недавно разобранные главы", "s_feed": "Подписаться", "s_last": "Последнее прочитанное"},
}
TRI_TXT = {}  # 章 → 分享图三语（简体原文、英、日），各语种同一张；ascii 转义，繁体整页转换时不动
TAGLINE_L = {"zh-Hans": "逐字读经典原文", "zh-Hant": "逐字讀經典原文"}
MEIRI_TXT = {"zh-Hans": {"h": "今日《论语》", "read": "读这一章", "card": "生成分享图", "plan": "百日读完《论语》"}, "zh-Hant": {"h": "今日《論語》", "read": "讀這一章", "card": "生成分享圖", "plan": "百日讀完《論語》"}}
LANG_SHORT = {"zh-Hans": "简", "zh-Hant": "繁", "en": "EN", "ja": "日", "ko": "한", "fr": "FR", "es": "ES", "de": "DE", "vi": "VI", "id": "ID", "ru": "RU"}
LIVE_PILL = {"zh-Hans": "{o} 儒者在读 · 累计 {t}", "zh-Hant": "{o} 儒者在讀 · 累計 {t}", "en": "Confucians reading: {o} · total {t}", "ja": "{o} 人の儒者が読書中 · 累計 {t}", "ko": "유학자 {o}명 읽는 중 · 누적 {t}", "fr": "Lettrés en lecture : {o} · {t} en tout",
             "es": "Letrados leyendo: {o} · {t} en total", "de": "Gelehrte lesen: {o} · {t} gesamt", "vi": "{o} nhà nho đang đọc · {t} lượt", "id": "Cendekiawan membaca: {o} · total {t}", "ru": "Книжники читают: {o} · всего {t}"}
# 11-09 晚主人定：不再显示、也不再统计“来自几个国家和地区”
# 主人 11-08：单位用“儒者”，来的都是儒者；外文取各语里读书人的说法（英文 Confucians、越南 nhà nho、法 lettrés），写成“X：数”免得单复数不合
LIVE_TXT = {"zh-Hans": "此刻 {o} 位儒者在读 · 已有 {t} 位儒者来过", "zh-Hant": "此刻 {o} 位儒者在讀 · 已有 {t} 位儒者來過",
            "en": "Confucians reading now: {o} · Confucians so far: {t}", "ja": "いま {o} 人の儒者が読書中 · これまで {t} 人の儒者が来訪", "ko": "지금 유학자 {o}명이 읽는 중 · 지금까지 유학자 {t}명",
            "fr": "Lettrés en lecture : {o} · lettrés venus jusqu’ici : {t}", "es": "Letrados leyendo ahora: {o} · letrados hasta hoy: {t}", "de": "Gelehrte lesen gerade: {o} · bisher {t} Gelehrte",
            "vi": "{o} nhà nho đang đọc · {t} nhà nho đã ghé", "id": "Cendekiawan sedang membaca: {o} · cendekiawan sejauh ini: {t}", "ru": "Сейчас читают книжники: {o} · всего книжников: {t}"}

FOLD_RE = re.compile(r'<section class="sec ([^"]*)"((?: id="[^"]*")?)><h2>(.*?)</h2>(.*?)</section>', re.S)
def fold(h):  # 下半各节收成可点开的 <details>；锚点跳进来时由 FOLD_JS 自动展开
    return FOLD_RE.sub(lambda m: f'<details class="sec fold {m.group(1)}"{m.group(2)}><summary><h2>{m.group(3)}</h2></summary>{m.group(4)}</details>', h)
FOLD_JS = """<script>(function(){function op(){var h=decodeURIComponent(location.hash.slice(1));if(!h)return;var e=document.getElementById(h);if(!e)return;var d=e.closest("details");while(d){d.open=true;d=d.parentElement&&d.parentElement.closest("details")}setTimeout(function(){e.scrollIntoView()},0)}addEventListener("hashchange",op);op();document.addEventListener("click",function(ev){var a=ev.target.closest&&ev.target.closest('a[href^="#"]');if(a&&a.getAttribute("href")==location.hash)op()});var b=document.querySelector(".foldall");if(b)b.onclick=function(){var ds=document.querySelectorAll(".deep details.fold"),o=[].some.call(ds,function(d){return!d.open});[].forEach.call(ds,function(d){d.open=o});b.textContent=o?b.dataset.c:b.dataset.o}})();</script>"""
def cta_html(L, P):  # 上半末尾：免费读本、问一孔两张卡
    W = lang_tab(WEN, L.code)
    return (f'<div class="ctas"><a href="{P}duben.html"><b>{L.t("db_link")}</b><span>{L.t("cta_db_p")}</span></a>'
            f'<a href="{P}about.html#wen"><b>{W["link"]}</b><span>{L.t("cta_wen_p")}</span></a></div>')

def meta_desc(L, title, rend, yw):  # 外语章页摘要：先本语言（标题＋译文），原文放后，读者在搜索结果里先看到自己的语言
    if not rend: return f"{yw[:40]}… {L.t('book_lead')}"
    d = f"{title} — {rend}"
    cap = 90 if L.code in ("ja", "ko") else 150
    if len(d) > cap:
        d = d[:cap]
        if " " in d[cap // 2:]: d = d.rsplit(" ", 1)[0]
        d = d.rstrip(" ,.;:，。") + "…"
    return d

def page(L, title, desc, rel, body, jsonld=None, cls="", alts=None, og_img=None, head_extra="", codes=None):
    """rel：不带语种前缀的站内路径（"" 为首页）。"""
    if not L.code.startswith("zh"): body = hant_scripture(body)
    url = f"{DOMAIN}/{L.prefix}{rel}"
    fp = __import__("hashlib").sha1(f"yikonglu.com|{L.code}|{rel}".encode()).hexdigest()[:12]  # 每页固定出处编号，搬走的页也带着
    def _own(d):
        if not isinstance(d, dict) or d.get("@type") in (None, "Organization", "BreadcrumbList", "Person"): return d
        return dict(d, copyrightHolder={"@type": "Organization", "name": "一孔录", "url": DOMAIN},
                    license="https://creativecommons.org/licenses/by/4.0/", identifier=f"yikonglu:{fp}")
    if isinstance(jsonld, dict):
        jsonld = dict(jsonld, **{"@graph": [_own(x) for x in jsonld["@graph"]]}) if "@graph" in jsonld else _own(jsonld)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    codes = codes or list(LANGS)  # 只有部分语种的页（如“故事”栏只出简繁）
    if rel.startswith("renwu/"): codes = ["zh-Hans", "zh-Hant"] + [k for k in GX.langs() if k in LANGS]  # 人物卡：简繁＋已译的外文（11-14）
    elif rel.startswith(("gushi/", "zhuanti/lu-")) or (rel.startswith("shuyuan/") and rel != "shuyuan/ruyuan.html") or rel in ("zhuanti/keben.html", "jihua/bairi.html"): codes = ["zh-Hans", "zh-Hant"]  # 课本专题只有简繁（11-09 谷歌报外文版 404）
    if rel == "404.html": codes = ["zh-Hans"]  # 404 页只有一份，不指向不存在的外文 404
    alt_links = "".join(f'<link rel="alternate" hreflang="{LANGS[k][2]}" href="{DOMAIN}/{LANGS[k][0]}{rel}">' for k in codes)
    alt_links += f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/{rel}">'
    sw = "".join(f'<a href="{DOMAIN}/{LANGS[k][0]}{rel if k in codes else ""}" data-lang="{k}"{" class=cur" if k == L.code else ""}>{LANGS[k][1]}</a>' for k in LANGS)
    gs = GUSHI_ON and L.code.startswith("zh")
    rw = RENWU_ON and L.code.startswith("zh")
    P = "/" + L.prefix
    note = f'<p class="trnote wrap">{L.t("translated_note")}</p>' if L.t("translated_note") else ""
    if rel and not rel.startswith(("lunyu/", "offline", "404", "nianli/", "changhe/", "daidu/")):  # 11-14 全站“今日《论语》”细条（首页、论语各页不放）：与首页今日卡同一章，可关一天
        LU = lyui(L)
        note += (f'<div class="lystrip" id="lyst" hidden><div class="wrap"><b></b><span lang="zh-Hans"></span><a href="#">{esc(LU["read"])}</a><button type="button" title="{esc(LU["close"])}" aria-label="{esc(LU["close"])}">×</button></div></div>'
                 '<script>(function(){var d=Math.floor((Date.now()+288e5)/864e5),k="ykl_lyst";try{if(localStorage.getItem(k)==String(d))return}catch(e){}'
                 + ('if(d>=' + str(LX.NL0) + '){var bj=new Date(Date.now()+288e5);fetch("/data/nianli-' + L.code + '.json").then(function(r){return r.json()}).then(function(N){var y=N[(bj.getUTCMonth()+1)+"-"+bj.getUTCDate()];if(!y)return;var S=document.getElementById("lyst");S.querySelector("b").textContent=' + json.dumps(LU["strip"], ensure_ascii=False) + '+" "+y[6];S.querySelector("span").textContent=y[3];S.querySelector("a").href=y[2];S.hidden=false;S.querySelector("button").onclick=function(){S.hidden=true;try{localStorage.setItem(k,String(d))}catch(e){}}}).catch(function(){});return}' if L.code in ("zh-Hans", "zh-Hant") or ((FILL.get(L.code) or {}).get("c") and NLTR) else '')
                 + 'fetch("/data/meiri-' + L.code + '.json").then(function(r){return r.json()}).then(function(R){var d0=d*864e5-288e5,C=R.filter(function(x){return !x[2]||Date.parse(x[2])<d0});if(!C.length)return;'
                 'var x=C[(d*7919)%C.length],S=document.getElementById("lyst");S.querySelector("b").textContent=' + json.dumps(LU["strip"], ensure_ascii=False) + '+" "+x[0];S.querySelector("span").textContent=x[3];S.querySelector("a").href=x[1];S.hidden=false;'
                 'S.querySelector("button").onclick=function(){S.hidden=true;try{localStorage.setItem(k,String(d))}catch(e){}}}).catch(function(){})})();</script>')
    return f"""<!doctype html>
<html lang="{L.hreflang}" data-yk="{fp}">
<head>
<meta charset="utf-8">
<!-- 一孔录 yikonglu.com · {fp} · 原载 {url} -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="一孔录"><meta name="copyright" content="一孔录 yikonglu.com"><link rel="license" href="https://creativecommons.org/licenses/by/4.0/">
<link rel="canonical" href="{url}">
{alt_links}
<link rel="alternate" type="application/atom+xml" title="一孔录" href="/{L.prefix}feed.xml">
<link rel="icon" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/seal-180.png">
<link rel="manifest" href="/{L.prefix}manifest.webmanifest">
<meta name="theme-color" content="#f2f1ea" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#111513" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="一孔录">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="一孔录">
<meta property="og:image" content="{DOMAIN}/{og_img or "assets/og.jpg"}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">{head_extra}
<meta name="twitter:card" content="summary_large_image">
{HEAD_FONTS}
<link rel="stylesheet" href="/style.css">
{ld}
{analytics(L)}
</head>
<body class="{cls}">
<header class="top"><div class="wrap">
<a href="{P}" class="brand"><img src="/assets/seal-180.png" alt="" width="30" height="30">一孔录</a>{'<span class="livep" id="livep" hidden></span>' if ANALYTICS.get("live") else ""}
<nav><a href="{P}lunyu/" class="lynav">{lyui(L)["nav"]}</a><a href="{P}shumu/">{L.t("nav_books")}</a><a href="{P}zhuanti/">{L.t("nav_topics")}</a><a href="{P}search.html">{L.t("nav_search")}</a><a href="{P}kanwu.html">{L.t("nav_errata")}</a>{f'<a href="{P}shuyuan/" class="gsnav">书院</a>' if gs else ""}
<details class="lang more"><summary>{L.t("nav_more")}</summary><div>{f'<a href="{P}lunyu/guanxi/">关系图</a>' if rw else (f'<a href="{P}lunyu/guanxi/">{esc(GX.TR[L.code]["S"]["gx_h1"])}</a>' if not L.code.startswith("zh") and GXD and GX.has_lang(L.code) else "")}<a href="{P}duben.html">{L.t("db_link")}</a><a href="{P}fangfa.html">{lang_tab(FANGFA, L.code)["link"]}</a><a href="{P}kaifang.html">{L.t("dt_link")}</a><a href="{P}feed.xml">{L.t("feed")}</a><a href="{P}about.html">{L.t("nav_about")}</a><a href="{P}zhichi.html" class="zc">{L.t("zc_link")}</a></div></details>
<details class="lang"><summary><span class="lfull">{L.name}</span><span class="lshort" aria-hidden="true">{LANG_SHORT.get(L.code, L.code[:2].upper())}</span></summary><div>{sw}</div></details></nav>
</div></header>{'<script>(function(){var l=document.querySelector(".top nav>.lang:not(.more)"),w=document.querySelector(".top .wrap");if(l&&w&&innerWidth<=700)w.style.setProperty("--lw",(l.offsetWidth+10)+"px")})()</script>' if ANALYTICS.get("live") else ""}
{note}
{body}
<section class="follow{'' if L.code.startswith('zh') else ' intl'}"><div class="wrap"><h2>{L.t("follow_h")}</h2><div class="fl"><figure><img src="/assets/wechat-qr.jpg" alt="WeChat QR" width="129" height="129" loading="lazy"><figcaption>{L.t("follow_wx")}{(" " if not L.code.startswith("zh") else "") + lang_tab(WEN, L.code)["foot"].replace("{p}", P)}{"" if not L.code.startswith("zh") else "。"}</figcaption></figure><a class="btn yt" id="fyt" href="https://www.youtube.com/@yikonglu?sub_confirmation=1" target="_blank" rel="noopener">▶ {L.t("follow_yt")}</a></div></div></section><script>(function(){{var z="";try{{z=Intl.DateTimeFormat().resolvedOptions().timeZone||""}}catch(e){{}}if(!/^Asia\\/(Shanghai|Chongqing|Chungking|Harbin|Urumqi|Kashgar)$|^PRC$/.test(z))return;var a=document.getElementById("fyt");if(!a)return;a.href="https://space.bilibili.com/18385461";a.className="btn bl";a.textContent="{"在哔哩哔哩关注" if L.code.startswith("zh") else "Follow on Bilibili"}"}})();</script>
<footer><div class="wrap">
<div class="fbrand"><img src="/assets/seal-180.png" alt="" width="36" height="36"><div><b>一孔录</b><span>{L.t("tagline")}</span></div></div>
<p>{L.t("foot_src")}</p>
<p class="where">{where_html(L)}</p>
<div class="fgrp"><p><b>{L.t("grp_read")}</b><a href="{P}shumu/">{L.t("nav_books")}</a><a href="{P}zhuanti/">{L.t("nav_topics")}</a>{f'<a href="{P}lunyu/guanxi/">《论语》关系图</a>' if rw else (f'<a href="{P}lunyu/guanxi/">{esc(GX.TR[L.code]["S"]["gx_h1"])}</a>' if not L.code.startswith("zh") and GXD and GX.has_lang(L.code) else "")}{f'<a href="{P}shuyuan/">书院</a>' if gs else ""}</p><p><b>{L.t("grp_check")}</b><a href="{P}search.html">{L.t("nav_search")}</a><a href="{P}kanwu.html">{L.t("nav_errata")}</a><a href="{P}lunyu/banben/">{L.t("bb_link")}</a><a href="{P}fangfa.html">{lang_tab(FANGFA, L.code)["link"]}</a></p><p><b>{L.t("grp_use")}</b><a href="{P}duben.html">{L.t("db_link")}</a><a href="{P}kaifang.html">{L.t("dt_link")}</a><a href="{P}feed.xml">{L.t("feed")}</a><a href="{P}about.html">{L.t("nav_about")}</a><a href="{P}yinsi.html">{PRIVACY.get(L.code, PRIVACY["en"])[0]}</a><a href="{P}zhichi.html">{L.t("zc_link")}</a>{SY.link(L, P)}</p></div>
<p class="langs">{sw}</p>
<p class="fcopy">© 2026 {L.t("foot_org")}</p>
<p class="freuse">{L.t("foot_reuse", p=P)}</p>
</div></footer>
{LANG_JS}
{MIRROR_JS.replace("@BAR@", L.t("mirror_bar")).replace("@GO@", L.t("mirror_go"))}
<script>if("serviceWorker" in navigator)addEventListener("load",function(){{navigator.serviceWorker.register("/sw.js").catch(function(){{}})}})</script>
<script defer src="/assets/a2hs.js?v={A2V}"></script>
<script defer src="/assets/xudu.js?v={XDV}"></script>
</body>
</html>
"""

def yxl_counts(D):
    """一孔影响力的跨书计数：开讲几部书、已讲原文多少字、视频已公开几集（章数各书单位不同，不作总数）。"""
    now = datetime.datetime.now(datetime.timezone.utc)
    books = len(D.get("live_books") or ["论语"])
    zi = sum(len(re.sub(r"[^\u4e00-\u9fff]", "", D["yw"].get(c, ""))) for c in D["pub"])
    eps = {D["ch2ep"][c][0] for c in D["pub"] if c in D["ch2ep"] and D["ch2ep"][c][1].get("youtube") and (not D["ch2ep"][c][1].get("public_at") or datetime.datetime.fromisoformat(D["ch2ep"][c][1]["public_at"]) <= now)}
    return books, zi, len(eps)

def yxl_block(L, D, P, full=False):
    """首页“一孔影响力”栏（简繁）。四格自证数从站内数据算；“能找到吗”用 影响力.json。full=True 给方法页多出的说明。"""
    y = D.get("yxl") or {}
    n_all = sum(PIAN[p][3] for p in PIAN)
    n_cites = sum(1 for g in D["gao"].values() for x in g["cites"] if x["pages"])
    fam = (1 if D["pages_avail"] else 0) + (1 if any("huang" in v for v in D["zhuben"].values()) else 0)
    kw = D["kw"]; readers = [r for r in kw if r[7] != "一孔录自查"]
    now = datetime.datetime.now(datetime.timezone.utc)
    vid = {c for c in D["pub"] if c in D["ch2ep"] and D["ch2ep"][c][1].get("youtube") and (not D["ch2ep"][c][1].get("public_at") or datetime.datetime.fromisoformat(D["ch2ep"][c][1]["public_at"]) <= now)}
    nb, zi, ne = yxl_counts(D)
    grid = (f'<div class="yxgrid"><a class="c" href="{P}shumu/"><b>{zi:,}<small>字</small></b><span>原文已讲 · 开讲 {nb} 部书 · 视频已公开 {ne} 集</span></a>'
            f'<a class="c" href="{P}lunyu/banben/"><b>{n_cites}<small>条</small></b><span>引文可核到底本原页</span></a>'
            f'<a class="c" href="{P}lunyu/banben/"><b>{fam}<small>家</small></b><span>注本上了原页图</span></a>'
            f'<a class="c" href="{P}kanwu.html"><b>{len(readers)}<small>条</small></b><span>读者来信 · 勘误共 {len(kw)} 条（均公开）</span></a></div>')
    rows = ""
    for pf in y.get("platforms", []):
        sc = pf.get("score")
        if sc is None: continue
        sh = pf.get("share"); shs = f'<small>占比 {sh}%</small>' if sh is not None else ""
        ms = pf.get("measured"); mtx = f'<small>本周已测 {ms}/{y.get("chapters")} 章</small>' if pf.get("partial") and ms is not None and y.get("chapters") else ""
        rows += f'<div class="row"><span>{esc(pf["name"])}{mtx}</span><div class="bar"><i style="width:{min(max(float(sc), 0), 100):g}%"></i></div><em>{sc}{shs}</em></div>'
    hist = [h for h in y.get("history", []) if h.get("score") is not None]; score = y.get("score")
    if len(hist) >= 2:
        W, H = 320, 60; mx = max(max(h["score"] for h in hist), 1)
        pts = " ".join(f"{10 + i * (W - 20) / (len(hist) - 1):.1f},{H - 8 - h['score'] / mx * (H - 16):.1f}" for i, h in enumerate(hist))
        svg = f'<svg class="yxline" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true"><polyline fill="none" stroke="currentColor" stroke-width="2" points="{pts}"/>' + "".join(f'<circle cx="{pt.split(",")[0]}" cy="{pt.split(",")[1]}" r="3" fill="currentColor"/>' for pt in pts.split()) + "</svg>"
        trend = svg + f'<small>{hist[0]["week"]} 起，每周一点</small>'
    elif hist:
        trend = f'<svg class="yxline" viewBox="0 0 320 60" width="320" height="60" aria-hidden="true"><circle cx="20" cy="30" r="4" fill="currentColor"/></svg><small>{hist[0]["week"][:7]} 从 {hist[0]["score"]} 分起步</small>'
    else: trend = ""
    find = "" if score is None else (f'<div class="yxfind"><h3>在平台上搜一句原文，能找到一孔录吗</h3>{rows}'
            f'<div class="yxscore"><b>找到分 <strong>{score}</strong></b>' + (f'<b>占比 <strong>{y["share"]}%</strong></b>' if y.get("share") is not None else "") + f'{trend}</div>'
            f'<p>做法：取已发各章首句，不登录搜索，看一孔录讲读是否在前 20 条，折成 0—100 的平台分；平台搜索因人因地而异，你搜到的可能不同。<a class="more" href="{P}yingxiangli.html">方法与原始数据 ›</a></p></div>')
    ix = y.get("index") or {}
    ixp = [f"{nm} {ix[k]['indexed']} / {ix[k]['total']} 页" for k, nm in (("google", "谷歌"), ("bing", "必应")) if isinstance(ix.get(k), dict) and ix[k].get("indexed") is not None and ix[k].get("total")]
    if ixp: find += f'<p class="yxindex">收录：{" · ".join(ixp)}</p>'
    sub = f'每天更新 · 最近一次 {esc(y.get("updated") or D["today"])} · 每个数都可点开核对'
    return f'<section class="wrap narrow yxl"><h2 class="ph">一孔影响力</h2><p class="sub">{sub}</p>{grid}{find}</section>'

def draft_sec(D):
    """方法页“初稿改动比例”一节与逐集表。"""
    dr = D.get("draft") or {}
    if not SHOW_DRAFT or not dr.get("rows"): return ""
    trs = "".join(f"<tr><td>{esc(r['ep'])}</td><td>{r['segments']}</td><td>{r['changed']}</td><td>{100 * r['changed'] / r['segments']:.1f}%</td></tr>" for r in dr["rows"] if r.get("segments"))
    return (f'<h2 id="chugao">初稿改动比例</h2><p>初稿改动比例＝每集最早版与定版旁白/原文段按编号逐段比对，文字不同即算改动，改动段数÷总段数；只算已进定版的集；按季汇总。'
            f'现为 {dr.get("ratio")}%（{dr.get("episodes")} 集、{dr.get("segments")} 段，{esc(str(dr.get("updated", "")))} 更新）。</p>'
            f'<table><thead><tr><th>集</th><th>段数</th><th>改动段</th><th>比例</th></tr></thead><tbody>{trs}</tbody></table>'
            f'<p><a href="/data/chugao-gaidong.json">chugao-gaidong.json</a>（逐集明细）</p>')

HERO_V = __import__("hashlib").md5(b"".join(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", f), "rb").read() for f in ("hero-w.jpg", "hero-m.jpg"))).hexdigest()[:8]  # 横幅换图后换地址，免得手机上旧图配新比例（11-14 主人见柯基只剩头）

LY_ICON = {  # 《论语》书页入口图标（11-14 主人：一行一条，配图标）：线描，跟随文字色
 "nl": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M8 3v4M16 3v4"/><path d="M8 13h2M12 13h2M16 13h0.01M8 16.5h2M12 16.5h2"/>',
 "gx": '<circle cx="12" cy="5.5" r="2.3"/><circle cx="5" cy="18" r="2.3"/><circle cx="19" cy="18" r="2.3"/><circle cx="12" cy="13" r="1.6"/><path d="M12 7.8v3.6M10.7 14.1l-4 2.4M13.3 14.1l4 2.4M7.3 18h9.4"/>',
 "ch": '<path d="M4 5.5h16v10H10l-4.5 3.5v-3.5H4z"/><path d="M8 9.5h8M8 12.5h5"/>',
 "kb": '<path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5z"/><path d="M12 6.5v13"/>',
 "dd": '<circle cx="8" cy="7" r="2.6"/><path d="M3 19.5c0-3.3 2.2-5.5 5-5.5s5 2.2 5 5.5"/><circle cx="16.5" cy="9" r="2.1"/><path d="M14.2 14.6c.7-.4 1.5-.6 2.3-.6 2.4 0 4.2 1.9 4.2 4.8"/>',
 "bb": '<path d="M6 3.5h9l3.5 3.5v13.5H6z"/><path d="M15 3.5V7h3.5"/><circle cx="11.5" cy="13" r="2.8"/><path d="M13.6 15.1l2.4 2.4"/>',
}

def ly_links(L, D, P):
    """《论语》书页入口：一行一条，左图标、中标题与一句说明、右箭头。外文只有版本说明一条（其余页只有中文）。"""
    zh = L.code.startswith("zh")
    rows = []
    if zh:
        if D["lx"]["nl"]: rows.append(("nl", f"{P}nianli/", "《论语》年历", "一天一课，一年一轮，从元旦读到除夕"))
        if GXD: rows.append(("gx", f"{P}lunyu/guanxi/", "关系图", "498 章怎样连着，197 位人物各在哪几章"))
        if D["lx"]["ch"]: rows.append(("ch", f"{P}changhe/", "场合用句", "取名、开学、结婚、送别，该说哪一句"))
        rows.append(("kb", f"{P}zhuanti/keben.html", "语文课本里的《论语》", "初中、高中课文选的各章"))
        if D["lx"]["dd"]: rows.append(("dd", f"{P}daidu/", "课本十二章带读", "给老师和家长：怎么带孩子读"))
        rows.append(("bb", f"{P}lunyu/banben/", "版本说明", "五家注本用的哪个本子，原页从哪来"))
        if L.code == "zh-Hant":
            T = __import__("opencc").OpenCC("s2twp").convert
            rows = [(k, h, T(a), T(b)) for k, h, a, b in rows]
    else:
        rows.append(("bb", f"{P}lunyu/banben/", L.t("bb_title"), L.t("bb_sub")))
    li = "".join(f'<li><a href="{h}"><span class="lyi" aria-hidden="true"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{LY_ICON[k]}</svg></span>'
                 f'<span class="lyt"><b>{esc(a)}</b><small>{esc(b)}</small></span><span class="lya" aria-hidden="true">›</span></a></li>' for k, h, a, b in rows)
    return f'<ul class="lylinks">{li}</ul>'

def redirect_page(L, target, frag, title):
    """旧网址跳新址：保留 #锚点；noindex＋canonical 指新址。"""
    return (f'<!doctype html><meta charset="utf-8"><title>{esc(title)}｜一孔录</title><link rel="canonical" href="{DOMAIN}/{target}">'
            f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url=/{target}{frag}">'
            f'<script>location.replace("/{target}"+(location.hash||"{frag}"))</script><a href="/{target}{frag}">{esc(title)}</a>')

def about_zh(L, D, P):
    """关于页（简繁）：一孔自述。主人 11-09 定：不露脸，把匿名当神秘感，信赖靠可查；照片栏放脸是空洞的头像，寓意一孔。主人删掉平台、数字和转载一节（转载说明在开放数据页）。"""
    kwn = len(D["kw"])
    cards = [
        ("原", "每句有出处", "原文照底本逐字录入，注家原话标页码，附原书影像。", f"{P}lunyu/banben/", "看底本"),
        ("勘", "讲错公开记", "原来怎么说、改成什么、依据什么，按日期列着，旧的不删。", f"{P}kanwu.html", f"已记 {kwn} 处"),
        ("法", "做法写明白", "智器帮我起草、配音、出图；底本、读法、引文由我逐字核定。我的读法署“一孔按”，不冒充古人。", f"{P}fangfa.html", "看做法"),
        ("开", "数据公开", "原文、白话、读音、引文出处按篇下载，谁都能拿去核。", f"{P}kaifang.html", "下载"),
    ]
    grid = "".join(f'<a href="{h}"><i>{i}</i><b>{t}</b><p>{x}</p><span class="n">{n} →</span></a>' for i, t, x, h, n in cards)
    return f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("tagline")}</span>关于一孔</h1></div></div>
<main class="wrap narrow prose yks"><p class="about-def">{L.t("about_def")}</p>
<div class="ykhead"><figure class="ykphoto"><img src="/assets/yikong-kong.svg" alt="一孔的照片：脸是一个空洞，洞里透出《论语》原文" width="400" height="480"><figcaption>一孔</figcaption></figure>
<div><p class="ykmotto">一孔不重要，经文和出处才重要。</p>
<p>我是一孔，不露面，不讲身世，照片只有这一张。古书里“佚名”“某氏曰”多的是，传下来的是话，不是说话的人。</p>
<p>你不必信我，下面这些都能查。</p></div></div>
<div class="ykg">{grid}</div>
<h2 id="zhuanzai">{L.t("about_h4")}</h2><ul><li>{L.t("about_r1")}</li><li>{L.t("about_r2")}</li><li>{L.t("about_r3")}</li><li>{L.t("about_r4")}</li><li>{L.t("about_r5", p=P)}</li></ul>
<h2>在哪里找我</h2><p>留言或写信，每封都看。</p><p class="mailp">{MAIL}</p></main>'''


def yxl_line(L, D, P):
    """首页搜索框下一行小字（简繁）。主人 11-07 定：只留原文已讲字数、视频集数、公开勘误数，找到分等都放方法页。"""
    nb, zi, ne = yxl_counts(D)
    parts = [f"原文已讲 {zi:,} 字", f"视频 {ne} 集", f"公开勘误 {len(D['kw'])} 条"]
    return f'<p class="yxline-s"><a href="{P}yingxiangli.html">一孔影响力</a> · ' + " · ".join(f"<span>{x}</span>" for x in parts) + "</p>"

# 隐私说明页（/yinsi.html）：七语各一份，繁体由简体转
PRIVACY = {
 "zh-Hans": ("隐私", "隐私说明", "本站收什么、不收什么", [
   "不用注册，不设留言区，不收表单。",
   "访问统计用 Cloudflare Web Analytics：不设 cookie，不认人，只计页面访问量、来路和国家或地区。简体中文页另装百度统计，它会设 cookie，用来计访问量和来路；繁体和外文页不装。",
   "首页那行“此刻在读 / 读者来过”的人数，由我们自己在 Cloudflare 上的一个小程序计：你的浏览器本地存一个随机编号，每分钟告诉它一声“还在读”，它只记这个编号和时间，用来数人数，不存 IP，也不记别的。",
   "“一孔书院”筹备页上的“我想第一批加入”和“最想要哪样”，只给计数加一，不收姓名、邮箱、电话；同一浏览器点过一次，本地记个标记，不再重复计。",
   "章节页里的视频：简体中文页在中国大陆时区的设备上嵌哔哩哔哩播放器（player.bilibili.com），它可能设 cookie，按哔哩哔哩的隐私政策处理；其他情况用 YouTube 的隐私增强模式（youtube-nocookie.com）嵌入，点播放之后才由 YouTube 按它的隐私政策处理。选哪个只看你设备的时区设置，不上传；你手动切换后，选择记在本地。",
   "字体从 Google Fonts 加载，你的浏览器会向谷歌请求字体文件。",
   "语言选择、是否已关掉“装到桌面”提示，记在你浏览器的本地存储里；看过的页面缓存在你的设备上，离线也能打开。这些都不上传。",
   "写信来勘误或提问，信只用来核对和回复。记入勘误页时只署你给的网名，不公开邮箱；想撤下署名，写信说一声就撤。",
   "以上有变动，会改这一页并更新下面的日期。"], "有问题请写信："),
 "en": ("Privacy", "Privacy", "What this site collects, and what it does not", [
   "No accounts, no comment section, no forms.",
   "Visits are counted with Cloudflare Web Analytics, which sets no cookies and does not identify you; it counts page views, referrers and country or region. Simplified-Chinese pages also carry Baidu Tongji, which does set cookies for counting visits and referrers; other language versions do not.",
   "The “reading now / readers so far” line on the home page is counted by a small program of ours on Cloudflare: your browser keeps a random ID in local storage and pings it once a minute while you read. It keeps only that ID and the time, to count heads; it does not store your IP address or anything else.",
   "On the Yikonglu Academy page, “I'd like to join” and “what would you want most” only add one to a count; no name, email or phone is collected. Your browser keeps a local mark so you are counted once.",
   "Videos on chapter pages are embedded in YouTube's privacy-enhanced mode (youtube-nocookie.com); once you press play, YouTube handles data under its own privacy policy.",
   "Fonts load from Google Fonts, so your browser requests font files from Google.",
   "Your language choice and whether you dismissed the “add to home screen” tip are kept in your browser's local storage; pages you have read are cached on your device for offline use. None of this is uploaded.",
   "If you write to us with a correction or question, the email is used only to check and reply. If your correction is listed on the corrections page, we show only the username you give us, never your address; write to us and we will remove it.",
   "If anything here changes, we will update this page and the date below."], "Questions: "),
 "ja": ("プライバシー", "プライバシーについて", "このサイトが集めるもの・集めないもの", [
   "登録不要、コメント欄やフォームはありません。",
   "アクセス集計は Cloudflare Web Analytics を使います。cookie を使わず個人を識別せず、閲覧数・参照元・国や地域のみを数えます。簡体字中国語のページにのみ百度統計を入れており、これは閲覧数と参照元を数えるため cookie を使います。",
   "トップページの「いま読書中／これまでの読者」の人数は、Cloudflare 上の小さなプログラムで数えています。ブラウザのローカルストレージにランダムな番号を一つ置き、読んでいる間 1 分ごとに知らせるだけで、記録するのはその番号と時刻のみです。IP アドレスなどは保存しません。",
   "「一孔書院」準備ページの「最初のメンバーになりたい」「一番ほしいもの」は人数を数えるだけで、名前・メール・電話は集めません。同じブラウザで一度押すとローカルに印を残し、二重に数えません。",
   "章ページの動画は YouTube のプライバシー強化モード（youtube-nocookie.com）で埋め込んでいます。再生後は YouTube のプライバシーポリシーに従って扱われます。",
   "フォントは Google Fonts から読み込むため、ブラウザが Google にフォントを要求します。",
   "言語の選択と「ホーム画面に追加」の案内を閉じたかどうかはブラウザのローカルストレージに保存し、読んだページはオフライン用に端末にキャッシュします。いずれも送信しません。",
   "訂正や質問のメールは確認と返信にのみ使います。訂正ページに載せる場合はお知らせいただいたハンドル名のみを記し、メールアドレスは公開しません。削除をご希望ならご連絡ください。",
   "内容を変更した場合はこのページと下の日付を更新します。"], "お問い合わせ："),
 "ko": ("개인정보", "개인정보 안내", "이 사이트가 수집하는 것과 수집하지 않는 것", [
   "가입이 필요 없고, 댓글란이나 양식이 없습니다.",
   "방문 통계는 Cloudflare Web Analytics로 집계합니다. 쿠키를 쓰지 않고 개인을 식별하지 않으며 페이지 조회수, 유입 경로, 국가·지역만 셉니다. 간체 중국어 페이지에만 바이두 통계를 넣었으며, 이는 조회수와 유입 경로 집계를 위해 쿠키를 씁니다.",
   "첫 페이지의 ‘지금 읽는 중 / 지금까지 독자’ 숫자는 Cloudflare에 둔 작은 프로그램이 셉니다. 브라우저 로컬 저장소에 무작위 번호 하나를 두고 읽는 동안 1분마다 알릴 뿐이며, 그 번호와 시각만 기록합니다. IP 주소 등은 저장하지 않습니다.",
   "‘일공서원’ 준비 페이지의 ‘첫 회원이 되고 싶다’와 ‘가장 원하는 것’은 숫자만 하나 더하며 이름·이메일·전화번호는 받지 않습니다. 같은 브라우저에서는 로컬에 표시를 남겨 한 번만 셉니다.",
   "장 페이지의 영상은 YouTube 개인정보 보호 강화 모드(youtube-nocookie.com)로 넣었습니다. 재생한 뒤에는 YouTube의 개인정보처리방침에 따릅니다.",
   "글꼴은 Google Fonts에서 불러오므로 브라우저가 Google에 글꼴 파일을 요청합니다.",
   "언어 선택과 ‘홈 화면에 추가’ 안내를 닫았는지 여부는 브라우저 로컬 저장소에 두고, 읽은 페이지는 오프라인용으로 기기에 캐시합니다. 어느 것도 전송하지 않습니다.",
   "정정이나 질문 메일은 확인과 답장에만 씁니다. 정정 페이지에 올릴 때는 알려 주신 닉네임만 적고 메일 주소는 공개하지 않습니다. 삭제를 원하시면 메일로 알려 주세요.",
   "내용이 바뀌면 이 페이지와 아래 날짜를 고칩니다."], "문의: "),
 "fr": ("Confidentialité", "Confidentialité", "Ce que ce site recueille, et ce qu'il ne recueille pas", [
   "Pas de compte, pas d'espace de commentaires, pas de formulaire.",
   "Les visites sont comptées avec Cloudflare Web Analytics, sans cookie et sans vous identifier : pages vues, provenance, pays ou région. Les pages en chinois simplifié utilisent en plus Baidu Tongji, qui dépose des cookies pour compter les visites et leur provenance ; les autres langues non.",
   "La ligne « en train de lire / lecteurs jusqu’ici » de l’accueil est comptée par un petit programme à nous sur Cloudflare : votre navigateur garde un identifiant aléatoire en stockage local et le signale une fois par minute pendant la lecture. Seuls cet identifiant et l’heure sont gardés, pour compter ; ni votre adresse IP ni rien d’autre n’est conservé.",
   "Sur la page de l'Académie Yikonglu, « Je veux rejoindre le premier groupe » et « ce que vous voulez le plus » ne font qu'ajouter un à un compteur ; aucun nom, e-mail ni téléphone n'est collecté. Votre navigateur garde une marque locale pour ne compter qu'une fois.",
   "Les vidéos des pages de chapitre sont intégrées en mode de confidentialité renforcée de YouTube (youtube-nocookie.com) ; une fois la lecture lancée, YouTube traite les données selon sa propre politique.",
   "Les polices sont chargées depuis Google Fonts : votre navigateur demande les fichiers de police à Google.",
   "Votre choix de langue et le fait d'avoir fermé l'invitation « ajouter à l'écran d'accueil » sont gardés dans le stockage local de votre navigateur ; les pages lues sont mises en cache sur votre appareil pour la lecture hors ligne. Rien de cela n'est envoyé.",
   "Si vous nous écrivez pour une correction ou une question, le courriel ne sert qu'à vérifier et à répondre. Une correction citée sur la page des corrections ne porte que le pseudonyme que vous nous donnez, jamais votre adresse ; écrivez-nous pour le faire retirer.",
   "Si quelque chose change, nous mettrons à jour cette page et la date ci-dessous."], "Questions : "),
 "es": ("Privacidad", "Privacidad", "Qué recoge este sitio y qué no", [
   "Sin registro, sin sección de comentarios, sin formularios.",
   "Las visitas se cuentan con Cloudflare Web Analytics, que no usa cookies ni le identifica: solo cuenta páginas vistas, procedencia y país o región. Las páginas en chino simplificado usan además Baidu Tongji, que sí usa cookies para contar visitas y procedencia; las demás lenguas no.",
   "La línea «leyendo ahora / lectores hasta hoy» de la portada la cuenta un pequeño programa nuestro en Cloudflare: su navegador guarda un identificador aleatorio en el almacenamiento local y lo avisa una vez por minuto mientras lee. Solo se guardan ese identificador y la hora, para contar; no se guarda su dirección IP ni nada más.",
   "En la página de la Academia Yikonglu, «Quiero estar en el primer grupo» y «lo que más quiere» solo suman uno a un contador; no se recoge nombre, correo ni teléfono. Su navegador guarda una marca local para contarle una sola vez.",
   "Los vídeos de las páginas de capítulo se insertan en el modo de privacidad mejorada de YouTube (youtube-nocookie.com); al pulsar reproducir, YouTube trata los datos según su propia política.",
   "Las fuentes se cargan desde Google Fonts, así que su navegador pide los archivos de fuente a Google.",
   "Su elección de idioma y si cerró el aviso de «añadir a la pantalla de inicio» se guardan en el almacenamiento local de su navegador; las páginas leídas quedan en caché en su dispositivo para leer sin conexión. Nada de esto se envía.",
   "Si nos escribe con una corrección o una pregunta, el correo solo se usa para comprobar y responder. Si su corrección aparece en la página de correcciones, solo figura el nombre de usuario que nos dé, nunca su dirección; escríbanos y lo retiramos.",
   "Si algo cambia, actualizaremos esta página y la fecha de abajo."], "Preguntas: "),
}
PRIVACY["zh-Hant"] = PRIVACY["zh-Hans"]

DATE_TOK, DATE_TOK_SL = "\ue0f0DATE\ue0f1", "\ue0f0DATESL\ue0f1"

DDJ_DIR = os.environ.get("YK_DDJ_DIR") or os.path.join(GAO_DIR, "_道德经")  # 道德经网站素材（内容线程交，结构同论语）
DDJ_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddj.json")  # {"live": false, "src": 底本名, "img": 原页图根地址}
def load_ddj():
    """主人 11-08 定：网站这条线开始做道德经，不等视频。ddj.json live 为 true 且有原文才出页；原文到前一页不出。"""
    cfg = json.load(open(DDJ_CFG, encoding="utf-8")) if os.path.exists(DDJ_CFG) else {}
    if not (cfg.get("live") or os.environ.get("YK_DDJ_LIVE")): return None
    qf = sorted(glob.glob(os.path.join(DDJ_DIR, "_原文", "道德经原文-v*.json")))
    if not qf: return None
    qw = {k: v for k, v in json.load(open(qf[-1], encoding="utf-8")).items() if re.fullmatch(r"\d+", k) and 1 <= int(k) <= 81 and (v or {}).get("text")}
    if not qw: return None
    bh, bh_ok = {}, set()
    for f in sorted(glob.glob(os.path.join(DDJ_DIR, "_白话", "*.md")), key=lambda f: ("核定" in f, f)):  # 核定稿最后读，盖过初稿
        for l in open(f, encoding="utf-8"):
            m = re.match(r"^- 第?(\d+)章?[：:]\s*(.+)$", l.strip())  # 白话稿写“- 第1章：……”
            if m:
                bh[m.group(1)] = m.group(2).strip()
                if "核定" in f: bh_ok.add(m.group(1))
    rd = lambda sub: {os.path.basename(f)[:-5]: json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(DDJ_DIR, sub, "*.json")) if re.fullmatch(r"\d+", os.path.basename(f)[:-5])}
    hj = {}
    for f in sorted(glob.glob(os.path.join(DDJ_DIR, "_互见", "*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            if r.get("章号") and r.get("内容"):
                hj.setdefault(r["章号"].strip(), {}).setdefault((r.get("句") or "1").strip().lstrip("s"), []).append([r.get("类别", "").strip(), r["内容"].strip(), (r.get("出处") or "").strip(), (r.get("链接") or "").strip()])
    pm = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddj_pages.json")  # 原页图尺寸 {"p001": [w, h]}，出图时写
    return {"qw": qw, "bh": bh, "bh_ok": bh_ok, "zj": rd("_逐句"), "an": rd("_未讲"), "hj": hj, "src": cfg.get("src", ""), "img": cfg.get("img", ""), "zhu": cfg.get("zhu") or "注文",
            "pages": json.load(open(pm, encoding="utf-8")) if os.path.exists(pm) else {},
            "jl": json.load(open(jl, encoding="utf-8")) if os.path.exists(jl := os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddj_julie.json")) else {}}  # 逐句原页框（11-13 量列对字）

DDJ_FL = ("en", "ja")  # 道德经外文页（11-13 主人：英日版 81 章新译也做；译文初稿 tools/i18n/ddj-<语种>.json）
DDJ_TR = {x: json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", f"ddj-{x}.json"), encoding="utf-8")) for x in DDJ_FL if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", f"ddj-{x}.json"))}
DDJ_UI = {
 "en": {"book": "Daodejing", "dao": "Dao Jing", "de": "De Jing", "chn": "Daodejing, chapter {c}", "grp": "{pt} (chapters {a}–{b})", "prog": "{pt} · chapter {c} of 81",
        "lead": "Laozi’s Daodejing (Tao Te Ching) in 81 chapters: the original text of the Siku Quanshu edition with Wang Bi’s commentary, a scan of every page, and a draft English translation that follows Wang Bi’s reading.",
        "tr_h": "Translation", "tr_note": "Draft translation following Wang Bi’s commentary; it will be revised when the chapter is taught.",
        "cap": "Original text from the Siku Quanshu edition of the Laozi Daodejing with Wang Bi’s commentary, page {p} of the base edition.",
        "bh_note": "Draft plain-Chinese rendering following Wang Bi; it will be checked when the chapter is taught.",
        "bt": "Daodejing (Tao Te Ching): original text, page scans and translation | 81 chapters | 一孔录 Yikonglu",
        "bd": "Laozi’s Daodejing chapter by chapter: the Wang Bi base text, a scan of each page, and an English translation.",
        "md": "Daodejing chapter {c}: the original Chinese, the base-edition page and an English translation. {tr}", "done": "{n} of 81 chapters online", "bili": "Bilibili"},
 "ja": {"book": "道徳経", "dao": "道経", "de": "徳経", "chn": "『道徳経』第{c}章", "grp": "{pt}（第 {a}—{b} 章）", "prog": "{pt}・第 {c}/81 章",
        "lead": "老子『道徳経』八十一章。四庫全書本（王弼注）の原文、全ページの原本画像、王弼注の読みに沿った日本語訳（初稿）を載せています。",
        "tr_h": "現代語訳", "tr_note": "訳は初稿です。王弼注の読みに沿って訳し、講読のときに見直します。",
        "cap": "原文は四庫全書本『老子道徳経』（王弼注）、底本第 {p} ページによる。",
        "bh_note": "現代中国語訳は王弼注に沿った初稿です。講読時に見直します。",
        "bt": "『道徳経』原文・原本・現代語訳｜八十一章｜一孔録",
        "bd": "老子『道徳経』を一章ずつ。王弼注本の原文、各ページの原本画像、日本語訳。",
        "md": "『道徳経』第{c}章の原文、原本画像と日本語訳。{tr}", "done": "全 81 章中 {n} 章を掲載", "bili": "ビリビリ"}}
DDJ_CODES = ["zh-Hans", "zh-Hant"] + [x for x in DDJ_FL if x in DDJ_TR]
def ddj_tr_title(code, t):  # 外文章题：译文第一句，截短
    if not t: return ""
    if code == "ja":
        x = re.split(r"(?<=[。])", t)[0].rstrip("。")
        if len(x) > 22: x = re.split(r"[、]", x)[0]
        return x[:22] + ("…" if len(x) > 22 else "")
    x = re.split(r"(?<=[.;?!:])\s", t)[0].rstrip(".;:,")
    if len(x) > 60: x = x[:60].rsplit(" ", 1)[0].rstrip(",;") + "…"
    return x
def ddj_title(qw):  # 章题：取原文开头一句，撞名的往后接
    out = {c: wj_title(v["text"]) for c, v in qw.items()}
    for n in range(2, 6):
        seen = {}
        for c, t in out.items(): seen.setdefault(t, []).append(c)
        dup = [c for v in seen.values() if len(v) > 1 for c in v]
        if not dup: break
        for c in dup: out[c] = wj_title(qw[c]["text"], n)
    return out

def ddj_eps():
    """道德经各集视频（11-14：每发一集，章页和书内路线页自动带上视频）。发布线程照论语的做法，在 数据/网站素材/_时间/章节起点.json 记一条：
    键“道德经-NN-第X章”（或带 "chapters": ["12", "13"]），值 youtube / bvid / public_at / starts（{"12": 秒}）。没有这一条的章照旧显示“视频在做”。"""
    f = os.path.join(GAO_DIR, "_时间", "章节起点.json"); out = {}
    if not os.path.exists(f): return out
    for k, e in json.load(open(f, encoding="utf-8")).items():
        if not (k.startswith("道德经-") and isinstance(e, dict) and e.get("youtube")): continue
        chs = [str(x) for x in e.get("chapters") or []]
        if not chs:
            m = re.search(r"第([〇零一二三四五六七八九十百]+|\d+)章", k)
            if m:
                t = m.group(1); n = int(t) if t.isdigit() else None
                if n is None:
                    D_ = {c: i for i, c in enumerate("零一二三四五六七八九")}; D_["〇"] = 0
                    t2 = t.replace("百", "")
                    if "十" in t2:
                        a, _, b = t2.partition("十"); n = (D_.get(a, 1) if a else 1) * 10 + (D_.get(b, 0) if b else 0)
                    else: n = D_.get(t2, 0)
                chs = [str(n)]
        for c in chs: out.setdefault(c, dict(e, name=k.split("-", 2)[-1]))
    return out
DDJ_EPS = ddj_eps()
GXD = GX.load()
def ddj_vid_html(L, c, F):
    """道德经章页视频块：有发布记录就嵌 YouTube（简体页另给哔哩哔哩链接），定时公开的到点由页内脚本显示。"""
    ep = DDJ_EPS.get(str(c))
    if not ep: return ""
    yt = ep["youtube"]; st = (ep.get("starts") or {}).get(str(c)); pub = ep.get("public_at", "")
    future = bool(pub) and datetime.datetime.fromisoformat(pub) > datetime.datetime.now(datetime.timezone.utc)
    src = f'https://www.youtube-nocookie.com/embed/{yt}{f"?start={st}" if st else ""}'
    bl = f'<a href="https://www.bilibili.com/video/{ep["bvid"]}{f"?t={st}" if st else ""}" target="_blank" rel="noopener">{"哔哩哔哩" if L.code.startswith("zh") else "Bilibili"}</a>' if ep.get("bvid") else ""
    return (f'<section class="video"{f' hidden data-pub="{pub}"' if future else ""}><h2><i>{"▶" if F else "看"}</i>{L.t("video")}</h2>'
            f'<div class="vid"><iframe loading="lazy" src="{src}" title="{esc(ep.get("name", ""))}" allowfullscreen></iframe></div>'
            f'<p class="vlinks"><a href="https://www.youtube.com/watch?v={yt}{f"&amp;t={st}s" if st else ""}" target="_blank" rel="noopener">YouTube</a>{bl}</p></section>'
            + ('<script>(function(){var s=document.querySelector("section.video[data-pub]");if(s&&Date.now()>=Date.parse(s.dataset.pub)){s.hidden=false;var o=document.querySelector("section.video.soon");if(o)o.remove()}})()</script>' if future else ""))
def ddj_has_vid(c):
    ep = DDJ_EPS.get(str(c))
    return bool(ep) and (not ep.get("public_at") or datetime.datetime.fromisoformat(ep["public_at"]) <= datetime.datetime.now(datetime.timezone.utc))
DDJ_RT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddj_routes.json")  # 道德经书内路线（11-14 主人定）：专题页一条路线一页，章页标本章在哪几条路线上
DDJ_RT = json.load(open(DDJ_RT_FILE, encoding="utf-8"))["routes"] if os.path.exists(DDJ_RT_FILE) else []
DDJ_RT_UI = {"zh": {"h": "本章在这几条路线上", "sec": "《道德经》书内路线", "p": "按一个问题读《道德经》：每条路线串起几章，跟着读完一条，这个问题就有了老子自己的回答。视频一集一章，发出后加进对应路线。", "n": "{n} 章", "stop": "第 {k} / {n} 站", "lead": "《道德经》书内路线 · {n} 章", "all": "《道德经》全部八十一章", "rd": "已读 {x} / {n} 章", "zt": "专题"},
             "en": {"h": "Reading routes through this chapter", "sec": "Reading routes through the Daodejing", "p": "Read the Daodejing by one question at a time: each route strings together a few chapters, so Laozi answers the question in his own words.", "n": "{n} chapters", "stop": "stop {k} of {n}", "lead": "A route through the Daodejing · {n} chapters", "all": "All 81 chapters of the Daodejing", "rd": "Read {x} of {n}", "zt": "Topics"},
             "ja": {"h": "この章が入っている読みルート", "sec": "『道徳経』の読みルート", "p": "一つの問いで『道徳経』を読む：各ルートは数章をつなぎ、読み通すと老子自身の答えが見えてきます。", "n": "{n} 章", "stop": "{n} 章中 第 {k} 章目", "lead": "『道徳経』読みルート · {n} 章", "all": "『道徳経』全八十一章", "rd": "{n} 章中 {x} 章読了", "zt": "テーマ"}}
DDJ_RT_CARDS = {}  # 语种 → 专题总页上的路线卡（build_ddj 先算好，专题页取用）
DDJ_RT_JS = """<script>(function(){var s=[];try{s=((JSON.parse(localStorage.getItem("yk_xd")||"{}").b||{}).daodejing||{}).seen||[]}catch(e){}
document.querySelectorAll("[data-ddj]").forEach(function(el){var C=JSON.parse(el.getAttribute("data-ddj")),x=C.filter(function(c){return s.indexOf(c)>=0}).length,t=el.querySelector(".rdn");
if(x&&t)t.textContent=t.getAttribute("data-t").replace("{x}",x).replace("{n}",C.length);var b=el.querySelector(".bar i");if(b)b.style.width=(x/C.length*100).toFixed(1)+"%"});
document.querySelectorAll(".rtl li[data-c]").forEach(function(li){if(s.indexOf(li.getAttribute("data-c"))>=0)li.classList.add("done")})})();</script>"""

def build_ddj(L, D, write, P, S_IDX=None):
    """道德经：书页（道经、德经两组目录）＋各章页（只出简繁）。结构照论语未讲章：原文（可点句）、原页、一孔按、白话、视频位。返回 URL 列表。"""
    G = D.get("ddj")
    F = not L.code.startswith("zh"); TRD = DDJ_TR.get(L.code) or {}; DU = DDJ_UI.get(L.code, {})
    if not G or (F and not (L.code in DDJ_FL and TRD)): return []
    qw, urls = G["qw"], []
    cs = sorted(qw, key=int); tt = ddj_title(qw)
    if F: tt = {c: ddj_tr_title(L.code, TRD.get(c, "")) or tt[c] for c in cs}
    # 底本录文是四库本繁体：简体页转简体；繁体页用 \ue010…\ue011 包住，to_hant 整页转繁时不碰，原样还底本字形（11-13 主人要道德经先上网站）
    hant = L.code == "zh-Hant"; _t2s = __import__("opencc").OpenCC("t2s").convert
    Y = (lambda s_: s_) if F else (lambda s_: f"\ue010{s_}\ue011" if s_ else s_) if hant else _t2s
    part = (lambda c: DU["dao"] if int(c) <= 37 else DU["de"]) if F else (lambda c: "道经" if int(c) <= 37 else "德经")
    TL = (lambda s_: esc(s_)) if F else (lambda s_: esc(Y(s_)))  # 章题：外文页是译文，不转
    rel_of = lambda c: f"daodejing/{c}.html"
    def li(c):
        t = qw[c]["text"]
        if F:
            r = TRD.get(c, "")
            return f'<li class="{"" if ddj_has_vid(c) else "wj"}" data-c="{c}"><a href="{P}{rel_of(c)}"><em>{c}</em><b>{TL(tt[c])}</b><span><i class="wjtag">{"▶" if ddj_has_vid(c) else L.t("toc_wj")}</i><span>{esc(r[:90] + ("…" if len(r) > 90 else ""))}</span></span></a></li>'
        return f'<li class="{"" if ddj_has_vid(c) else "wj"}" data-c="{c}"><a href="{P}{rel_of(c)}"><em>{c}</em><b>{esc(Y(tt[c]))}</b><span><i class="wjtag">{"▶ 视频" if ddj_has_vid(c) else L.t("toc_wj")}</i><span lang="zh-Hans">{esc(Y(t[:40]) + ("……" if len(t) > 40 else ""))}</span></span></a></li>'
    def side(c0):
        pt = part(c0)
        return "".join(f'<li class="{"cur" if c == c0 else ""} wj" data-c="{c}"><a href="{P}{rel_of(c)}"><em>{c}</em>{TL(tt[c])}</a></li>' for c in cs if part(c) == pt)
    # 书页
    groups = "".join(f'<h2 class="ph">{DU["grp"].format(pt=pt, a=a, b=b) if F else f"{pt}（第 {a}—{b} 章）"}</h2><ol class="toc">{"".join(li(c) for c in cs if a <= int(c) <= b)}</ol>' for pt, a, b in ((part("1"), 1, 37), (part("38"), 38, 81)) if any(a <= int(c) <= b for c in cs))
    body = f"""<div class="chhead bk"><div class="wrap">{mcv(P, "", True, "daodejing", "道德经")}<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a></p>
<h1><span class="no">{DU["done"].format(n=len(cs)) if F else f"《道德经》 · 已上 {len(cs)} / 81 章"}</span>{DU["book"] if F else "道德经"}</h1></div></div>
<main class="wrap narrow"><p class="lead">{DU["lead"] if F else L.t("ddj_lead")}</p>{groups}</main>"""
    ld = {"@context": "https://schema.org", "@type": "Book", "name": DU["book"] if F else "道德经", "author": {"@type": "Person", "name": "Laozi" if L.code == "en" else "老子"}, "url": f"{DOMAIN}/{L.prefix}daodejing/", "inLanguage": L.hreflang}
    write("daodejing/index.html", page(L, DU["bt"] if F else "《道德经》原文、白话与注｜八十一章｜一孔录", DU["bd"] if F else f"《道德经》八十一章逐章原文与白话直译，附底本原页。", "daodejing/", body, ld, "pg-book", codes=DDJ_CODES)); urls.append(f"{DOMAIN}/{L.prefix}daodejing/")
    lab = L.t("wj_pane")
    RU = DDJ_RT_UI["zh" if not F else L.code if L.code in DDJ_RT_UI else "en"]
    RN = lambda r: (r.get(L.code) or r["en"]) if F else r["zh"]
    rt_of = {}
    for r in DDJ_RT:
        for k_, x in enumerate(r["cs"], 1): rt_of.setdefault(str(x), []).append((r, k_))
    def rt_html(c):
        if c not in rt_of: return ""
        return (f'<section class="sec rtsec"><h2><i>{"路" if not F else "⇢"}</i>{esc(RU["h"])}</h2><ul class="rtin">' + "".join(
            f'<li><a href="{P}zhuanti/ddj-{r["slug"]}.html"><b>{esc(RN(r))}</b><small>{RU["stop"].format(k=k_, n=len(r["cs"]))}</small></a></li>' for r, k_ in rt_of[c]) + "</ul></section>")
    DDJ_SH = {"bk": "道德经", "tot": 81, "src": "王弼注《老子道德经》四库全书本", "src2": "王弼注《老子道德经》（四库全书本）", "pf": "ddj."}  # 分享图按书：书名、章数、底本、读过记录分书
    for k, c in enumerate(cs):
        q = qw[c]; text = q["text"]; url = f"{DOMAIN}/{L.prefix}{rel_of(c)}"; pt = part(c)
        cite_src = f"Daodejing {c}, 一孔录 Yikonglu" if L.code == "en" else f"『道徳経』第{c}章、一孔録" if F else f"道德经 {c} · 一孔录"
        tr = TRD.get(c, "")
        sents = split_ju(text); hjd = {j_: [[h[0], Y(h[1]), h[2] if hant else _t2s(h[2]), h[3]] for h in v_] for j_, v_ in G["hj"].get(c, {}).items()}
        pgs = [int(x) for x in (q.get("pages") or ([q["pdf_page"]] if q.get("pdf_page") else []))]
        cap = (esc(DU["cap"].format(p=", ".join(str(x) for x in pgs) if L.code == "en" else "、".join(str(x) for x in pgs))) if F
               else f'原文据{esc(G["src"])}' + (f'，底本第 {"、".join(str(x) for x in pgs)} 页' if pgs else "") + "。" if G["src"] else L.t("source_line"))
        jl = G["jl"].get(c) if len(G["jl"].get(c) or []) == len(sents) else []  # 点句亮列：每句在原页上的框
        hlr = lambda pp: "".join(f'<rect class="hl" data-s="{i}" x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6"/>' for i, bx in enumerate(jl, 1) for (p_, x0, y0, x1, y1) in bx if p_ == pp)
        pane = "".join(f'<a class="yyp" href="{G["img"]}p{x:03d}.jpg" target="_blank" data-p="p{x:03d}"><svg viewBox="0 0 {G["pages"][f"p{x:03d}"][0]} {G["pages"][f"p{x:03d}"][1]}" role="img" aria-label="{lab} {x}"><image href="{G["img"]}p{x:03d}.jpg" width="{G["pages"][f"p{x:03d}"][0]}" height="{G["pages"][f"p{x:03d}"][1]}"/>{hlr(f"p{x:03d}")}</svg><span>{lab} {x}</span></a>'
                       for x in pgs if G["img"] and f"p{x:03d}" in G["pages"])
        zs = [] if F else (G["zj"].get(c) or {}).get("句") or []
        if zs and len(zs) != len(sents): print(f"  道德经逐句条数不符 {c}：网站 {len(sents)} 句，_逐句 {len(zs)} 句"); zs = []
        bq = f'<blockquote lang="{"zh-Hant" if F else "zh-Hans"}" data-src="{esc(cite_src)}" data-url="{url}" data-short="{"" if F else f"yikonglu.com/daodejing/{c}"}" data-sep="{", " if F else "，"}" data-reads="[]" data-rl="" data-hj="{esc(json.dumps(hjd, ensure_ascii=False))}">'
        rows = []
        dz = bool(zs or pane) and not F
        if dz:
            for j, x in enumerate(sents, 1):
                d = {k_: zs[j-1].get(k_) for k_ in ("bh", "zhu", "jj", "yk") if zs[j-1].get(k_)} if zs else {}
                d["hj"] = [[f"{h[0]}：{h[1]}", h[2], ""] for h in hjd.get(str(j), [])]
                rows.append(d)
        ju_html = "".join(f'<span class="ju" id="s{j}" data-n="{j}" tabindex="0">{esc(Y(x))}</span>' + (f'<span class="yi" hidden>{esc(rows[j-1]["bh"])}</span>' if rows and rows[j-1].get("bh") else "") for j, x in enumerate(sents, 1))
        if F:  # 英日：原页同屏点句亮列，不挂小卡（同论语外文页）；译文在原文下
            rend = f'<p class="rend">{esc(tr)}</p><figcaption>{esc(DU["tr_note"])}</figcaption>' if tr else ""
            fig = (f'<figure class="yuanwen dz nocard{"" if pane else " nopane"}"><div class="dzgrid"><div>{bq}{ju_html}</blockquote>{langdu_html(L.code, c, "daodejing")}<figcaption>{cap}</figcaption>{rend}</div>'
                   + (f'<div class="yypane">{pane}</div>' if pane else "") + '</div></figure>')
        elif dz:
            yib = '<button type="button" class="yibtn" aria-pressed="false" title="每句下面显示白话">译</button>' if any(r.get("bh") for r in rows) else ""
            fig = (f'<figure class="yuanwen dz{"" if pane else " nopane"}"><div class="dztools"><span class="prog">{pt} · 第 {c}/81 章</span>{yib}{langdu_btn(L.code, c, "daodejing")}</div>'
                   f'<div class="dzgrid"><div>{bq}{ju_html}</blockquote><figcaption>{cap}</figcaption></div>' + (f'<div class="yypane">{pane}</div>' if pane else "") + '</div>'
                   f'<script type="application/json" class="zjdata">{json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")}</script></figure>')
        else:
            fig = f'<figure class="yuanwen">{bq}{ju_html}</blockquote><figcaption>{cap}</figcaption></figure>'
        an = G["an"].get(c) or {}; gist = ""; faq = []
        if an.get("片里落点"):
            a_lab, a_txt = ykan("zh", an["片里落点"], an.get("常见读法"), an.get("字眼"), basis=f'{G["zhu"]}原话：')
            gist = (f'<section class="gist ykan"><h2>{L.t("ch_gist")}</h2><p lang="zh-Hans"><b class="anlab">{esc(a_lab)}</b>{quotes(a_txt)}</p><p class="note">{L.t("wj_an_note")}</p></section>' if F
                    else f'<section class="gist ykan"><h2>{L.t("ch_gist")}</h2><p><b class="anlab">{esc(a_lab)}</b>{quotes(a_txt)}</p></section>')
            if F: an = dict(an, 片里落点="")  # 外文页不出 FAQ
            faq = [] if F else [{"@type": "Question", "name": f"《道德经》第 {c} 章讲什么？", "acceptedAnswer": {"@type": "Answer", "text": an["片里落点"]}},
                   {"@type": "Question", "name": "一孔录怎么读这一章？", "acceptedAnswer": {"@type": "Answer", "text": a_lab + a_txt}}]
        bh = G["bh"].get(c)
        bh_html = ((f'<section class="sec sec-白"><h2><i>白</i>{L.t("baihua")}</h2><p lang="zh-Hans">{esc(bh)}</p>' + ("" if c in G["bh_ok"] else f'<p class="note">{esc(DU["bh_note"])}</p>') + "</section>") if F else
                   (f'<section class="sec sec-白"><h2><i>白</i>{L.t("baihua")}：“{esc(Y(seo_q(text)))}”是什么意思</h2><p lang="zh-Hans">{esc(bh)}</p>'
                   + ("" if c in G["bh_ok"] else '<p class="note">白话为初稿，按底本直译；开讲时再核。</p>') + "</section>")) if bh else ""
        vid = ("" if ddj_has_vid(c) else f'<section class="video soon"><h2><i>看</i>{L.t("video")}</h2><p class="vlinks">{L.t("wj_vid")}'
               f'<a href="https://www.youtube.com/@yikonglu" target="_blank" rel="noopener">YouTube</a><a href="https://space.bilibili.com/18385461" target="_blank" rel="noopener">{DU["bili"] if F else "哔哩哔哩"}</a></p></section>') + ddj_vid_html(L, c, F)
        prev_c = cs[k-1] if k > 0 else None; next_c = cs[k+1] if k+1 < len(cs) else None
        pn = "".join(f'<a class="pncard {cl}" href="{P}{rel_of(cc)}"><small>{L.t(lb)}</small><b>{cc}　{TL(tt[cc])}</b></a>' if cc else "<span></span>" for cc, lb, cl in ((prev_c, "prev", "prev"), (next_c, "next", "next")))
        LIVE_A.setdefault(L.code, {})["ddj." + c] = [f'{DU["book"] if F else "道德经"} · {tt[c] if F else Y(tt[c])}', rel_of(c)]
        TRI_TXT["ddj." + c] = {"h": f"《道德经》第 {c} 章 · Daodejing {c} · 道徳経 第{c}章", "y": text if (hant or F) else _t2s(text), "en": (DDJ_TR.get("en") or {}).get(c, ""), "ja": (DDJ_TR.get("ja") or {}).get(c, "")}  # 分享图（外王卡）；英日译文上了再填
        body = f"""<div class="chhead bk"><div class="wrap">{mcv(P, "", False, "daodejing", "道德经")}
<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}daodejing/">{DU["book"] if F else "道德经"}</a> › {pt}</p>
<h1><span class="no">{DU["prog"].format(pt=pt, c=c) if F else f"道德经 {c} · {pt}"}{"" if ddj_has_vid(c) else f' · <em class="wjtag">{L.t("wj_tag")}</em>'}</span>{TL(tt[c])}</h1>
</div></div>
<main class="wrap chapter">
<article>
{"" if ddj_has_vid(c) else f'<p class="wjlead">{L.t("wj_lead")}</p>'}
{fig}
{gist}
{"" if F else lyhj_html([r for r in DDJ_LYHJ if str(r["ch"]) == str(c)], P, "ddj")}
{bh_html}
{rt_html(c)}
{vid}
<div class="chacts">{share_html(L, "ddj." + c, url, DU["chn"].format(c=c) if F else f"道德经 {c}", tt[c] if F else Y(tt[c]), Y(text), "" if F else an.get("片里落点") or "", tr if F else "", DDJ_SH)}</div>
<section class="citeit"><p class="mailp">{L.t("report")} {MAIL}</p></section>
<nav class="pn">{pn}</nav>
</article>
<aside><h3>{pt}</h3><ol>{side(c)}</ol></aside>
</main><i id="rc" data-c="ddj.{c}" hidden></i><script type="application/json" class="xddata">{json.dumps({"c": c, "ti": tt[c] if F else Y(tt[c])}, ensure_ascii=False)}</script>"""
        hj_static = "<ul></ul>"
        ld = {"@type": "Article", "headline": f'{DU["chn"].format(c=c)} {tt[c]}' if F else f"道德经 {c} {Y(tt[c])}", "inLanguage": L.hreflang, "url": url,
              "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN}, "about": {"@type": "Book", "name": "道德经"}}
        ld = {"@context": "https://schema.org", "@graph": [ld] + ([{"@type": "FAQPage", "mainEntity": faq}] if faq else [])}
        if F: js = SHARE_JS + JU_JS.replace("@HJH@", L.t("hj_h")).replace("@HJ@", "<ul></ul>").replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied")) + ZJ.HL_JS
        else: js = SHARE_JS + (ZJ.ZJ_JS.replace("@IMG@", "做成分享图").replace("@TABS@", json.dumps([["bh", "白话"], ["zhu", G["zhu"]], ["jj", "集解"], ["yk", "一孔读法"], ["hj", "本句互见"]], ensure_ascii=False)).replace("@NONE@", "这一句的逐句白话和注还在整理，整章白话见下文。")
              if dz else JU_JS.replace("@HJH@", L.t("hj_h")).replace("@HJ@", hj_static)).replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied"))
        if S_IDX is not None: S_IDX.append({"c": f'{DU["book"] if F else "道德经"} {c}', "t": tt[c] if F else Y(tt[c]), "u": P + rel_of(c), "y": Y(text), "x": tr if F else (bh or "") + " " + (an.get("片里落点") or "")})
        if F: ttl, desc = f'{DU["chn"].format(c=c)} {tt[c]} | 一孔录 Yikonglu', DU["md"].format(c=c, tr=tr[:110] + ("…" if len(tr) > 110 else ""))
        else: ttl, desc = f"{Y(seo_head(text))}｜原文与白话｜道德经 {c}｜一孔录", f"{Y(text[:70])}……《道德经》第 {c} 章原文与白话直译。"
        write(rel_of(c), page(L, ttl, desc, rel_of(c), body + js, ld, "pg-chapter pg-wj", codes=DDJ_CODES)); urls.append(url)
    cards = ""
    for r in DDJ_RT:
        rc = [str(x) for x in r["cs"] if str(x) in qw]
        if not rc: continue
        nm = esc(RN(r))
        rd = f'<p class="rdbox" data-ddj="{esc(json.dumps(rc))}"><span class="bar"><i></i></span><span class="rdn" data-t="{esc(RU["rd"])}"></span></p>'
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}zhuanti/">{RU["zt"]}</a> › <a href="{P}zhuanti/#ddjrt">{esc(RU["sec"])}</a></p><h1><span class="no">{RU["lead"].format(n=len(rc))}</span>{nm}</h1></div></div>
<main class="wrap narrow">{rd}<ol class="ztl rtl">{"".join(li(c) for c in rc)}</ol><p class="note"><a href="{P}daodejing/">{esc(RU["all"])}</a></p>
<p class="chmore">''' + "".join(f'<a href="{P}zhuanti/ddj-{q["slug"]}.html">{esc(RN(q))}</a>' for q in DDJ_RT if q is not r) + f"</p></main>{DDJ_RT_JS}"
        ttl = f"{RN(r)} | {DU['book']} | 一孔录 Yikonglu" if F else f"{RN(r)}｜《道德经》书内路线 {len(rc)} 章｜一孔录"
        desc = (RU["lead"].format(n=len(rc)) + ": " + ", ".join(rc)) if F else f"《道德经》书内路线“{RN(r)}”：按王弼本第 {'、'.join(rc)} 章读，每章原文、白话与底本原页。"
        write(f"zhuanti/ddj-{r['slug']}.html", page(L, ttl, desc, f"zhuanti/ddj-{r['slug']}.html", body, codes=DDJ_CODES)); urls.append(f"{DOMAIN}/{L.prefix}zhuanti/ddj-{r['slug']}.html")
        cards += f'<a class="gsroute rtcard" data-ddj="{esc(json.dumps(rc))}" href="{P}zhuanti/ddj-{r["slug"]}.html"><div><b>{nm}<span>{RU["n"].format(n=len(rc))}</span></b><p><span class="bar"><i></i></span><span class="rdn" data-t="{esc(RU["rd"])}"></span></p></div></a>'
    if cards: DDJ_RT_CARDS[L.code] = f'<h2 class="ph" id="ddjrt">{esc(RU["sec"])}</h2><p class="note">{esc(RU["p"])}</p><div class="gsroutes rtcards">{cards}</div>{DDJ_RT_JS}'
    return urls

SZJ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "szj.json")  # 三字经（11-13 主人“先上”：按一孔录讲义原文，三十九讲；白话初稿；王相训诂原页待补）
SZJ = json.load(open(SZJ_FILE, encoding="utf-8")) if os.path.exists(SZJ_FILE) else []
SZJ_JL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "szj_julie.json")  # 王相《三字经训诂》1831 年和刻本原页（图片仓库 sanzijing/pNNN.jpg，拆单页、校平）与逐组框 {pages, jl:{讲:{组:[[页,x0,y0,x1,y1],…]}}}
SZJ_JL = json.load(open(SZJ_JL_FILE, encoding="utf-8")) if os.path.exists(SZJ_JL_FILE) else {"pages": {}, "jl": {}}
SZJ_IMG = "https://img.yikonglu.com/sanzijing/"
SZJ_WX_NO = {22, 23, 24, 26, 69, 70, 71, 72, 73, 74, 75}  # 王相本没有的组（讲义据后出通行本补）
SZJ_YW = {  # 讲义与王相本对照（11-13 逐句核对）：组号 → 说明
    11: "王相本作“首孝弟”，“弟”通“悌”。",
    22: "王相本无此组。五色、五味、五臭三组是后出通行本补的，讲义据通行本。",
    23: "王相本无此组（同上，后出通行本补）。",
    24: "王相本无此组（同上，后出通行本补）。",
    26: "王相本无此组。“四声”一组是后出通行本补的，讲义据通行本。",
    28: "王相本作“至元曾”，清人避康熙帝玄烨的名讳，改“玄”为“元”。",
    32: "王相本作“详训诂”，“故”“诂”相通。",
    69: "王相本无此组。王相本讲历代到宋为止（“炎宋兴，受周禅，十八传，南北混”），下接“十七史”；辽、金、元、明、清到民国这七组是后人续写，讲义据通行本。",
    70: "王相本无此组（后人续写，见第 69 组）。", 71: "王相本无此组（后人续写，见第 69 组）。", 72: "王相本无此组（后人续写，见第 69 组）。",
    73: "王相本无此组（后人续写，见第 69 组）。", 74: "王相本无此组（后人续写，见第 69 组）。", 75: "王相本无此组（后人续写，见第 69 组）。",
    76: "王相本作“十七史”。后来正史增多，通行本改作“廿二史”，讲义从通行本。",
    89: "王相本作“能赋碁”，“碁”同“棋”。",
    90: "王相本“颖”作“頴”，同字异写。",
    100: "王相本“籝”作“籯”，同字异写。",
}
LANGDU_SZJ = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "langdu-szj.json"), encoding="utf-8"))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "langdu-szj.json")) else set()
CNUM = lambda n: "一二三四五六七八九十"[n - 1] if n <= 10 else ("十" + "一二三四五六七八九"[n - 11] if n < 20 else ("一二三四五六七八九"[n // 10 - 1] + "十" + ("一二三四五六七八九"[n % 10 - 1] if n % 10 else "")))
LIVE_A = {}  # 各语种“今天有人读了”里论语之外的书：{语种: {"ddj.6"/"szj.15": [标题, 相对路径]}}（11-13 主人问别的书有没有人读）
SZJ_FL = ("en", "ja")  # 三字经外文页（11-13 主人：“三字经的多语种搞定一下”；先英日，译文初稿 tools/i18n/szj-<语种>.json：g 逐组、name 讲名、jt 卷名、sum 讲义摘要、yw 异文）
SZJ_TR = {x: json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", f"szj-{x}.json"), encoding="utf-8")) for x in SZJ_FL if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", f"szj-{x}.json"))}
SZJ_CODES = ["zh-Hans", "zh-Hant"] + [x for x in SZJ_FL if x in SZJ_TR]
SZJ_JUAN = {"卷一": 1, "卷二": 2, "卷三": 3, "卷四": 4, "卷五": 5, "卷六": 6}
SZJ_UI = {
 "en": {"book": "Three Character Classic", "juan": "Part {j}", "grp": "Part {j} · {jt} (lectures {a}–{b})", "lec": "Lecture {n}", "prog": "{jt} · lecture {n} · {k} groups",
        "lead": "The Three Character Classic (Sanzijing), 1,200 characters in 101 groups, read in 39 weekly lectures following Yikonglu's Father's Lecture Notes. Each lecture gives the Chinese text, a scan of the base edition, Wang Xiang's Sanzijing xungu (1831 Japanese reprint), with every group framed on the page, a recording of the text and a draft English translation.",
        "cap": "Text from Yikonglu's Father's Lecture Notes, checked line by line against the base edition, Wang Xiang's Sanzijing xungu (1831 Japanese reprint). The page scans are from that edition; click a group to frame it on the page.",
        "cap_nopane": "Text from Yikonglu's Father's Lecture Notes. None of the groups in this lecture are in the base edition, Wang Xiang's Sanzijing xungu; they come from later popular editions, so there is no page scan. See 'Compared with Wang Xiang\'s edition' below.",
        "cap_no": " Groups marked * are not in Wang Xiang's edition; the lecture notes take them from later popular editions.", "cap_yw": " Differences are listed under 'Compared with Wang Xiang\'s edition'.",
        "tr_h": "Translation", "tr_note": "Draft translation; it will be revised when the lecture is filmed.", "yw_h": "Compared with Wang Xiang's edition", "grp_n": "Group {g}",
        "jy_h": "From the Father's Lecture Notes", "jy_note": "Translated from Yikonglu's Father's Lecture Notes for the Three Character Classic, written for a parent teaching a child.",
        "vlead": "The video for this lecture is still in production. For now this page gives the text, the base-edition pages, a recording and a translation.",
        "none": "This lecture adds no new text.", "bt": "Three Character Classic (Sanzijing): text, page scans and translation | 39 lectures | 一孔录 Yikonglu",
        "bd": "The Three Character Classic in 39 lectures: the Chinese text, scans of Wang Xiang's base edition with each group framed, recordings and an English translation.",
        "md": "Three Character Classic, lecture {n}: the Chinese text, the base-edition pages and an English translation. {tr}", "bili": "Bilibili", "pane": "Page"},
 "ja": {"book": "三字経", "juan": "巻{j}", "grp": "巻{j}・{jt}（第 {a}—{b} 講）", "lec": "第 {n} 講", "prog": "{jt}・第 {n} 講・{k} 組",
        "lead": "『三字経』千二百字・百一組を、一孔録『三字経・父の講義』に沿って三十九講に分け、週に一講ずつ読みます。各講に原文、底本の王相『三字経訓詁』（1831 年和刻本）の原本画像（組ごとに枠表示）、朗読、日本語訳（初稿）を載せています。",
        "cap": "原文は一孔録『三字経・父の講義』本により、底本の王相『三字経訓詁』（1831 年和刻本）と一句ずつ照合済み。原本画像は同本。組をクリックすると原本の該当箇所に枠が出ます。",
        "cap_nopane": "原文は一孔録『三字経・父の講義』本による。この講の組はどれも底本の王相『三字経訓詁』になく、後世の通行本で補われたものなので、原本画像はありません。下の「王相本との対照」を参照。",
        "cap_no": "「補」印の組は王相本になく、講義は後世の通行本によって補っています。", "cap_yw": "異同は下の「王相本との対照」に。",
        "tr_h": "現代語訳", "tr_note": "訳は初稿です。講義動画を作るときに見直します。", "yw_h": "王相本との対照", "grp_n": "第 {g} 組",
        "jy_h": "『父の講義』より", "jy_note": "一孔録『三字経・父の講義』（親が子に教えるための講義ノート）から訳出。",
        "vlead": "この講の動画は制作中です。まず原文・原本画像・朗読・訳を載せています。",
        "none": "この講では新しい原文を読みません。", "bt": "『三字経』原文・原本・現代語訳｜三十九講｜一孔録",
        "bd": "『三字経』を三十九講で。原文、王相本の原本画像（組ごとに枠表示）、朗読、日本語訳。",
        "md": "『三字経』第{n}講の原文、原本画像と日本語訳。{tr}", "bili": "ビリビリ", "pane": "原本"}}
# 11-14 主人定“给《论语》特殊地位”（图样 1—4 做）：导航第一项“论语”、首页今日《论语》放大＋本周读了几天、首页主经一格、书架页主书一格；口号暂不进首页横幅
LY_UI = {
 "zh-Hans": {"nav": "论语", "h": "主经", "k": "一生一本《论语》：一天一章，一年一轮", "s": "二十篇 {n} 章原文全在站上 · 已讲 {d} 章 · 朱熹集注本原页可查", "go": "从学而篇读起", "toc": "全书目录", "kb": "语文课本里的《论语》", "db": "免费读本",
             "more": "书架上还有：", "soon": "{n} 部筹备中 ›", "open": "打开《论语》", "strip": "今日《论语》", "read": "读这一章 →", "close": "今天不再显示", "wk": "本周你读了 {n} 天", "wk0": "本周还没读", "cal": "按《论语》年历，一年一轮", "shelf": "书架 · 能读的书"},
 "zh-Hant": {"nav": "論語", "h": "主經", "k": "一生一本《論語》：一天一章，一年一輪", "s": "二十篇 {n} 章原文全在站上 · 已講 {d} 章 · 朱熹集注本原頁可查", "go": "從學而篇讀起", "toc": "全書目錄", "kb": "語文課本裡的《論語》", "db": "免費讀本",
             "more": "書架上還有：", "soon": "{n} 部籌備中 ›", "open": "打開《論語》", "strip": "今日《論語》", "read": "讀這一章 →", "close": "今天不再顯示", "wk": "本週你讀了 {n} 天", "wk0": "本週還沒讀", "cal": "按《論語》年曆，一年一輪", "shelf": "書架 · 能讀的書"},
 "en": {"nav": "Analects", "h": "The main book", "k": "One chapter a day, the whole book every year", "s": "All {n} chapters online · {d} taught on video · Zhu Xi's commentary with page scans", "go": "Start with Book 1", "toc": "Contents", "kb": "", "db": "",
        "more": "Also on the shelf: ", "soon": "{n} more in preparation ›", "open": "Open the Analects", "strip": "Today's Analects", "read": "Read this chapter →", "close": "Hide for today", "wk": "Days you read this week: {n}", "wk0": "Not read yet this week", "cal": "", "shelf": "On the shelf"},
 "ja": {"nav": "論語", "h": "主たる一冊", "k": "一日一章、一年で一巡り", "s": "全 {n} 章の原文を掲載 · 動画で解説 {d} 章 · 朱熹『論語集注』の原本画像つき", "go": "学而篇から読む", "toc": "目次", "kb": "", "db": "",
        "more": "書架にはほかに：", "soon": "ほか {n} 部を準備中 ›", "open": "『論語』を開く", "strip": "今日の『論語』", "read": "この章を読む →", "close": "今日は表示しない", "wk": "今週読んだ日：{n} 日", "wk0": "今週はまだ読んでいません", "cal": "", "shelf": "書架"},
}
def lyui(L): return dict(LY_UI["en"], **{k: v for k, v in ((FILL.get(L.code) or {}).get("ly") or {}).items() if LY_UI["en"].get(k) and k != "nav"}, nav=L.t("lunyu").replace("The ", "")) if L.code not in LY_UI else LY_UI[L.code]
SZJ_PROG = {"zh-Hans": "原文全 · 视频制作中", "zh-Hant": "原文全 · 視頻製作中", "en": "{n} lectures online", "ja": "全 {n} 講を掲載",
            "ko": "{n}강 모두 공개", "fr": "{n} leçons en ligne", "es": "{n} lecciones en línea", "de": "Alle {n} Lektionen online",
            "vi": "Đủ {n} bài", "id": "{n} pelajaran tersedia", "ru": "Все {n} уроков"}
WJ_PROG = {"en": "{n} / {total} chapters online", "ja": "{n} / {total} 章を掲載", "ko": "{n} / {total}장 공개", "fr": "{n} / {total} chapitres en ligne", "es": "{n} / {total} capítulos en línea",
           "de": "{n} / {total} Kapitel online", "vi": "{n} / {total} chương", "id": "{n} / {total} bab tersedia", "ru": "{n} / {total} глав"}  # 道德经等未讲书的进度（外文；中文仍用 bk_prog_wj）
def wjprog(L, n, total): return WJ_PROG[L.code].format(n=n, total=total) if L.code in WJ_PROG else L.t("bk_prog_wj", n=n, total=total)

SZJ_LYHJ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "szj_lyhj.json")  # 三字经各讲《论语》互见（11-14 主人“全上”；表见 评审/2026-11-14-论语互见/）
SZJ_LYHJ = json.load(open(SZJ_LYHJ_FILE, encoding="utf-8")) if os.path.exists(SZJ_LYHJ_FILE) else []
LYHJ_SRC = [("wx-", "王相"), ("yinshu", "《三字经音疏》"), ("beiyao", "《三字经备要》"), ("zengzhu", "《增注三字经》"), ("jizhu", "渥美《三字经集注》")]
DDJ_LYHJ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddj_lyhj.json")  # 道德经各章《论语》互见（11-14 主人“全上”，138 条；表见 评审/2026-11-14-论语互见/道德经-论语互见-v1.md）
DDJ_LYHJ = json.load(open(DDJ_LYHJ_FILE, encoding="utf-8")) if os.path.exists(DDJ_LYHJ_FILE) else []
def lyhj_html(rows, P, book="szj"):
    """其他书章页上的“《论语》互见”一栏（11-14 主人定：每本书都做一次）。rows：[{zu, szj, c, kind, q, src, note}]"""
    if not rows: return ""
    def who(r):
        if r.get("who"): return r["who"]
        if r["kind"] == "出处": return "原句出自这一章"
        if r["kind"] == "相通": return "一孔录对读"
        ns = []
        for k, v in LYHJ_SRC:
            if k in r["src"] and v not in ns: ns.append(v)
        return ("、".join(ns) + "注里引了这一章") if ns else "注家引了这一章"
    def link(c): return f"{P}lunyu/" if c == "book" else f"{P}lunyu/{PIAN[c.split('.')[0]][1]}/{c.split('.')[1]}.html"
    lis = "".join(f'<li><em>{esc(r["kind"])}</em><a href="{link(r["c"])}"><b>' + (f'《论语》全书' if r["c"] == "book" else f'论语 {r["c"]} {esc(r["q"])}') + f'</b></a>'
                  f'<p>{esc(r["note"])}<small>（{(esc(r["szj"][:6]) + "…… · ") if r.get("szj") else ""}{who(r)}）</small></p></li>' for r in rows)
    return f'<section class="lyhj" id="lyhj"><h2>《论语》互见</h2><ul>{lis}</ul><p class="note">{"出处＝《论语》里直接说到老子这句话" if book == "ddj" else "出处＝三字经原句出自这一章"}；注家引＝旧注本里引了这一章；相通＝意思相通，一孔录对读。点进去是《论语》这一章的原文、原页和朱熹注。</p></section>'

def build_szj(L, write, P, S_IDX=None):
    """三字经：书页（六卷三十九讲）＋各讲页。简繁（繁体页由整页转繁）＋英日（SZJ_TR，原文繁体、逐组译文、原页点组亮框）。每组十二字一“句”，点组看白话（中文小卡）或亮框（外文）。"""
    F = not L.code.startswith("zh"); TR = SZJ_TR.get(L.code) or {}; SU = SZJ_UI.get(L.code, {})
    if not SZJ or (F and not TR): return []
    T2S = __import__("opencc").OpenCC("s2t") if F else None
    Y = (lambda x: T2S.convert(x)) if F else (lambda x: x)
    urls = []; rel_of = lambda n: f"sanzijing/{n}.html"; JS = [j for j in SZJ]
    jt_of = lambda j: TR["jt"].get(j["jt"], j["jt"]) if F else j["jt"]
    name_of = lambda j: TR["name"].get(str(j["n"]), j["name"]) if F else j["name"]
    juan_of = lambda j: (SU["juan"].format(j=(CNUM(SZJ_JUAN[j["juan"]]) if L.code == "ja" and j["juan"] in SZJ_JUAN else SZJ_JUAN.get(j["juan"], j["juan"]))) + (" · " if L.code == "en" else "・") + jt_of(j)) if F else f'{j["juan"]} {j["jt"]}'
    lec_of = lambda n: SU["lec"].format(n=n) if F else f"第{CNUM(n)}讲"
    def li(j):
        if F:
            t = " ".join(TR["g"].get(str(g[0]), "") for g in j["groups"]) or TR["sum"].get(str(j["n"]), "")
            sn = esc(t[:70] + ("…" if len(t) > 70 else ""))
        else:
            t = "".join(g[1] for g in j["groups"])
            sn = esc(t[:36] + ("……" if len(t) > 36 else "")) if t else esc(j["sum"][:36] + "……")
        return f'<li class="wj" data-c="{j["n"]}"><a href="{P}{rel_of(j["n"])}"><em>{j["n"]}</em><b>{esc(name_of(j))}</b><span><i class="wjtag">{L.t("toc_wj")}</i><span>{sn}</span></span></a></li>'
    juans = []
    for j in JS:
        if not juans or juans[-1][0] != j["juan"]: juans.append((j["juan"], j["jt"], []))
        juans[-1][2].append(j)
    groups = "".join(f'<h2 class="ph">{SU["grp"].format(j=(CNUM(SZJ_JUAN[jn]) if L.code == "ja" and jn in SZJ_JUAN else SZJ_JUAN.get(jn, jn)), jt=jt_of(js[0]), a=js[0]["n"], b=js[-1]["n"]) if F else f"{jn} · {jt}（第 {js[0]["n"]}—{js[-1]["n"]} 讲）"}</h2><ol class="toc">{"".join(li(j) for j in js)}</ol>' for jn, jt, js in juans)
    pdf = os.path.exists(os.path.join(HERE, "root", "duben", "sanzijing-fuqin.pdf"))
    lead = SU["lead"] if F else ("《三字经》一千二百字，一百零一组，按一孔录《三字经·父亲讲义》分六卷三十九讲，每周一讲，一年读完。每讲有原文、逐组白话（初稿）和朗读。"
            "原文据讲义本，已与底本清王相《三字经训诂》（1831 年和刻本）逐句核对，每讲附王相本原页，点一组就在原页上框出来。讲义比王相本多出十一组（五色、五味、五臭、四声，以及辽金元明清到民国七组），是后出通行本补的，页内都标了“补”。" + (f'讲义全本可在<a href="{P}duben/">免费读本</a>下载。' if pdf else ""))
    bname = SU["book"] if F else "三字经"
    body = f"""<div class="chhead bk"><div class="wrap">{mcv(P, "", True, "sanzijing", "三字经")}<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a></p>
<h1><span class="no">{SZJ_PROG.get(L.code, SZJ_PROG["en"]).format(n=len(JS)) if F else "《三字经》 · 六卷三十九讲 · 一百零一组"}</span>{esc(bname)}</h1></div></div>
<main class="wrap narrow"><p class="lead">{lead}</p>{groups}</main>"""
    ld = {"@context": "https://schema.org", "@type": "Book", "name": bname, "url": f"{DOMAIN}/{L.prefix}sanzijing/", "inLanguage": L.hreflang}
    write("sanzijing/index.html", page(L, SU["bt"] if F else "《三字经》全文、白话与朗读｜三十九讲｜一孔录", SU["bd"] if F else "《三字经》全文按一孔录父亲讲义分三十九讲，逐组白话直译，附王相训诂本原页与原文朗读。", "sanzijing/", body, ld, "pg-book", codes=SZJ_CODES)); urls.append(f"{DOMAIN}/{L.prefix}sanzijing/")
    SH = {"bk": "三字经", "tot": len(JS), "src": "一孔录《三字经》讲义本", "src2": "一孔录《三字经》讲义本", "pf": "szj."}
    for k, j in enumerate(JS):
        n = j["n"]; url = f"{DOMAIN}/{L.prefix}{rel_of(n)}"; gs = j["groups"]; text = "".join(g[1] for g in gs)
        jtag = SU["prog"].format(jt=juan_of(j), n=n, k=len(gs)) if F else f'三字经 {n} · {j["juan"]} {j["jt"]}'
        cite_src = (f"Three Character Classic, lecture {n}, 一孔录 Yikonglu" if L.code == "en" else f"『三字経』第{n}講、一孔録") if F else f"三字经 {n} · 一孔录"
        trs = [TR["g"].get(str(g[0]), "") for g in gs] if F else []
        tr_all = " ".join(x for x in trs if x)
        jl = SZJ_JL["jl"].get(str(n), {})
        rect = lambda pg: "".join(f'<rect class="hl" data-s="{i}" x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6"/>' for i, g in enumerate(gs, 1) for (p_, x0, y0, x1, y1) in jl.get(str(g[0]), []) if p_ == pg)
        pgs = sorted({b[0] for v in jl.values() for b in v if b[0] in SZJ_JL["pages"]})
        plab = SU["pane"] if F else "原页"
        pane = "".join(f'<a class="yyp" href="{SZJ_IMG}{pg}.jpg" target="_blank" data-p="{pg}"><svg viewBox="0 0 {SZJ_JL["pages"][pg][0]} {SZJ_JL["pages"][pg][1]}" role="img" aria-label="{"Wang Xiang, Sanzijing xungu, page" if L.code == "en" else ("王相『三字経訓詁』" if F else "王相《三字经训诂》原页")} {int(pg[1:])}"><image href="{SZJ_IMG}{pg}.jpg" width="{SZJ_JL["pages"][pg][0]}" height="{SZJ_JL["pages"][pg][1]}"/>{rect(pg)}</svg><span>{plab} {int(pg[1:])}</span></a>' for pg in pgs)
        no = [i for i, g in enumerate(gs, 1) if g[0] in SZJ_WX_NO]
        has_yw = any(g[0] in SZJ_YW and g[0] not in SZJ_WX_NO for g in gs)
        if F and not pane and gs: cap = SU["cap_nopane"]
        elif F: cap = SU["cap"] + (SU["cap_no"] if no else "") + (SU["cap_yw"] if has_yw else "")
        elif not pane and gs: cap = "原文据一孔录《三字经·父亲讲义》本。这一讲各组王相《三字经训诂》本都没有，是后出通行本补的，所以不附原页；说明见下方“与王相本对照”。"
        else: cap = ("原文据一孔录《三字经·父亲讲义》本，已与底本清王相《三字经训诂》（1831 年和刻本）逐句核对；右边是王相本原页，点一组，原页上框出这一组。"
               + (f"标“补”的{len(no)}组王相本没有，讲义据后出通行本补。" if no else "") + ("异文见下方“与王相本对照”。" if has_yw else ""))
        ywd = TR.get("yw", {}) if F else {str(x): v for x, v in SZJ_YW.items()}
        yw_html = "".join(f'<p><b>{esc(SU["grp_n"].format(g=g[0]) if F else f"第 {g[0]} 组")}　<span lang="{"zh-Hant" if F else "zh-Hans"}">{esc(Y(g[1]))}</span></b><br>{esc(ywd[str(g[0])])}</p>' for g in gs if str(g[0]) in ywd)
        yw_html = f'<section class="sec szjyw"><h2>{esc(SU["yw_h"] if F else "与王相本对照")}</h2>{yw_html}</section>' if yw_html else ""
        bq = f'<blockquote lang="{"zh-Hant" if F else "zh-Hans"}" data-src="{esc(cite_src)}" data-url="{url}" data-short="{"" if F else f"yikonglu.com/sanzijing/{n}"}" data-sep="{", " if F else "，"}" data-reads="[]" data-rl="" data-hj="{{}}">'
        rows = [{"bh": g[2], "hj": []} for g in gs]
        NO_T = {"en": "Not in Wang Xiang's edition; taken from later popular editions", "ja": "王相本になく、通行本によって補った組"}.get(L.code, "王相本无此组，讲义据通行本补")
        if gs:
            ju_html = "".join(f'<span class="ju{" wxno" if g[0] in SZJ_WX_NO else ""}" id="s{i}" data-n="{i}" tabindex="0"{f" title={chr(34)}{NO_T}{chr(34)}" if g[0] in SZJ_WX_NO else ""}>{esc(Y(g[1]))}</span>' + ("" if F else f'<span class="yi" hidden>{esc(g[2])}</span>') for i, g in enumerate(gs, 1))
            if F:
                fig = (f'<figure class="yuanwen dz nocard{"" if pane else " nopane"}"><div class="dzgrid"><div>{bq}{ju_html}</blockquote>{langdu_html(L.code, str(n), "sanzijing")}<figcaption>{esc(cap)}</figcaption></div>'
                       + (f'<div class="yypane">{pane}</div>' if pane else "") + '</div></figure>')
                bh_html = (f'<section class="sec sec-白"><h2><i>{"Tr" if L.code == "en" else "訳"}</i>{esc(SU["tr_h"])}</h2>'
                           + "".join(f'<p><b lang="zh-Hant">{esc(Y(g[1]))}</b><br>{esc(t)}</p>' for g, t in zip(gs, trs) if t) + f'<p class="note">{esc(SU["tr_note"])}</p></section>')
            else:
                ld_btn = langdu_btn(L.code, str(n), "sanzijing") if str(n) in LANGDU_SZJ else ""
                fig = (f'<figure class="yuanwen dz{"" if pane else " nopane"}"><div class="dztools"><span class="prog">{jtag} · {len(gs)} 组</span><button type="button" class="yibtn" aria-pressed="false" title="每组下面显示白话">译</button>{ld_btn}</div>'
                       f'<div class="dzgrid"><div>{bq}{ju_html}</blockquote><figcaption>{cap}</figcaption></div>' + (f'<div class="yypane">{pane}</div>' if pane else "") + '</div>'
                       f'<script type="application/json" class="zjdata">{json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")}</script></figure>')
                bh_html = (f'<section class="sec sec-白"><h2><i>白</i>{L.t("baihua")}：“{esc(gs[0][1].split("，")[0] + "，" + gs[0][1].split("，")[1])}”是什么意思</h2>'
                           + "".join(f'<p lang="zh-Hans"><b>{esc(g[1])}</b><br>{esc(g[2])}</p>' for g in gs) + '<p class="note">白话为初稿，开讲时再核。</p></section>')
        else:
            fig = f'<p class="note">{esc(SU["none"]) if F else "这一讲不讲新原文。"}</p>'; bh_html = ""
        sm = TR["sum"].get(str(n), "") if F else j["sum"]
        if F: jy = f'<section class="gist ykan"><h2>{esc(SU["jy_h"])}</h2><p>{esc(sm)}</p><p class="note">{esc(SU["jy_note"])}</p></section>' if sm else ""
        else: jy = (f'<section class="gist ykan"><h2>父亲讲义里的这一讲</h2><p>{esc(sm)}</p>'
              + (f'<p class="note">摘自一孔录《三字经·父亲讲义》，全本见<a href="{P}duben/">免费读本</a>。</p>' if pdf else '<p class="note">摘自一孔录《三字经·父亲讲义》。</p>') + "</section>") if sm else ""
        vid = (f'<section class="video soon"><h2><i>{"▶" if F else "看"}</i>{L.t("video")}</h2><p class="vlinks">{L.t("wj_vid")}'
               f'<a href="https://www.youtube.com/@yikonglu" target="_blank" rel="noopener">YouTube</a><a href="https://space.bilibili.com/18385461" target="_blank" rel="noopener">{SU["bili"] if F else "哔哩哔哩"}</a></p></section>')
        prev_j = JS[k-1] if k > 0 else None; next_j = JS[k+1] if k+1 < len(JS) else None
        pn = "".join(f'<a class="pncard {cl}" href="{P}{rel_of(jj["n"])}"><small>{L.t(lb)}</small><b>{lec_of(jj["n"])}　{esc(name_of(jj))}</b></a>' if jj else "<span></span>" for jj, lb, cl in ((prev_j, "prev", "prev"), (next_j, "next", "next")))
        side = "".join(f'<li class="{"cur" if jj["n"] == n else ""} wj" data-c="{jj["n"]}"><a href="{P}{rel_of(jj["n"])}"><em>{jj["n"]}</em>{esc(name_of(jj))}</a></li>' for jj in JS if jj["juan"] == j["juan"])
        tre = " ".join((SZJ_TR.get("en") or {}).get("g", {}).get(str(g[0]), "") for g in gs).strip()
        trj = "".join((SZJ_TR.get("ja") or {}).get("g", {}).get(str(g[0]), "") for g in gs)
        LIVE_A.setdefault(L.code, {})[f"szj.{n}"] = [f"{bname} · {name_of(j)}", rel_of(n)]
        TRI_TXT[f"szj.{n}"] = {"h": f"《三字经》第{CNUM(n)}讲 · Three Character Classic {n} · 三字経 第{n}講", "y": text, "en": tre, "ja": trj}
        head_t = SU["lec"].format(n=n) if F else f"三字经 {n}"
        share = share_html(L, f"szj.{n}", url, f'{bname} · {head_t}' if F else head_t, name_of(j), Y(text) if F else text, "" if F else j["sum"][:60], tr_all if F else "", SH) if gs else ""
        crumb_j = juan_of(j)
        body = f"""<div class="chhead bk"><div class="wrap">{mcv(P, "", False, "sanzijing", "三字经")}
<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}sanzijing/">{esc(bname)}</a> › {esc(crumb_j)}</p>
<h1><span class="no">{esc(jtag)} · <em class="wjtag">{L.t("wj_tag")}</em></span>{esc(name_of(j))}</h1>
</div></div>
<main class="wrap chapter">
<article>
<p class="wjlead">{esc(SU["vlead"]) if F else "这一讲的视频还在制作。网站先放原文、白话和朗读，视频上线后补全讲解。"}</p>
{fig}
{bh_html if F else ""}
{yw_html}
{jy}
{"" if F else lyhj_html([r for r in SZJ_LYHJ if r["jiang"] == n], P)}
{"" if F else bh_html}
{vid}
<div class="chacts">{share}</div>
<section class="citeit"><p class="mailp">{L.t("report")} {MAIL}</p></section>
<nav class="pn">{pn}</nav>
</article>
<aside><h3>{esc(crumb_j)}</h3><ol>{side}</ol></aside>
</main><i id="rc" data-c="szj.{n}" hidden></i><script type="application/json" class="xddata">{json.dumps({"c": str(n), "ti": name_of(j)}, ensure_ascii=False)}</script>"""
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": f'{bname} {head_t} {name_of(j)}' if F else f"三字经 {n} {j['name']}", "inLanguage": L.hreflang, "url": url,
              "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN}, "about": {"@type": "Book", "name": bname}}
        if F: js = SHARE_JS + JU_JS.replace("@HJH@", L.t("hj_h")).replace("@HJ@", "<ul></ul>").replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied")) + ZJ.HL_JS
        else: js = SHARE_JS + (ZJ.ZJ_JS.replace("@IMG@", "做成分享图").replace("@TABS@", json.dumps([["bh", "白话"]], ensure_ascii=False)).replace("@NONE@", "这一组的白话还在整理。") if gs else "").replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied"))
        if S_IDX is not None and gs: S_IDX.append({"c": f'{bname} {n}' if F else f"三字经 {n}", "t": name_of(j), "u": P + rel_of(n), "y": Y(text) if F else text, "x": tr_all if F else " ".join(g[2] for g in gs)})
        if F: ttl, desc = f'{bname} · {head_t}: {name_of(j)} | 一孔录 Yikonglu', SU["md"].format(n=n, tr=tr_all[:110] + ("…" if len(tr_all) > 110 else "")) if gs else f'{bname} · {head_t}: {name_of(j)}. {sm[:100]}'
        else:
            head = (gs[0][1][:12] if gs else j["name"])
            ttl = f"{head}｜原文与白话｜三字经 {n} {j['name']}｜一孔录"
            desc = f"{text[:60]}……《三字经》第{CNUM(n)}讲“{j['name']}”原文、逐组白话与朗读。" if gs else f"《三字经》第{CNUM(n)}讲“{j['name']}”。{j['sum'][:60]}"
        write(rel_of(n), page(L, ttl, desc, rel_of(n), body + js, ld, "pg-chapter pg-wj", codes=SZJ_CODES)); urls.append(url)
    return urls

def build_lang(L, D, write):
    """D：公共数据。write(rel, html) 写到该语种目录。返回本语种 URL 列表。"""
    notes, yw, gao, kw, pub, by_pian, ch2ep, pages_avail = (D[k] for k in ("notes", "yw", "gao", "kw", "pub", "by_pian", "ch2ep", "pages_avail"))
    today = DATE_TOK  # 页内日期先占位，写盘时按本页内容真有变动的那天填
    P = "/" + L.prefix
    urls = []
    def rel_of(c):
        p, n = c.split("."); return f"lunyu/{PIAN[p][1]}/{n}.html"
    WJF = L.code in WJ_FL  # 本语种也出未讲章页（英日）
    def title_of(c): return L.ch(c).get("title") or (notes[c]["title"] if c in notes else ((WJF and wj_tr_title(L.code, c)) or wj_titles(D["qw"])[c]))
    if ANALYTICS.get("live") and "OUT_ROOT" in globals():  # 页脚“今天有人读了”、首页“最常被抄走的一句”查标题用
        os.makedirs(os.path.join(OUT_ROOT, "data"), exist_ok=True)
        _pl = lambda t: re.sub(r"\s*[（(][^（）()]*[）)]", "", t).strip() or t  # 11-13 主人：“今天有人读了”等只显示章名，括号里的补充不进阅读记录
        json.dump({"p": "/" + L.prefix, "c": {c: [_pl(title_of(c)), rel_of(c), split_ju(yw[c])] for c in pub}, "a": {c: [_pl(title_of(c)), rel_of(c)] for c in sorted(set(pub) | set(wj_titles(D["qw"])), key=lambda x: tuple(map(int, x.split("."))))}}, open(os.path.join(OUT_ROOT, "data", f"live-{L.code}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    def field(c, k):
        v = L.ch(c).get(k)
        return (v, True) if v else (notes[c]["fields"].get(k), False)
    _nqf = os.path.join(HERE, "nextq.json" if L.code.startswith("zh") else f"nextq-{L.code}.json")  # 英日问句译文（11-13 主人定做）：nextq-en/ja.json
    NEXTQ = json.load(open(_nqf, encoding="utf-8")) if os.path.exists(_nqf) else {}  # 11-13 主人要每章都有问句，逐章写在 nextq.json
    NQ_TW = __import__("opencc").OpenCC("s2twp") if NEXTQ and L.code == "zh-Hant" else None
    def next_q(c):  # 章末“下一章”卡下的一句问话：先用 nextq.json；没有时常见读法本身是问句就用它，否则问原文首句什么意思
        if c in NEXTQ: return NQ_TW.convert(NEXTQ[c]) if L.code == "zh-Hant" else NEXTQ[c]
        if not L.code.startswith("zh"): return ""
        v = notes[c]["fields"].get("常见读法") or ""
        v = v.strip()
        if v.endswith(("？", "?")) and len(v) <= 40: return v
        return f"“{seo_q(yw[c])}”是什么意思？" if yw.get(c) else ""
    search_idx = []
    pubset = set(pub)
    LB = LIVE_BOOKS | ({"daodejing"} if D.get("ddj") else set()) | ({"sanzijing"} if SZJ else set())  # 书目、首页亮着的书：论语＋已上原文的书
    def href(c):  # 已讲章各语种都有页；未讲章出简繁和英日（WJ_FL），其余外文页链到简体
        return (P if c in pubset or L.code.startswith("zh") or WJF else "/") + rel_of(c)
    def ctitle(c): return title_of(c) if c in pubset else ((WJF and wj_tr_title(L.code, c)) or wj_titles(D["qw"])[c])
    def gx_short(c):  # 关系栏、关系图里章的短题：原文头十来个字
        t = re.sub(r"^(子曰|孔子曰)[：:]?", "", yw.get(c) or (D["qw"].get(c) or {}).get("text", ""))
        return t[:14] + ("……" if len(t) > 14 else "")
    def hj_of(c):  # 本句互见：链到已讲章（各语种）或未讲章（简繁有页，外文链简体页）
        kname = {"注": L.t("hj_note"), "本书": L.t("hj_book"), "他书": L.t("hj_other")}
        hj_data = {}
        for r in D["hujian"].get(c, []):
            link = r["link"]
            m = re.fullmatch(r"(\d+\.\d+)(#s\d+)?", link or "")
            if m and (m.group(1) in pubset or m.group(1) in D["qw"]): link = href(m.group(1)) + (m.group(2) or "")
            elif m: link = ""
            hj_data.setdefault(r["ju"], []).append([kname.get(r["kind"], r["kind"]), r["text"], r["src"], link])
        return hj_data
    def sidebar(pnum, c):
        return "".join(f'<li data-c="{cc}" class="{"cur" if cc == c else ""}{" wj" if cc not in pubset else ""}"><a href="{href(cc)}"><em>{cc.split(".")[1]}</em>{esc(ctitle(cc))}</a></li>' for cc in D["all_by_pian"].get(pnum, by_pian.get(pnum, [])))
    def yiwen_html(c):
        rs = D["yiwen"].get(c)
        if not rs: return ""
        return (f'<section class="sec yiwen"><h2><i>异</i>{L.t("yiwen")}</h2><p class="note">{L.t("yiwen_note")}</p><table><thead><tr><th>{L.t("th_di")}</th><th>{L.t("th_tong")}</th><th>{L.t("th_shuo")}</th></tr></thead><tbody lang="zh-Hans">'
                + "".join(f'<tr><td class="zi">{esc(r["底本"])}</td><td>{esc(r["通行本"])}</td><td>{esc(r["说明"])}</td></tr>' for r in rs) + "</tbody></table></section>")
    def zb_section(c, url, cite_src):
        zb = D["zhuben"].get(c, {})
        if not zb: return ""
        blocks, diffs = "", []
        if "huang" in zb:
            h = zb["huang"]
            hurl = HUANG_SCAN.format(n=h["page"]) if h.get("ed", "zbz") == "zbz" else HUANG_WK.format(ce=h["ce"], n=h["page"])
            hmeta = L.t("zb_huang_meta", j=h["juan"]) if h.get("ed", "zbz") == "zbz" else L.t("zb_huang_meta2", j=h["juan"])
            blocks += (f'<div class="zb" id="zb-huangkan"><h3>{L.t("zb_huang")}<small>{esc(hmeta)}</small></h3>'
                       f'<p lang="zh-Hant">“{esc(h["text"])}”……</p><p class="zbsrc"><a class="pg" href="{hurl}" target="_blank" rel="noopener">{L.t("zb_scan", n=h["page"]) if h.get("ed", "zbz") == "zbz" else L.t("zb_scan2", ce=h["ce"], n=h["page"])}</a>'
                       + cpbtn(L, f'“{h["text"]}”——皇侃《论语义疏》，{cite_src}', url + "#zb-huangkan") + f'<a class="bb" href="{P}lunyu/banben/#huangkan">{L.t("bb_link")}</a></p></div>')
        for key, nk, mk in (("yang", "zb_yang", "zb_yang_meta"), ("qian", "zb_qian", "zb_qian_meta")):
            if key not in zb: continue
            z = zb[key]
            aid = {"yang": "yangbojun", "qian": "qianmu"}[key]; zh_n = {"yang": "杨伯峻《论语译注》", "qian": "钱穆《论语新解》"}[key]
            blocks += (f'<div class="zb" id="zb-{aid}"><h3>{L.t(nk)}<small>{L.t(mk)}</small></h3><p lang="zh-Hans">“{esc(z["text"])}”</p><p class="zbsrc">'
                       + cpbtn(L, f'“{z["text"]}”——{zh_n}，转引自{cite_src}', url + f"#zb-{aid}") + f'<a class="bb" href="{P}lunyu/banben/#{aid}">{L.t("bb_link")}</a></p></div>')
            zs = L.ch(c).get("zb_say", {}).get(key)  # 外语版：“与朱注异同”说明的译文（关键字、引文仍中文）
            diffs.append((L.t(nk), {**z, "say": zs, "say_l": L.hreflang} if zs else z))
        order = {"k_diff": 0, "k_word": 1, "k_shade": 2, "k_add": 3, "k_same": 4}
        diffs.sort(key=lambda t: order.get(t[1]["kind"], 9))
        has_s = any(z.get("sure") for _, z in diffs)  # “把握”列：CSV 有“把握”列（定／较稳／存疑）才显示
        scell = lambda z: (f'<td><span class="sure {z["sure"]}">{L.t(z["sure"])}</span></td>' if z.get("sure") else "<td></td>") if has_s else ""
        trs = "".join(f'<tr class="{z["kind"]}"><td>{esc(nm)}</td><td class="zi">{esc(z["key"])}</td><td><span class="kind">{L.t(z["kind"])}</span></td>{scell(z)}<td lang="{z.get("say_l", "zh-Hans")}">{esc(z["say"])}</td></tr>' for nm, z in diffs)
        sth = f'<th>{L.t("th_sure")}</th>' if has_s else ""
        dtab = f'<h3 class="zbd">{L.t("zb_diff")}</h3><table class="zbt"><thead><tr><th>{L.t("th_zb")}</th><th>{L.t("th_key")}</th><th>{L.t("th_kind")}</th>{sth}<th>{L.t("th_say")}</th></tr></thead><tbody>{trs}</tbody></table>' if diffs else ""
        return f'<section class="sec zhuben" id="zhuben"><h2><i>家</i>{L.t("zb_h")}</h2><p class="note">{L.t("zb_note")}</p><div class="zbs">{blocks}</div>{dtab}</section>'

    for i, c in enumerate(pub):
        n = notes[c]; pnum, cnum = c.split("."); pname, slug, pfull, _ = PIAN[pnum]
        epname, ep = ch2ep[c]; rel = rel_of(c); url = f"{DOMAIN}/{L.prefix}{rel}"
        og_img = D["og"].get(c, {}).get("tri") or D["og"].get(c, {}).get("hans")  # 三语图（原文＋英＋日），各语种共用
        bname = L.book(pnum)
        name = f"论语 {c} · {pname} {n['title']}" if L.code == "zh-Hans" else f"{L.t('lunyu')} {c} {title_of(c)}"
        desc = f"{yw[c][:60]}……原文、白话、朱熹注的关键字、诸家说法与一孔录的读法。" if L.code == "zh-Hans" else meta_desc(L, title_of(c), L.ch(c).get("yw"), yw[c])
        secs = ""; gist_html = ""
        for k, lab, mark in FIELDS:
            v, translated = field(c, k)
            if not v: continue
            if k == "片里落点":  # 一页两层：落点放上半，当“这一章讲什么”
                _cm, _ct = field(c, "常见读法"); _ky, _ = field(c, "字眼")
                an_lab, an_txt = ykan(L.code if translated else "zh", v, _cm if (_ct == translated) else None, _ky)
                gist_html = f'<section class="gist ykan" id="ykan"><h2>{L.t("ch_gist")}</h2><p{"" if translated or L.code=="zh-Hans" else " lang=zh-Hans"}><b class="anlab">{esc(an_lab)}</b>{quotes(an_txt)}</p>{YKCITE if L.code.startswith("zh") else ""}</section>'
                continue
            secs += f'<section class="sec sec-{mark}"><h2><i>{mark}</i>{L.t(lab)}</h2><p{"" if translated or L.code=="zh-Hans" else " lang=zh-Hans"}>{quotes(v)}</p></section>'
        if L.code == "zh-Hans" and c in D["zy"]:  # 争议读法主人选定的一孔按（11-08，tools/zhengyi.json 出自 规范/争议读法-选定表.md；待核出处已去人名）盖过自动短答；繁体由简体整页转
            gist_html = f'<section class="gist ykan" id="ykan"><h2>{L.t("ch_gist")}</h2><p><b class="anlab">{esc(YKAN["zh"][0])}</b>{quotes(D["zy"][c]["text"])}</p>{YKCITE}</section>'
        prev_c = pub[i-1] if i > 0 else None; next_c = pub[i+1] if i+1 < len(pub) else None
        def card(cc, lab, cls):
            if not cc: return '<span></span>'
            hq = f'<span class="nq">{esc(next_q(cc))}</span>' if cls == "next" and next_q(cc) else ""
            return f'<a class="pncard {cls}" href="{P}{rel_of(cc)}"><small>{lab}</small><b>{cc}　{esc(title_of(cc))}</b>{hq}</a>'
        side = sidebar(pnum, c)
        yt = ep.get("youtube", ""); g = gao.get(c, {"cites": [], "reads": []})
        st = ep.get("starts", {}).get(c) or D["starts"].get(yt, {}).get(c)  # 本章在视频里从第几秒讲起
        pub_at = ep.get("public_at", "")  # 定时公开的集：公开前视频块先藏着，到点由页内脚本显示
        future = bool(pub_at) and datetime.datetime.fromisoformat(pub_at) > datetime.datetime.now(datetime.timezone.utc)
        yt_src = f'https://www.youtube-nocookie.com/embed/{yt}{f"?start={st}" if st else ""}'
        if L.code == "zh-Hans" and ep.get("bilibili"):
            # 主人 11-07 定：简体页给大陆读者嵌哔哩哔哩。哔哩哔哩嵌入播放器在海外打不开（主人在日本实测），
            # 所以按设备时区选：中国大陆时区放哔哩哔哩，其他放 YouTube；下面一个按钮可以手动切换。没有脚本时默认 YouTube。
            bl_src = f'https://player.bilibili.com/player.html?bvid={ep["bilibili"]}&page=1&high_quality=1&danmaku=0&autoplay=0{f"&t={st}" if st else ""}'
            frame = (f'<iframe id="vplayer" loading="lazy" src="{yt_src}" data-yt="{yt_src}" data-bl="{esc(bl_src)}" title="{esc(epname)}" allowfullscreen scrolling="no"></iframe>'
                     '<script>(function(){var f=document.getElementById("vplayer");if(!f)return;var z="";try{z=Intl.DateTimeFormat().resolvedOptions().timeZone||""}catch(e){}'
                     'var cn=/^Asia\\/(Shanghai|Chongqing|Chungking|Harbin|Urumqi|Kashgar)$|^PRC$/.test(z),k="";try{k=localStorage.getItem("yk_vp")||""}catch(e){}'
                     'var bl=k?k==="bl":cn;function set(b){f.src=b?f.dataset.bl:f.dataset.yt;var s=document.getElementById("vswap");if(s)s.textContent=b?"播放不了？换 YouTube":"播放不了？换哔哩哔哩"}'
                     'if(bl)set(true);window.ykVswap=function(){bl=!bl;try{localStorage.setItem("yk_vp",bl?"bl":"yt")}catch(e){}set(bl)};'
                     'document.addEventListener("DOMContentLoaded",function(){set(bl)})})();</script>')
            swap = '<button type="button" id="vswap" class="vswap" onclick="ykVswap()">播放不了？换哔哩哔哩</button>'
        else:
            frame = f'<iframe loading="lazy" src="{yt_src}" title="{esc(epname)}" allowfullscreen></iframe>'
            swap = ""
        vid_html = (f"""<section class="video"{f' hidden data-pub="{pub_at}"' if future else ""}><h2><i>看</i>{L.t("video")}</h2>
<div class="vid">{frame}</div>
<p class="vlinks">{L.t("video_in", ep=epname)}<a href="https://www.youtube.com/watch?v={yt}{f'&amp;t={st}s' if st else ''}">YouTube</a>{f'<a href="https://www.bilibili.com/video/{ep["bilibili"]}{f"?t={st}" if st else ""}">{"哔哩哔哩" if L.code.startswith("zh") else "Bilibili"}</a>' if ep.get("bilibili") else ""}{swap}</p></section>""" + (f'<script>(function(){{var s=document.querySelector("section.video[data-pub]");if(!s)return;function f(){{if(Date.now()>=Date.parse(s.dataset.pub)){{s.hidden=false;return true}}}}if(!f())var t=setInterval(function(){{if(f())clearInterval(t)}},60000)}})();</script>' if future else "")) if yt else ""  # 视频还没上传（只排了时间）就先不放视频块
        def pg(nums):
            return " ".join(f'<a class="pg" href="/yuanye/p{int(x):03d}.jpg" target="_blank">{L.t("pg", n=x)}</a>' if x in pages_avail else f'<span class="pg">{L.t("pg", n=x)}</span>' for x in nums)
        extra = ""
        if g["cites"]:
            extra += (f'<section class="sec cites" id="zb-zhuxi"><h2><i>核</i>{L.t("cites")}</h2><p class="note">{L.t("cites_note")} <a class="bb" href="{P}lunyu/banben/#zhuxi">{L.t("bb_link")}</a> {cpbtn(L, "", url + "#zb-zhuxi", link_only=True)}</p><table><thead><tr><th>{L.t("th_quote")}</th><th>{L.t("th_src")}</th><th>{L.t("th_page")}</th></tr></thead><tbody>'
                      + "".join(f'<tr><td lang="zh-Hans">{"<span class=para>" + L.t("para") + "</span>" + esc(x["text"]) if x["para"] else "“" + esc(x["text"]) + "”"}</td><td>{esc(L.src(x["src"]))}</td><td>{pg(x["pages"]) if x["pages"] else "<span class=oth>" + esc(x["other"] or L.t("other_ed")) + "</span>"}</td></tr>' for x in g["cites"]) + "</tbody></table></section>")
        if g["reads"]:
            extra += (f'<section class="sec reads"><h2><i>音</i>{L.t("reads")}</h2><table><thead><tr><th>{L.t("th_zi")}</th><th>{L.t("th_pos")}</th><th>{L.t("th_du")}</th></tr></thead><tbody>'
                      + "".join(f'<tr><td class="zi">{esc(x["zi"])}</td><td>{esc(x["pos"])}</td><td>{esc(x["du"])}</td></tr>' for x in g["reads"]) + "</tbody></table></section>")
        allpages = sorted({x for r in g["cites"] for x in r["pages"]} | set(g.get("qw_pages", [])), key=int)
        imgs = "".join(f'<a href="/yuanye/p{int(x):03d}.jpg" target="_blank"><img loading="lazy" src="/yuanye/p{int(x):03d}.jpg" alt="{f"论语 {c} 朱熹集注原页：四部备要本第 {x} 页" if L.code.startswith("zh") else L.t("pg", n=x)}"><span>{L.t("pg", n=x)}</span></a>' for x in allpages if x in pages_avail)
        if imgs: extra += f'<section class="sec shots"><h2><i>页</i>{L.t("shots")}</h2><div class="pages">{imgs}</div></section>'
        mine = [r for r in kw if r[2] == c]
        if mine:
            extra += (f'<section class="sec kw" id="kw"><h2><i>勘</i>{L.t("kw")}</h2>{"<p class=note>" + L.t("kw_note") + "</p>" if L.t("kw_note") else ""}<ul lang="zh-Hans">' + "".join(
                f'<li><b>{esc(r[0])}　{esc(r[3])}</b>原来：{esc(r[4])}；改为：{esc(r[5])}（依据：{esc(r[6])}；勘误者：{esc(r[7])}）</li>' for r in mine) + '</ul></section>')
        cite_txt = L.t("cite_fmt", book=(pname if L.code == "zh-Hans" else bname), c=c, title=title_of(c), url=url, d=today)
        citeit = f'<section class="citeit"><b>{L.t("cite")}</b><code>{esc(cite_txt)}</code><button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent);this.textContent=\'{L.t("copied")}\'">{L.t("copy")}</button><p>{L.t("checked", d=today)}<a href="{P}kanwu.html">{L.t("errata_page")}</a>.</p><p class="mailp">{L.t("report")} {MAIL}</p></section>'
        search_idx.append({"c": c, "t": title_of(c), "u": P + rel, "y": yw[c],
                           "x": " ".join(v for k, _, _ in FIELDS for v in [field(c, k)[0]] if v) + " " + " ".join(x["text"] + x["src"] for x in g["cites"])
                                + " " + " ".join(v["text"] for v in D["zhuben"].get(c, {}).values())})
        ju_html = "".join(f'<span class="ju" id="s{j}" data-n="{j}" tabindex="0">{zx(L.code, c, j, x)}</span>' for j, x in enumerate(split_ju(yw[c]), 1))
        cite_src = (f"论语 {c} · 一孔录" if L.code.startswith("zh") else f"{L.t('lunyu')} {c}, 一孔录 Yikonglu")
        zb = D["zhuben"].get(c, {}); hj_data = hj_of(c)
        extra = zb_section(c, url, cite_src) + extra
        bh = D["baihua"].get(c)
        bh_h2 = f'{L.t("baihua")}：“{esc(seo_q(yw[c]))}”是什么意思' if L.code.startswith("zh") else L.t("baihua")  # 主人 11-07 定：标题带读者会问的话
        bh_html = f'<section class="sec sec-白"><h2><i>白</i>{bh_h2}</h2><p lang="zh-Hans">{esc(bh)}</p><p class="note">{L.t("baihua_note")}</p></section>' if bh else ""
        rend = L.ch(c).get("yw")
        rend_html = f'<p class="rend">{esc(rend)}</p><figcaption>{L.t("rendering")}</figcaption>' if rend else ""
        ZJD = D.get("zhuju") or {"on": set(), "jl": {}, "zj": {}}
        dz = c in ZJD["on"] and L.code.startswith("zh") and c in ZJD["jl"]
        if dz:
            sents = split_ju(yw[c]); zpages, zper = ZJ.spans_of(c, sents, ZJD); zs = ZJ.card_data(c, ZJD, len(sents)) or []
            zrows = []
            for j, x in enumerate(sents, 1):
                d = {k: zs[j-1].get(k) for k in ("bh", "zhu", "jj", "yk") if zs[j-1].get(k)} if j <= len(zs) else {}
                d["hj"] = [[f"{h[0]}：{h[1]}", h[2], ""] for h in hj_data.get(str(j), [])]
                zrows.append(d)
            ju_html = "".join(f'<span class="ju" id="s{j}" data-n="{j}" tabindex="0">{zx(L.code, c, j, x)}</span><span class="yi" hidden>{esc(zrows[j-1].get("bh", ""))}</span>' for j, x in enumerate(sents, 1))
            fig_html = (f'<figure class="yuanwen dz"><div class="dztools"><span class="prog">{pfull} · 本篇第 {cnum}/{PIAN[pnum][3]} 章</span><button type="button" class="yibtn" aria-pressed="false" title="每句下面显示白话">译</button>{langdu_btn(L.code, c)}</div>'
                        f'<div class="dzgrid"><div><blockquote lang="zh-Hans" data-src="{esc(cite_src)}" data-url="{url}" data-short="{f'yikonglu.com/lunyu/{c}' if L.code.startswith('zh') else ''}" data-sep="，" data-reads="{esc(json.dumps([[x["zi"], x["pos"], x["du"]] for x in g["reads"]], ensure_ascii=False))}" data-rl="{esc(L.t("ju_reads"))}">{ju_html}</blockquote><figcaption>{L.t("source_line")}</figcaption>{rend_html}</div>'
                        f'<div class="yypane">{ZJ.page_pane(c, zpages, zper, "原页", ZJ.YDIR, f"论语 {c} 原文原页：朱熹《论语集注》四部备要本第 {{n}} 页")}</div></div>'
                        f'<script type="application/json" class="zjdata">{json.dumps(zrows, ensure_ascii=False).replace("</", "<\\/")}</script></figure>')
        else:
            fig_html = None
            if not L.code.startswith("zh") and c in ZJD["jl"]:  # 外文页（11-13 主人：英日版也要原页）：原文旁同屏原页，点句亮列；小卡只在简繁页
                _buf = io.StringIO()
                with contextlib.redirect_stdout(_buf): zp_, zr_ = ZJ.spans_of(c, split_ju(yw[c]), ZJD)
                if zp_:
                    fig_html = (f'<figure class="yuanwen dz nocard"><div class="dzgrid"><div><blockquote lang="zh-Hans" data-src="{esc(cite_src)}" data-url="{url}" data-short="{f'yikonglu.com/lunyu/{c}' if L.code.startswith('zh') else ''}" data-sep=", " data-reads="{esc(json.dumps([[x['zi'], x['pos'], x['du']] for x in g['reads']], ensure_ascii=False))}" data-rl="{esc(L.t('ju_reads'))}" data-hj="{esc(json.dumps(hj_data, ensure_ascii=False))}">{ju_html}</blockquote>{langdu_html(L.code, c)}<figcaption>{L.t("source_line")}</figcaption>{rend_html}</div>'
                                f'<div class="yypane">{ZJ.page_pane(c, zp_, zr_, L.t("pg", n="").strip(), ZJ.YDIR, L.t("pg", n="{n}"))}</div></div></figure>')
        if fig_html is None:
            fig_html = f"""<figure class="yuanwen"><blockquote lang="zh-Hans" data-src="{esc(cite_src)}" data-url="{url}" data-short="{f'yikonglu.com/lunyu/{c}' if L.code.startswith('zh') else ''}" data-sep="{'，' if L.code.startswith('zh') else ', '}" data-reads="{esc(json.dumps([[x['zi'], x['pos'], x['du']] for x in g['reads']], ensure_ascii=False))}" data-rl="{esc(L.t('ju_reads'))}" data-hj="{esc(json.dumps(hj_data, ensure_ascii=False))}">{ju_html}</blockquote>{langdu_html(L.code, c)}<figcaption>{L.t("source_line")}</figcaption>{rend_html}</figure>"""
        body = f"""<div class="chhead bk"><div class="wrap">{mcv(P)}
<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}lunyu/">{L.t("lunyu")}</a> › <a href="{P}lunyu/{slug}/">{bname}</a></p>
<h1><span class="no">{f"论语 {c} · {pname}" if L.code.startswith("zh") else L.t("chapter_no", book=bname, n=cnum)}</span>{esc(title_of(c))}</h1>{LX.nl_tag(L, P, D["lx"], c)}{f'<p class="kwtag"><a href="#kw">{L.t("kw")} {len(mine)} 条</a> · <a href="{P}kanwu.html">全部勘误</a></p>' if mine and L.code.startswith("zh") else ""}
</div></div>
<main class="wrap chapter">
<article>
{fig_html}{zi_tail(L.code, c, P)}
{gist_html}
{bh_html}
{vid_html}
<div class="chacts">{done_html(L, c) if c in D["pub"] else ""}{share_html(L, c, url, (f"论语 {c} · {pname}" if L.code.startswith("zh") else L.t("chapter_no", book=bname, n=cnum)), title_of(c), yw[c], field(c, "片里落点")[0], rend)}</div>
{'<p class="steps" id="steps" hidden></p>' if ANALYTICS.get("live") and c in D["pub"] else ""}
{GX.section(GXD, c, P, href, gx_short) if L.code.startswith("zh") else (GX.section_f(GXD, c, P, href, gx_short, L) if GXD and GX.has_lang(L.code) else "")}
{cta_html(L, P)}
<div class="deep"><div class="deephead"><h2>{L.t("ch_deep")}</h2><button type="button" class="foldall" data-o="{L.t("ch_open_all")}" data-c="{L.t("ch_close_all")}">{L.t("ch_open_all")}</button></div><p class="note">{L.t("ch_deep_note")}</p>
{fold(secs + yiwen_html(c) + extra)}
{citeit}
</div>
<p class="tags">{''.join(f'<span>#{esc(t)}</span>' for t in n['tags'])}</p>{RW.chip_line(D.get("renwu"), c, P) if L.code.startswith("zh") else ""}{GS.footer_line(D.get("gushi"), c, P) if L.code.startswith("zh") else ""}
<nav class="pn">{card(prev_c, L.t("prev"), 'prev')}{card(next_c, L.t("next"), 'next')}</nav>
</article>
<aside><h3>{bname}</h3><ol>{side}</ol></aside>
</main>{FROM_JS if L.code.startswith("zh") else ""}{BOOK_JS}"""
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": name,
              "inLanguage": L.hreflang, "url": url, "dateModified": today, "image": f"{DOMAIN}/{og_img or 'assets/og.jpg'}",
              "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN},
              "publisher": {"@type": "Organization", "name": "一孔录", "url": DOMAIN, "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/assets/seal-180.png"}},
              "about": {"@type": "Book", "name": "论语"},
              "isBasedOn": {"@type": "Book", "name": "论语集注", "author": {"@type": "Person", "name": "朱熹"}},
              "video": {"@type": "VideoObject", "name": f"一孔录《{epname}》", "description": f"一孔录讲读《论语·{pname}》，含本章。",
                        "embedUrl": f"https://www.youtube.com/embed/{yt}", "url": f"https://www.youtube.com/watch?v={yt}",
                        "thumbnailUrl": f"https://i.ytimg.com/vi/{yt}/hqdefault.jpg"}}
        if not yt or future: ld.pop("video")
        else: ld["video"]["uploadDate"] = pub_at or (D["first"].get(c, today) + "T12:00:00+08:00")  # 谷歌视频结构化数据必填
        if st and "video" in ld:
            _all = {**D["starts"].get(yt, {}), **ep.get("starts", {})}
            _end = min((int(v) for v in _all.values() if v and int(v) > int(st)), default=None)  # 本章到下一章开讲为止
            if _end: ld["video"]["hasPart"] = [{"@type": "Clip", "name": f"{c} {title_of(c)}", "startOffset": int(st), "endOffset": _end, "url": f"https://www.youtube.com/watch?v={yt}&t={int(st)}s"}]
        ttl = f"{seo_head(yw[c])}｜{"意思、读音与朱熹注" if g["reads"] else "意思与朱熹注"}｜论语 {c} · {pname}｜一孔录" if L.code.startswith("zh") else f"{name} | 一孔录 Yikonglu"
        first = D["first"].get(c, today)
        hj_static = "<ul>" + (f'<li><a href="#zhuben">{L.t("hj_zb")}</a></li>' if zb else "") + (f'<li><a href="#zb-zhuxi">{L.t("hj_cites")}</a></li>' if g["cites"] else "") \
            + (f'<li><a href="https://www.youtube.com/watch?v={yt}&amp;t={st}s" target="_blank" rel="noopener">{L.t("hj_video", t=f"{st//60}:{st%60:02d}")}</a></li>' if st else "") + "</ul>"
        bc = {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "一孔录", "item": f"{DOMAIN}/{L.prefix}"},
            {"@type": "ListItem", "position": 2, "name": L.t("lunyu"), "item": f"{DOMAIN}/{L.prefix}lunyu/"},
            {"@type": "ListItem", "position": 3, "name": bname, "item": f"{DOMAIN}/{L.prefix}lunyu/{slug}/"},
            {"@type": "ListItem", "position": 4, "name": f"{c} {title_of(c)}", "item": url}]}
        ld.pop("@context"); ld["datePublished"] = first
        faq = ([{"@type": "Question", "name": f"“{seo_q(yw[c])}”是什么意思？", "acceptedAnswer": {"@type": "Answer", "text": bh}}] if bh else []) + \
              ([{"@type": "Question", "name": f"论语 {c}（{pname}）这一章讲什么？", "acceptedAnswer": {"@type": "Answer", "text": field(c, "片里落点")[0]}}] if field(c, "片里落点")[0] else []) + \
              ([{"@type": "Question", "name": "一孔录怎么读这一章？", "acceptedAnswer": {"@type": "Answer", "text": (YKAN["zh"][0] + D["zy"][c]["text"]) if c in D["zy"] else "".join(ykan("zh", field(c, "片里落点")[0], field(c, "常见读法")[0], field(c, "字眼")[0]))}}] if (field(c, "片里落点")[0] or c in D["zy"]) else [])
        ld = {"@context": "https://schema.org", "@graph": [ld, bc] + ([{"@type": "FAQPage", "mainEntity": faq}] if faq and L.code.startswith("zh") else [])}
        cit = "".join(f'<meta name="{k}" content="{esc(v)}">' for k, v in [
            ("citation_title", name), ("citation_author", "一孔录"), ("citation_publisher", "一孔录 yikonglu.com"),
            ("citation_publication_date", first.replace("-", "/")), ("citation_online_date", DATE_TOK_SL),
            ("citation_language", L.hreflang), ("citation_public_url", url),
            ("DC.title", name), ("DC.creator", "一孔录"), ("DC.date", first), ("DC.language", L.hreflang), ("DC.source", SOURCE)])
        write(rel, page(L, ttl, desc, rel, body + SHARE_JS + FOLD_JS + (ZJ.ZJ_JS.replace("@TABS@", json.dumps([["bh", "白话"], ["zhu", "朱注"], ["jj", "集解"], ["yk", "一孔读法"], ["hj", "本句互见"]], ensure_ascii=False)).replace("@IMG@", "做成分享图").replace("@NONE@", "这一句没有收。") if dz else JU_JS.replace("@HJH@", L.t("hj_h")).replace("@HJ@", hj_static)).replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied")) + (ZJ.HL_JS if "nocard" in fig_html else ""), ld, "pg-chapter", og_img=og_img, head_extra=cit)); urls.append(url)


    # 未讲各章：出简繁和英日（WJ_FL）。原文（朱注分章底本）、白话初稿、本句互见、异文、各家注本；原页同屏、视频位（11-08）
    # 英日页（11-13 主人：英日版做起来、各语言功能尽量一致）：原文下放英日译文（tri-weijiang.json），一孔按仍中文、加一句说明；原页点句亮列，小卡只在简繁页
    if L.code.startswith("zh") or WJF:
        zhL = L.code.startswith("zh"); WJ_CODES = ["zh-Hans", "zh-Hant"] + [x for x in WJ_FL if x in LANGS]
        ZJD = D.get("zhuju") or {"on": set(), "jl": {}, "zj": {}}
        WJ_PAGES = wj_pages()
        for p_, cs in D["all_by_pian"].items():
            for k, c in enumerate(cs):
                if c in pubset: continue
                q = D["qw"][c]; text = q["text"]; pnum, cnum = c.split("."); pname, slug, pfull, _ = PIAN[pnum]
                rel = rel_of(c); url = f"{DOMAIN}/{L.prefix}{rel}"; bname = L.book(pnum)
                cite_src = f"论语 {c} · 一孔录" if zhL else f"{L.t('lunyu')} {c}, 一孔录 Yikonglu"
                tr = "" if zhL else WJ_TR.get(c, {}).get(L.code, "")
                rend_html = f'<p class="rend">{esc(tr)}</p><figcaption>{L.t("rendering")}</figcaption>' if tr else ""
                ju_html = "".join(f'<span class="ju" id="s{j}" tabindex="0">{zx(L.code, c, j, x)}</span>' for j, x in enumerate(split_ju(text), 1))
                pgn = str(q.get("pdf_page", ""))
                pgl = (f'<a class="pg" href="/yuanye/p{int(pgn):03d}.jpg" target="_blank">{pgn}</a>' if pgn in pages_avail else pgn) if pgn else ""
                cap = L.t("wj_src", src=SOURCE, n=pgl) if pgn else L.t("source_line")
                y = D["fz"].get(c)
                if y and y != c: cap += " " + L.t("wj_yang", y=y)
                bh = D["baihua"].get(c)
                bh_note = "" if c in D.get("bh_ok", ()) else f'<p class="note">{L.t("wj_bh_note")}</p>'
                bh_html = f'<section class="sec sec-白"><h2><i>白</i>{L.t("baihua")}</h2><p lang="zh-Hans">{esc(bh)}</p>{bh_note}</section>' if bh else ""
                prev_c = cs[k-1] if k > 0 else None; next_c = cs[k+1] if k+1 < len(cs) else None
                pn = "".join(f'<a class="pncard {cl}" href="{href(cc)}"><small>{L.t(lab)}</small><b>{cc}　{esc(ctitle(cc))}</b></a>' if cc else "<span></span>" for cc, lab, cl in ((prev_c, "prev", "prev"), (next_c, "next", "next")))
                # 主人 11-08：网站先行，不等视频。未讲章也上原页同屏与逐句小卡：有校平句列且字对得上的点句亮列；只有页图的整页并排；
                # 逐句白话、朱注取 _逐句（内容线程交，朱注只收稿里核过页的原话）；“这一章讲什么”一孔按取 _未讲/<章>.json；视频位先写“正在制作”
                hjd = hj_of(c); wj_dz = False; wj_rows = []; sents = split_ju(text)
                bq = f'<blockquote lang="zh-Hans" data-src="{esc(cite_src)}" data-url="{url}" data-short="{f'yikonglu.com/lunyu/{c}' if L.code.startswith('zh') else ''}" data-sep="{"，" if zhL else ", "}" data-reads="[]" data-rl="" data-hj="{esc(json.dumps(hjd, ensure_ascii=False))}">'
                zpages = zper = None
                if c in ZJD["jl"]:
                    _buf = io.StringIO()
                    with contextlib.redirect_stdout(_buf): zp_, zr_ = ZJ.spans_of(c, sents, ZJD)
                    if zp_ and not _buf.getvalue() and all(p_ in WJ_PAGES for p_ in zp_): zpages, zper = zp_, zr_
                pp = f"p{int(pgn):03d}" if pgn else ""
                palt = f"论语 {c} 原文原页：朱熹《论语集注》四部备要本第 {{n}} 页" if zhL else L.t("pg", n="{n}")
                pane = (ZJ.page_pane(c, zpages, zper, L.t("wj_pane"), ZJ.YDIR, palt) if zpages
                        else ZJ.page_pane(c, {pp: WJ_PAGES[pp]}, [], L.t("wj_pane"), ZJ.YDIR, palt) if pp in WJ_PAGES else "")
                zs = (ZJ.card_data(c, ZJD, len(sents)) or []) if zhL else []
                if zs and len(zs) != len(sents): zs = []  # 句数对不上就不挂小卡，免得张冠李戴
                if not zhL and zpages:  # 英日：原页同屏点句亮列，不挂小卡（同已讲章外文页）
                    ju_html = "".join(f'<span class="ju" id="s{j}" data-n="{j}" tabindex="0">{esc(x)}</span>' for j, x in enumerate(sents, 1))
                    wj_fig = (f'<figure class="yuanwen dz nocard"><div class="dzgrid"><div>{bq}{ju_html}</blockquote>{langdu_html(L.code, c)}<figcaption>{cap}</figcaption>{rend_html}</div>'
                              f'<div class="yypane">{pane}</div></div></figure>')
                elif zpages or zs:
                    wj_dz = True
                    for j, x in enumerate(sents, 1):
                        d = {k_: zs[j-1].get(k_) for k_ in ("bh", "zhu", "jj", "yk") if zs[j-1].get(k_)} if j <= len(zs) else {}
                        d["hj"] = [[f"{h[0]}：{h[1]}", h[2], ""] for h in hjd.get(str(j), [])]
                        wj_rows.append(d)
                    ju_html = "".join(f'<span class="ju" id="s{j}" data-n="{j}" tabindex="0">{zx(L.code, c, j, x)}</span>' + (f'<span class="yi" hidden>{esc(wj_rows[j-1]["bh"])}</span>' if wj_rows[j-1].get("bh") else "") for j, x in enumerate(sents, 1))
                    yib = '<button type="button" class="yibtn" aria-pressed="false" title="每句下面显示白话">译</button>' if any(r.get("bh") for r in wj_rows) else ""
                    wj_fig = (f'<figure class="yuanwen dz{"" if pane else " nopane"}"><div class="dztools"><span class="prog">{pfull} · 本篇第 {cnum}/{PIAN[pnum][3]} 章</span>{yib}{langdu_btn(L.code, c)}</div>'
                              f'<div class="dzgrid"><div>{bq}{ju_html}</blockquote><figcaption>{cap}</figcaption></div>'
                              + (f'<div class="yypane">{pane}</div>' if pane else "") + '</div>'
                              f'<script type="application/json" class="zjdata">{json.dumps(wj_rows, ensure_ascii=False).replace("</", "<\\/")}</script></figure>')
                elif pane:
                    wj_fig = (f'<figure class="yuanwen wjpg"><div class="dzgrid"><div>{bq}{ju_html}</blockquote>{langdu_html(L.code, c)}<figcaption>{cap}</figcaption>{rend_html}</div>'
                              f'<div class="yypane">{pane}</div></div></figure>')
                else:
                    wj_fig = f'<figure class="yuanwen">{bq}{ju_html}</blockquote>{langdu_html(L.code, c)}<figcaption>{cap}</figcaption>{rend_html}</figure>'
                an = D.get("wjan", {}).get(c) or {}
                wj_gist, wj_faq = "", []
                if an.get("片里落点") or c in D["zy"]:
                    an_lab, an_txt = (YKAN["zh"][0], D["zy"][c]["text"]) if c in D["zy"] else ykan("zh", an["片里落点"], an.get("常见读法"), an.get("字眼"))
                    wj_gist = (f'<section class="gist ykan"><h2>{L.t("ch_gist")}</h2><p><b class="anlab">{esc(an_lab)}</b>{quotes(an_txt)}</p></section>' if zhL else
                               f'<section class="gist ykan"><h2>{L.t("ch_gist")}</h2><p lang="zh-Hans"><b class="anlab">{esc(an_lab)}</b>{quotes(an_txt)}</p><p class="note">{L.t("wj_an_note")}</p></section>')
                    wj_faq = [] if not zhL else ([{"@type": "Question", "name": f"论语 {c}（{pname}）这一章讲什么？", "acceptedAnswer": {"@type": "Answer", "text": an["片里落点"]}}] if an.get("片里落点") else []) + \
                             [{"@type": "Question", "name": "一孔录怎么读这一章？", "acceptedAnswer": {"@type": "Answer", "text": an_lab + an_txt}}]
                # 主人 11-08 问“细读与核对为啥只有各家注本”：把未讲章已有的素材也收进来——常见理解、注里的关键字（_未讲）、朱注逐句原话（_逐句，只收核过页的）、本句互见
                wj_deep = ""
                if len(an.get("常见读法") or "") >= 10:
                    wj_deep += f'<section class="sec sec-常"><h2><i>常</i>{L.t("f_common")}</h2><p{"" if zhL else " lang=zh-Hans"}>{quotes(an["常见读法"])}</p></section>'
                if an.get("字眼"):
                    wj_deep += f'<section class="sec sec-注"><h2><i>注</i>{L.t("f_keys")}</h2><p{"" if zhL else " lang=zh-Hans"}>{quotes(an["字眼"])}</p></section>'
                _zrows, _seen = [], set()
                _ss = (ZJD["zj"].get(c) or {}).get("句", []); _ok = len(_ss) == len(sents)  # 句数对不上就不标句
                for j, z in enumerate(_ss, 1):
                    for zz in (z.get("zhu") or []):
                        if not zz or not zz[0] or zz[0] in _seen: continue
                        _seen.add(zz[0]); _pgs = re.findall(r"\d+", zz[1] if len(zz) > 1 else "")
                        _pg = ("—".join(_pgs[:2]) if _pgs else "")
                        _zrows.append((j if _ok else 0, zz[0], _pg))
                if _zrows:
                    def _pgl(x):
                        a = x.split("—")[0]
                        return f'<a class="pg" href="/yuanye/p{int(a):03d}.jpg" target="_blank">{L.t("pg", n=x)}</a>' if a and a in pages_avail else (L.t("pg", n=x) if x else "")
                    wj_deep += (f'<section class="sec cites" id="zb-zhuxi"><h2><i>核</i>{"朱熹集注逐句原话" if zhL else L.t("wj_deep_zx")}</h2><p class="note">{"朱注里说到本章各句的原话，都对过底本原页；视频开讲时再补诸家说法。" if zhL else L.t("wj_deep_zx_p")} <a class="bb" href="{P}lunyu/banben/#zhuxi">{L.t("bb_link")}</a></p>'
                                f'<table><thead><tr><th>{"句" if zhL else L.t("th_ju")}</th><th>{L.t("th_quote")}</th><th>{L.t("th_page")}</th></tr></thead><tbody>'
                                + "".join(f'<tr><td>{f"<a href=#s{j}>{esc(sents[j-1][:8])}</a>" if j else ""}</td><td lang="zh-Hans">“{esc(t)}”</td><td>{_pgl(pg_)}</td></tr>' for j, t, pg_ in _zrows) + "</tbody></table></section>")
                _hjr = [(int(j), r) for j, rs in hjd.items() if str(j).isdigit() for r in rs if not (_zrows and r[0] == L.t("hj_note"))]  # 朱注条上面表里已有
                if _hjr:
                    wj_deep += (f'<section class="sec hujian"><h2><i>见</i>{L.t("hj_h")}</h2><ul lang="zh-Hans">'
                                + "".join(f'<li><a href="#s{j}">{esc(sents[j-1][:8]) if 0 < j <= len(sents) else ""}</a>　{esc(r[0])}：{esc(r[1])}（' + (f'<a href="{r[3]}">{esc(r[2])}</a>' if r[3] else esc(r[2])) + '）</li>' for j, r in sorted(_hjr, key=lambda x: x[0])) + '</ul></section>')
                TRI_TXT.setdefault(c, {"h": f"《论语·{pname}》第 {cnum} 章 · Analects {c} · 論語 {c}", "y": text, "en": WJ_TR.get(c, {}).get("en", ""), "ja": WJ_TR.get(c, {}).get("ja", "")})  # 分享图：未讲章英日译文见 i18n/tri-weijiang.json（11-09 补）
                wj_vid = (f'<section class="video soon"><h2><i>看</i>{L.t("video")}</h2><p class="vlinks">{L.t("wj_vid")}'
                          f'<a href="https://www.youtube.com/@yikonglu" target="_blank" rel="noopener">YouTube</a><a href="https://space.bilibili.com/18385461" target="_blank" rel="noopener">{"哔哩哔哩" if zhL else "Bilibili"}</a></p></section>')
                body = f"""<div class="chhead bk"><div class="wrap">{mcv(P)}
<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}lunyu/">{L.t("lunyu")}</a> › <a href="{P}lunyu/{slug}/">{bname}</a></p>
<h1><span class="no">{f"论语 {c} · {pname}" if zhL else L.t("chapter_no", book=bname, n=cnum)} · <em class="wjtag">{L.t("wj_tag")}</em></span>{esc(ctitle(c))}</h1>{LX.nl_tag(L, P, D["lx"], c)}
</div></div>
<main class="wrap chapter">
<article>
<p class="wjlead">{L.t("wj_lead")}</p>
{wj_fig}{zi_tail(L.code, c, P)}
{wj_gist}
{bh_html}
{wj_vid}
<div class="chacts">{done_html(L, c)}{share_html(L, c, url, f"论语 {c} · {pname}" if zhL else L.t("chapter_no", book=bname, n=cnum), ctitle(c), text, an.get("片里落点") or (D["zy"].get(c) or {}).get("text", ""), tr)}</div>
{'<p class="steps" id="steps" hidden></p>' if ANALYTICS.get("live") else ""}
{GX.section(GXD, c, P, href, gx_short) if zhL else (GX.section_f(GXD, c, P, href, gx_short, L) if GXD and GX.has_lang(L.code) else "")}
<div class="deep"><div class="deephead"><h2>{L.t("ch_deep")}</h2><button type="button" class="foldall" data-o="{L.t("ch_open_all")}" data-c="{L.t("ch_close_all")}">{L.t("ch_open_all")}</button></div><p class="note">{L.t("ch_deep_note")}</p>
{fold(wj_deep + yiwen_html(c) + zb_section(c, url, cite_src))}
<section class="citeit"><p class="mailp">{L.t("report")} {MAIL}</p></section>
</div>
<nav class="pn">{pn}</nav>
</article>
<aside><h3>{bname}</h3><ol>{sidebar(pnum, c)}</ol></aside>
</main>{BOOK_JS}"""
                hj_static = "<ul>" + (f'<li><a href="#zhuben">{L.t("hj_zb")}</a></li>' if D["zhuben"].get(c) else "") + "</ul>"
                desc = f"{text[:70]}……论语 {c}（{pname}第 {cnum} 章）原文与白话直译。" if zhL else meta_desc(L, ctitle(c), tr, text)
                ld = {"@context": "https://schema.org", "@type": "Article", "headline": f"论语 {c} · {pname} {ctitle(c)}" if zhL else f"{L.t('lunyu')} {c} {ctitle(c)}", "inLanguage": L.hreflang, "url": url,
                      "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN}, "about": {"@type": "Book", "name": "论语"},
                      "isBasedOn": {"@type": "Book", "name": "论语集注", "author": {"@type": "Person", "name": "朱熹"}}}
                if wj_faq: ld.pop("@context"); ld = {"@context": "https://schema.org", "@graph": [ld, {"@type": "FAQPage", "mainEntity": wj_faq}]}
                write(rel, page(L, L.t("wj_title", book=pname, c=c, head=seo_head(text)) if zhL else f"{L.t('lunyu')} {c} {ctitle(c)} | 一孔录 Yikonglu", desc, rel, body + SHARE_JS + FOLD_JS + (ZJ.ZJ_JS.replace('<button data-a="img">@IMG@</button>', "").replace("@TABS@", json.dumps([["bh", "白话"], ["zhu", "朱注"], ["jj", "集解"], ["yk", "一孔读法"], ["hj", "本句互见"]], ensure_ascii=False)).replace("@NONE@", "这一句的逐句白话和注还在整理，整章白话见下文。") if wj_dz else JU_JS.replace("@HJH@", L.t("hj_h")).replace("@HJ@", hj_static)).replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied")) + (ZJ.HL_JS if "nocard" in wj_fig else ""), ld, "pg-chapter pg-wj", og_img=D["og"].get(c, {}).get("tri"), codes=WJ_CODES)); urls.append(url)
                search_idx.append({"c": c, "t": ctitle(c), "u": P + rel, "y": text, "x": (tr + " " if tr else "") + (bh or "") + " " + " ".join(v["text"] for v in D["zhuben"].get(c, {}).values())})

    urls += build_ddj(L, D, write, P, search_idx if (L.code.startswith("zh") or L.code in DDJ_TR) else None)
    urls += build_szj(L, write, P, search_idx if (L.code.startswith("zh") or L.code in SZJ_TR) else None)  # 三字经（只简繁）  # 道德经（只简繁；没开就是空）
    if ANALYTICS.get("live") and "OUT_ROOT" in globals() and os.path.exists(_lf := os.path.join(OUT_ROOT, "data", f"live-{L.code}.json")):  # 道德经、三字经也进“今天有人读了”；本语种没有的书链简体页
        _up = "../" * L.prefix.count("/"); _ex = {k: [v[0], _up + v[1]] for k, v in LIVE_A.get("zh-Hans", {}).items()} if L.code != "zh-Hans" else {}
        _ex.update(LIVE_A.get(L.code, {})); _J = json.load(open(_lf, encoding="utf-8")); _J.setdefault("a", {}).update(_ex)
        json.dump(_J, open(_lf, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    def toc(cs):
        def li(c):
            if c in pubset:
                return f'<li data-c="{c}"><a href="{P}{rel_of(c)}"><em>{c}</em><b>{esc(title_of(c))}</b><span>{esc((field(c, "片里落点")[0] or "").split("；")[0].split(". Today")[0])}</span><i class="heat" hidden><s></s><small></small></i></a></li>'
            t = D["qw"][c]["text"]; tt = WJ_TR.get(c, {}).get(L.code, "") if WJF else ""
            sn = (f'<span>{esc(tt[:90] + ("…" if len(tt) > 90 else ""))}</span>' if tt else f'<span lang="zh-Hans">{esc(t[:40] + ("……" if len(t) > 40 else ""))}</span>')
            return f'<li class="wj"><a href="{href(c)}"><em>{c}</em><b>{esc(ctitle(c))}</b><span><i class="wjtag">{L.t("toc_wj")}</i>{sn}</span></a></li>'
        return '<ol class="toc">' + "".join(li(c) for c in cs) + "</ol>"
    def pcard(p):
        pname, slug, pfull, total = PIAN[p]; done = len(by_pian.get(p, [])); pct = round(done * 100 / total)
        return (f'<a class="pcard" data-p="{p}" href="{P}lunyu/{slug}/"><b>{pname}</b><small>{L.book(p)}</small><span class="bar"><i style="width:{pct}%"></i></span><em>{L.t("covered", done=done, total=total)}</em></a>')

    toc_all = ""
    ALLP = sorted(set(by_pian) | set(D["all_by_pian"]), key=int)
    for p in ALLP:
        pname, slug, pfull, total = PIAN[p]; cs = D["all_by_pian"].get(p) or by_pian[p]
        body = f'''<div class="chhead bk"><div class="wrap">{mcv(P, pfull if L.code.startswith("zh") else "", True)}<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}lunyu/">{L.t("lunyu")}</a></p>
<h1><span class="no">{L.t("book_no", n=p, done=len(by_pian.get(p, [])), total=total)}</span>{L.book(p)}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("book_lead")}</p><div class="mulu">{toc(cs)}</div></main>{BOOK_JS}'''
        ttl = f"《论语·{pname}》逐章原文与读法｜一孔录" if L.code == "zh-Hans" else f"{L.t('lunyu')} · {L.book(p)} | 一孔录 Yikonglu"
        write(f"lunyu/{slug}/index.html", page(L, ttl, L.t("book_lead"), f"lunyu/{slug}/", body)); urls.append(f"{DOMAIN}/{L.prefix}lunyu/{slug}/")
        if p in by_pian: toc_all += f'<h2 class="ph"><a href="{P}lunyu/{slug}/">{L.book(p)}</a></h2>{toc(by_pian[p])}'
    body = f'''<div class="chhead bk"><div class="wrap">{mcv(P, "", True)}<p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a></p><h1><span class="no">{L.t("lunyu_sub")}</span>{L.t("lunyu")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("by_chapter")}</p>{ly_links(L, D, P)}<div class="pcards">{"".join(pcard(p) for p in ALLP)}</div>{toc_all}</main>{BOOK_JS}'''
    write("lunyu/index.html", page(L, ("《论语》逐章原文与读法｜一孔录" if L.code == "zh-Hans" else f"{L.t('lunyu')} | 一孔录 Yikonglu"), L.t("by_chapter"), "lunyu/", body)); urls.append(f"{DOMAIN}/{L.prefix}lunyu/")

    # 书目：各本书一张卡；开讲的链到该书目录，其余是坑位
    n_all = sum(PIAN[p][3] for p in PIAN)
    def bcard(slug, zh, live):
        name = L.t("bk_" + slug); sub = L.t("bk_sub_" + slug)
        zhname = f"《{zh}》" if L.code.startswith("zh") else f"《{zh}》 {name}"
        if live and slug == "sanzijing":
            return f'<a class="bcard" href="{P if (L.code.startswith("zh") or L.code in SZJ_TR) else "/"}sanzijing/"><b>{zhname}</b><small>{sub}</small><span class="bar"><i style="width:100%"></i></span><em>{SZJ_PROG.get(L.code, SZJ_PROG["en"]).format(n=len(SZJ))}</em></a>'
        if live and slug == "daodejing":
            nd = len(D["ddj"]["qw"])
            return f'<a class="bcard" href="{P if (L.code.startswith("zh") or L.code in DDJ_TR) else "/"}daodejing/"><b>{zhname}</b><small>{sub}</small><span class="bar"><i style="width:{round(nd * 100 / 81)}%"></i></span><em>{wjprog(L, nd, 81)}</em></a>'
        if live:
            pct = round(len(pub) * 100 / n_all)
            return f'<a class="bcard" href="{P}lunyu/"><b>{zhname}</b><small>{sub}</small><span class="bar"><i style="width:{pct}%"></i></span><em>{L.t("bk_prog", done=len(pub), total=n_all)}</em></a>'
        kids = "".join(f'<i>《{z}》 {L.t("bk_" + sl2)}</i>' if not L.code.startswith("zh") else f'<i>《{z}》</i>' for sl2, z in BOOK_SUB.get(slug, []))
        return f'<span class="bcard soon" aria-disabled="true"><b>{zhname}</b><small>{sub}</small>{f"<span class=kids>{kids}</span>" if kids else ""}<em>{L.t("soon")}</em></span>'
    def bgroup(gk, bs):
        return f'<h2 class="ph">{L.t(gk)}</h2><div class="bcards">' + "".join(bcard(sl, zh, sl in LB) for sl, zh in bs) + "</div>"
    bcards = "".join(bgroup(gk, bs) for gk, bs in BOOK_GROUPS)
    # 首页（主人 11-07 定）：只放开讲的书，其余收成一行“《道德经》等 N 部筹备中”，完整书目在书目页
    n_soon = sum(1 for _, bs in BOOK_GROUPS for sl, _ in bs if sl not in LB)
    LU = lyui(L); zhL = L.code.startswith("zh")
    def zhushu(home):  # 《论语》主经一格（首页、书架页）
        lk = ([(f"{P}lunyu/xue-er/1.html", LU["go"], " class=go"), (f"{P}lunyu/", LU["toc"], "")] if home else [(f"{P}lunyu/", LU["open"], " class=go")]) \
             + (([(f"{P}nianli/", "《论语》年历", "")] if D["lx"]["nl"] else []) + [(f"{P}zhuanti/keben.html", LU["kb"], ""), (f"{P}duben.html", LU["db"], "")] if home and zhL else [])
        return (f'<div class="zhushu"><a class="cvbig" href="{P}lunyu/" aria-label="{esc(L.t("lunyu"))}"><span class="qb" lang="zh-Hans">论语</span></a><div><h3><a href="{P}lunyu/">{"《" + L.t("lunyu") + "》" if zhL else esc(L.t("lunyu"))}</a></h3>'
                f'<p class="zk">{esc(LU["k"])}</p><p class="zs">{esc(LU["s"].format(n=n_all, d=len(pub)))}</p><p class="zl">' + "".join(f'<a href="{u}"{c}>{esc(x)}</a>' for u, x, c in lk if x) + '</p></div></div>')
    shelfline = (f'<p class="shelfline">{esc(LU["more"])}' + " · ".join(f'<a href="{P if (zhL or (sl == "sanzijing" and L.code in SZJ_TR) or (sl == "daodejing" and L.code in DDJ_TR)) else "/"}{sl}/">{"《" + zh + "》" if zhL else esc(L.t("bk_" + sl))}</a>'
                 for _, bs in BOOK_GROUPS for sl, zh in bs if sl in LB and sl != "lunyu") + f' · <a href="{P}shumu/">{esc(LU["soon"].format(n=n_soon))}</a></p>')
    bcards_home = '<div class="bcards">' + "".join(bcard(sl, zh, True) for _, bs in BOOK_GROUPS for sl, zh in bs if sl in LB) + f'</div><p class="soonline"><a href="{P}shumu/">{L.t("soon_line", n=n_soon)}</a></p>'
    # 书目页做成书架（11-13 主人：书目页用书架式，首页不动）：一格一类，线装书封面＋题签，亮着的能读，其余筹备中
    def tome(slug, zh, live):
        name = L.t("bk_" + slug); sub = L.t("bk_sub_" + slug); zhL = L.code.startswith("zh")
        cap = f"《{zh}》" if zhL else name
        kids = "、".join((f"《{z}》" if zhL else L.t("bk_" + sl2)) for sl2, z in BOOK_SUB.get(slug, []))
        cv = f'<span class="cv"><span class="qian{" l6" if len(zh) >= 6 else (" l5" if len(zh) == 5 else "")}" lang="zh-Hans">{esc(zh)}</span></span>'
        if live:
            if slug == "sanzijing":
                return (f'<a class="tome on" href="{P if (zhL or L.code in SZJ_TR) else "/"}sanzijing/" data-bk="{slug}" data-t="{len(SZJ)}">{cv}<span class="cap"><b>{esc(cap)}</b><small>{esc(sub)}</small>'
                        f'<span class="bar"><i style="width:100%"></i></span><em>{SZJ_PROG.get(L.code, SZJ_PROG["en"]).format(n=len(SZJ))}</em><em class="mine" hidden></em></span></a>')
            if slug == "daodejing": nd, tt, u, key = len(D["ddj"]["qw"]), 81, f'{P if (zhL or L.code in DDJ_TR) else "/"}daodejing/', "bk_prog_wj"
            else: nd, tt, u, key = len(pub), n_all, f"{P}lunyu/", "bk_prog"
            return (f'<a class="tome on" href="{u}" data-bk="{slug}" data-t="{tt}">{cv}<span class="cap"><b>{esc(cap)}</b><small>{esc(sub)}</small>'
                    f'<span class="bar"><i style="width:{round(nd * 100 / tt)}%"></i></span><em>{wjprog(L, nd, tt) if key == "bk_prog_wj" else L.t(key, done=nd, n=nd, total=tt)}</em><em class="mine" hidden></em></span></a>')
        return (f'<span class="tome" aria-disabled="true">{cv}<span class="cap"><b>{esc(cap)}</b><small>{esc(sub)}{"<br>" + esc(kids) if kids else ""}</small>'
                f'<em class="soon">{L.t("soon")}</em></span></span>')
    shelves = "".join(f'<section class="shelf"><h2 class="ph">{L.t(gk)}</h2><div class="shrow">' + "".join(tome(sl, zh, sl in LB) for sl, zh in bs if sl != "lunyu") + "</div></section>" for gk, bs in BOOK_GROUPS if any(sl != "lunyu" for sl, _ in bs))
    CANREAD = {"zh-Hans": "能读的书", "zh-Hant": "能讀的書", "en": "Ready to read", "ja": "いま読める本", "ko": "지금 읽을 수 있는 책", "fr": "Déjà en ligne", "es": "Ya disponibles", "de": "Schon lesbar", "vi": "Sách đã đọc được", "id": "Sudah bisa dibaca", "ru": "Уже можно читать"}
    if L.code in CANREAD:  # 最上面一格放已经能读的书，手机上不用往下翻找（11-13 各语言一致）
        shelves = (f'<section class="shelf"><h2 class="ph">{LU["shelf"] if L.code in LY_UI else CANREAD[L.code]}</h2><div class="shrow">' + "".join(tome(sl, zh, True) for _, bs in BOOK_GROUPS for sl, zh in bs if sl in LB and sl != "lunyu") + "</div></section>") + shelves
    shelves = f'<section class="shelf zsshelf"><h2 class="ph">{LU["h"]}</h2>{zhushu(False)}</section>' + shelves
    MINE = {"zh-Hans": "你读过 {n} 章", "zh-Hant": "你讀過 {n} 章", "en": "You've read {n}", "ja": "{n} 章読了", "ko": "{n}장 읽음", "fr": "{n} lus", "es": "{n} leídos", "de": "{n} gelesen", "vi": "Đã đọc {n} chương", "id": "{n} bab dibaca", "ru": "Прочитано: {n}"}.get(L.code, "")
    shelf_js = ("<script>(function(){try{var S=JSON.parse(localStorage.getItem('yk_xd')||'{}');S=S.b||{}}catch(e){return}"
                "document.querySelectorAll('.tome.on').forEach(function(a){var n=((S[a.dataset.bk]||{}).seen||[]).length,m=a.querySelector('.mine');if(n&&m){m.textContent=" + json.dumps(MINE) + ".replace('{n}',n);m.hidden=false;a.classList.add('read')}})})();</script>") if MINE else ""
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("shumu_sub")}</span>{L.t("shumu_title")}</h1></div></div>
<main class="wrap narrow shumu">{shelves}</main>{shelf_js}'''
    write("shumu/index.html", page(L, f'{L.t("shumu_title")}｜一孔录', L.t("shumu_p"), "shumu/", body)); urls.append(f"{DOMAIN}/{L.prefix}shumu/")
    recent = pub[-6:][::-1]
    # 首页“从最新一章读起”“最新一章”都指向视频已公开的最新一章
    _now = datetime.datetime.now(datetime.timezone.utc)
    _vpub = [c for c in pub if ch2ep[c][1].get("youtube") and (not ch2ep[c][1].get("public_at") or datetime.datetime.fromisoformat(ch2ep[c][1]["public_at"]) <= _now)]
    lc = (_vpub or pub)[-1]; lc_gist = (field(lc, "片里落点")[0] or "")
    def _lcard(c):
        g = field(c, "片里落点")[0] or ""
        return f'<small>{L.t("lunyu")} {c}</small><b>{esc(title_of(c))}</b><blockquote lang="zh-Hans">{esc(yw[c])}</blockquote>{f"<p>{esc(g)}</p>" if g else ""}<em>{L.t("h_read")} →</em>'
    # 已上传、公开时间未到的章：构建时一并写进首页，页面脚本到点自动换上（不必等重建）
    _fut = [c for c in pub[pub.index(lc) + 1:] if ch2ep[c][1].get("youtube") and ch2ep[c][1].get("public_at") and datetime.datetime.fromisoformat(ch2ep[c][1]["public_at"]) > _now]
    lc_js = ("<script>(function(){var L=" + json.dumps([{"t": ch2ep[c][1]["public_at"], "h": P + rel_of(c), "c": _lcard(c)} for c in _fut], ensure_ascii=False).replace("</", "<\\/")
             + ';function f(){var n=Date.now(),x=null;for(var i=0;i<L.length;i++)if(n>=Date.parse(L[i].t))x=L[i];if(!x)return;var b=document.getElementById("lcard");if(b){b.href=x.h;b.innerHTML=x.c}}f();setInterval(f,60000)})();</script>') if _fut else ""
    # 首页主按钮“今日一句”：在视频已公开（或到点公开）的章里随机抽一章；没有脚本时落到最新一章
    # 首页主按钮“今日共读一章”：按北京日期定一章，候选只取北京当天零点前已公开的章（当天到点公开的不进候选，免得一天里换几次），全站同一天同一章；没有脚本时落到最新一章
    def _key(c):  # 每日一句取该章的关键句（同格物卡：章节起点 keys 指定，缺省取首个够四字的句），白话取逐句白话
        ss = split_ju(yw[c]); k = SHARE_KEYS.get(c); kn = 0
        if isinstance(k, int) and 0 < k <= len(ss): kn = k
        elif isinstance(k, str): kn = next((i for i, x in enumerate(ss, 1) if k in x), 0)
        strip_ = lambda t: re.sub(r"^[^，。：；？！]{1,8}(曰|问|对曰|问曰)：", "", t)
        if not kn: kn = next((i for i, x in enumerate(ss, 1) if len(re.sub(r"[^\u3400-\u9fff]", "", strip_(x))) >= 4), 1)
        ZJD_ = D.get("zhuju") or {"zj": {}}; zs = (ZJD_.get("zj", {}).get(c) or {}).get("句", [])
        b = (zs[kn - 1].get("bh") if kn <= len(zs) and isinstance(zs[kn - 1], dict) else "") or ""
        full = D["baihua"].get(c) or ""
        if not b and (len(ss) == 1 or len(full) <= 48): b = full
        return strip_(ss[kn - 1]), b
    def _fkey(c):  # 外文“今日共读”卡：原文短（≤60 字）就整章原文＋整章译文；长的取关键句原文，下面放本章译名（11-09 主人“外文也动”）
        t = (L.ch(c).get("yw") or "").strip()
        if len(re.sub(r"\s", "", yw[c])) <= 60 and t and len(t) <= 260: return {"y": yw[c], "b": t}
        return {"y": _key(c)[0], "b": title_of(c)}
    _rc = [dict({"c": c, "h": P + rel_of(c), "t": ch2ep[c][1].get("public_at") or "", "ti": title_of(c)}, **(dict(zip(("y", "b"), _key(c))) if L.code.startswith("zh") else _fkey(c))) for c in pub if ch2ep[c][1].get("youtube")]
    MY = MEIRI_TXT.get(L.code) or {"h": DONE_TXT.get(L.code, DONE_TXT["en"])["h"].replace("’", "'"), "read": L.t("h_read"), "card": SHARE_TXT.get(L.code, SHARE_TXT["en"])["card"], "plan": ""}  # 今日共读卡（11-09 简繁先上；同晚主人“外文也动”，外文同样，只是没有百日计划）
    LU = lyui(L)
    wk_html = (f'<p class="wk" id="wkl"><span class="wt" data-t="{esc(LU["wk"])}" data-z="{esc(LU["wk0"])}">{esc(LU["wk0"])}</span><span class="dots">' + "<i></i>" * 7 + f'</span>{f"<span class=wn>{esc(LU["cal"])}</span>" if LU["cal"] else ""}</p>'
               '<script>(function(){try{var o=JSON.parse(localStorage.getItem("ykl_wk")||"{}"),d=new Date(Date.now()+288e5),m=new Date(d-((d.getUTCDay()+6)%7)*864e5).toISOString().slice(0,10);if(o.m!==m||!o.a||!o.a.length)return;'
               'var I=document.querySelectorAll("#wkl .dots i");o.a.forEach(function(x){var k=Math.round((Date.parse(x)-Date.parse(m))/864e5);if(I[k])I[k].className="on"});var s=document.querySelector("#wkl .wt");s.textContent=s.getAttribute("data-t").replace("{n}",o.a.length)}catch(e){}})();</script>')  # 本周读了几天：只在读者本机记（章页停满一分钟算一天），不上传
    meiri_html = (f'<section class="meiri big" id="meiri" hidden><p class="mh"><b>{MY["h"]}</b><span class="md"></span></p><blockquote lang="zh-Hans"></blockquote><p class="mb"></p>'
                  f'<p class="ma"><a class="mc" href="#">{MY["read"]} →</a><a class="mk" href="#">{MY["card"]}</a></p>{wk_html}</section>') if MY else ""
    if "OUT_ROOT" in globals():  # 全站“今日《论语》”细条用：各页按同一算法挑同一章
        os.makedirs(os.path.join(OUT_ROOT, "data"), exist_ok=True)
        json.dump([[x["c"], x["h"], x["t"], x["y"]] for x in _rc], open(os.path.join(OUT_ROOT, "data", f"meiri-{L.code}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    meiri_js = ('<script>(function(){var R=' + json.dumps(_rc, ensure_ascii=False).replace("</", "<\\/") + ',W="日一二三四五六";var n=Date.now(),day=Math.floor((n+8*3600e3)/864e5),d0=day*864e5-8*3600e3,C=R.filter(function(x){return !x.t||Date.parse(x.t)<d0});' + ('if(day>=' + str(LX.NL0) + ')return;' if L.code in LX.ZH and D["lx"]["nl"] else '') + 'if(!C.length)return;var x=C[(day*7919)%C.length],M=document.getElementById("meiri");if(!M||!x.y)return;'
                'var bj=new Date(n+8*3600e3);M.querySelector(".md").textContent=' + ('(bj.getUTCMonth()+1)+"月"+bj.getUTCDate()+"日 · 《论语》"+x.c;' if L.code.startswith("zh") else 'bj.toLocaleDateString(' + json.dumps(L.code) + ',{month:"long",day:"numeric",timeZone:"UTC"})+" · "+' + json.dumps(L.t("lunyu")) + '+" "+x.c;') + 'M.querySelector("blockquote").textContent=x.y;M.querySelector(".mb").textContent=x.b||"";'
                'M.querySelector(".mc").href=x.h;M.setAttribute("data-c",x.c);M.querySelector(".mk").href=x.h+"#ka";M.hidden=false})();</script>') if MY else ""
    if MY and L.code in LX.ZH and D["lx"]["nl"]:  # 2027 元旦起首页“今日《论语》”按年历取当天那一课（11-14 主人定）；闰年 2 月 29 日是补读日
        meiri_js += ('<script>(function(){var n=Date.now(),day=Math.floor((n+288e5)/864e5);if(day<' + str(LX.NL0) + ')return;var bj=new Date(n+288e5),dt=(bj.getUTCMonth()+1)+"月"+bj.getUTCDate()+"日",md=(bj.getUTCMonth()+1)+"-"+bj.getUTCDate();'
                     'fetch("/data/nianli-' + L.code + '.json").then(function(r){return r.json()}).then(function(N){var M=document.getElementById("meiri"),x=N[md];if(!M)return;var q=M.querySelector("blockquote"),b=M.querySelector(".mb"),c=M.querySelector(".mc"),k=M.querySelector(".mk");'
                     'if(!x){M.querySelector(".md").textContent=dt+" · 补读日";q.textContent="今天不排新课，前几天落下的课，今天补上。";b.textContent="";c.href="' + P + 'nianli/";k.hidden=true;M.hidden=false;return}'
                     'M.querySelector(".md").textContent=dt+" · 年历第 "+x[0]+" 课 · 《论语》"+x[6];q.textContent=x[3];b.textContent=x[4]+(x[5].length?(x[4]?" · ":"")+"今日加读 "+x[5].map(function(a){return a[0]}).join(" "):"");'
                     'c.href=x[2];k.href=x[2]+"#ka";M.setAttribute("data-c",x[1]);M.hidden=false}).catch(function(){})})();</script>')
    if MY and L.code in LX.ZH and D["lx"]["nl"]:  # 11-14 主人：首页“今日《论语》”现在起按年历取当天一课，模块做成日历样子（有时间感）；一周七天七位领读人轮值（六位原创角色＋Lisa）
        _ht = L.code == "zh-Hant"
        _T = (lambda s: __import__("opencc").OpenCC("s2twp").convert(s)) if _ht else (lambda s: s)
        _lead = [[k, _T(n), _T(RW_LINE[k][0]) if k in RW_LINE else _T(t)] for k, n, t in LEAD_WEEK]
        _y0 = datetime.date.today().year
        _cal = {"jt": {str(y): JIEQI_DAYS[str(y)] for y in range(_y0 - 1, _y0 + 2) if str(y) in JIEQI_DAYS}, "jn": [_T(x) for x in JIEQI_NAMES["zh"]], "hou": [_T(x) for x in QISHIER_HOU], "ld": _lead}
        _wd = "一二三四五六日"
        meiri_html = (f'<section class="meiri big mcal" id="meiri" hidden><div class="mrow"><div class="mcalb" aria-hidden="true"><p class="cm"></p><p class="cd"></p><p class="cw"></p><p class="cl"></p></div>'
                      f'<div class="mtxt"><p class="mh"><b>{MY["h"]}</b></p><p class="mtag"></p><blockquote lang="zh-Hans"></blockquote><p class="mb"></p>'
                      f'<p class="ma"><a class="mc" href="#">{MY["read"]} →</a><a class="mk" href="#">{MY["card"]}</a></p></div><img class="mhalf" alt="" width="300" height="400" hidden></div>'
                      f'<p class="wk" id="wkl"><span class="wt" data-t="{esc(LU["wk"])}" data-z="{esc(LU["wk0"])}">{esc(LU["wk0"])}</span><span class="dots">'
                      + "<i></i>" * 7 + '</span><span class="wn md"></span></p>'
                      + '</section>')
        meiri_js = wk_js_only(wk_html) + ('<script>(function(){var K=' + json.dumps(_cal, ensure_ascii=False).replace("</", "<\\/") + ',HT=' + ("true" if _ht else "false") + ';'
                    'function T(s){return HT?s.replace(/农历/g,"農曆").replace(/后第/g,"後第").replace(/腊/g,"臘").replace(/闰/g,"閏").replace(/节/g,"節").replace(/补读日/g,"補讀日").replace(/马/g,"馬").replace(/鸡/g,"雞").replace(/猪/g,"豬").replace(/龙/g,"龍").replace(/课/g,"課"):s}'
                    'var n=Date.now(),bj=new Date(n+288e5),Y=bj.getUTCFullYear(),m=bj.getUTCMonth()+1,d=bj.getUTCDate(),wd=bj.getUTCDay(),M=document.getElementById("meiri");if(!M)return;'
                    'var dt=new Date(Y,m-1,d),N="一二三四五六七八九十",lu="",fe=[],jq="";'
                    'try{var o={};new Intl.DateTimeFormat("zh-CN-u-ca-chinese",{year:"numeric",month:"numeric",day:"numeric"}).formatToParts(dt).forEach(function(p){o[p.type]=p.value});var ms=(o.month||"").replace(/^闰|bis$/g,"").replace(/月$/,""),CM=["正","二","三","四","五","六","七","八","九","十","十一","十二"],lm=/^\\d+$/.test(ms)?parseInt(ms,10):CM.indexOf(ms)+1,ld=parseInt((o.day||"").replace(/\\D/g,""),10),lp=/闰|bis/.test(o.month||"");'
                    'if(lm&&ld){lu="农历"+(lp?"闰":"")+["正","二","三","四","五","六","七","八","九","十","冬","腊"][lm-1]+"月"+(ld<=10?"初"+N[ld-1]:ld<20?"十"+N[ld-11]:ld===20?"二十":ld<30?"廿"+N[ld-21]:"三十");var LF={"1.1":"春节","1.15":"元宵节","5.5":"端午节","7.7":"七夕","8.15":"中秋节","9.9":"重阳节","12.8":"腊八节"};if(!lp&&LF[lm+"."+ld])fe.push(LF[lm+"."+ld])}}catch(e){}'
                    'var GF=HT?{"1.1":"元旦","4.23":"世界讀書日","9.28":"教師節 · 孔子誕辰"}:{"1.1":"元旦","4.23":"世界读书日","5.1":"劳动节","5.4":"青年节","6.1":"儿童节","9.10":"教师节","9.28":"孔子诞辰","10.1":"国庆节"};if(GF[m+"."+d])fe.unshift(GF[m+"."+d]);'
                    'try{var dd=function(y,i){var s=K.jt[y];return s?s.charCodeAt(i)-48:0},ix=-1,sy=Y,sm,sd;for(var i=23;i>=0;i--){var mo=1+(i>>1),dy=dd(Y,i);if(!dy)break;if(mo<m||(mo===m&&dy<=d)){ix=i;sm=mo;sd=dy;break}}if(ix<0&&dd(Y-1,23)){sy=Y-1;ix=23;sm=12;sd=dd(sy,23)}'
                    'if(ix>=0){var k=Math.round((dt-new Date(sy,sm-1,sd))/864e5),h=Math.min(2,Math.floor(k/5));jq=(k===0?"今日"+K.jn[ix]:K.jn[ix]+"后第 "+k+" 天")+" · "+K.hou[ix*3+h]}}catch(e){}'
                    'var MN=["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"];M.querySelector(".cm").textContent=MN[m-1];M.querySelector(".cd").textContent=d;M.querySelector(".cw").textContent="星期"+"日一二三四五六"[wd];M.querySelector(".cl").textContent=T(lu.replace(/^农历/,""));'
                    'var tg=M.querySelector(".mtag");fe.forEach(function(f){var s=document.createElement("span");s.className="fe";s.textContent=T(f);tg.appendChild(s)});if(jq){var s=document.createElement("span");s.textContent=T(jq);tg.appendChild(s)}'
                    'var li=(wd+6)%7,P=K.ld[li],hf=M.querySelector(".mhalf");hf.src="/assets/lead/"+P[0]+"-half.webp";hf.alt=P[1];hf.hidden=false;'
                    'var I=M.querySelectorAll(".dots i");if(I[li])I[li].classList.add("td");'
                    'fetch("/data/nianli-' + L.code + '.json").then(function(r){return r.json()}).then(function(R){var x=R[m+"-"+d],q=M.querySelector("blockquote"),b=M.querySelector(".mb"),c=M.querySelector(".mc"),kk=M.querySelector(".mk");'
                    'if(!x){M.querySelector(".md").textContent=T("补读日");q.textContent=T("今天不排新课，前几天落下的课，今天补上。");b.textContent="";c.href="' + P + 'nianli/";kk.hidden=true;M.hidden=false;return}'
                    'M.querySelector(".md").textContent=T("年历第 "+x[0]+" 课 / 365 · 《论语》")+x[6];q.textContent=x[3];b.textContent=x[4]+(x[5].length?(x[4]?" · ":"")+T("今日加读 ")+x[5].map(function(a){return a[0]}).join(" "):"");'
                    'c.href=x[2];kk.href=x[2]+"#ka";M.setAttribute("data-c",x[1]);M.hidden=false;try{document.dispatchEvent(new Event("ykmeiri"))}catch(e){}}).catch(function(){})})();</script>')
    FU = (FILL.get(L.code) or {}).get("c") or {}
    if MY and D["lx"]["nl"] and L.code not in LX.ZH and FU and NLTR:  # 11-14 外文首页同步：今日《论语》按年历取课、日历样、七位领读人；今日一句用本语种译文
        if "OUT_ROOT" in globals():
            os.makedirs(os.path.join(OUT_ROOT, "data"), exist_ok=True)
            json.dump({r["md"]: [r["n"], r["c"], href(r["c"]), hant_plain(r["q"]), (NLTR.get(str(r["n"])) or {}).get(L.code, ""), [[a, href(a)] for a in r["add"]], " ".join(r["cs"])] for r in D["lx"]["nl"]},
                      open(os.path.join(OUT_ROOT, "data", f"nianli-{L.code}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        FL_ = FILL[L.code]; LD_ = FL_.get("lead") or {}
        _jn = FL_.get("jq") or JIEQI_NAMES.get(L.code) or JIEQI_NAMES["en"]
        _y0 = datetime.date.today().year
        _u = {"lu": FU["cal_lunar"], "lmd": FU["lunar_md"], "leap": FU["lunar_leap"], "after": FU["cal_after"], "today": FU["cal_today"], "lesson": FU["cal_lesson"], "mkh": FU["cal_makeup_h"], "mkp": FU["cal_makeup_p"], "add": FU["cal_add"],
              "gf": {"1.1": FU["fe_ny"], "4.23": FU["fe_book"], "9.28": FU["fe_kz"]},
              "lf": {"1.1": FU["fe_spring"], "1.15": FU["fe_lantern"], "5.5": FU["fe_duanwu"], "7.7": FU["fe_qixi"], "8.15": FU["fe_mid"], "9.9": FU["fe_chongyang"], "12.8": FU["fe_laba"]}}
        _cal = {"jt": {str(y): JIEQI_DAYS[str(y)] for y in range(_y0 - 1, _y0 + 2) if str(y) in JIEQI_DAYS}, "jn": _jn, "hou": FL_.get("hou") or [], "ld": [[k, (LD_.get(k) or {}).get("name") or n] for k, n, t in LEAD_WEEK], "u": _u}
        meiri_html = (f'<section class="meiri big mcal" id="meiri" hidden><div class="mrow"><div class="mcalb" aria-hidden="true"><p class="cm"></p><p class="cd"></p><p class="cw"></p><p class="cl"></p></div>'
                      f'<div class="mtxt"><p class="mh"><b>{esc(L.t("cal_h"))}</b></p><p class="mtag"></p><blockquote lang="zh-Hans"></blockquote><p class="mb"></p>'
                      f'<p class="ma"><a class="mc" href="#">{MY["read"]} →</a><a class="mk" href="#">{MY["card"]}</a></p></div><img class="mhalf" alt="" width="300" height="400" hidden></div>'
                      f'<p class="wk" id="wkl"><span class="wt" data-t="{esc(LU["wk"])}" data-z="{esc(LU["wk0"])}">{esc(LU["wk0"])}</span><span class="dots">'
                      + "<i></i>" * 7 + '</span><span class="wn md"></span></p></section>')
        meiri_js = wk_js_only(wk_html) + ('<script>(function(){var K=' + json.dumps(_cal, ensure_ascii=False).replace("</", "<\\/") + ',U=K.u,LC=' + json.dumps(L.code) + ';'
                    'var n=Date.now(),bj=new Date(n+288e5),Y=bj.getUTCFullYear(),m=bj.getUTCMonth()+1,d=bj.getUTCDate(),wd=bj.getUTCDay(),M=document.getElementById("meiri");if(!M)return;'
                    'var dt=new Date(Y,m-1,d),lu="",fe=[],jq="";'
                    'try{var o={};new Intl.DateTimeFormat("zh-CN-u-ca-chinese",{year:"numeric",month:"numeric",day:"numeric"}).formatToParts(dt).forEach(function(p){o[p.type]=p.value});var ms=(o.month||"").replace(/^闰|bis$/g,"").replace(/月$/,""),CM=["正","二","三","四","五","六","七","八","九","十","十一","十二"],lm=/^\\d+$/.test(ms)?parseInt(ms,10):CM.indexOf(ms)+1,ld=parseInt((o.day||"").replace(/\\D/g,""),10),lp=/闰|bis/.test(o.month||"");'
                    'if(lm&&ld){lu=(lp?U.leap:"")+U.lmd.replace("{m}",lm).replace("{d}",ld);if(!lp&&U.lf[lm+"."+ld])fe.push(U.lf[lm+"."+ld])}}catch(e){}'
                    'if(U.gf[m+"."+d])fe.unshift(U.gf[m+"."+d]);'
                    'try{var dd=function(y,i){var s=K.jt[y];return s?s.charCodeAt(i)-48:0},ix=-1,sy=Y,sm,sd;for(var i=23;i>=0;i--){var mo=1+(i>>1),dy=dd(Y,i);if(!dy)break;if(mo<m||(mo===m&&dy<=d)){ix=i;sm=mo;sd=dy;break}}if(ix<0&&dd(Y-1,23)){sy=Y-1;ix=23;sm=12;sd=dd(sy,23)}'
                    'if(ix>=0){var k=Math.round((dt-new Date(sy,sm-1,sd))/864e5),h=Math.min(2,Math.floor(k/5));jq=(k===0?U.today.replace("{t}",K.jn[ix]):U.after.replace("{t}",K.jn[ix]).replace("{k}",k))+(K.hou.length?" · "+K.hou[ix*3+h]:"")}}catch(e){}'
                    'var mn="",wn="";try{mn=new Date(Date.UTC(2026,m-1,15)).toLocaleDateString(LC,{month:"long",timeZone:"UTC"});wn=dt.toLocaleDateString(LC,{weekday:"long"})}catch(e){}'
                    'M.querySelector(".cm").textContent=mn;M.querySelector(".cd").textContent=d;M.querySelector(".cw").textContent=wn;M.querySelector(".cl").textContent=lu?U.lu+"\\n"+lu:"";'
                    'var tg=M.querySelector(".mtag");fe.forEach(function(f){var s=document.createElement("span");s.className="fe";s.textContent=f;tg.appendChild(s)});if(jq){var s=document.createElement("span");s.textContent=jq;tg.appendChild(s)}'
                    'var li=(wd+6)%7,P=K.ld[li],hf=M.querySelector(".mhalf");hf.src="/assets/lead/"+P[0]+"-half.webp";hf.alt=P[1];hf.hidden=false;'
                    'var I=M.querySelectorAll(".dots i");if(I[li])I[li].classList.add("td");'
                    'fetch("/data/nianli-' + L.code + '.json").then(function(r){return r.json()}).then(function(R){var x=R[m+"-"+d],q=M.querySelector("blockquote"),b=M.querySelector(".mb"),c=M.querySelector(".mc"),kk=M.querySelector(".mk");'
                    'if(!x){M.querySelector(".md").textContent=U.mkh;q.textContent=U.mkp;q.lang=LC;b.textContent="";c.href="/nianli/";kk.hidden=true;M.hidden=false;return}'
                    'M.querySelector(".md").textContent=U.lesson.replace("{n}",x[0]).replace("{c}",x[6]);q.textContent=x[3];b.textContent=x[4]+(x[5].length?(x[4]?" · ":"")+U.add+" "+x[5].map(function(a){return a[0]}).join(" "):"");'
                    'c.href=x[2];kk.href=x[2]+"#ka";M.setAttribute("data-c",x[1]);M.hidden=false;try{document.dispatchEvent(new Event("ykmeiri"))}catch(e){}}).catch(function(){})})();</script>')
    home = f'''<section class="hero slim"><picture><source media="(max-width:700px)" srcset="/assets/hero-m.jpg?v={HERO_V}" width="1080" height="745"><img src="/assets/hero-w.jpg?v={HERO_V}" alt="{"一孔录原创角色同坐长桌读《论语》" if L.code.startswith("zh") else esc(L.t("hero_alt"))}" width="1920" height="790"></picture>
<div class="herotext"><h1>一孔录<small>{L.t("tagline")}</small></h1></div></section>
<main class="home">
<section class="intro wrap narrow">
{'<p class="steps" id="steps" hidden></p>' if ANALYTICS.get("live") else ""}
{meiri_html}{meiri_js}
<form class="sbox" action="{P}search.html"><input name="q" placeholder="{esc(L.t("search_ph"))}"><button>{L.t("nav_search")}</button></form>
</section>
<section class="wrap narrow"><h2 class="ph">{L.t("h_latest")}</h2>
<a class="latest" id="lcard" href="{P}{rel_of(lc)}">{_lcard(lc)}</a>{lc_js}</section>
{f'<section class="wrap narrow topju" id="topju" hidden><h2 class="ph">{DONE_TXT.get(L.code, DONE_TXT["en"])["topju"]}</h2><blockquote lang="zh-Hans"></blockquote><p><a href="{P}"></a></p></section>' if ANALYTICS.get("live") else ""}
<section class="wrap narrow" id="remen"><h2 class="ph">{DONE_TXT.get(L.code, DONE_TXT["en"])["hot"]}</h2>{toc(recent[1:])}</section>
<section class="wrap narrow">{cta_html(L, P)}</section>
<section class="wrap narrow shumu-home"><h2 class="ph"><a href="{P}lunyu/">{LU["h"]}</a></h2>{zhushu(True)}{shelfline}</section>
<section class="wrap narrow deephome"><h2 class="ph">{L.t("h_deep_h")}</h2><p class="motto2">{L.t("h_deep_p")}</p></section>
<section class="pillars wrap">
<div><i>原</i><b>{L.t("p1t")}</b><p>{L.t("p1")}</p></div>
<div><i>注</i><b>{L.t("p2t")}</b><p>{L.t("p2")}</p></div>
<div><i>勘</i><b>{L.t("p3t")}</b><p>{L.t("p3")}</p></div>
</section>
<section class="wrap"><div class="tools t3 t2"><a href="{P}zhuanti/"><b>{L.t("zt_title")}</b><span>{L.t("t_zt")}</span></a><a href="{P}kaifang.html"><b>{L.t("dt_title")}</b><span>{L.t("t_dt")}</span></a></div>
{yxl_line(L, D, P) if L.code.startswith("zh") else ""}
<p class="cta"><a class="btn ghost" href="{P}kanwu.html">{L.t("btn_errata")}</a><a class="btn ghost" href="{P}fangfa.html">{lang_tab(FANGFA, L.code)["link"]}</a></p></section>
</main>'''
    write("index.html", page(L, (f"一孔录｜{TAGLINE}" if L.code == "zh-Hans" else f"一孔录 Yikonglu | {L.t('tagline')}"), L.t("intro"), "", home,
          {"@context": "https://schema.org", "@type": "Organization", "name": "一孔录", "alternateName": "Yikonglu", "url": DOMAIN, "logo": f"{DOMAIN}/assets/seal-180.png", "sameAs": SAME_AS + [u for _, u in PLAT_LINKS if u not in SAME_AS]}, "pg-home"))
    urls.insert(0, f"{DOMAIN}/{L.prefix}")
    about = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("tagline")}</span>{L.t("about_title")}</h1></div></div>
<main class="wrap narrow prose"><p class="about-def">{L.t("about_def")}</p><p>{L.t("about_p")}</p>
<h2>{L.t("about_h1")}</h2><p>{L.t("about_site").replace('href="kanwu.html"', f'href="{P}kanwu.html"').replace('href="errata.html"', f'href="{P}kanwu.html"')}</p>
<h2>{L.t("about_h2")}</h2><ul><li>{L.t("about_c1")}</li><li>{L.t("about_c2")}</li><li>{L.t("about_c3")}</li></ul>
<h2>{L.t("about_h3")}</h2><p>{L.t("about_where")}</p>
<h2 id="zhuanzai">{L.t("about_h4")}</h2><ul><li>{L.t("about_r1")}</li><li>{L.t("about_r2")}</li><li>{L.t("about_r3")}</li><li>{L.t("about_r4")}</li><li>{L.t("about_r5", p=P)}</li></ul><p class="mailp">{MAIL}</p><p class="outl"><a class="btn yt" href="https://www.youtube.com/@yikonglu?sub_confirmation=1" target="_blank" rel="noopener">▶ YouTube</a> <a class="btn ghost" href="https://space.bilibili.com/18385461" target="_blank" rel="noopener">Bilibili</a></p></main>'''
    if L.code.startswith("zh"): about = about_zh(L, D, P)  # 11-09 主人：关于页并入“一孔是谁”，一孔自述；外文仍用旧版
    W = lang_tab(WEN, L.code)  # 问一孔（并进关于页，11-14 主人）：按钮由脚本拼出邮箱，源码不露明文
    wen_sec = (f'<section class="wen" id="wen"><h2>{W["title"]}</h2><p>{W["p"]}</p><p><a class="btn" id="wenbtn" href="#wen">{W["btn"]}</a></p><p class="note">{W["only"]}</p></section>'
               '<script>(function(){var a=document.getElementById("wenbtn"),u=["yikonglu","99"].join(""),d=["gmail","com"].join(".");a.href="mai"+"lto:"+u+String.fromCharCode(64)+d+"?subject="+encodeURIComponent("\\u95ee\\u4e00\\u5b54\\uff1a");})();</script>')
    i = about.rfind("</main>")
    about = about[:i] + wen_sec + about[i:] if i >= 0 else about + wen_sec
    write("about.html", page(L, L.t("about_title"), L.t("about_p")[:120], "about.html", about)); urls.append(f"{DOMAIN}/{L.prefix}about.html")
    _, ys_t, ys_sub, ys_items, ys_q = PRIVACY.get(L.code, PRIVACY["en"])
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{ys_sub}</span>{ys_t}</h1></div></div>
<main class="wrap narrow prose"><ul>{"".join(f"<li>{esc(x)}</li>" for x in ys_items)}</ul><p class="mailp">{ys_q}{MAIL}</p><p class="note">{today}</p></main>'''
    write("yinsi.html", page(L, f"{ys_t}｜一孔录", ys_sub, "yinsi.html", body)); urls.append(f"{DOMAIN}/{L.prefix}yinsi.html")

    if kw:
        # 勘误条目（11-13 主人：表格太宽、格子太窄，手机看不了）：改成一条一张卡，电脑上“原来/改为”左右并排，手机上上下排
        kcards = "".join(f'<li class="kwc"><p class="kwm"><span class="kwd">{esc(r[0])}</span><span class="kwe">{esc(r[1])} {esc(r[2])}</span><span class="kwt">{esc(r[3])}</span><span class="who">{esc(r[7])}</span></p>'
                         f'<div class="kwx"><p class="kwo"><small>原来</small><span>{esc(r[4])}</span></p><p class="kwn"><small>改为</small><span>{esc(r[5])}</span></p></div>'
                         + (f'<p class="kwy"><small>依据</small>{esc(r[6])}</p>' if r[6] else "") + "</li>" for r in reversed(kw))
        ktable = f'<ol class="kwcards" lang="zh-Hans">{kcards}</ol>'
    else:
        ktable = f'<p class="empty">{L.t("errata_empty")}</p>'
    stats = ""
    if kw:
        from collections import Counter
        cats = Counter(r[3] for r in kw); readers = [r for r in kw if r[7] != "一孔录自查"]
        stats = '<p class="kwstats">' + esc(L.t("kw_stats", n=len(kw), cats="、".join(f"{k} {v}" for k, v in cats.most_common()), m=len(readers))) + "</p>"
    names = list(dict.fromkeys(r[7] for r in sorted(kw, key=lambda r: r[0]) if r[7] != "一孔录自查"))
    thanks = f'<h2>{L.t("thanks_h")}</h2>' + (f'<p>{L.t("thanks_p")}</p><p class="thanks">' + "".join(f"<span>{esc(n)}</span>" for n in names) + "</p>" if names else f'<p class="empty">{L.t("thanks_none")}</p>')
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("errata_sub")}</span>{L.t("errata_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("errata_p1")}</p><p>{L.t("errata_p2")}</p><p class="mailp">{MAIL}<small>{L.t("mail_note")}</small></p>{"<p class=note>" + L.t("kw_note") + "</p>" if L.t("kw_note") else ""}{stats}{ktable}{thanks}</main>'''
    write("kanwu.html", page(L, f'{L.t("errata_title")}｜一孔录', L.t("errata_p1"), "kanwu.html", body)); urls.append(f"{DOMAIN}/{L.prefix}kanwu.html")
    write("search.json", json.dumps(search_idx, ensure_ascii=False))
    # 检索页（11-13 主人：简洁，但带点再来的理由）：框下几个可点的词；没在搜时，下面放今日共读、最近新讲的章、上次读到哪
    s_extra = s_more = ""
    if True:  # 11-13 起今日共读、最近新讲、上次读到各语种都有；可点词是中文词，只放简繁
        zhS = L.code.startswith("zh")
        SW = (lambda x: x) if L.code == "zh-Hans" else __import__("opencc").OpenCC("s2twp").convert if L.code == "zh-Hant" else (lambda x: {"最近新讲的章": L.t("s_new"), "订阅更新": L.t("s_feed"), "上次读到": L.t("s_last")}.get(x, x))
        chips = ["鸟数飞", "主一无适", "孝弟", "巧言令色", "君子不器", "温故知新", "朝闻道"]
        if zhS: s_extra = '<p class="schips">' + SW("试试") + "：" + "".join(f'<a href="?q={esc(SW(w))}">{esc(SW(w))}</a>' for w in chips) + "</p>"
        _new = [c for c in (_vpub or pub)][-4:][::-1]
        def _d(c):
            t = ch2ep[c][1].get("public_at") or ""
            return f"{int(t[5:7])}-{int(t[8:10])}" if len(t) >= 10 else ""
        newl = "".join(f'<li><a href="{P}{rel_of(c)}"><em>{c}</em><b>{esc(title_of(c))}</b><small>{_d(c)}</small></a></li>' for c in _new)
        s_more = (f'<div class="smore">{meiri_html}<section class="snew"><h2>{SW("最近新讲的章")}<a href="{P}feed.xml">{SW("订阅更新")}</a></h2><ol>{newl}</ol></section>'
                  f'<p class="slast" id="slast" hidden></p></div>'
                  '<script>(function(){try{var L=((JSON.parse(localStorage.getItem("yk_xd")||"{}").b||{}).lunyu||{}).last}catch(e){return}if(!L||!L.p)return;var p=document.getElementById("slast");'
                  'p.innerHTML=' + json.dumps(SW("上次读到") + ("：" if zhS or L.code == "ja" else ": ")) + '+\'<a href="\'+L.p+\'">\'+(L.no||L.c).replace(/[<>&]/g,"")+(L.ti?" "+L.ti.replace(/[<>&]/g,""):"")+\' →</a>\';p.hidden=false})();'
                  '(function(){var q=document.getElementById("q"),M=document.querySelector(".smore");if(!q||!M)return;function t(){M.hidden=!!new URLSearchParams(location.search).get("q")}t();window.addEventListener("popstate",t);document.querySelector(".sbox").addEventListener("submit",function(){setTimeout(function(){M.hidden=!!q.value.trim()},0)})})();</script>')
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("search_sub")}</span>{L.t("search_title")}</h1></div></div>
<main class="wrap narrow"><form class="sbox" onsubmit="go();return false"><input id="q" placeholder="{esc(L.t("search_ph2"))}"><button>{L.t("nav_search")}</button></form>{s_extra}<div id="res"></div>{s_more}</main>{meiri_js if s_more else ""}
<script>
let D=null;const q=document.getElementById('q'),R=document.getElementById('res');
const E=s=>s.replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
function cut(s,k){{const i=s.toLowerCase().indexOf(k.toLowerCase());if(i<0)return E(s.slice(0,60));const a=Math.max(0,i-24);return(a?'…':'')+E(s.slice(a,i))+'<mark>'+E(k)+'</mark>'+E(s.slice(i+k.length,i+k.length+36))+'…'}}
async function go(){{const k=q.value.trim();if(!k){{R.innerHTML='';return}}
if(!D){{try{{D=await (await fetch('{P}search.json')).json()}}catch(e){{R.textContent='…';return}}}}
history.replaceState(null,'','?q='+encodeURIComponent(k));
const kl=k.toLowerCase(),hit=D.filter(d=>(d.y+d.t+d.x).toLowerCase().includes(kl));
R.innerHTML=hit.length?'<p class="lead">'+{json.dumps(L.t("search_n", n="N"))}.replace('N',hit.length)+'</p><ol class="toc">'+hit.map(d=>'<li><a href="'+d.u+'"><em>'+d.c+'</em><b>'+E(d.t)+'</b><span>'+cut(d.y.toLowerCase().includes(kl)?d.y:(d.x.toLowerCase().includes(kl)?d.x:d.t),k)+'</span></a></li>').join('')+'</ol>':{json.dumps("<p class=empty>" + L.t("search_none") + "</p>")}}}
const p=new URLSearchParams(location.search).get('q');if(p){{q.value=p;go()}}
</script>'''
    write("search.html", page(L, f'{L.t("search_title")}｜一孔录', L.t("search_sub"), "search.html", body))
    if L.code == "zh-Hans":  # GitHub Pages 只认根目录 404.html
        en = EXTRA_UI["en"]
        body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">404</span>{L.t("nf_h")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("nf_p")}</p><p class="lead" lang="en">{en["nf_h"]}. {en["nf_p"]}</p>
<form class="sbox" action="/search.html"><input name="q" placeholder="{esc(L.t("search_ph"))}"><button>{L.t("nav_search")}</button></form>
<p class="cta"><a class="btn" href="/shumu/">{L.t("btn_books")}</a><a class="btn ghost" href="/">yikonglu.com</a></p><h2 class="ph">{L.t("recent")}</h2>{toc(recent)}</main>'''
        write("404.html", page(L, f'{L.t("nf_h")}｜一孔录', L.t("nf_p"), "404.html", body, head_extra='<meta name="robots" content="noindex">' + SHORT_404_JS))
    # 支持一孔录（赞助）
    kofi = SUPPORT.get("kofi", "").strip()
    kbtn = f'<p><a class="btn" href="{esc(kofi)}" target="_blank" rel="noopener">{L.t("zc_kofi")}</a></p>' if kofi else f'<p class="note">{L.t("zc_soon")}</p>'
    order = [f"<p>{L.t('zc_wx')}</p>", kbtn] if L.code == "zh-Hans" else [kbtn, f"<p>{L.t('zc_wx')}</p>"]
    u = SUPPORT.get("usdt") or {}
    if u.get("address") and L.code != "zh-Hans":  # 加密货币只放外文和繁体页，不放面向大陆的简体页
        order.insert(1, f'<h2>{L.t("zc_usdt")}</h2><p class="usdt"><code>{esc(u["address"])}</code><button class="cp2" onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent);this.textContent=\'{L.t("copied")}\'">{L.t("copy")}</button></p><p class="note">{esc(L.t("zc_usdt_net", n=u.get("network", "")))}</p>')
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("zc_sub")}</span>{L.t("zc_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("zc_p")}</p>{"".join(order)}</main>'''
    write("zhichi.html", page(L, f'{L.t("zc_title")}｜一孔录', L.t("zc_sub"), "zhichi.html", body)); urls.append(f"{DOMAIN}/{L.prefix}zhichi.html")
    urls += SY.build(L, write, page, ANALYTICS.get("live"), DOMAIN)  # 一孔书院筹备页（11-09）
    # 核验方法页（/fangfa.html）
    F = lang_tab(FANGFA, L.code)
    try: DC = json.load(open(DRAFT_FILE, encoding="utf-8"))
    except Exception: DC = None
    ul = lambda xs: "<ul>" + "".join(f"<li>{x.replace('{p}', P)}</li>" for x in xs) + "</ul>"
    tbl = '<table><thead><tr>' + "".join(f"<th>{h}</th>" for h in F["th"]) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in F["rows"]) + "</tbody></table>"
    s5 = f'<p>{F["s5p"].replace("{p}", P)}</p>'
    if "bth" in F:  # 11-14 主人：公开的数字不必按章、按集列，以书为单位算
        _now = datetime.datetime.now(datetime.timezone.utc)
        _dc = {}
        for r in (DC or {}).get("rows", []):
            bk = (r.get("first") or "论语-").split("-")[0]; t = _dc.setdefault(bk, [0, 0, 0]); t[0] += 1; t[1] += r["segments"]; t[2] += r["changed"]
        _ly_vid = {D["ch2ep"][c][0] for c in pub if c in D["ch2ep"] and D["ch2ep"][c][1].get("youtube") and (not D["ch2ep"][c][1].get("public_at") or datetime.datetime.fromisoformat(D["ch2ep"][c][1]["public_at"]) <= _now)}
        _ddj_v = [c for c in range(1, 82) if ddj_has_vid(c)]
        BK = [("论语", "lunyu/", sum(PIAN[p][3] for p in PIAN), F["u_zhang"], len(pages_avail), len(pub), len(_ly_vid), None),
              ("道德经", "daodejing/", 81, F["u_zhang"], len(json.load(open(os.path.join(HERE, "ddj_pages.json"), encoding="utf-8"))), len(_ddj_v), len({DDJ_EPS[str(c)].get("youtube") for c in _ddj_v}), len(DDJ_LYHJ)),
              ("三字经", "sanzijing/", len(SZJ), F["u_jiang"], len(SZJ_JL["pages"]), 0, 0, len(SZJ_LYHJ))]
        def _chg(bk):
            t = _dc.get(bk)
            return F["chg"].format(e=t[0], s=t[1], c=t[2], r=round(100 * t[2] / t[1], 1)) if t and t[1] else F["chg0"]
        _rows = [[f"{n}{un}" for b, u, n, un, pg, done, nv, hj in BK], [f"{pg}{F['u_ye']}" for b, u, n, un, pg, done, nv, hj in BK],
                 [f"{done}{un}" for b, u, n, un, pg, done, nv, hj in BK], [f"{nv}{F['u_ji']}" for b, u, n, un, pg, done, nv, hj in BK],
                 [F["lyhj_main"] if hj is None else F["lyhj"].format(n=hj) for b, u, n, un, pg, done, nv, hj in BK], [_chg(b) for b, *_ in BK]]
        s5 += ('<table class="num bybook"><thead><tr><th></th>' + "".join(f'<th><a href="{P if (L.code.startswith("zh") or u == "lunyu/" or (u == "daodejing/" and L.code in DDJ_FL) or (u == "sanzijing/" and L.code in SZJ_FL)) else "/"}{u}">{F.get("bn", [x[0] for x in BK])[i]}</a></th>' for i, (b, u, *_) in enumerate(BK)) + "</tr></thead><tbody>"
               + "".join(f'<tr><th scope="row">{h}</th>' + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for h, r in zip(F["bth"], _rows))
               + "</tbody></table>")
        if DC: s5 += f'<p><small>{F["s5c"].format(d=DC.get("updated", ""))}</small></p>'
    elif DC and DC.get("rows"):
        s5 += f'<p>{F["s5c"].format(n=DC["episodes"], s=DC["segments"], c=DC["changed"], r=DC["ratio"], d=DC["updated"])}</p>'
        def eplink(ep):
            ch = (EPIS.get(ep) or {}).get("chapters") or []
            if not ch: return esc(ep)
            pn, cn = ch[0].split("."); return f'<a href="{P}lunyu/{PIAN[pn][1]}/{cn}.html">{esc(ep)}</a>'
        s5 += '<table class="num"><thead><tr>' + "".join(f"<th>{h}</th>" for h in F["cth"]) + "</tr></thead><tbody>" + "".join(f'<tr><td>{eplink(r["ep"])}</td><td>{r["segments"]}</td><td>{r["changed"]}</td><td>{round(100 * r["changed"] / r["segments"], 1) if r["segments"] else 0}%</td></tr>' for r in DC["rows"]) + "</tbody></table>"
    logs = "".join(f"<li>{a} {b}</li>" for a, b in F["logs"])
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{F["sub"]}</span>{F["title"]}</h1></div></div>
<main class="wrap narrow prose"><p>{F["intro"]}</p><h2>{F["s1h"]}</h2>{ul(F["s1"])}<h2>{F["s2h"]}</h2><ol>{"".join(f"<li>{x.replace('{p}', P)}</li>" for x in F["s2"])}</ol>
<h2>{F["s3h"]}</h2><p>{F["s3p"]}</p>{tbl}<p>{F["s3n"]}</p><h2>{F["s4h"]}</h2>{ul(F["s4"])}<h2>{F["s5h"]}</h2>{s5}<h2>{F["s6h"]}</h2><p>{F["s6"].replace("{p}", P)}</p><h3>{F["log"]}</h3><ul>{logs}</ul></main>'''
    write("fangfa.html", page(L, f'{F["title"]}｜一孔录', F["sub"], "fangfa.html", body)); urls.append(f"{DOMAIN}/{L.prefix}fangfa.html")
    # 11-14 主人：问一孔并进关于页（about.html#wen），旧 /wen.html 跳过去（视频简介里写过“官网点问一孔”）
    write("wen.html", redirect_page(L, f"{L.prefix}about.html", "#wen", lang_tab(WEN, L.code)["title"]))
    # 免费读本（PDF 放 tools/root/duben/，原样拷到站点 /duben/）
    # 主人 11-08：读本分两种（成人逐字读本／亲子讲读本），每种写明给谁、怎么用；书架式，封面图为主（cover-<f>[-hant].jpg，A5 竖比例）
    # 每本：(标题键或文字, 说明键或文字, 文件名, 有无繁体)
    DB_KINDS = [("db_k_cj", "db_k_cj_who", "db_k_cj_how", [("db_cj", "db_cj_meta", "lunyu-chongjian", True)])] if os.path.exists(os.path.join(HERE, "root", "duben", "lunyu-chongjian.pdf")) else []  # 11-14 主人“过”：《论语》智器重建本排最前，学而篇逐字读本留在下面
    # 11-14 主人：学而篇逐字读本退役（全书智器重建本已覆盖），旧 /duben/lunyu-xueer*.pdf 由 404 页跳到智器重建本
    if os.path.exists(os.path.join(HERE, "root", "duben", "sanzijing-fuqin.pdf")):  # 三字经父亲讲义（主人 11-08 定免费放出）
        DB_KINDS.append(("db_k_kids", "db_k_kids_who", "db_k_kids_how", [("db_szj", "db_szj_meta", "sanzijing-fuqin", False)]))
    hz = "-hant" if L.code == "zh-Hant" else ""
    XL = {"en": "English", "ja": "日本語"}  # 11-14 智器重建本出了英日版：英日站书架以本语种 PDF 为主，其余语种多两个按钮
    def db_item(n, m, f, hant):
        xl = [k for k in XL if os.path.exists(os.path.join(HERE, "root", "duben", f"{f}-{k}.pdf"))]
        if L.code in xl:
            return (f'<li><a class="dbcover" href="/duben/{f}-{L.code}.pdf" download><img src="/duben/cover-{f}-{L.code}.jpg" alt="{L.t(n)}" width="240" height="340" loading="lazy"></a>'
                    f'<b>{L.t(n)}</b><span class="note">{L.t(m)}</span><span class="dbbtns"><a class="btn" href="/duben/{f}-{L.code}.pdf" download>{XL[L.code]} PDF</a>'
                    f'<a class="btn ghost" href="/duben/{f}.pdf" download>{L.t("db_hans")} PDF</a><a class="btn ghost" href="/duben/{f}-hant.pdf" download>{L.t("db_hant")} PDF</a></span></li>')
        xb = "".join(f'<a class="btn ghost" href="/duben/{f}-{k}.pdf" download lang="{k}">{XL[k]} PDF</a>' for k in xl)
        cf = f + (hz if hant else "")
        return (f'<li><a class="dbcover" href="/duben/{cf}.pdf" download><img src="/duben/cover-{cf}.jpg" alt="{L.t(n)}" width="240" height="340" loading="lazy"></a>'
                f'<b>{L.t(n)}</b><span class="note">{L.t(m)}</span><span class="dbbtns"><a class="btn" href="/duben/{f}.pdf" download>{L.t("db_hans") if hant else ("下载" if L.code.startswith("zh") else "Download")}{" PDF" if hant else ""}</a>'
                + (f'<a class="btn ghost" href="/duben/{f}-hant.pdf" download>{L.t("db_hant")} PDF</a>' if hant else "") + xb + '</span></li>')
    rows = "".join(f'<section class="dbkind"><h2 class="ph">{L.t(kt)}</h2><p class="dbwho"><b>{L.t("db_who")}</b>{L.t(kw)}</p><p class="dbwho"><b>{L.t("db_how")}</b>{L.t(kh)}</p>'
                   f'<ul class="duben shelf">{"".join(db_item(*it) for it in items)}</ul></section>' for kt, kw, kh, items in DB_KINDS)
    wx = ""  # 主人 11-08：删“公众号回复读本领取”——到公众号还是回这条链接，绕圈
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("db_sub")}</span>{L.t("db_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("db_p")}</p>{rows}{wx}<p class="note">{L.t("db_note")} <a href="{P}kanwu.html">{L.t("nav_errata")}</a></p></main>'''
    write("duben.html", page(L, f'{L.t("db_title")}｜一孔录', L.t("db_sub"), "duben.html", body)); urls.append(f"{DOMAIN}/{L.prefix}duben.html")
    # 读本总页地址固定为 /duben.html（11-08 发布线程定，各平台简介指这里）；/duben/ 只做跳转，免得有人敲成目录 404
    write("duben/index.html", f'<!doctype html><meta charset="utf-8"><title>{L.t("db_title")}</title><link rel="canonical" href="{DOMAIN}/{L.prefix}duben.html"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url=/{L.prefix}duben.html"><a href="/{L.prefix}duben.html">{L.t("db_title")}</a>')
    # 版本与许可
    cards = ""
    for aid, name, rows in BANBEN:
        cards += f'<section class="bbcard" id="{aid}"><h2>{esc(name)}</h2><dl lang="zh-Hans">' + "".join(f"<dt>{L.t(k)}</dt><dd>{v}</dd>" for k, v in rows) + "</dl></section>"
    body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}shumu/">{L.t("nav_books")}</a> › <a href="{P}lunyu/">{L.t("lunyu")}</a></p><h1><span class="no">{L.t("bb_sub")}</span>{L.t("bb_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("bb_p")}</p>{cards}</main>'''
    write("lunyu/banben/index.html", page(L, f'《论语》{L.t("bb_title")}｜一孔录' if L.code.startswith("zh") else f'{L.t("bb_title")}｜一孔录', L.t("bb_sub"), "lunyu/banben/", body)); urls.append(f"{DOMAIN}/{L.prefix}lunyu/banben/")
    write("banben/index.html", redirect_page(L, f"{L.prefix}lunyu/banben/", "", L.t("bb_title")))  # 11-14 主人：版本说明只讲《论语》，并进论语书里；旧网址跳转
    # 专题：一专题一页，页内按书分段（现在只有论语有章；其余书上网后自动长出一段）
    zlist = ""
    tx = lambda c: yw[c] if c in pubset else D["qw"][c]["text"]
    allc = sorted(pubset | set(D["qw"]), key=lambda c: tuple(map(int, c.split("."))))
    book_order = [sl for _, bs in BOOK_GROUPS for sl, _ in bs] + [sl for v in BOOK_SUB.values() for sl, _ in v]
    def zt_items(terms, hit):
        def mark(t):
            t = esc(t)
            for w in terms: t = t.replace(esc(w), f"<mark>{esc(w)}</mark>")
            return t
        return "".join(f'<li data-c="{c}"{"" if c in pubset else " class=wj"}><a href="{href(c)}"><em>{c}</em><b>{esc(ctitle(c))}</b>{"" if c in pubset else "<i class=wjtag>" + L.t("toc_wj") + "</i>"}</a><p class="zy" lang="zh-Hans">{mark(tx(c))}</p>'
                       + (f'<p class="zd">{esc(field(c, "片里落点")[0])}</p>' if c in pubset and field(c, "片里落点")[0] else "") + "</li>" for c in hit)
    # 专题闯关（11-13 主人：专题页结合游戏任务）：一关一个字，读过本关一章点亮，章章读过通关；进度只看本机读过的章（yk_xd），只在简繁页
    QUEST = True  # 11-13 起各语种都开（主人：各语言功能尽量一致）
    QT = QUEST_TXT.get(L.code, QUEST_TXT["en"])
    _qo = ["xue", "xiao", "you", "xin", "li", "le", "shi", "junzi", "ren", "zheng", "ming", "tianming", "dao", "xin2", "xing"]
    QORD = [x for x in _qo if any(t["slug"] == x for t in D["zhuanti"])] + [t["slug"] for t in D["zhuanti"] if t["slug"] not in _qo]
    QNAME = {t["slug"]: t["name"] for t in D["zhuanti"]}
    QW = (lambda s_: s_) if L.code != "zh-Hant" else __import__("opencc").OpenCC("s2twp").convert
    qmeta = {}
    for t in D["zhuanti"]:
        slug, name, intro = t["slug"], t["name"], t.get("intro") or ""
        segs, total, nb = "", 0, 0
        qcs = []
        for bk in book_order:
            bd = t.get("books", {}).get(bk)
            if not bd or bk not in LIVE_BOOKS: continue  # 没上网的书不出段
            terms = [w for w in (bd.get("match") or bd.get("terms") or []) if w]
            hit = [c for c in allc if any(w in tx(c) for w in terms)] if terms else []
            if not hit: continue
            nb += 1; total += len(hit); qcs += hit
            bname_ = f"《{dict((x for g in BOOK_GROUPS for x in g[1]))[bk]}》" if L.code.startswith("zh") else L.t("bk_" + bk)
            segs += (f'<section class="ztbook" id="{bk}"><h2 class="ph">{esc(bname_)}<small>{L.t("zt_n", n=len(hit))}</small></h2>'
                     + (f'<p class="lead" lang="zh-Hans">{esc(bd["intro"])}</p>' if bd.get("intro") else "") + f'<ol class="ztl">{zt_items(terms, hit)}</ol>'
                     + f'<p class="note"><a href="{P}lunyu/">{L.t("zt_all", b=bname_.strip("《》"))}</a></p></section>')
        qmeta[slug] = qcs
        qk = QORD.index(slug) + 1 if slug in QORD else 0
        qbar = qnext = ""
        if QUEST and qk and qcs:
            qbar = (f'<div class="qbar" data-cs="{esc(json.dumps(qcs))}"><p class="qbh"><b>{QT["lv"].format(k=qk)} · {esc(name)}</b><span class="qbs">{esc(QT["bar"].format(n=len(qcs)))}</span></p>'
                    f'<span class="bar"><i></i></span><p class="qgo"></p></div>')
            if qk < len(QORD):
                n2 = QORD[qk]; qnext = f'<p class="qnext"><a class="btn ghost" href="{P}zhuanti/{n2}.html">{QT["nx"]}{"：" if L.code.startswith("zh") or L.code == "ja" else ": "}{QT["lv"].format(k=qk + 1)} · {esc(QNAME[n2])} ›</a></p>'
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}zhuanti/">{L.t("zt_title")}</a></p><h1><span class="no">{L.t("zt_nb", n=nb, m=total)}</span>{esc(name)}</h1></div></div>
<main class="wrap narrow">{qbar}{f'<p class="lead" lang="zh-Hans">{esc(intro)}</p>' if intro else ""}<p class="note">{L.t("zt_p")}</p>{segs or "<p class=empty>" + L.t("zt_none") + "</p>"}{qnext}</main>{quest_js(L.code) if qbar else ""}'''
        d1 = intro or next((b_.get("intro") for b_ in t.get("books", {}).values() if b_.get("intro")), "")
        write(f"zhuanti/{slug}.html", page(L, f"“{name}”｜{L.t('zt_title')}｜一孔录" if L.code.startswith("zh") else f"{name} | {L.t('zt_title')} | 一孔录 Yikonglu", d1[:110] or name, f"zhuanti/{slug}.html", body)); urls.append(f"{DOMAIN}/{L.prefix}zhuanti/{slug}.html")
        zlist += f'<a class="ztcard" href="{P}zhuanti/{slug}.html"><b>{esc(name)}</b><small>{L.t("zt_n", n=total)}</small></a>'
    routes = ""
    if D.get("gushi") and L.code.startswith("zh") and D["gushi"]["routes"]:  # 乙类：路线页并入专题栏
        routes = f'<h2 class="ph">{L.t("zt_routes")}</h2><p class="note">{L.t("zt_routes_p")}</p><div class="gsroutes">' + "".join(
            f'<a class="gsroute" href="{P}zhuanti/lu-{pid}.html">' + (f'<img src="{D["gushi"]["by"][pid]["_头像"]}" alt="" loading="lazy">' if D["gushi"]["by"][pid].get("_头像") else "") + f'<div><b>跟着{esc(D["gushi"]["by"][pid]["名"])}读<span>{esc(rt["title"])}</span></b><p>{esc(rt["intro"])}</p></div></a>' for pid, rt in D["gushi"]["routes"].items() if rt["items"]) + "</div>"
    if QUEST and D.get("gushi") and D["gushi"]["routes"]:  # 跟着一个人读：每条路线也记进度
        routes = routes.replace('<a class="gsroute" href=', '<a class="gsroute" data-cs="@CS@" href=')
        for pid, rt in D["gushi"]["routes"].items():
            if rt["items"]: routes = routes.replace('data-cs="@CS@" href="' + f'{P}zhuanti/lu-{pid}.html"', 'data-cs="' + esc(json.dumps([c for c, _, _ in rt["items"]])) + '" href="' + f'{P}zhuanti/lu-{pid}.html"', 1)
    def qmap():
        lis = ""
        for k, sl in enumerate([x for x in QORD if qmeta.get(x)], 1):
            r5, c5 = (k - 1) // 5 + 1, (k - 1) % 5 + 1
            if r5 % 2 == 0: c5 = 6 - c5
            r3, c3 = (k - 1) // 3 + 1, (k - 1) % 3 + 1
            if r3 % 2 == 0: c3 = 4 - c3
            dcls = (" qt5" if k > 1 and (k - 1) % 5 == 0 else (" qr5" if r5 % 2 == 0 else "")) + (" qt3" if k > 1 and (k - 1) % 3 == 0 else (" qr3" if r3 % 2 == 0 else ""))
            lis += (f'<li class="qn{dcls}" style="--r5:{r5};--c5:{c5};--r3:{r3};--c3:{c3}" data-cs="{esc(json.dumps(qmeta[sl]))}"><a href="{P}zhuanti/{sl}.html"><span class="qo"><b>{esc(QNAME[sl])}</b></span>'
                    f'<i class="qno">{QT["lv"].format(k=k)}</i><small class="qc">{QT["ch"].format(n=len(qmeta[sl]))}</small></a></li>')
        n = len([x for x in QORD if qmeta.get(x)])
        return (f'<section class="quest"><p class="qstat" id="qstat">{esc(QT["intro"].format(n=n, f=QW(QNAME[QORD[0]])))}</p>'
                f'<ol class="qmap" style="--rows5:{(n + 4) // 5};--rows3:{(n + 2) // 3}">{lis}</ol><p class="note">{QT["note"]}</p></section>')
    body_zt_index = lambda zl: f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("zt_sub")}</span>{L.t("zt_title")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("zt_p")}</p>{qmap() if QUEST else f'<div class="ztcards">{zl}</div>'}{routes}{DDJ_RT_CARDS.get(L.code, "")}</main>{quest_js(L.code) if QUEST else ""}'''
    body = body_zt_index(zlist)
    if L.code.startswith("zh"):  # 语文课本里的《论语》（11-08 主人定，网站推广建议第 2 条）：只简繁；课文各章逐章对过朱注分章原文
        kb_items = ""
        for kid, kname, knote, kcs in KEBEN:
            lis = ""
            for k_, c in enumerate(kcs, 1):
                if c not in pubset and c not in D["qw"]: continue
                bh_ = D["baihua"].get(c) or ""
                lis += (f'<li{"" if c in pubset else " class=wj"}><a href="{href(c)}"><em>{c}</em><b>{esc(ctitle(c))}</b>{"" if c in pubset else "<i class=wjtag>" + L.t("toc_wj") + "</i>"}</a>'
                        f'<p class="zy" lang="zh-Hans">{esc(tx(c))}</p>' + (f'<p class="zd">白话：{esc(bh_)}</p>' if bh_ else "") + "</li>")
            kb_items += (f'<section class="ztbook" id="{kid}"><h2 class="ph">{esc(kname)}<small>{len(kcs)} 章</small></h2><p class="lead">{esc(knote)}</p><ol class="ztl">{lis}</ol></section>')
        kb_toc = "".join(f'<a class="ztcard" href="#{kid}"><b>{esc(kname)}</b><small>{len(kcs)} 章</small></a>' for kid, kname, _, kcs in KEBEN)
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}zhuanti/">{L.t("zt_title")}</a></p><h1><span class="no">初中 · 高中 语文课</span>语文课本里的《论语》</h1></div></div>
<main class="wrap narrow"><p class="lead">统编语文教材选了这几课《论语》：七年级上册《〈论语〉十二章》、高中必修下册《子路、曾皙、冉有、公西华侍坐》、高中选择性必修上册《〈论语〉十二章》。下面按课列出每一章的原文和白话，点进去是这一章的原页、逐句朱熹注、读音和各家注本。</p>
<div class="ztcards">{kb_toc}</div>{kb_items}
<p class="note">原文照朱熹《论语集注》（《四部备要》本），标点、个别用字可能和课本不同；章号按朱注分章，课本注释多用杨伯峻本，章号有时差一两号。标“未讲”的章视频还在做，网站先放原文、白话和注。发现错处请写信：{MAIL}</p></main>'''
        write("zhuanti/keben.html", page(L, "论语十二章原文及翻译、读音、朱熹注｜语文课本里的《论语》｜一孔录", "统编语文七年级上册、高中选择性必修上册《论语》十二章，高中必修下册《侍坐》：每章原文、白话翻译、读音、朱熹注与宋以来各家注本，逐章链到原页。", "zhuanti/keben.html", body))
        urls.append(f"{DOMAIN}/{L.prefix}zhuanti/keben.html")
        # 百日读完《论语》（11-09 主人定）：全书 498 章按字数切成 100 份，每天一份；进度看本机读过的章，不按日历催
        allc = sorted(D["qw"], key=lambda c: tuple(map(int, c.split("."))))
        ln = [len(re.sub(r"[^\u3400-\u9fff]", "", D["qw"][c]["text"])) + 40 for c in allc]  # 每章另加 40 字的“开页”分量，免得一天塞太多短章
        tot = sum(ln); days = []; cur = []; acc = 0
        for c, n_ in zip(allc, ln):
            cur.append(c); acc += n_
            if acc >= tot * (len(days) + 1) / 100 and len(days) < 99: days.append(cur); cur = []
        if cur: days.append(cur)
        def _rng(cs):
            ps = []
            for c in cs:
                p_, n_ = c.split(".")
                if ps and ps[-1][0] == p_: ps[-1][2] = n_
                else: ps.append([p_, n_, n_])
            return "、".join(f"{PIAN[a][0]} {b}" + (f"—{e}" if e != b else "") for a, b, e in ps)
        if L.code == "zh-Hans" and "OUT_ROOT" in globals():
            os.makedirs(os.path.join(OUT_ROOT, "data"), exist_ok=True)
            from opencc import OpenCC as _OC; _tw = _OC("s2twp")
            json.dump({"d": days, "r": [_rng(x) for x in days], "rt": [_tw.convert(_rng(x)) for x in days]}, open(os.path.join(OUT_ROOT, "data", "bairi.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        dl = "".join(f'<li data-d="{i}"><a href="{href(x[0])}"><em>第 {i} 天</em><b>{_rng(x)}</b><small>{len(x)} 章</small></a></li>' for i, x in enumerate(days, 1))
        body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">读经计划</span>百日读完《论语》</h1></div></div>
<main class="wrap narrow bairi"><p class="lead">《论语》全书 498 章，每天读一份，约五章、十分钟，一百天读完。讲过的章有一孔录的片子和细读，没讲的章有原文、原页和译文。</p>
<p class="note">哪天没读不要紧，第二天接着读，计划跟着你走，不按日历催。进度只存在这台设备上，一孔录无需登录，不取隐私，不打扰。</p>
<div class="brbox" id="brbox"><button type="button" class="btn" id="brgo">从今天开始</button></div>
<ol class="brl">{dl}</ol></main>
<script>(function(){{var K="yk_xd",S;try{{S=JSON.parse(localStorage.getItem(K)||"{{}}")}}catch(e){{S={{}}}}S.b=S.b||{{}};var seen=(S.b.lunyu||{{}}).seen||[],D={json.dumps(days)},P={json.dumps([[href(c) for c in x] for x in days])};
function save(){{try{{localStorage.setItem(K,JSON.stringify(S))}}catch(e){{}}}}
var cur=0;for(var i=0;i<D.length;i++){{var ok=D[i].every(function(c){{return seen.indexOf(c)>=0}});var li=document.querySelector('.brl li[data-d="'+(i+1)+'"]');if(ok)li.classList.add("done");else if(!cur)cur=i+1}}
var box=document.getElementById("brbox"),go=document.getElementById("brgo");
function show(){{if(!S.plan||S.plan.id!=="bairi")return;var d=cur||D.length,li=document.querySelector('.brl li[data-d="'+d+'"]');if(li)li.classList.add("now");var nx=D[d-1].filter(function(c){{return seen.indexOf(c)<0}})[0],u=nx?P[d-1][D[d-1].indexOf(nx)]:P[d-1][0];
var n=0;D.forEach(function(x){{if(x.every(function(c){{return seen.indexOf(c)>=0}}))n++}});
box.innerHTML='<p class="brnow">已读完 <b>'+n+'</b> / 100 天 · 今天读第 '+d+' 天</p><p><a class="btn" href="'+u+'">接着读 →</a> <button type="button" class="btn ghost" id="brstop">不跟这个计划了</button></p>';
document.getElementById("brstop").onclick=function(){{if(!confirm("不跟这个计划了？读过的章还记着。"))return;delete S.plan;save();location.reload()}}}}
go.onclick=function(){{S.plan={{id:"bairi",s:Date.now()}};save();show()}};show()}})();</script>'''
        write("jihua/bairi.html", page(L, "百日读完《论语》：每天五章，一百天读完全书｜一孔录", "《论语》498 章分成一百天，每天约五章、十分钟。免登录，进度存在自己的设备上，哪天没读第二天接着读。", "jihua/bairi.html", body))
        urls.append(f"{DOMAIN}/{L.prefix}jihua/bairi.html")
        GX.RWID = GX.rw_ids(GXD, D.get("renwu"))  # 关系图人物 id → 人物卡 id
        urls += GX.build(L, GXD, write, page, P, href, gx_short, PIAN, pubset, DOMAIN)
        urls += LX.build(L, D, D["lx"], write, page, P, href, ctitle, tx, pubset, PIAN, DOMAIN, json.load(open(ZD_FILE, encoding="utf-8"))["per"] if os.path.exists(ZD_FILE) else {})
        LX.write_data(L, D["lx"], globals().get("OUT_ROOT"), href, tx, D["baihua"])
        routes = (f'<h2 class="ph">课本</h2><p class="note">按语文课读：课文里的每一章，原文、翻译、读音、朱熹注。</p><p><a href="{P}zhuanti/keben.html"><b>语文课本里的《论语》</b></a>：七年级上册、高中必修下册、高中选择性必修上册，3 课 25 章</p>') + routes  # 主人 11-08：不放单字网格
        body = body_zt_index(zlist)
    write("zhuanti/index.html", page(L, f'{L.t("zt_title")}｜一孔录', L.t("zt_sub"), "zhuanti/", body)); urls.append(f"{DOMAIN}/{L.prefix}zhuanti/")
    if D.get("gushi") and L.code.startswith("zh"):  # “故事”栏：只简繁
        gsu = GS.build(L, D, D["gushi"], write, page, P, rel_of, title_of, split_ju, DOMAIN); urls += gsu
        for u in gsu:  # 旧“故事”栏 /gushi/ 全部转跳到 /shuyuan/（11-09 主人改名并入书院）
            new = u[len(DOMAIN) + 1 + len(L.prefix):]
            if not new.startswith("shuyuan/"): continue  # 跟着人物读已搬到 zhuanti/，转跳在 gushi.py 里写
            if new == "shuyuan/juese.html": continue
            new_rel = new + ("index.html" if new.endswith("/") else "")
            write("gushi/" + new_rel[len("shuyuan/"):], SY.redirect(f"/{L.prefix}{new}"))
    if D.get("renwu") and L.code.startswith("zh"):  # 论语人物：先只简繁
        RW.GXID = {v: k for k, v in GX.rw_ids(GXD, D["renwu"]).items()}  # 11-14 主人定：人物总页并入关系图，每人一页留作人物卡
        urls += RW.build(L, D, D["renwu"], write, page, P, rel_of, title_of, DOMAIN)
    if not L.code.startswith("zh") and GXD and GX.has_lang(L.code):  # 11-14 外文关系图与人物卡（智器译）
        GX.RWID = GX.rw_ids(GXD, D.get("renwu"))
        _gxc = ["zh-Hans", "zh-Hant"] + [k for k in GX.langs() if k in LANGS]
        urls += GX.build_f(L, GXD, write, page, P, href, gx_short, PIAN, pubset, DOMAIN, _gxc)
        if D.get("renwu"):
            RW.GXID = {v: k for k, v in GX.rw_ids(GXD, D["renwu"]).items()}
            urls += RW.build_f(L, D, D["renwu"], write, page, P, rel_of, ctitle, DOMAIN, GX.TR[L.code], _gxc)
    # 一孔影响力方法页（先只简繁；外文页由语种切换链到简体）
    if L.code.startswith("zh"):
        body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">找到分怎么算、怎么测</span>一孔影响力</h1></div></div>
{yxl_block(L, D, P)}
<main class="wrap narrow prose">
<h2>什么是找到分</h2>
<p>一个平台上，一句原文搜出来，一孔录的讲读排在第 r 名，记 V = 1 / log₂(1 + r)；不在前 20 条记 0。</p>
<p>平台分 = 100 × 各章 V 的平均。</p>
<p>占比 = 各章搜索结果前 20 条中本站条数之和 ÷ 前 20 条总数。只在能看到全部结果的平台计算（现只 YouTube），不点名其他频道。</p>
<p>找到分 = 各平台平台分的平均。YouTube 取台湾繁体、美国简体两种设定的平均，合成一个平台分；哔哩哔哩、谷歌、必应各一个平台分。本周还没测完的平台也照列，注明已测几章，测完后换成整周数。</p>
<p>收录＝搜索引擎已编入索引的本站页数 ÷ 网站地图页数；谷歌按逐页检查接口每周轮查一遍，必应取 Webmaster 报告的索引页数；百度未接。</p>
<h2>怎么测</h2>
<p>词表：已发各章的第一句原文，简体、繁体各一条。每周滚动测，未测到的章暂不计分，跑完后换成整周数；更新日期为最近一次计算日。</p>
<p>搜索用不登录的新会话；YouTube 走数据接口按地区和语言设定搜，和网页搜索结果可能有出入。搜索平台会按人、按地、按时调整结果，你在自己设备上搜到的名次未必一样。</p>
<h2>规矩</h2>
<p>不为这个数改标题、改讲书顺序。数字难看也照登，每周原样更新，旧数不删。</p>
<h2>下载</h2>
<p><a href="/data/yingxiangli.json">yingxiangli.json</a>（每周的找到分、占比、各平台分）。逐周逐章的明细，发布满四周后放出。</p>
{draft_sec(D)}
</main>'''
        write("yingxiangli.html", page(L, "一孔影响力：找到分怎么算、怎么测｜一孔录", "在平台上搜一句原文，能找到一孔录吗：每周公开测，分数叫找到分。", "yingxiangli.html", body, codes=["zh-Hans", "zh-Hant"])); urls.append(f"{DOMAIN}/{L.prefix}yingxiangli.html")
    # 开放数据（文件只在根目录 /data/，各语种只出说明页）
    rows = "".join(f'<tr><td>{L.book(p)}</td><td><a href="/data/lunyu-{PIAN[p][1]}.json">JSON</a> · <a href="/data/lunyu-{PIAN[p][1]}.csv">CSV</a></td><td>{len(by_pian[p])}</td></tr>' for p in sorted(by_pian, key=int))
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("dt_sub")}</span>{L.t("dt_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("dt_p")}</p><div class="tw"><table class="zitab"><thead><tr><th>{L.t("lunyu")}</th><th>{L.t("dt_file")}</th><th>{L.t("dt_rows")}</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">{L.t("dt_lic")} · <a href="https://creativecommons.org/licenses/by/4.0/deed.zh-hans" rel="license noopener" target="_blank">CC BY 4.0</a> · <a href="{P}lunyu/banben/">{L.t("bb_link")}</a></p>{kf_html(L)}</main>'''
    write("kaifang.html", page(L, f'{L.t("dt_title")}｜一孔录', L.t("dt_sub"), "kaifang.html", body)); urls.append(f"{DOMAIN}/{L.prefix}kaifang.html")
    # 读音索引页撤掉（11-13 主人：读者不会一个个字看下来）；旧地址转到检索页，不进站点地图。章页读音、难字字典不动
    write("zi.html", f'<!doctype html><meta charset="utf-8"><title>{L.t("search_title")}｜一孔录</title><link rel="canonical" href="{DOMAIN}/{L.prefix}search.html"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url=/{L.prefix}search.html"><a href="/{L.prefix}search.html">{L.t("search_title")}</a>')
    # 订阅源（Atom）
    X = lambda t: html.escape(t, quote=False)
    ents = ""
    for c in sorted(pub, key=lambda c: (D["first"].get(c, today), tuple(map(int, c.split(".")))), reverse=True)[:50]:
        u = f"{DOMAIN}/{L.prefix}{rel_of(c)}"; d = D["first"].get(c, today)
        summ = yw[c] + (" —— " + (field(c, "片里落点")[0] or "") if field(c, "片里落点")[0] else "")
        ents += f"<entry><title>{X(c + ' ' + title_of(c))}</title><link href=\"{u}\"/><id>{u}</id><updated>{d}T12:00:00+08:00</updated><summary>{X(summ)}</summary></entry>\n"
    write("feed.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="{L.hreflang}"><title>{X("一孔录 · " + L.t("tagline"))}</title><subtitle>{X(L.t("motto"))}</subtitle>
<link href="{DOMAIN}/{L.prefix}feed.xml" rel="self"/><link href="{DOMAIN}/{L.prefix}"/><id>{DOMAIN}/{L.prefix}</id><updated>{today}T12:00:00+08:00</updated><author><name>一孔录</name></author>
{ents}</feed>
''')
    llms = [f"# 一孔录 Yikonglu ({L.name})\n\n> {L.t('motto')} {L.t('intro')}\n\n## 论语 {L.t('lunyu')}\n"]
    for c in pub:
        llms.append(f"- [{c} {title_of(c)}]({DOMAIN}/{L.prefix}{rel_of(c)}): {field(c, '片里落点')[0] or ''}\n")
    write("llms.txt", "".join(llms))
    # PWA：每个语种一份 manifest（从哪个语种添加到主屏幕，就从哪个语种打开），离线页列出已存的章节
    write("manifest.webmanifest", json.dumps({"id": P, "name": "一孔录", "short_name": "一孔录", "description": L.t("tagline"), "lang": L.hreflang,
        "start_url": P + "?source=pwa", "scope": "/", "display": "standalone", "background_color": "#f2f1ea", "theme_color": "#f2f1ea",
        "icons": [{"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "/assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, ensure_ascii=False))
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("off_t")}</span>{L.t("off_h")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("off_p")}</p><ol class="toc" id="offl"></ol><p class="empty" id="offn" hidden>{L.t("off_none")}</p><p class="cta"><a class="btn" href="{P}">{L.t("off_home")}</a></p></main>
<script>(function(){{var O=document.getElementById("offl"),N=document.getElementById("offn");if(!window.caches){{N.hidden=false;return}}
caches.open("yk-pages").then(function(c){{return c.keys().then(function(ks){{ks=ks.filter(function(r){{return /\\/lunyu\\/[^/]+\\/\\d+\\.html$/.test(new URL(r.url).pathname)&&new URL(r.url).pathname.indexOf("{P}lunyu/")===0}});
if(!ks.length){{N.hidden=false;return}}return Promise.all(ks.map(function(r){{return c.match(r).then(function(x){{return x.text()}}).then(function(t){{var m=t.match(/<title>([^<]*)<\\/title>/);return [new URL(r.url).pathname,m?m[1].split(/[｜|]/)[0]:r.url]}})}})).then(function(a){{
a.sort(function(x,y){{return x[0]<y[0]?-1:1}});a.forEach(function(x){{var li=document.createElement("li"),e=document.createElement("a");e.href=x[0];e.textContent=x[1];li.appendChild(e);O.appendChild(li)}})}})}})}}).catch(function(){{N.hidden=false}})}})();</script>'''
    write("offline.html", page(L, f'{L.t("off_h")}｜一孔录', L.t("off_p"), "offline.html", body, head_extra='<meta name="robots" content="noindex">'))
    return urls

def write_data(D, outdir):
    """开放数据：每篇一份 JSON 和 CSV（核对用的底子：原文、白话、引文出处、读音、皇疏首句；不含一孔录读法与现代注本引文）。"""
    os.makedirs(os.path.join(outdir, "data"), exist_ok=True)
    lic = {"license": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); 原文与古注为公版", "attribution": "一孔录 Yikonglu, https://yikonglu.com"}
    for p, cs in D["by_pian"].items():
        rows = []
        for c in cs:
            n = D["notes"][c]; g = D["gao"].get(c, {"cites": [], "reads": []}); h = D["zhuben"].get(c, {}).get("huang")
            rows.append({"chapter": c, "title": n["title"], "url": f"{DOMAIN}/lunyu/{PIAN[p][1]}/{c.split('.')[1]}.html", "text": D["yw"][c],
                         "sentences": split_ju(D["yw"][c]), "baihua": D["baihua"].get(c, ""),
                         "citations": [{"text": x["text"], "source": x["src"], "pages": x["pages"], "paraphrase": x["para"]} for x in g["cites"]],
                         "readings": g["reads"], "huangkan_first_line": ({"text": h["text"], "scan_page": h["page"]} if h else None)})
        slug = PIAN[p][1]
        json.dump({**lic, "book": "论语", "pian": PIAN[p][0], "chapters": rows}, open(os.path.join(outdir, "data", f"lunyu-{slug}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        with open(os.path.join(outdir, "data", f"lunyu-{slug}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(["章号", "标题", "原文", "白话", "网址"])
            for r in rows: w.writerow([r["chapter"], r["title"], r["text"], r["baihua"], r["url"]])
    open(os.path.join(outdir, "data", "LICENSE.txt"), "w", encoding="utf-8").write("一孔录 Yikonglu 开放数据\n原文与古注：公版。\n一孔录所写的白话、一孔按、引文出处表、读音：CC BY 4.0（https://creativecommons.org/licenses/by/4.0/），可转载、改编、商用（含训练模型与再分发），只须署名“一孔录 yikonglu.com”并附原链接。\n现代注本引文、视频、配音、原创角色形象与插图不在许可内。\n")
    # 数据集卡（11-08 推广建议第 5 条）：Hugging Face 与 GitHub 都认这份 README.md 的 YAML 头；许可、署名与 LICENSE.txt 一致
    slugs = [PIAN[p][1] for p in D["by_pian"]]
    nch = sum(len(cs) for cs in D["by_pian"].values())
    cfg = "\n".join(f"- config_name: {sl}\n  data_files: lunyu-{sl}.csv" for sl in slugs)
    open(os.path.join(outdir, "data", "README.md"), "w", encoding="utf-8").write(f"""---
license: cc-by-4.0
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
{cfg}
---

# 一孔录《论语》逐章开放数据

**来源与署名：一孔录 Yikonglu，<https://yikonglu.com>**（转用请署“一孔录 yikonglu.com”并附原章网址）

一孔录逐字读《论语》，以朱熹《论语集注》（《四部备要》本）为底本，每章对照底本原页。本数据集是网站上已讲各章的核对底子，按篇各一份 CSV 与 JSON，随网站更新。现收 {len(slugs)} 篇 {nch} 章，开讲一篇加一篇。

## 文件

| 文件 | 内容 |
|---|---|
| `lunyu-<篇>.csv` | 章号、标题、原文、白话、网址 |
| `lunyu-<篇>.json` | 以上各项，加分句、视频引到的注文原话及底本页码（citations）、读音（readings）、皇侃《论语义疏》首句及扫描页（huangkan_first_line） |

篇：{"、".join(PIAN[p][0] for p in D["by_pian"])}。章号按朱注分章（与杨伯峻《论语译注》分章偶有一两号之差）。

## 许可

- 《论语》原文与古注：公版。
- 一孔录所写的白话、一孔按、引文出处表、读音：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，可转载、改编、商用（含训练模型与再分发），只须署名“一孔录 yikonglu.com”并附原链接。
- 一孔录自己的读法（常见读法、注里的关键字、诸家、一孔按）与现代注本引文不在本数据集里。

## 引用

```
一孔录. 一孔录《论语》逐章开放数据. https://yikonglu.com/kaifang.html
```

发现错处请按网站页尾邮箱来信，核实后记入勘误页 <https://yikonglu.com/kanwu.html>，署你的网名。
""")

def kf_html(L):  # 开放数据页的分界说明
    K = lang_tab(KAIFANG, L.code)
    li = lambda xs: "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"
    return (f'<h2 id="fenjie">{K["h"]}</h2><p>{K["p"]}</p><h3>{K["oh"]}</h3>{li(K["o"])}<h3>{K["ch"]}</h3>{li(K["c"])}'
            f'<p>{K["biz"]}</p><p class="mailp">{MAIL}</p><p>{K["rule"]}</p><h3>{K["log"]}</h3>' + li([f"{a} {b}" for a, b in K["logs"]]))

# 页底平台行：有网页主页的直接外链，微信系只能搜
PLAT_LINKS = [("YouTube", "https://www.youtube.com/@yikonglu"), ("哔哩哔哩", "https://space.bilibili.com/18385461"), ("TikTok", "https://www.tiktok.com/@yikonglu"), ("X", "https://x.com/yikonglu"), ("抖音", "https://www.douyin.com/user/MS4wLjABAAAAXpVHXn9zMrJpCNeOBO1s4G2i1KhXcstcIBil6H9TFQM"), ("快手", "https://www.kuaishou.com/profile/3xi6ey79zwx7edu"), ("知乎", "https://www.zhihu.com/people/yikonglu"), ("百家号", "https://mr.baidu.com/r/25FydpLvBKM"), ("小红书", "https://www.xiaohongshu.com/user/profile/567f4fd5e4251d7509b0893a"), ("微博", "https://www.weibo.com/u/8256104044"),
              ("Spotify", "https://open.spotify.com/show/2tc129X7b7yqlqqGWzUbon"), ("Apple 播客", "https://podcasts.apple.com/us/podcast/id6808549970"),
              ("Amazon Music", "https://music.amazon.co.uk/podcasts/40c8bab4-c9ec-41fa-a5ce-dba2e2d7aa91/%E4%B8%80%E5%AD%94%E5%BD%95%EF%BD%9C%E8%BD%BB%E6%9D%BE%E8%AF%BB%E7%BB%8F%E5%85%B8"),
              ("喜马拉雅", "https://www.ximalaya.com/album/132166955"), ("小宇宙", "https://www.xiaoyuzhoufm.com/podcast/6a9a7681f62860437cd2d85e")]
PLAT_NAME = {"哔哩哔哩": "Bilibili", "微博": "Weibo", "Apple 播客": "Apple Podcasts", "喜马拉雅": None, "知乎": None, "小宇宙": None, "百家号": None, "抖音": None, "快手": None, "小红书": None}
PLAT_WX = {"zh": "视频号、公众号：微信搜「一孔录」", "en": "WeChat: search “一孔录”", "ja": "WeChat：「一孔录」で検索",
           "ko": "WeChat: 「一孔录」 검색", "fr": "WeChat : cherchez « 一孔录 »", "es": "WeChat: busque «一孔录»"}
def where_html(L):
    zh = L.code.startswith("zh")
    out = []
    for name, url in PLAT_LINKS:
        if not zh:
            name = PLAT_NAME.get(name, name)
            if name is None: continue
        out.append(f'<a href="{url}" target="_blank" rel="noopener">{name}</a>')
    return " · ".join(out) + " · " + PLAT_WX["zh" if zh else L.code if L.code in PLAT_WX else "en"]

def img_sitemap(outdir):
    """图片站点地图（11-08 推广建议第 6 条）：简体页面里引到的原页图（img 域名 yuanye/、ddj/），按页面列 image:image，robots.txt 加一行。外语页同图不重复列。"""
    pre = {LANGS[k][0].strip("/") for k in LANGS if LANGS[k][0]}
    rx = re.compile(r'(?:href|src)="(https://img\.yikonglu\.com/(?:yuanye|ddj)/[^"?]+\.jpg)(?:\?v=\w+)?"')
    rows = []
    for root, dirs, files in os.walk(outdir):
        relr = os.path.relpath(root, outdir)
        if relr.split(os.sep)[0] in pre: dirs[:] = []; continue
        for f in sorted(files):
            if not f.endswith(".html"): continue
            rel = os.path.normpath(os.path.join(relr, f)).replace(os.sep, "/")
            imgs = list(dict.fromkeys(rx.findall(open(os.path.join(root, f), encoding="utf-8").read())))
            if not imgs or rel.startswith("."): continue
            u = f"{DOMAIN}/" + (rel[:-10] if rel.endswith("index.html") else rel)
            rows.append(f"<url><loc>{u}</loc>" + "".join(f"<image:image><image:loc>{i}</image:loc></image:image>" for i in imgs[:1000]) + "</url>")
    rows.sort()
    open(os.path.join(outdir, "sitemap-images.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "\n".join(rows) + "\n</urlset>\n")
    with open(os.path.join(outdir, "robots.txt"), "a") as fh: fh.write(f"Sitemap: {DOMAIN}/sitemap-images.xml\n")
    print(f"  图片站点地图：{len(rows)} 页、{sum(r.count('<image:image>') for r in rows)} 张")


def yuanye_wm_out(ydir, dst):
    """论语原页出图（11-14 主人“过”）：按版框切白边，底边一行“一孔录 yikonglu.com · 论语集注 朱熹 卷X 篇 · 第 N 页”＋镂空一孔印压进版框右下角。
    tools/yuanye/ 原图不动；印只用工坊 assets/一孔印.png 原件（tools/yuanye_wm/一孔印.png，先核 sha）。出图逐字节稳定，图片仓库只在真变了才重写。"""
    import hashlib
    from PIL import Image
    sp = os.path.join(HERE, "yuanye_wm", "一孔印.png")
    if not hashlib.sha256(open(sp, "rb").read()).hexdigest().startswith(ZJ.WM.SEAL_SHA): sys.exit("一孔印不是工坊原件（sha 不对），停。")
    seal = Image.open(sp); seal.load(); os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(ydir)):
        if not f.endswith(".jpg"): continue
        p = f[:-4]; src = os.path.join(ydir, f)
        im = ZJ.WM.mark(ZJ.WM.prep("lunyu", Image.open(src), p, src), seal, ZJ.WM.label("lunyu", p))
        im.save(os.path.join(dst, f), quality=82, optimize=True, progressive=True)


def img_out(outdir):
    """图片挪去图片仓库：页面里 /yuanye/ /og/ /gushi/img/ 换成 IMG 绝对地址，文件同步到 IMG_DIR（只写有变的、删多余的），再从 docs 删掉。"""
    import filecmp
    if not IMG:
        print("  图片留在本站（YK_IMG 为空，回退）"); return
    if not os.path.isdir(os.path.join(IMG_DIR, ".git")):  # 别悄悄把两百多兆图片又塞回网站仓库
        sys.exit(f"没有图片仓库 {os.path.abspath(IMG_DIR)}：先 git clone https://github.com/davidokant/yikonglu-img 到那里（或设 YK_IMG_DIR），要回退就设 YK_IMG= 。")
    import hashlib
    yd = os.path.join(outdir, "yuanye")
    YV = {f[:-4]: hashlib.md5(open(os.path.join(yd, f), "rb").read()).hexdigest()[:8] for f in os.listdir(yd) if f.endswith(".jpg")} if os.path.isdir(yd) else {}
    XV = {s: {f[:-4]: hashlib.md5(open(os.path.join(IMG_DIR, s, f), "rb").read()).hexdigest()[:8] for f in os.listdir(os.path.join(IMG_DIR, s)) if f.endswith(".jpg")} if os.path.isdir(os.path.join(IMG_DIR, s)) else {} for s in ("ddj", "sanzijing")}
    for f in glob.glob(os.path.join(outdir, "**", "*.*"), recursive=True):
        if not f.endswith((".html", ".xml", ".json", ".js")) or f.endswith("sw.js"): continue
        t = open(f, encoding="utf-8").read(); t0 = t
        for sub in IMG_SUBS:
            if sub not in t: continue
            t = t.replace(f"{DOMAIN}/{sub}", f"{IMG}/{sub}")
            for q in "\"'(":
                t = t.replace(f"{q}/{sub}", f"{q}{IMG}/{sub}")
        if f.endswith(".html") and "/yuanye/p" in t:  # 原页图带内容版本号：换图（如 11-13 校平）后浏览器和 sw.js 缓存里的旧图不再顶替
            t = re.sub(r'(/yuanye/(p\d+)\.jpg)(?=["\')])', lambda m: m.group(1) + ("?v=" + YV[m.group(2)] if m.group(2) in YV else ""), t)
        if f.endswith(".html") and ("/ddj/p" in t or "/sanzijing/p" in t):  # 道德经、三字经原页（只在图片仓库）同样带版本号：11-13 切白边后框坐标跟新图走
            t = re.sub(r'(/(ddj|sanzijing)/(p\d+)\.jpg)(?=["\')])', lambda m: m.group(1) + ("?v=" + XV[m.group(2)][m.group(3)] if m.group(3) in XV[m.group(2)] else ""), t)
        if t != t0: open(f, "w", encoding="utf-8").write(t)
    nw = nd = 0
    for sub in IMG_SUBS:
        src, dst = os.path.join(outdir, sub), os.path.join(IMG_DIR, sub)
        if not os.path.isdir(src): continue
        have = set()
        for f in glob.glob(os.path.join(src, "**", "*"), recursive=True):
            if os.path.isdir(f): continue
            r = os.path.relpath(f, src); have.add(r); d = os.path.join(dst, r)
            if not (os.path.exists(d) and filecmp.cmp(f, d, shallow=False)):
                os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(f, d); nw += 1
        for f in glob.glob(os.path.join(dst, "**", "*"), recursive=True):
            if not os.path.isdir(f) and os.path.relpath(f, dst) not in have: os.remove(f); nd += 1
        shutil.rmtree(src)
    print(f"  图片 → {os.path.abspath(IMG_DIR)}：新写 {nw}、删 {nd}；页面改用 {IMG}")


def short_links(outdir):
    """章号短网址（11-14 定：章号统一成“论语 2.1”、和网址对得上）：/lunyu/2.1 → 该章页。抄一句复制出来带“yikonglu.com/lunyu/2.1”。
    每章一个 /lunyu/<篇.章>/index.html 跳转页（canonical 指正式章页、noindex）；404 页另有脚本兜底。道德经、三字经正式网址本来就是 /daodejing/1、/sanzijing/1。"""
    yw = json.load(open(os.path.join(YW_DIR, "论语原文-集注分章-v1.json"), encoding="utf-8"))
    for c, lp in ((c, lp) for lp in ("", "en/", "ja/") for c in yw):  # 英日 498 章都有页（11-14 英日读本章末印 yikonglu.com/en/lunyu/12.1）
        p_, n_ = c.split(".")
        dst = f"/{lp}lunyu/{PIAN[p_][1]}/{n_}.html"
        d = os.path.join(outdir, lp, "lunyu", c); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            f'<!doctype html><meta charset="utf-8"><title>论语 {c}｜一孔录</title><link rel="canonical" href="{DOMAIN}{dst}">'
            f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={dst}">'
            f'<script>location.replace("{dst}"+location.hash)</script><a href="{dst}">论语 {c}</a>')

SHORT_404_JS = "<script>(function(){var x=location.pathname.match(/^\\/duben\\/lunyu-xueer(-hant)?\\.pdf$/);if(x){location.replace('/duben/lunyu-chongjian'+(x[1]||'')+'.pdf');return}var m=location.pathname.match(/^\\/(zh-hant\\/|en\\/|ja\\/)?lunyu\\/(\\d+)\\.(\\d+)\\/?$/),S=" + json.dumps({k: v[1] for k, v in PIAN.items()}) + ";if(m&&S[m[2]])location.replace('/'+(m[1]||'')+'lunyu/'+S[m[2]]+'/'+m[3]+'.html'+location.hash)})()</script>"

def main(zdir, outdir, kanwu=None):
    yw = json.load(open(os.path.join(HERE, "yuanwen.json"), encoding="utf-8"))
    eps = json.load(open(os.path.join(HERE, "episodes.json"), encoding="utf-8"))
    stp0 = os.path.join(GAO_DIR, "_时间", "章节起点.json")  # 各集 youtube / bvid / public_at；有则盖过 episodes.json 里的
    if os.path.exists(stp0):
        for k, e in json.load(open(stp0, encoding="utf-8")).items():
            name = k.split("-")[-1] if isinstance(e, dict) else ""
            if name in eps:
                for a, b in (("youtube", "youtube"), ("bvid", "bilibili"), ("public_at", "public_at")):
                    if e.get(a): eps[name][b] = e[a]
    notes = {}
    for f in sorted(os.listdir(zdir)):
        if f.endswith(".md") and f not in ("说明.md", "主题线.md"):
            notes.update(parse_zhaji(os.path.join(zdir, f)))
    gao = {}
    for f in sorted(glob.glob(os.path.join(GAO_DIR, "*", "*稿*.md"))):
        for c, v in parse_gao(f, yw).items():
            gao.setdefault(c, {"cites": [], "reads": []}); gao[c]["cites"] += v["cites"]; gao[c]["reads"] += v["reads"]; gao[c].setdefault("qw_pages", []).extend(v.get("qw_pages", []))
    ch2ep = {c: (name, e) for name, e in eps.items() for c in e["chapters"]}
    key = lambda c: tuple(map(int, c.split(".")))
    pub = [c for c in sorted(ch2ep, key=key) if c in notes and c in yw]
    for c in sorted(ch2ep, key=key):
        if c not in pub: print("跳过（缺札记或原文）", c)
    by_pian = {}
    for c in pub: by_pian.setdefault(c.split(".")[0], []).append(c)
    today = datetime.date.today().isoformat()
    if os.path.isdir(outdir):
        for x in os.listdir(outdir):
            p = os.path.join(outdir, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(outdir, exist_ok=True)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(outdir, "assets"))
    rdir = os.path.join(HERE, "root")  # 站长验证文件等，原样放根目录
    if os.path.isdir(rdir): shutil.copytree(rdir, outdir, dirs_exist_ok=True)
    ydir = os.path.join(HERE, "yuanye"); os.makedirs(ydir, exist_ok=True)  # 原页 jpg 缓存留在仓库：共享盘会给 jpg 注入 C2PA、字节全变，不能放那里
    for png in sorted(glob.glob(os.path.join(GAO_DIR, "*", "p*.png"))):
        jpg = os.path.join(ydir, os.path.basename(png)[:-4] + ".jpg")
        if not os.path.exists(jpg):
            from PIL import Image
            im = Image.open(png).convert("RGB")
            if im.width > 1400: im = im.resize((1400, int(im.height * 1400 / im.width)))
            im.save(jpg, quality=78, optimize=True, progressive=True)
    ZJD = ZJ.load(); ZJ.YDIR = ydir; ZJ.swap_pages(ZJD, ydir)  # 句列表里校平过的页换成校平图
    yuanye_wm_out(ydir, os.path.join(outdir, "yuanye"))
    pages_avail = {re.sub(r"\D", "", f).lstrip("0") for f in os.listdir(ydir) if f.endswith(".jpg")}
    zhuben = parse_zhuben(ZB_DIR)
    wjan = {}  # 未讲章“一孔按”：内容线程交 数据/网站素材/_未讲/<章>.json（片里落点、常见读法、字眼、核）
    for f in glob.glob(os.path.join(GAO_DIR, "_未讲", "*.json")):
        c_ = os.path.basename(f)[:-5]
        if re.fullmatch(r"\d+\.\d+", c_): wjan[c_] = json.load(open(f, encoding="utf-8"))
    fsp = os.path.join(HERE, "firstseen.json")  # 每章第一次上网的日期（订阅源、引用元数据用）
    first = json.load(open(fsp, encoding="utf-8")) if os.path.exists(fsp) else {}
    for c in pub: first.setdefault(c, today)
    json.dump(first, open(fsp, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    baihua, bh_new = {}, set()
    bh_ok = set()  # 核过的白话（_白话/白话-核定-*.md）：最后读，盖过初稿与改写稿，未讲页不再标“初稿”
    for f in sorted(glob.glob(os.path.join(BH_DIR, "*.md")), key=lambda f: ("核定" in f, "改写" in f, f)):  # 改写稿后读，覆盖同章旧稿；核定稿最后
        for l in open(f, encoding="utf-8"):
            m = re.match(r"^- (\d+\.\d+)[：:]\s*(.+)$", l.strip())
            if m:
                baihua[m.group(1)] = m.group(2).strip()
                if "改写" in f or "核定" in f: bh_new.add(m.group(1))
                if "核定" in f: bh_ok.add(m.group(1))
    hp = os.path.join(HERE, "baihua_hold.json")
    for c in (json.load(open(hp, encoding="utf-8")).get("chapters", []) if os.path.exists(hp) else []): baihua.pop(c, None)
    for c in [c for c in baihua if int(c.split(".")[0]) <= 10 and c not in pub and c not in bh_new]: baihua.pop(c)  # 前十篇未讲章旧稿白话先不放，改写稿到了再上
    stp = os.path.join(GAO_DIR, "_时间", "章节起点.json")
    starts = {}  # {YouTube ID: {章号: 秒}}，按集追加
    if os.path.exists(stp):
        for e in json.load(open(stp, encoding="utf-8")).values():
            if isinstance(e, dict): SHARE_KEYS.update(e.get("keys") or {})
            if isinstance(e, dict) and e.get("youtube"): starts.setdefault(e["youtube"], {}).update({k: int(v) for k, v in e.get("starts", {}).items()})
    hujian = {}  # 互见列：数据/网站素材/_互见/*.csv，列：章号,句,类别(注/本书/他书),内容,出处,链接（链接可写章号如 1.4 或 1.4#s2）
    for f in sorted(glob.glob(os.path.join(GAO_DIR, "_互见", "*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            if r.get("章号") and r.get("内容"):
                hujian.setdefault(r["章号"].strip(), []).append({"ju": (r.get("句") or "1").strip().lstrip("s"), "kind": r.get("类别", "").strip(), "text": r["内容"].strip(), "src": (r.get("出处") or "").strip(), "link": (r.get("链接") or "").strip()})
    # 全书原文（朱注分章 498 章）：已讲章仍用 yuanwen.json（与视频一致），未讲章用这份
    qf = sorted(glob.glob(os.path.join(YW_DIR, "论语原文-集注分章-v*.json")))
    QW = json.load(open(qf[-1], encoding="utf-8")) if qf else {}
    for c, a, b in (("1.6", "泛爱众", "汎爱众"),):  # 原文 JSON 与异文表不符处，照底本
        if c in QW: QW[c]["text"] = QW[c]["text"].replace(a, b)
    fz, yiwen = {}, {}
    if os.path.exists(os.path.join(YW_DIR, "分章对照表.csv")):
        for r in csv.DictReader(open(os.path.join(YW_DIR, "分章对照表.csv"), encoding="utf-8-sig")):
            if r.get("朱注章号"): fz.setdefault(r["朱注章号"].strip(), []).append(r["杨伯峻章号"].strip())
        fz = {k: "、".join(dict.fromkeys(x for y in v for x in y.split("|"))) for k, v in fz.items()}
    if os.path.exists(os.path.join(YW_DIR, "异文表.csv")):
        for r in csv.DictReader(open(os.path.join(YW_DIR, "异文表.csv"), encoding="utf-8-sig")):
            if r.get("章号"): yiwen.setdefault(r["章号"].strip(), []).append(r)
    all_by_pian = {}
    for c in sorted(set(QW) | set(pub), key=key): all_by_pian.setdefault(c.split(".")[0], []).append(c)
    # 互见的“句”是按全书原文的标点切的；已讲章网站原文标点不全同，按字位换算成网站的句号
    han = lambda t: re.sub(r"[^\u3400-\u9fff]", "", t)
    def jmap(c, j):
        if c not in pub or c not in QW: return j
        src, dst = split_ju(QW[c]["text"]), split_ju(yw[c])
        off = sum(len(han(x)) for x in src[:j - 1]); acc = 0
        for k, x in enumerate(dst, 1):
            acc += len(han(x))
            if off < acc: return k
        return len(dst)
    from opencc import OpenCC
    t2s = OpenCC("t2s")
    for c, rs in hujian.items():
        for r in rs:
            if r["ju"].isdigit(): r["ju"] = str(jmap(c, int(r["ju"])))
            m = re.fullmatch(r"(\d+\.\d+)#s(\d+)", r["link"])
            if m: r["link"] = f"{m.group(1)}#s{jmap(m.group(1), int(m.group(2)))}"
            if r["kind"] == "注": r["text"] = t2s.convert(r["text"])
            r["src"] = re.sub(r"（(?:本章)?底本(?:经文)?PDF(\d+(?:—\d+)?)）", r"（底本第 \1 页）", r["src"])
    global GUSHI_ON, RENWU_ON
    RWD = RW.load(RENWU_DIR); RENWU_ON = bool(RWD)
    G = GS.load(GUSHI_DIR, pub)
    if G: GS.copy_images(G, outdir); GUSHI_ON = True
    yxl = json.load(open(YXL_FILE, encoding="utf-8")) if os.path.exists(YXL_FILE) else {}
    yxl = yxl_merge(yxl, json.load(open(YXL_WEEK_FILE, encoding="utf-8")) if os.path.exists(YXL_WEEK_FILE) else {})
    draft = json.load(open(DRAFT_FILE, encoding="utf-8")) if os.path.exists(DRAFT_FILE) else {}
    D = dict(draft=draft, book_slugs={zh: sl for _, bs in BOOK_GROUPS for sl, zh in bs}, live_books=LIVE_BOOKS, yxl=yxl, zhuanti=load_zhuanti(), qw=QW, fz=fz, yiwen=yiwen, all_by_pian=all_by_pian, renwu=RWD, gushi=G, hujian=hujian, starts=starts, first=first, baihua=baihua, zhuben=zhuben, notes=notes, yw=yw, gao=gao, kw=parse_kanwu(kanwu or KANWU_DEFAULT), pub=pub, by_pian=by_pian, ch2ep=ch2ep, pages_avail=pages_avail, today=today, zhuju=ZJD, wjan=wjan, ddj=load_ddj(), bh_ok=bh_ok, lx=LX.load(), zy=json.load(open(os.path.join(HERE, "zhengyi.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "zhengyi.json")) else {})

    pdp = os.path.join(HERE, "pagedates.json")  # 每页 [内容指纹, 内容最后变动日]：没改的页不换日期
    pdates = json.load(open(pdp, encoding="utf-8")) if os.path.exists(pdp) else {}
    seen = set()
    def writer(prefix, post=None):
        def write(rel, text):
            p = os.path.join(outdir, prefix, rel); os.makedirs(os.path.dirname(p) or outdir, exist_ok=True)
            text = post(text) if post else text
            key = (prefix + "/" if prefix else "") + rel
            h = __import__("hashlib").md5(text.encode()).hexdigest()[:16]
            if pdates.get(key, [None])[0] != h: pdates[key] = [h, today]
            seen.add(key)
            open(p, "w", encoding="utf-8").write(text.replace(DATE_TOK, pdates[key][1]).replace(DATE_TOK_SL, pdates[key][1].replace("-", "/")))
        return write

    share_x(D)
    # 每章分享图：简体图给简、英、法、西；繁体图给繁、日、韩
    D["og"] = {}
    _tr_en, _tr_ja = ({k: v for k, v in json.load(open(os.path.join(HERE, "i18n", f"{x}.json"), encoding="utf-8")).get("chapters", {}).items()} if os.path.exists(os.path.join(HERE, "i18n", f"{x}.json")) else {} for x in ("en", "ja"))
    for c in pub:
        pnum, cnum = c.split(".")
        TRI_TXT[c] = {"h": f"《论语·{PIAN[pnum][0]}》第 {cnum} 章 · Analects {c} · 論語 {c}", "y": yw[c], "en": _tr_en.get(c, {}).get("yw", ""), "ja": _tr_ja.get(c, {}).get("yw", "")}
    if OG.available():
        for c in pub:
            pnum, cnum = c.split(".")
            head = f"《论语·{PIAN[pnum][0]}》第 {cnum} 章"
            D["og"][c] = {"hans": OG.make("hans", c, head, yw[c], TAGLINE)}
            D["og"][c]["tri"] = OG.make3(c, f"{head} · Analects {c} · 論語 {c}", yw[c], _tr_en.get(c, {}).get("yw", ""), _tr_ja.get(c, {}).get("yw", ""), "逐字读经典原文 · Reading the classics word by word")
    else:
        print("没有字体，分享图跳过：", OG.FONT)
    if OG.available():  # 未讲章也出三语分享图（11-09 主人定补齐）
        for c, q in D["qw"].items():
            if c in pub or c in D["og"] or not WJ_TR.get(c, {}).get("en"): continue
            pnum, cnum = c.split(".")
            D["og"][c] = {"tri": OG.make3(c, f"《论语·{PIAN[pnum][0]}》第 {cnum} 章 · Analects {c} · 論語 {c}", q["text"], WJ_TR[c]["en"], WJ_TR[c].get("ja", ""), "逐字读经典原文 · Reading the classics word by word")}
    global OUT_ROOT; OUT_ROOT = outdir
    urls = build_lang(Lang("zh-Hans", ZH_UI), D, writer(""))
    write_data(D, outdir)
    if yxl: json.dump(yxl, open(os.path.join(outdir, "data", "yingxiangli.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if SHOW_DRAFT and D.get("draft", {}).get("rows"):
        json.dump(dict({k: v for k, v in D["draft"].items() if k in ("updated", "episodes", "segments", "changed", "ratio")}, rows=[{k: r.get(k) for k in ("ep", "segments", "changed")} for r in D["draft"]["rows"]]), open(os.path.join(outdir, "data", "chugao-gaidong.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 繁体：由简体页面整页转换，台湾用字；站内链接改前缀
    from opencc import OpenCC
    cc = OpenCC("s2twp")
    keep = ("/assets/", "/yuanye/", "/style.css", "https://", "http://", "#")
    # 古文与人名里不能按今字转的（简繁同形或 OpenCC 会转错），先护住再转
    PROTECT = ["范祖禹", "范氏", "游酢", "游氏", "坐如尸", "尸", "咸", "丑", "干禄", "云：", "云，", "子云", "诗云", "余力", "余，", "余者", "托看"]
    # 皇疏录文本来就是原刻字形，不再转一遍（长的先护，免得被短的拆开）
    KEEP = sorted({x for z in D["zhuben"].values() if "huang" in z for x in (z["huang"]["text"], esc(z["huang"]["text"]))}, key=len, reverse=True)
    def to_hant(text):
        DK = []  # 道德经底本字形：\ue010…\ue011 里的原样留着
        def _dk(m): DK.append(m.group(1)); return f"\ue012{len(DK) - 1}\ue013"
        text = re.sub("\ue010(.*?)\ue011", _dk, text, flags=re.S)
        for i, w in enumerate(KEEP): text = text.replace(w, f"\ue002{i}\ue003")
        for i, w in enumerate(PROTECT): text = text.replace(w, f"\ue000{i}\ue001")
        text = re.sub(r'<script>var _hmt=.*?</script>', "", text)  # 百度统计只留简体页
        t = cc.convert(text)
        for i, w in enumerate(PROTECT): t = t.replace(f"\ue000{i}\ue001", HANT_FIX.get(w, w))
        for a_, b_ in HANT_POST: t = t.replace(a_, b_)
        for i, w in enumerate(KEEP): t = t.replace(f"\ue002{i}\ue003", w)
        t = re.sub("\ue012(\\d+)\ue013", lambda m: DK[int(m.group(1))], t)
        t = re.sub(r'(href|action|src)="/(?!zh-hant/)([^"]*)"', lambda m: m.group(0) if m.group(2).startswith(("assets/", "yuanye/", "style.css", "data/", "og/", "gushi/img/", "duben/")) else f'{m.group(1)}="/zh-hant/{m.group(2)}"', t)
        t = t.replace("fetch('/search.json')", "fetch('/zh-hant/search.json')").replace("&quot;/lunyu/", "&quot;/zh-hant/lunyu/").replace("&quot;/daodejing/", "&quot;/zh-hant/daodejing/")
        t = t.replace('"u": "/lunyu', '"u": "/zh-hant/lunyu')
        def _tri(m):  # 分享卡三语数据是 ascii 转义的，整页转换碰不到；繁体页只把标题、原文、节气物候转繁，英日不动（11-09 主人）
            d_ = json.loads(m.group(1))
            for k_ in ("h", "y"):
                if d_.get(k_): d_[k_] = to_hant(d_[k_])
            if d_.get("rl"): d_["rl"] = dict(d_["rl"], jn=[cc.convert(x) for x in d_["rl"]["jn"]], hou=[cc.convert(x) for x in d_["rl"]["hou"]])
            return '<script type="application/json" class="shtri">' + json.dumps(d_) + '</script>'
        t = re.sub(r'<script type="application/json" class="shtri">(.*?)</script>', _tri, t)
        return t
    if OG.available():
        for c in pub:
            pnum, cnum = c.split(".")
            D["og"][c]["hant"] = OG.make("hant", c, to_hant(f"《论语·{PIAN[pnum][0]}》第 {cnum} 章"), to_hant(yw[c]), to_hant(TAGLINE))
        shutil.copytree(os.path.join(HERE, "og"), os.path.join(outdir, "og"), ignore=shutil.ignore_patterns("*.sig"))
    hant_ui = dict(ZH_UI); hant_ui["translated_note"] = ZH_UI["hant_note"]
    urls += build_lang(Lang("zh-Hant", hant_ui), D, writer("zh-hant", to_hant))
    for code in [k for k in LANGS if not k.startswith("zh")]:
        tr = json.load(open(os.path.join(HERE, "i18n", code + ".json"), encoding="utf-8"))
        for key, tab in (("fangfa", FANGFA), ("kaifang", KAIFANG), ("wen", WEN)):  # 新语种把这些页的译文放在自己的 i18n 文件里
            if key in tr: tab[code] = tr[key]
        if "privacy" in tr: PRIVACY[code] = tuple(tr["privacy"])
        if "wx" in tr: PLAT_WX[code] = tr["wx"]
        ui = dict((FILL.get(code) or {}).get("ui") or {}); ui.update(EXTRA_UI.get(code, {})); ui.update(tr["ui"]); ui.update(WJ_UI.get(code, {}))
        urls += build_lang(Lang(code, ui, tr), D, writer(code))

    # 站点地图里写各语种互指（只指真有的页），谷歌、必应据此把同一章的七语版本认作一组
    pre = sorted(((LANGS[k][0], LANGS[k][2]) for k in LANGS if LANGS[k][0]), key=lambda x: -len(x[0]))
    def split_lang(u):
        k = u[len(DOMAIN) + 1:]
        for pf, hl in pre:
            if k.startswith(pf): return hl, k[len(pf):]
        return LANGS["zh-Hans"][2], k
    groups = {}
    for u in urls:
        hl, r = split_lang(u); groups.setdefault(r, {})[hl] = u
    def sm_alts(u):
        g = groups[split_lang(u)[1]]
        if len(g) < 2: return ""
        x = "".join(f'<xhtml:link rel="alternate" hreflang="{hl}" href="{v}"/>' for hl, v in g.items())
        dz = g.get(LANGS["zh-Hans"][2])
        return x + (f'<xhtml:link rel="alternate" hreflang="x-default" href="{dz}"/>' if dz else "")
    def lastmod(u):
        k = u[len(DOMAIN) + 1:]
        return pdates.get(k + "index.html" if k.endswith("/") or not k else k, [None, today])[1]
    open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' +
        "".join(f"<url><loc>{u}</loc><lastmod>{lastmod(u)}</lastmod>{sm_alts(u)}</url>\n" for u in urls) + "</urlset>\n")
    json.dump({k: v for k, v in pdates.items() if k in seen}, open(pdp, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    ver = __import__("hashlib").md5((CSSV + A2V + open(os.path.join(HERE, "sw.js"), encoding="utf-8").read() + "".join(sorted(v[0] for k, v in pdates.items() if k in seen))).encode()).hexdigest()[:10]
    open(os.path.join(outdir, "sw.js"), "w", encoding="utf-8").write(open(os.path.join(HERE, "sw.js"), encoding="utf-8").read().replace("@VER@", ver).replace("@PREFIXES@", json.dumps([""] + [LANGS[k][0] for k in LANGS if LANGS[k][0]])))
    # 11-13 GSC 报 /done /top /copy /intent /data/live- 404：是页面脚本里计数服务的接口路径被当成链接抓了；脚本已改成拼接，这里再挡一下
    open(os.path.join(outdir, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /done\nDisallow: /copy$\nDisallow: /top$\nDisallow: /hit$\nDisallow: /reads\nDisallow: /intent\nDisallow: /data/live-\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    open(os.path.join(outdir, "CNAME"), "w").write("yikonglu.com\n")
    open(os.path.join(outdir, ".nojekyll"), "w").write("")
    shutil.copy(os.path.join(HERE, "style.css"), os.path.join(outdir, "style.css"))
    print(f"生成 {len(urls)} 页 → {outdir}")
    img_out(outdir)
    short_links(outdir)
    img_sitemap(outdir)
    rc = __import__("subprocess").run([sys.executable, os.path.join(HERE, "check.py"), outdir]).returncode  # 发版前检查，不过别推
    if rc: sys.exit("检查没过，先别推。")
    __import__("subprocess").run([sys.executable, os.path.join(HERE, "shangxian.py"), outdir, os.path.join(os.path.dirname(os.path.abspath(zdir)), "数据", "网站素材")])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
