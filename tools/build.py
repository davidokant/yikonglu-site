#!/usr/bin/env python3
"""一孔录 yikonglu.com 静态站生成器（多语种）。
输入：读法札记/*.md（只取“片里的读法”，丢“书里可走处”“观众疑问”和待核内容）、
      yuanwen.json（章号→原文）、episodes.json（集名→章号与平台 ID，只列已公开的集）、assets/（横幅、印章）、
      共享盘 数据/网站素材/<期名>/（定版稿：引文取处、读音表；原页 png）、数据/网站勘误.md、
      i18n/<lang>.json（界面与各章译文；缺的章回落到中文并标注）。
语种：zh-Hans（根目录）、zh-Hant（/zh-hant/，OpenCC 自动转台湾用字）、en（/en/）。
用法：python3 tools/build.py <读法札记目录> docs
"""
import json, re, sys, html, os, shutil, datetime, glob, csv
import og as OG
import gushi as GS
import renwu as RW

DOMAIN = "https://yikonglu.com"
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
YW_DIR = os.path.join("/mnt/project-files/一孔学-内-自媒体/数据/网站素材", "_原文")  # Codex 全书原文（朱注分章 498 章）、分章对照、异文表
FIELDS = [("常见读法", "f_common", "常"), ("字眼", "f_keys", "注"), ("诸家", "f_others", "家"), ("片里落点", "f_ours", "读")]
SOURCE = "朱熹《论语集注》（《四部备要》本）"
TAGLINE = "逐字读经典原文"
GAO_DIR = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材"  # 定版稿只在共享盘读取，不进公开仓库
GUSHI_DIR = os.environ.get("YK_GUSHI_DIR") or os.path.join(GAO_DIR, "_故事")  # “故事”栏资料；没有人物表就整栏不出
GUSHI_ON = False
RENWU_DIR = os.environ.get("YK_RENWU_DIR") or os.path.join(GAO_DIR, "_人物")  # 论语真实人物表（Codex 交）；没有就整栏不出
RENWU_ON = False
BH_DIR = os.path.join(GAO_DIR, "_白话")  # 白话直译：每行“- 1.1：……”，跟定版稿走
ZB_DIR = os.path.join(GAO_DIR, "_注本")  # Codex 注本索引（皇疏、杨伯峻、钱穆逐章 CSV）
HUANG_WK = "https://commons.wikimedia.org/w/index.php?title=File:WUL-ro12_00916_%E8%AB%96%E8%AA%9E%E9%9B%86%E8%A7%A3%E7%BE%A9%E7%96%8F_{ce}.pdf&page={n}"  # 早稻田大学图书馆藏 1750 年和刻本，册2—5
HUANG_SCAN = "https://commons.wikimedia.org/w/index.php?title=File:SSID-13146346_%E7%9F%A5%E4%B8%8D%E8%B6%B3%E9%BD%8B_%E7%AC%AC7%E9%9B%86_%E8%AB%96%E8%AA%9E%E7%BE%A9%E7%96%8F%E6%95%98_%E5%8D%B71-2.pdf&page={n}"
SUPPORT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "support.json"))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "support.json")) else {}
ANALYTICS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics.json"))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics.json")) else {}
KANWU_DEFAULT = "/mnt/project-files/一孔学-内-自媒体/数据/网站勘误.md"
INTERNAL = re.compile(r"（[^（）]*(只|转述|不上屏|不念|常识|核不到|见注|今读)[^（）]*）")

HANT_FIX = {"余力": "餘力", "余，": "餘，", "余者": "餘者", "托看": "託看", "诗云": "詩云", "子云": "子云", "干禄": "干祿"}  # 护住后手工给的繁体
LANGS = {  # code: (路径前缀, 自称, hreflang)
    "zh-Hans": ("", "简体中文", "zh-Hans"),
    "zh-Hant": ("zh-hant/", "繁體中文", "zh-Hant"),
    "en": ("en/", "English", "en"),
    "ja": ("ja/", "日本語", "ja"),
    "ko": ("ko/", "한국어", "ko"),
    "fr": ("fr/", "Français", "fr"),
    "es": ("es/", "Español", "es"),
}

ZH_UI = {
 "tagline": TAGLINE, "nav_books": "书目", "nav_search": "检索", "nav_errata": "勘误", "nav_about": "关于",
 "motto": "一孔录讲过的每一句，都能在这里核。",
 "intro": "原文、底本页码、注家原话、读音、我们的读法、公开勘误，按书按章排好。视频在各平台看，核对来这里。",
 "search_ph": "搜原文、注家原话，如：鸟数飞", "btn_books": "按书目找", "btn_errata": "看勘误",
 "p1t": "底本可查", "p1": "原文和注都从古刻本原页取，每条引文标出底本页，原页图可放大看。",
 "p2t": "注家原话", "p2": "引到谁就写谁，朱熹、程子、谢氏分开标；转述和原话分开，核不到出处的不放。",
 "p3t": "勘误公开", "p3": "讲错的地方改了就记：哪集哪句、原来怎么说、改成什么、依据是什么。",
 "books": "书目", "recent": "最近收录", "lunyu": "论语", "lunyu_sub": "二十篇 · 持续更新",
 "by_chapter": f"按篇按章排。底本：{SOURCE}。",
 "book_lead": "每章有原文、注里的关键字、诸家说法和一孔录的读法，附视频。", "covered": "已讲 {done} / {total} 章",
 "f_common": "常见的理解", "f_keys": "注里的关键字", "f_others": "诸家怎么说", "f_ours": "一孔录这样读",
 "cites": "本章引文逐条核对", "cites_note": "视频里引到的每一句注：原话、出自谁、在底本哪一页。标“转述”的是我们概括的意思，不是原话。",
 "th_quote": "引文原话", "th_src": "出自", "th_page": "底本页", "para": "转述", "pg": "原页 {n}", "other_ed": "另本",
 "reads": "读音", "th_zi": "字", "th_pos": "位置", "th_du": "读", "shots": "底本原页",
 "kw": "本章勘误", "kw_note": "", "cite": "引用本页", "copy": "复制", "copied": "已复制",
 "checked": "本页最后核对：{d}。改动记在", "errata_page": "勘误页",
 "video": "看这一章的视频", "video_in": "这一章在一孔录《{ep}》里讲：", "cn_note": "（大陆请点 B站）",
 "prev": "上一章", "next": "下一章", "chapter_no": "{book} · 第 {n} 章", "book_no": "《论语》第 {n} 篇 · 已讲 {done} / {total} 章",
 "source_line": f"原文与注据{SOURCE}", "rendering": "",
 "errata_title": "公开勘误", "errata_sub": "原文·引文·出处·读音·读法",
 "errata_p1": "一孔录讲错或说满的地方，改了就记在这里，按时间倒排，旧记录不删。画面上的小问题不记，只记内容。",
 "errata_p2": "发现错误，请写邮件到下面这个邮箱，写明哪集哪句、依据是什么，再写上你想署的网名。核实后记入此页，勘误者一栏署你的网名。也可以在任一平台「一孔录」视频下留言。", "mail_note": "邮箱做成了图片防垃圾邮件，请手动输入。", "report": "本章有错？写信告诉我们，核实后署你的网名记入勘误：", "errata_empty": "目前没有勘误。",
 "search_title": "检索", "search_sub": "原文 · 注家原话 · 读法", "search_ph2": "输入几个字，如：鸟数飞、主一无适、孝弟",
 "search_n": "找到 {n} 章", "search_none": "没有找到。未讲各章只收原文和白话。",
 "about_title": "关于一孔录", "about_p": "一孔录是一个逐字逐章读中国经典原文的频道，用讲书动画和几位固定的人物，把一句原文落到具体的人和处境上。默认你没读过原书，也不用看过前几期。",
 "about_h1": "这个网站做什么", "about_site": "平台上的视频面向大众，这里面向想核对的人：一孔录讲过的每一句，原文、底本页码、注家原话、读音、我们的读法，都能在这里查到，讲错的地方在<a href=\"kanwu.html\">勘误页</a>公开记录。",
 "about_h2": "我们的承诺", "about_c1": "原文和注家的话都从古刻本原页取，页面写明底本。", "about_c2": "先讲注家怎么说，再讲我们怎么读；我们自己的看法明说是一孔录的读法，不冒充古人。", "about_c3": "核不到出处的话不放。发现错误请告诉我们，勘误公开。",
 "about_h3": "在哪里看", "about_where": "YouTube、B站、视频号「一孔录」，播客「一孔录」（Spotify、Apple 播客、小宇宙、喜马拉雅），公众号「一孔录」。",
 "follow_h": "关注一孔录，轻松读经典", "follow_wx": "微信扫码关注公众号，回复“目录”看全部章节", "follow_yt": "在 YouTube 订阅", "foot_src": "引文均据古刻本原页，各页注明底本。发现错误请告诉我们，勘误公开。", "foot_where": "YouTube · B站 · 视频号 · 公众号 · 播客：搜「一孔录」",
 "lang_bar": "", "lang_go": "", "lang_close": "", "translated_note": "",
 "cite_fmt": "一孔录《论语·{book}》{c}“{title}”，{url}，{d} 版。",
 "hant_note": "繁體頁面由簡體自動轉換，用字按台灣習慣；原文以底本原頁為準。",
}

# 11-03 第一批新增界面字（各语种；缺的回落简体）
EXTRA_UI = {
 "zh-Hans": {"off_t": "离线", "off_h": "现在没有网络", "off_p": "看过的页面已经存在这台设备上，离线也能打开。下面是存着的章节；有网后自动更新。", "off_none": "还没有存下的章节。联网时打开几章，下次离线就能看。", "off_home": "回首页", "zb_huang_meta2": "梁 · 1750 年日本和刻本 · 卷{j}", "zb_scan2": "和刻本扫描 第 {ce} 册第 {n} 页", "wj": "未讲", "wj_tag": "未讲", "wj_lead": "这一章一孔录还没讲。先放原文和白话直译，开讲后补上注里的关键字、诸家说法和一孔录的读法。", "wj_bh_note": "白话为初稿，按朱注直译；开讲时按定版稿再核。", "wj_src": "原文据{src}，底本第 {n} 页。", "wj_yang": "杨伯峻《论语译注》分章作 {y}。", "yiwen": "异文", "yiwen_note": "底本与通行本用字不同处，原文照底本。", "th_di": "底本", "th_tong": "通行本", "th_shuo": "说明", "toc_wj": "未讲", "wj_title": "《论语·{book}》{c}｜原文与白话（未讲）｜一孔录", "foot_org": "东亚经籍校读社 · 一孔录独立编纂，无机构或基金资助", "nav_topics": "专题", "nav_more": "更多", "grp_read": "读", "grp_check": "核", "grp_use": "用", "tools_h": "查与用", "t_zt": "按仁、孝、礼等十个字读全书", "t_zi": "配音照读的每个字音", "t_bb": "每家注本用的哪个本子", "t_dt": "按篇下载，CC BY-NC 4.0", "zc_usdt": "加密货币（USDT）", "zc_usdt_net": "网络：{n}。只能用这个网络转 USDT，转错网络或别的币会丢失，无法找回。", "zc_link": "支持一孔录", "zc_title": "支持一孔录", "zc_sub": "内容全部免费，自愿赞助", "zc_p": "一孔录的原文、注、读法、勘误和开放数据永远免费，不会因为赞助多少而锁住任何一页。如果这里帮到了你，可以请我们喝杯茶，钱用在底本、扫描和配音上。", "zc_kofi": "海外读者：在 Ko-fi 赞助", "zc_wx": "国内读者：在公众号「一孔录」任一篇原创文章末尾点“赞赏”。", "zc_soon": "海外赞助页即将开通。", "cp_entry": "复制此条（带出处）", "cp_link": "复制此条链接", "bb_link": "版本说明", "hj_h": "本句互见", "hj_zb": "本章各家注", "hj_cites": "引文逐条核对", "hj_video": "视频里讲本章：{t} 起", "hj_book": "本书互见", "hj_other": "他书出处", "hj_note": "注", "bb_title": "版本与许可", "bb_sub": "每家注本用的哪个本子、页码怎么算、能不能转用", "bb_p": "一孔录引到的每一家注，都在这里说明底本、影像来源、页码算法和许可。章节页每条注旁的“版本说明”链到这里。", "bb_base": "底本", "bb_img": "影像来源", "bb_page": "页码", "bb_lic": "许可", "bb_use": "本站怎么用", "zt_title": "专题", "zt_sub": "按一个字、一个概念读《论语》", "zt_p": "每个专题列出原文里说到它的各章：已讲的章带一孔录的读法，没讲的标“未讲”，只放原文。", "zt_n": "已收 {n} 章", "zt_link": "专题", "zt_none": "已讲章节里还没有。", "dt_title": "开放数据", "dt_sub": "按篇下载原文、白话、读法、引文与读音", "dt_p": "本站数据按篇出 JSON 和 CSV，随网站每周更新。原文与古注是公版，照公版使用；白话、一孔录读法、引文核对表等一孔录自己写的内容，按 CC BY-NC 4.0 许可：可以转载、改编，须署名“一孔录 yikonglu.com”并附原页链接，不得商用。现代注本（杨伯峻、钱穆）的引文不在数据包里。", "dt_file": "文件", "dt_rows": "章数", "dt_lic": "许可：CC BY-NC 4.0（公版部分照公版）", "dt_link": "开放数据", "feed": "订阅更新（RSS）", "zi_title": "读音索引", "zi_sub": "各章配音照读的字音", "zi_p": "一孔录配音时照这里的读音读。点章号看那一章。", "th_ch": "章", "zi_link": "读音索引", "ju_reads": "本句读音：", "kw_stats": "已记 {n} 处勘误（{cats}），其中读者指出 {m} 处。", "thanks_h": "致谢", "thanks_p": "以下读者指出过一孔录的错误，按首次来信先后排：", "thanks_none": "还没有读者来信勘误。第一位指出错误的读者，网名会记在这里。", "baihua": "白话", "baihua_note": "按一孔录的读法直译，和视频一致；别家读法见下。", "ju_copy": "复制本句（带出处）", "ju_link": "复制本句链接", "ju_tip": "点原文任一句，可复制带出处的引文。",
   "zb_h": "各家注本", "zb_note": "本站底本是朱熹《论语集注》，见上文。这里并列别家：古注录疏文第一句，附原刻本扫描页；现代注本只短引一句译文，作通行读法对照。“与朱注异同”是一孔录写的说明，不是注本原文。",
   "zb_huang": "皇侃《论语义疏》", "zb_huang_meta": "梁 · 知不足斋丛书本 · 卷{j}", "zb_scan": "原刻本扫描第 {n} 页",
   "zb_yang": "杨伯峻《论语译注》", "zb_yang_meta": "中华书局 · 现代通行本，短引", "zb_qian": "钱穆《论语新解》", "zb_qian_meta": "现代通行本，短引",
   "zb_diff": "与朱注异同", "th_zb": "注本", "th_key": "关键处", "th_kind": "异同", "th_say": "说明",
   "th_sure": "把握", "s_ding": "定", "s_wen": "较稳", "s_yi": "存疑", "k_same": "同解", "k_diff": "异读", "k_add": "补充", "k_shade": "轻重不同", "k_word": "字义不同",
   "nf_h": "这一页不在了", "nf_p": "链接可能拼错，或这一页改过地址。可以搜原文，或按书目找。"},
 "en": {"off_t": "Offline", "off_h": "You are offline", "off_p": "Pages you have visited are saved on this device and open offline. Saved chapters are listed below; they update when you are back online.", "off_none": "No chapters saved yet. Open a few while online and they will be here next time.", "off_home": "Home", "zb_huang_meta2": "Liang dynasty · 1750 Japanese woodblock edition · juan {j}", "zb_scan2": "woodblock scan vol. {ce} p. {n}", "toc_wj": "not yet covered", "yiwen": "Textual variants", "yiwen_note": "Where the base edition differs from the common text; the original follows the base edition.", "th_di": "Base edition", "th_tong": "Common text", "th_shuo": "Note", "foot_org": "East Asian Classics Collation Society · independently compiled by Yikonglu, with no institutional or foundation funding", "nav_topics": "Topics", "nav_more": "More", "grp_read": "Read", "grp_check": "Check", "grp_use": "Use", "tools_h": "Tools", "t_zt": "Ten key words across the book", "t_zi": "Every reading our narration follows", "t_bb": "Which edition each commentary uses", "t_dt": "Download by book, CC BY-NC 4.0", "zc_usdt": "Crypto (USDT)", "zc_usdt_net": "Network: {n}. Send USDT on this network only; other networks or tokens will be lost and cannot be recovered.", "zc_link": "Support us", "zc_title": "Support Yikonglu", "zc_sub": "Everything stays free; support is voluntary", "zc_p": "The text, commentaries, readings, corrections and open data on this site will always be free; no page will ever be locked behind support. If this site helps you, you can buy us a tea — it pays for editions, scans and narration.", "zc_kofi": "Support on Ko-fi", "zc_wx": "Readers in mainland China: use “appreciate” at the end of any original article on our WeChat account “一孔录”.", "zc_soon": "Our Ko-fi page is coming soon.", "cp_entry": "Copy with source", "cp_link": "Copy link", "bb_link": "About this edition", "hj_h": "Cross-references", "hj_zb": "Commentaries on this chapter", "hj_cites": "Citation check", "hj_video": "In the video from {t}", "hj_book": "Elsewhere in the Analects", "hj_other": "Other sources", "hj_note": "Commentary", "bb_title": "Editions & licenses", "bb_sub": "Which edition each commentary comes from, how pages are counted, and how it may be reused", "bb_p": "For every commentary we cite, this page states the base edition, image source, page numbering and license. The “about this edition” links on chapter pages lead here.", "bb_base": "Base edition", "bb_img": "Images", "bb_page": "Pages", "bb_lic": "License", "bb_use": "How we use it", "zt_title": "Topics", "zt_sub": "Read the Analects by one word or idea", "zt_p": "Each topic lists the chapters whose original text mentions it: chapters we have covered include our reading; others show the original only.", "zt_n": "{n} chapters", "zt_link": "Topics", "zt_none": "None among covered chapters yet.", "dt_title": "Open data", "dt_sub": "Download text, renderings, readings, citations and pronunciations by book", "dt_p": "Data is published per book as JSON and CSV and updated weekly. The original text and old commentaries are public domain. Our own content (plain renderings, readings, citation tables) is licensed CC BY-NC 4.0: attribute “一孔录 Yikonglu yikonglu.com” with a link, non-commercial. Quotations from modern commentaries are not included.", "dt_file": "File", "dt_rows": "Chapters", "dt_lic": "License: CC BY-NC 4.0 (public-domain parts remain public domain)", "dt_link": "Open data", "feed": "Subscribe (RSS)", "zi_title": "Pronunciation index", "zi_sub": "Readings used in our narration", "zi_p": "These are the readings our narration follows. Click a chapter number to open it.", "th_ch": "Chapter", "zi_link": "Pronunciation index", "ju_reads": "Readings: ", "kw_stats": "{n} corrections recorded ({cats}); {m} reported by readers.", "thanks_h": "Thanks", "thanks_p": "These readers have pointed out our mistakes, in order of first report:", "thanks_none": "No reader corrections yet. The first reader to catch a mistake will be credited here.", "baihua": "Plain Chinese", "baihua_note": "A plain modern-Chinese rendering following Yikonglu's reading.", "ju_copy": "Copy this line with source", "ju_link": "Copy link to this line", "ju_tip": "Tap any sentence of the original to copy it with its source.",
   "zb_h": "Other commentaries", "zb_note": "Our base text is Zhu Xi's Collected Commentaries (above). Here are other commentaries side by side: for old commentaries, the first line of the sub-commentary with a link to the woodblock scan; for modern editions, one short quoted translation for comparison. The “compared with Zhu Xi” notes are written by Yikonglu, not quoted.",
   "zb_huang_meta": "Liang dynasty · Zhibuzu Zhai edition · juan {j}", "zb_scan": "woodblock scan p. {n}", "zb_yang_meta": "Zhonghua Book Co. · modern, short quote", "zb_qian_meta": "modern, short quote",
   "zb_diff": "Compared with Zhu Xi", "th_zb": "Commentary", "th_key": "Point", "th_kind": "Relation", "th_say": "Note",
   "th_sure": "Confidence", "s_ding": "settled", "s_wen": "fairly sure", "s_yi": "uncertain", "k_same": "same", "k_diff": "differs", "k_add": "adds", "k_shade": "nuance", "k_word": "word sense",
   "nf_h": "Page not found", "nf_p": "The link may be mistyped or the page has moved. Search the original text or browse by book."},
 "ja": {"off_t": "オフライン", "off_h": "ネットワークに接続されていません", "off_p": "一度開いたページはこの端末に保存され、オフラインでも開けます。保存済みの章は下のとおりです。接続が戻ると自動で更新されます。", "off_none": "保存済みの章はまだありません。オンラインの時に何章か開くと、次からここに出ます。", "off_home": "トップへ", "zb_huang_meta2": "梁 · 1750年和刻本 · 巻{j}", "zb_scan2": "和刻本スキャン 第{ce}冊 {n} 頁", "toc_wj": "未講", "yiwen": "異文", "yiwen_note": "底本と通行本で字が異なる箇所。原文は底本に従います。", "th_di": "底本", "th_tong": "通行本", "th_shuo": "説明", "foot_org": "東亜経籍校読社 · 一孔録 独立編纂、機関・財団の助成なし", "feed": "更新を購読（RSS）", "zi_title": "読音索引", "zi_sub": "ナレーションで用いた字音", "zi_p": "一孔録のナレーションはこの読音に従います。章番号をクリックすると開きます。", "th_ch": "章", "zi_link": "読音索引", "ju_reads": "この句の読音：", "kw_stats": "勘誤 {n} 件（{cats}）、うち読者の指摘 {m} 件。", "thanks_h": "謝辞", "thanks_p": "一孔録の誤りを指摘してくださった読者（初回の順）：", "thanks_none": "まだ読者からの勘誤はありません。最初に誤りを指摘された方のお名前をここに記します。", "baihua": "現代中国語訳", "baihua_note": "一孔録の読みに沿った現代中国語の直訳です。", "zb_huang": "皇侃『論語義疏』", "zb_yang": "楊伯峻『論語訳注』", "zb_qian": "銭穆『論語新解』", "ju_copy": "この句を出典付きでコピー", "ju_link": "この句へのリンクをコピー", "ju_tip": "原文の句をタップすると、出典付きでコピーできます。",
   "zb_h": "諸家の注釈", "zb_note": "底本は朱熹『論語集注』（上記）。ここでは他の注釈を並べます。古注は疏の最初の一句と原刻本スキャンへのリンク、現代の注釈は訳文一句のみを短く引用します。「朱注との異同」は一孔録による説明です。",
   "zb_huang_meta": "梁 · 知不足斎叢書本 · 巻{j}", "zb_scan": "原刻本スキャン {n} 頁", "zb_yang_meta": "中華書局 · 現代の通行本、短い引用", "zb_qian_meta": "現代の通行本、短い引用",
   "zb_diff": "朱注との異同", "th_zb": "注釈", "th_key": "要点", "th_kind": "異同", "th_say": "説明",
   "th_sure": "確度", "s_ding": "確定", "s_wen": "ほぼ確実", "s_yi": "存疑", "k_same": "同じ", "k_diff": "異なる読み", "k_add": "補足", "k_shade": "軽重の差", "k_word": "字義の違い",
   "nf_h": "ページが見つかりません", "nf_p": "リンクの誤りか、ページが移動しました。原文を検索するか、書目からお探しください。"},
 "ko": {"off_t": "오프라인", "off_h": "네트워크에 연결되어 있지 않습니다", "off_p": "한 번 연 페이지는 이 기기에 저장되어 오프라인에서도 열립니다. 저장된 장은 아래와 같고, 연결되면 자동으로 갱신됩니다.", "off_none": "아직 저장된 장이 없습니다. 온라인일 때 몇 장을 열어 두면 다음부터 여기에 나옵니다.", "off_home": "홈", "zb_huang_meta2": "양나라 · 1750년 일본 화각본 · 권{j}", "zb_scan2": "화각본 스캔 제{ce}책 {n}쪽", "toc_wj": "아직 다루지 않음", "yiwen": "이문", "yiwen_note": "저본과 통행본의 글자가 다른 곳. 원문은 저본을 따릅니다.", "th_di": "저본", "th_tong": "통행본", "th_shuo": "설명", "foot_org": "東亞經籍校讀社 · 一孔錄 독립 편찬, 기관·재단 후원 없음", "feed": "업데이트 구독(RSS)", "zi_title": "독음 색인", "zi_sub": "내레이션에서 읽은 글자 음", "zi_p": "일공록 내레이션은 이 독음을 따릅니다. 장 번호를 누르면 열립니다.", "th_ch": "장", "zi_link": "독음 색인", "ju_reads": "이 구절의 독음: ", "kw_stats": "감오 {n}건({cats}), 그중 독자 지적 {m}건.", "thanks_h": "감사", "thanks_p": "일공록의 오류를 지적해 주신 독자(첫 제보 순):", "thanks_none": "아직 독자 감오가 없습니다. 처음 오류를 지적한 분의 이름을 여기에 적습니다.", "baihua": "현대 중국어 풀이", "baihua_note": "일공록의 해석에 따른 현대 중국어 직역입니다.", "zb_huang": "皇侃《論語義疏》", "zb_yang": "楊伯峻《論語譯注》", "zb_qian": "錢穆《論語新解》", "ju_copy": "이 구절을 출처와 함께 복사", "ju_link": "이 구절 링크 복사", "ju_tip": "원문의 구절을 누르면 출처와 함께 복사할 수 있습니다.",
   "zb_h": "여러 주석서", "zb_note": "저본은 주희 『논어집주』(위)입니다. 여기에는 다른 주석을 나란히 둡니다. 고주는 소(疏)의 첫 구절과 원각본 스캔 링크, 현대 주석은 번역 한 구절만 짧게 인용합니다. '주희 주석과의 이동'은 일공록의 설명입니다.",
   "zb_huang_meta": "양나라 · 지부족재총서본 · 권{j}", "zb_scan": "원각본 스캔 {n}쪽", "zb_yang_meta": "중화서국 · 현대 통행본, 짧은 인용", "zb_qian_meta": "현대 통행본, 짧은 인용",
   "zb_diff": "주희 주석과의 이동", "th_zb": "주석", "th_key": "요점", "th_kind": "이동", "th_say": "설명",
   "th_sure": "확실성", "s_ding": "확정", "s_wen": "비교적 확실", "s_yi": "의문", "k_same": "같음", "k_diff": "다른 해석", "k_add": "보충", "k_shade": "경중 차이", "k_word": "자의 차이",
   "nf_h": "페이지를 찾을 수 없습니다", "nf_p": "링크가 잘못되었거나 주소가 바뀌었습니다. 원문을 검색하거나 서목에서 찾아보세요."},
 "fr": {"off_t": "Hors ligne", "off_h": "Vous êtes hors ligne", "off_p": "Les pages déjà consultées sont gardées sur cet appareil et s'ouvrent hors ligne. Les chapitres gardés sont listés ci-dessous ; ils se mettent à jour au retour du réseau.", "off_none": "Aucun chapitre gardé pour l'instant. Ouvrez-en quelques-uns en ligne et ils apparaîtront ici.", "off_home": "Accueil", "zb_huang_meta2": "dynastie Liang · éd. japonaise de 1750 · juan {j}", "zb_scan2": "xylographie vol. {ce} p. {n}", "toc_wj": "pas encore traité", "yiwen": "Variantes", "yiwen_note": "Là où l'édition de base diffère du texte courant ; l'original suit l'édition de base.", "th_di": "Édition de base", "th_tong": "Texte courant", "th_shuo": "Note", "foot_org": "Société de collation des classiques d’Asie orientale · compilé de façon indépendante par Yikonglu, sans financement institutionnel ni de fondation", "feed": "S'abonner (RSS)", "zi_title": "Index des prononciations", "zi_sub": "Lectures suivies par notre narration", "zi_p": "Notre narration suit ces lectures. Cliquez sur un numéro de chapitre pour l'ouvrir.", "th_ch": "Chapitre", "zi_link": "Index des prononciations", "ju_reads": "Lectures : ", "kw_stats": "{n} corrections enregistrées ({cats}), dont {m} signalées par des lecteurs.", "thanks_h": "Remerciements", "thanks_p": "Ces lecteurs ont relevé nos erreurs, par ordre de premier signalement :", "thanks_none": "Aucune correction de lecteur pour l'instant. Le premier à relever une erreur sera crédité ici.", "baihua": "Chinois moderne", "baihua_note": "Rendu en chinois moderne selon la lecture de Yikonglu.", "ju_copy": "Copier la phrase avec la source", "ju_link": "Copier le lien de la phrase", "ju_tip": "Touchez une phrase du texte original pour la copier avec sa source.",
   "zb_h": "Autres commentaires", "zb_note": "Notre texte de base est le commentaire de Zhu Xi (ci-dessus). Voici d'autres commentaires en regard : pour les anciens, la première phrase du sous-commentaire et un lien vers la xylographie ; pour les modernes, une seule phrase de traduction, citée brièvement. Les notes « par rapport à Zhu Xi » sont de Yikonglu.",
   "zb_huang_meta": "dynastie Liang · éd. Zhibuzu Zhai · juan {j}", "zb_scan": "xylographie p. {n}", "zb_yang_meta": "Zhonghua · moderne, citation brève", "zb_qian_meta": "moderne, citation brève",
   "zb_diff": "Par rapport à Zhu Xi", "th_zb": "Commentaire", "th_key": "Point", "th_kind": "Relation", "th_say": "Note",
   "th_sure": "Certitude", "s_ding": "établi", "s_wen": "assez sûr", "s_yi": "incertain", "k_same": "identique", "k_diff": "diverge", "k_add": "complète", "k_shade": "nuance", "k_word": "sens du mot",
   "nf_h": "Page introuvable", "nf_p": "Le lien est peut-être erroné ou la page a changé d'adresse. Cherchez dans le texte original ou parcourez par livre."},
 "es": {"off_t": "Sin conexión", "off_h": "Estás sin conexión", "off_p": "Las páginas que ya abriste se guardan en este dispositivo y se abren sin conexión. Abajo están los capítulos guardados; se actualizan al volver la red.", "off_none": "Aún no hay capítulos guardados. Abre algunos con conexión y aparecerán aquí.", "off_home": "Inicio", "zb_huang_meta2": "dinastía Liang · ed. japonesa de 1750 · juan {j}", "zb_scan2": "xilografía vol. {ce} p. {n}", "toc_wj": "aún no tratado", "yiwen": "Variantes", "yiwen_note": "Donde la edición base difiere del texto común; el original sigue la edición base.", "th_di": "Edición base", "th_tong": "Texto común", "th_shuo": "Nota", "foot_org": "Sociedad de cotejo de clásicos de Asia oriental · compilado de forma independiente por Yikonglu, sin financiación institucional ni de fundaciones", "feed": "Suscribirse (RSS)", "zi_title": "Índice de pronunciación", "zi_sub": "Lecturas que sigue nuestra narración", "zi_p": "Nuestra narración sigue estas lecturas. Haz clic en un número de capítulo para abrirlo.", "th_ch": "Capítulo", "zi_link": "Índice de pronunciación", "ju_reads": "Lecturas: ", "kw_stats": "{n} correcciones registradas ({cats}); {m} señaladas por lectores.", "thanks_h": "Agradecimientos", "thanks_p": "Estos lectores han señalado nuestros errores, por orden del primer aviso:", "thanks_none": "Aún no hay correcciones de lectores. El primero en señalar un error figurará aquí.", "baihua": "Chino moderno", "baihua_note": "Versión en chino moderno según la lectura de Yikonglu.", "ju_copy": "Copiar la frase con la fuente", "ju_link": "Copiar el enlace de la frase", "ju_tip": "Toca una frase del original para copiarla con su fuente.",
   "zb_h": "Otros comentarios", "zb_note": "Nuestro texto base es el comentario de Zhu Xi (arriba). Aquí van otros comentarios en paralelo: de los antiguos, la primera frase del subcomentario y un enlace a la xilografía; de los modernos, una sola frase de traducción citada brevemente. Las notas «frente a Zhu Xi» son de Yikonglu.",
   "zb_huang_meta": "dinastía Liang · ed. Zhibuzu Zhai · juan {j}", "zb_scan": "xilografía p. {n}", "zb_yang_meta": "Zhonghua · moderno, cita breve", "zb_qian_meta": "moderno, cita breve",
   "zb_diff": "Frente a Zhu Xi", "th_zb": "Comentario", "th_key": "Punto", "th_kind": "Relación", "th_say": "Nota",
   "th_sure": "Certeza", "s_ding": "firme", "s_wen": "bastante firme", "s_yi": "dudoso", "k_same": "igual", "k_diff": "difiere", "k_add": "añade", "k_shade": "matiz", "k_word": "sentido de la palabra",
   "nf_h": "Página no encontrada", "nf_p": "Puede que el enlace esté mal escrito o que la página haya cambiado. Busca en el texto original o explora por libro."},
}
ZH_UI.update(EXTRA_UI["zh-Hans"])

# 第三批：版本说明（/banben/）。内容是中文底账，外文页照中文显示。
BANBEN = [
 ("zhuxi", "朱熹《论语集注》（宋）", [
   ("bb_base", "《四部备要》本《论语集注》。本站原文与注的底本，视频里的朱注原页也用这一本。"),
   ("bb_img", "工坊所藏该本影印扫描；本站“底本原页”是同一扫描压缩后的图。"),
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
   ("bb_img", "工坊所藏该本影印扫描，视频里“别家原页”用这一本。"),
   ("bb_page", "按扫描文件页（从 1 起算）。"),
   ("bb_lic", "公版。"),
   ("bb_use", "视频里讲到魏晋旧说时上原页；网站引文表里标“集解”的条目据此本。")]),
 ("yangbojun", "杨伯峻《论语译注》", [
   ("bb_base", "中华书局。"),
   ("bb_img", "不放书影。"),
   ("bb_page", "页码待按一孔录所购正版核过后补上。"),
   ("bb_lic", "在版权期。本站每章只短引一句译文，作“通行读法”对照，属适当引用；不收进开放数据。"),
   ("bb_use", "“各家注本”里的一句译文和“与朱注异同”表；异同说明是一孔录写的，不是原书文字。")]),
 ("qianmu", "钱穆《论语新解》", [
   ("bb_base", "一孔录所购正版（版本信息核后补）。"),
   ("bb_img", "不放书影。"),
   ("bb_page", "页码待按正版核过后补上。"),
   ("bb_lic", "在版权期。本站每章只短引一句，作通行读法对照，属适当引用；不收进开放数据。"),
   ("bb_use", "同上。")]),
 ("yikonglu", "一孔录自己的内容", [
   ("bb_base", "白话直译、“一孔录这样读”、引文逐条核对表、读音表、勘误记录。"),
   ("bb_img", "—"),
   ("bb_page", "—"),
   ("bb_lic", '<a href="https://creativecommons.org/licenses/by-nc/4.0/deed.zh-hans" target="_blank" rel="license noopener">CC BY-NC 4.0</a>：可以转载、改编，须署名“一孔录 yikonglu.com”并附原页链接，不得商用。'),
   ("bb_use", '可在<a href="/kaifang.html">开放数据</a>按篇下载。')]),
]
# 第三批：专题（slug, 名, 匹配字, 导语）
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

def split_ju(text):
    """原文按句切：句末是 。？！ 或其后紧跟的引号。"""
    out = re.findall(r"[^。？！]+[。？！]+[”’」』]*|[^。？！]+$", text)
    return [x for x in out if x.strip()]

def parse_zhuben(d):
    """读 Codex 注本索引 CSV，返回 {章号: {"huang": {...}, "yang": {...}, "qian": {...}}}。"""
    out = {}
    if not os.path.isdir(d): return out
    def rows(prefix):
        """同一家的多份 CSV（分篇交、v1/v2）合起来：版本号小的先读，大的覆盖；同版本按文件名。空行（暂停未核）不覆盖。"""
        ver = lambda f: (int((re.search(r"-v(\d+)", f) or [0, 0])[1]), f)
        out_ = {}
        for f in sorted(glob.glob(os.path.join(d, prefix + "-*逐章*.csv")), key=ver):
            for r in csv.DictReader(open(f, encoding="utf-8-sig")):
                if r.get("章号"): out_[r["章号"].strip()] = r
        return list(out_.values())
    CN = "一二三四五六七八九十"
    for r in rows("皇疏"):
        t = (r.get("义疏首句") or "").strip().replace("其其孝悌者也", "其，其孝悌者也")  # 11-03 核收意见：疏先单释“其”字
        sure = (r.get("把握") or "").strip()
        if not t or not r.get("义疏首句PDF页") or sure == "存疑" or "待" in (r.get("状态") or ""): continue  # 宁缺：存疑、待复核的不上
        p = int(r["章号"].split(".")[0]); j = (r.get("卷") or "").strip()
        if j.isdigit(): j = CN[int(j) - 1] if int(j) <= 10 else j
        ed = "zbz" if p <= 4 else "wk"  # 知不足斋本只有卷一二（学而至里仁）；公冶长起用 1750 年和刻本
        ce = {5: 2, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3, 12: 3, 13: 4, 14: 4, 15: 4, 16: 4}.get(p, 5)
        out.setdefault(r["章号"], {})["huang"] = {"text": t, "juan": j, "page": r["义疏首句PDF页"].strip(), "leaf": r.get("章首叶面", ""), "ed": ed, "ce": ce}
    pageref = re.compile(r"[^。；]*书\s*\d+(?:[—-]\d+)?页（PDF[^）]*）[。；]?|（PDF[^）]*）")
    for key, prefix in (("yang", "杨伯峻"), ("qian", "钱穆")):
        for r in rows(prefix):
            cmp_ = pageref.sub("", r["与朱注比较"]).strip().rstrip("；")
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
            out.setdefault(r["章号"], {})[key] = {"text": r["译文一句"].strip(), "key": head if head_is_word else "", "kind": kind, "say": body if head else cmp_, "sure": {"定": "s_ding", "较稳": "s_wen", "存疑": "s_yi"}.get((r.get("把握") or "").strip(), "")}
    return out

def esc(s): return html.escape(s, quote=True)

def wj_title(text):
    """未讲章没有标题：取原文开头一句（去掉“子曰：”之类），最多 12 字。"""
    t = re.sub(r"^(子|孔子)曰：", "", text)
    t = re.split(r"[，。？！；：]", t)[0]
    return t[:12]

def cpbtn(L, text, link, link_only=False):
    """复制按钮：data-t 是要复制的引文（空则只复制链接）。"""
    sep = "，" if L.code.startswith("zh") else ", "
    b = "" if link_only else f'<button class="cp" data-t="{esc(text + sep + link)}">{L.t("cp_entry")}</button>'
    return b + f'<button class="cp" data-t="{esc(link)}">{L.t("cp_link")}</button>'

def clean(text):
    text = re.sub(r"（[^（）]*(待核|书里)[^（）]*）", "", text)
    parts = [p for p in re.split(r"(?<=[，；])", text) if "待核" not in p]
    text = "".join(parts).strip()
    text = re.sub(r"^（标题问）", "", text)
    text = text.replace("照今：", "放到今天：").replace("片里", "这里")
    text = re.sub(r"【[^】]*】", "", text)
    return text.rstrip("；，").strip()

def parse_zhaji(path):
    out, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"^### \S+ (\d+\.\d+) (.+)$", line)
        if m:
            cur = {"no": m.group(1), "title": m.group(2).strip(), "fields": {}, "tags": []}
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
    if t.isdigit(): return int(t)
    if len(t) == 1: return CN[t]
    if t[0] == "十": return 10 + CN[t[1]]
    if t[-1] == "十": return CN[t[0]] * 10
    return CN[t[0]] * 10 + CN[t[2]]
PIAN_NUM = {v[0]: k for k, v in PIAN.items()}

def parse_gao(path, yw):
    L = open(path, encoding="utf-8").read().replace("\r", "").split("\n")
    kmap, cur = {}, None
    for l in L:
        m = re.match(r"^### 第(.+?)章", l)
        if m: cur = m.group(0)
        if re.match(r"^### (开场|片尾)", l): cur = None
        k = re.match(r"^\*\*(K\d+)", l)
        if k and cur: kmap[k.group(1)] = cur
    pnum = next((v for k2, v in PIAN_NUM.items() if k2 in os.path.basename(path)), None)
    out = {}
    sec2ch = {sec: f"{pnum}.{cn2int(re.match(r'^### 第(.+?)章', sec).group(1))}" for sec in set(kmap.values())} if pnum else {}
    for row in md_tables(L, r"^## 引文取处"):
        if len(row) < 4: continue
        k, text, src, page = row[:4]
        c = sec2ch.get(kmap.get(k))
        if not c or "待核" in page or "待核" in text: continue
        para = bool(re.search(r"（[^（）]*(转述)[^（）]*）", text)) and not re.search(r"只原样念|前半转述|前后转述", text)
        text = INTERNAL.sub("", text).strip("；; ")
        if src == "经文" or not text: continue
        pages = re.findall(r"PDF0*(\d+)", page)
        other = ""
        if not pages:
            m = re.search(r"核到（([^（）]*)", page)
            other = m.group(1).split("，")[0].split("；")[0] if m else ""
        out.setdefault(c, {"cites": [], "reads": []})["cites"].append({"text": text, "src": src.replace("**", ""), "pages": pages, "para": para, "other": other})
    for row in md_tables(L, r"^## 读音"):
        if len(row) < 3: continue
        zi, pos, du = row[:3]
        if "见注" in du: continue
        for c in sec2ch.values():
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

HEAD_FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;900&family=Noto+Serif+JP:wght@400;600;900&family=Noto+Serif+KR:wght@400;600;900&display=swap" rel="stylesheet" media="print" onload="this.media=\'all\'">'
MAIL = '<picture class="mail"><source srcset="/assets/mail-dark.png" media="(prefers-color-scheme:dark)"><img src="/assets/mail.png" alt="email (image)" width="211" height="26"></picture>'
SAME_AS = ["https://www.youtube.com/@yikonglu", "https://x.com/yikonglu", "https://ko-fi.com/yikonglu"]
CSSV = __import__("hashlib").md5(open(os.path.join(HERE, "style.css"), "rb").read()).hexdigest()[:8]

LANG_JS = """<script>
(function(){var P=document.documentElement.lang,K='yk_lang';try{var s=localStorage.getItem(K)}catch(e){var s=null}
document.querySelectorAll('[data-lang]').forEach(function(a){a.addEventListener('click',function(){try{localStorage.setItem(K,a.dataset.lang)}catch(e){}})});
if(s)return;var n=(navigator.language||'').toLowerCase(),w=null;
if(n.startsWith('en'))w='en';else if(n.startsWith('ja'))w='ja';else if(n.startsWith('ko'))w='ko';else if(n.startsWith('fr'))w='fr';else if(n.startsWith('es'))w='es';else if(n.startsWith('zh')&&/tw|hk|mo|hant/.test(n))w='zh-Hant';else if(n.startsWith('zh'))w='zh-Hans';
if(!w||w===P)return;var a=document.querySelector('link[hreflang="'+w+'"]');if(!a)return;
var t={en:['This page is available in English.','Switch to English'],ja:['このページには日本語版があります。','日本語に切り替える'],ko:['이 페이지는 한국어판이 있습니다.','한국어로 전환'],fr:['Cette page existe en français.','Passer au français'],es:['Esta página está disponible en español.','Cambiar a español'],'zh-Hant':['本頁有繁體中文版。','切換到繁體'],'zh-Hans':['本页有简体中文版。','切换到简体']}[w];
var b=document.createElement('div');b.className='langbar';b.innerHTML='<span>'+t[0]+'</span><a href="'+a.href+'">'+t[1]+' →</a><button aria-label="close">×</button>';
b.querySelector('a').onclick=function(){try{localStorage.setItem(K,w)}catch(e){}};b.querySelector('button').onclick=function(){try{localStorage.setItem(K,P)}catch(e){}b.remove()};
document.body.prepend(b)})();
</script>"""

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
put(b.dataset.a==='q'?'\u201c'+cur.textContent+'\u201d\u2014\u2014'+Q.dataset.src+Q.dataset.sep+u:u,b)});
var h=location.hash.slice(1);if(/^s\\d+$/.test(h)){var t=document.getElementById(h);if(t)t.classList.add('on')}})();
</script>"""

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
    """访问统计：tools/analytics.json 里填了才加。cloudflare＝Web Analytics token；baidu＝百度统计 hm.js 的 id（只加在中文页）。"""
    a = ""
    if ANALYTICS.get("cloudflare"):
        a += f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{ANALYTICS['cloudflare']}\"}}'></script>"
    if ANALYTICS.get("baidu") and L.code.startswith("zh"):
        a += f'<script>var _hmt=_hmt||[];(function(){{var hm=document.createElement("script");hm.src="https://hm.baidu.com/hm.js?{ANALYTICS["baidu"]}";var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(hm,s)}})();</script>'
    return a

def page(L, title, desc, rel, body, jsonld=None, cls="", alts=None, og_img=None, head_extra="", codes=None):
    """rel：不带语种前缀的站内路径（"" 为首页）。"""
    url = f"{DOMAIN}/{L.prefix}{rel}"
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    codes = codes or list(LANGS)  # 只有部分语种的页（如“故事”栏只出简繁）
    if rel.startswith(("gushi/", "renwu/")): codes = ["zh-Hans", "zh-Hant"]
    alt_links = "".join(f'<link rel="alternate" hreflang="{LANGS[k][2]}" href="{DOMAIN}/{LANGS[k][0]}{rel}">' for k in codes)
    alt_links += f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/{rel}">'
    sw = "".join(f'<a href="{DOMAIN}/{LANGS[k][0]}{rel if k in codes else ""}" data-lang="{k}"{" class=cur" if k == L.code else ""}>{LANGS[k][1]}</a>' for k in LANGS)
    gs = GUSHI_ON and L.code.startswith("zh")
    rw = RENWU_ON and L.code.startswith("zh")
    P = "/" + L.prefix
    note = f'<p class="trnote wrap">{L.t("translated_note")}</p>' if L.t("translated_note") else ""
    return f"""<!doctype html>
<html lang="{L.hreflang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
{alt_links}
<link rel="alternate" type="application/atom+xml" title="一孔录" href="/{L.prefix}feed.xml">
<link rel="icon" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/seal-180.png">
<link rel="manifest" href="/{L.prefix}manifest.webmanifest">
<meta name="theme-color" content="#f6f1e6" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#17150f" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="一孔录">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="一孔录">
<meta property="og:image" content="{DOMAIN}/{og_img or "assets/og.jpg"}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">{head_extra}
<meta name="twitter:card" content="summary_large_image">
{HEAD_FONTS}
<link rel="stylesheet" href="/style.css?v={CSSV}">
{ld}
{analytics(L)}
</head>
<body class="{cls}">
<header class="top"><div class="wrap">
<a href="{P}" class="brand"><img src="/assets/seal-180.png" alt="" width="30" height="30">一孔录</a>
<nav><a href="{P}lunyu/">{L.t("nav_books")}</a><a href="{P}zhuanti/">{L.t("nav_topics")}</a><a href="{P}search.html">{L.t("nav_search")}</a><a href="{P}kanwu.html">{L.t("nav_errata")}</a>{f'<a href="{P}gushi/" class="gsnav">故事</a>' if gs else ""}
<details class="lang more"><summary>{L.t("nav_more")}</summary><div>{f'<a href="{P}renwu/">《论语》人物</a>' if rw else ""}<a href="{P}zi.html">{L.t("zi_link")}</a><a href="{P}banben/">{L.t("bb_link")}</a><a href="{P}kaifang.html">{L.t("dt_link")}</a><a href="{P}feed.xml">{L.t("feed")}</a><a href="{P}about.html">{L.t("nav_about")}</a><a href="{P}zhichi.html" class="zc">{L.t("zc_link")}</a></div></details>
<details class="lang"><summary>{L.name}</summary><div>{sw}</div></details></nav>
</div></header>
{note}
{body}
<section class="follow{'' if L.code.startswith('zh') else ' intl'}"><div class="wrap"><h2>{L.t("follow_h")}</h2><div class="fl"><figure><img src="/assets/wechat-qr.jpg" alt="WeChat QR" width="129" height="129" loading="lazy"><figcaption>{L.t("follow_wx")}</figcaption></figure><a class="btn yt" href="https://www.youtube.com/@yikonglu?sub_confirmation=1" target="_blank" rel="noopener">▶ {L.t("follow_yt")}</a></div></div></section>
<footer><div class="wrap">
<div class="fbrand"><img src="/assets/seal-180.png" alt="" width="36" height="36"><div><b>一孔录</b><span>{L.t("tagline")}</span></div></div>
<p>{L.t("foot_src")}</p>
<p class="where">{L.t("foot_where")}</p>
<div class="fgrp"><p><b>{L.t("grp_read")}</b><a href="{P}lunyu/">{L.t("nav_books")}</a><a href="{P}zhuanti/">{L.t("nav_topics")}</a><a href="{P}zi.html">{L.t("zi_link")}</a>{f'<a href="{P}renwu/">人物</a>' if rw else ""}{f'<a href="{P}gushi/">故事</a>' if gs else ""}</p><p><b>{L.t("grp_check")}</b><a href="{P}search.html">{L.t("nav_search")}</a><a href="{P}kanwu.html">{L.t("nav_errata")}</a><a href="{P}banben/">{L.t("bb_link")}</a></p><p><b>{L.t("grp_use")}</b><a href="{P}kaifang.html">{L.t("dt_link")}</a><a href="{P}feed.xml">{L.t("feed")}</a><a href="{P}about.html">{L.t("nav_about")}</a><a href="{P}zhichi.html">{L.t("zc_link")}</a></p></div>
<p class="langs">{sw}</p>
<p class="fcopy">© 2026 {L.t("foot_org")}</p>
</div></footer>
{LANG_JS}
<script>if("serviceWorker" in navigator)addEventListener("load",function(){{navigator.serviceWorker.register("/sw.js").catch(function(){{}})}})</script>
</body>
</html>
"""

def build_lang(L, D, write):
    """D：公共数据。write(rel, html) 写到该语种目录。返回本语种 URL 列表。"""
    notes, yw, gao, kw, pub, by_pian, ch2ep, pages_avail, today = (D[k] for k in ("notes", "yw", "gao", "kw", "pub", "by_pian", "ch2ep", "pages_avail", "today"))
    P = "/" + L.prefix
    urls = []
    def rel_of(c):
        p, n = c.split("."); return f"lunyu/{PIAN[p][1]}/{n}.html"
    def title_of(c): return L.ch(c).get("title") or notes[c]["title"]
    def field(c, k):
        v = L.ch(c).get(k)
        return (v, True) if v else (notes[c]["fields"].get(k), False)
    search_idx = []
    pubset = set(pub)
    def href(c):  # 已讲章各语种都有页；未讲章只出简繁，外文页链到简体
        return (P if c in pubset or L.code.startswith("zh") else "/") + rel_of(c)
    def ctitle(c): return title_of(c) if c in pubset else wj_title(D["qw"][c]["text"])
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
        return "".join(f'<li class="{"cur" if cc == c else ""}{" wj" if cc not in pubset else ""}"><a href="{href(cc)}"><em>{cc.split(".")[1]}</em>{esc(ctitle(cc))}</a></li>' for cc in D["all_by_pian"].get(pnum, by_pian.get(pnum, [])))
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
                       + cpbtn(L, f'“{h["text"]}”——皇侃《论语义疏》，{cite_src}', url + "#zb-huangkan") + f'<a class="bb" href="{P}banben/#huangkan">{L.t("bb_link")}</a></p></div>')
        for key, nk, mk in (("yang", "zb_yang", "zb_yang_meta"), ("qian", "zb_qian", "zb_qian_meta")):
            if key not in zb: continue
            z = zb[key]
            aid = {"yang": "yangbojun", "qian": "qianmu"}[key]; zh_n = {"yang": "杨伯峻《论语译注》", "qian": "钱穆《论语新解》"}[key]
            blocks += (f'<div class="zb" id="zb-{aid}"><h3>{L.t(nk)}<small>{L.t(mk)}</small></h3><p lang="zh-Hans">“{esc(z["text"])}”</p><p class="zbsrc">'
                       + cpbtn(L, f'“{z["text"]}”——{zh_n}，转引自{cite_src}', url + f"#zb-{aid}") + f'<a class="bb" href="{P}banben/#{aid}">{L.t("bb_link")}</a></p></div>')
            diffs.append((L.t(nk), z))
        order = {"k_diff": 0, "k_word": 1, "k_shade": 2, "k_add": 3, "k_same": 4}
        diffs.sort(key=lambda t: order.get(t[1]["kind"], 9))
        has_s = any(z.get("sure") for _, z in diffs)  # “把握”列：CSV 有“把握”列（定／较稳／存疑）才显示
        scell = lambda z: (f'<td><span class="sure {z["sure"]}">{L.t(z["sure"])}</span></td>' if z.get("sure") else "<td></td>") if has_s else ""
        trs = "".join(f'<tr class="{z["kind"]}"><td>{esc(nm)}</td><td class="zi">{esc(z["key"])}</td><td><span class="kind">{L.t(z["kind"])}</span></td>{scell(z)}<td lang="zh-Hans">{esc(z["say"])}</td></tr>' for nm, z in diffs)
        sth = f'<th>{L.t("th_sure")}</th>' if has_s else ""
        dtab = f'<h3 class="zbd">{L.t("zb_diff")}</h3><table class="zbt"><thead><tr><th>{L.t("th_zb")}</th><th>{L.t("th_key")}</th><th>{L.t("th_kind")}</th>{sth}<th>{L.t("th_say")}</th></tr></thead><tbody>{trs}</tbody></table>' if diffs else ""
        return f'<section class="sec zhuben" id="zhuben"><h2><i>家</i>{L.t("zb_h")}</h2><p class="note">{L.t("zb_note")}</p><div class="zbs">{blocks}</div>{dtab}</section>'

    for i, c in enumerate(pub):
        n = notes[c]; pnum, cnum = c.split("."); pname, slug, pfull, _ = PIAN[pnum]
        epname, ep = ch2ep[c]; rel = rel_of(c); url = f"{DOMAIN}/{L.prefix}{rel}"
        og_img = D["og"].get(c, {}).get("hant" if L.code in ("zh-Hant", "ja", "ko") else "hans")
        bname = L.book(pnum)
        name = f"《论语·{pname}》{c} {n['title']}" if L.code == "zh-Hans" else f"{L.t('lunyu')} {c} {title_of(c)}"
        desc = f"{yw[c][:60]}……原文、白话、朱熹注的关键字、诸家说法与一孔录的读法。" if L.code == "zh-Hans" else f"{yw[c][:40]}… {L.t('book_lead')}"
        secs = ""
        for k, lab, mark in FIELDS:
            v, translated = field(c, k)
            if not v: continue
            secs += f'<section class="sec sec-{mark}"><h2><i>{mark}</i>{L.t(lab)}</h2><p{"" if translated or L.code=="zh-Hans" else " lang=zh-Hans"}>{quotes(v)}</p></section>'
        prev_c = pub[i-1] if i > 0 else None; next_c = pub[i+1] if i+1 < len(pub) else None
        def card(cc, lab, cls):
            if not cc: return '<span></span>'
            return f'<a class="pncard {cls}" href="{P}{rel_of(cc)}"><small>{lab}</small><b>{cc}　{esc(title_of(cc))}</b></a>'
        side = sidebar(pnum, c)
        yt = ep.get("youtube", ""); g = gao.get(c, {"cites": [], "reads": []})
        st = ep.get("starts", {}).get(c) or D["starts"].get(yt, {}).get(c)  # 本章在视频里从第几秒讲起（发布线程补）
        pub_at = ep.get("public_at", "")  # 定时公开的集：公开前视频块先藏着，到点由页内脚本显示
        future = bool(pub_at) and datetime.datetime.fromisoformat(pub_at) > datetime.datetime.now(datetime.timezone.utc)
        vid_html = (f"""<section class="video"{f' hidden data-pub="{pub_at}"' if future else ""}><h2><i>看</i>{L.t("video")}</h2>
<div class="vid"><iframe loading="lazy" src="https://www.youtube-nocookie.com/embed/{yt}{f'?start={st}' if st else ''}" title="{esc(epname)}" allowfullscreen></iframe></div>
<p class="vlinks">{L.t("video_in", ep=epname)}<a href="https://www.youtube.com/watch?v={yt}{f'&amp;t={st}s' if st else ''}">YouTube</a><a href="https://www.bilibili.com/video/{ep['bilibili']}{f'?t={st}' if st else ''}">Bilibili</a>{L.t("cn_note")}</p></section>""" + (f'<script>(function(){{var s=document.querySelector("section.video[data-pub]");if(!s)return;function f(){{if(Date.now()>=Date.parse(s.dataset.pub)){{s.hidden=false;return true}}}}if(!f())var t=setInterval(function(){{if(f())clearInterval(t)}},60000)}})();</script>' if future else "")) if yt else ""  # 视频还没上传（只排了时间）就先不放视频块
        def pg(nums):
            return " ".join(f'<a class="pg" href="/yuanye/p{int(x):03d}.jpg" target="_blank">{L.t("pg", n=x)}</a>' if x in pages_avail else f'<span class="pg">{L.t("pg", n=x)}</span>' for x in nums)
        extra = ""
        if g["cites"]:
            extra += (f'<section class="sec cites" id="zb-zhuxi"><h2><i>核</i>{L.t("cites")}</h2><p class="note">{L.t("cites_note")} <a class="bb" href="{P}banben/#zhuxi">{L.t("bb_link")}</a> {cpbtn(L, "", url + "#zb-zhuxi", link_only=True)}</p><table><thead><tr><th>{L.t("th_quote")}</th><th>{L.t("th_src")}</th><th>{L.t("th_page")}</th></tr></thead><tbody>'
                      + "".join(f'<tr><td lang="zh-Hans">{"<span class=para>" + L.t("para") + "</span>" + esc(x["text"]) if x["para"] else "“" + esc(x["text"]) + "”"}</td><td>{esc(L.src(x["src"]))}</td><td>{pg(x["pages"]) if x["pages"] else "<span class=oth>" + esc(x["other"] or L.t("other_ed")) + "</span>"}</td></tr>' for x in g["cites"]) + "</tbody></table></section>")
        if g["reads"]:
            extra += (f'<section class="sec reads"><h2><i>音</i>{L.t("reads")}</h2><table><thead><tr><th>{L.t("th_zi")}</th><th>{L.t("th_pos")}</th><th>{L.t("th_du")}</th></tr></thead><tbody>'
                      + "".join(f'<tr><td class="zi">{esc(x["zi"])}</td><td>{esc(x["pos"])}</td><td>{esc(x["du"])}</td></tr>' for x in g["reads"]) + "</tbody></table></section>")
        allpages = sorted({x for r in g["cites"] for x in r["pages"]}, key=int)
        imgs = "".join(f'<a href="/yuanye/p{int(x):03d}.jpg" target="_blank"><img loading="lazy" src="/yuanye/p{int(x):03d}.jpg" alt="{L.t("pg", n=x)}"><span>{L.t("pg", n=x)}</span></a>' for x in allpages if x in pages_avail)
        if imgs: extra += f'<section class="sec shots"><h2><i>页</i>{L.t("shots")}</h2><div class="pages">{imgs}</div></section>'
        mine = [r for r in kw if r[2] == c]
        if mine:
            extra += (f'<section class="sec kw"><h2><i>勘</i>{L.t("kw")}</h2>{"<p class=note>" + L.t("kw_note") + "</p>" if L.t("kw_note") else ""}<ul lang="zh-Hans">' + "".join(
                f'<li><b>{esc(r[0])}　{esc(r[3])}</b>原来：{esc(r[4])}；改为：{esc(r[5])}（依据：{esc(r[6])}；勘误者：{esc(r[7])}）</li>' for r in mine) + '</ul></section>')
        cite_txt = L.t("cite_fmt", book=(pname if L.code == "zh-Hans" else bname), c=c, title=title_of(c), url=url, d=today)
        extra += f'<section class="citeit"><b>{L.t("cite")}</b><code>{esc(cite_txt)}</code><button onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent);this.textContent=\'{L.t("copied")}\'">{L.t("copy")}</button><p>{L.t("checked", d=today)}<a href="{P}kanwu.html">{L.t("errata_page")}</a>.</p><p class="mailp">{L.t("report")} {MAIL}</p></section>'
        search_idx.append({"c": c, "t": title_of(c), "u": P + rel, "y": yw[c],
                           "x": " ".join(v for k, _, _ in FIELDS for v in [field(c, k)[0]] if v) + " " + " ".join(x["text"] + x["src"] for x in g["cites"])
                                + " " + " ".join(v["text"] for v in D["zhuben"].get(c, {}).values())})
        ju_html = "".join(f'<span class="ju" id="s{j}" tabindex="0">{esc(x)}</span>' for j, x in enumerate(split_ju(yw[c]), 1))
        cite_src = (f"《论语·{pname}》{c}，一孔录" if L.code.startswith("zh") else f"{L.t('lunyu')} {c}, 一孔录 Yikonglu")
        zb = D["zhuben"].get(c, {}); hj_data = hj_of(c)
        extra = zb_section(c, url, cite_src) + extra
        bh = D["baihua"].get(c)
        bh_html = f'<section class="sec sec-白"><h2><i>白</i>{L.t("baihua")}</h2><p lang="zh-Hans">{esc(bh)}</p><p class="note">{L.t("baihua_note")}</p></section>' if bh else ""
        rend = L.ch(c).get("yw")
        rend_html = f'<p class="rend">{esc(rend)}</p><figcaption>{L.t("rendering")}</figcaption>' if rend else ""
        body = f"""<div class="chhead"><div class="wrap">
<p class="crumb"><a href="{P}lunyu/">{L.t("lunyu")}</a> › <a href="{P}lunyu/{slug}/">{bname}</a></p>
<h1><span class="no">{L.t("chapter_no", book=(pname if L.code=="zh-Hans" else bname), n=cnum)}</span>{esc(title_of(c))}</h1>
</div></div>
<main class="wrap chapter">
<article>
<figure class="yuanwen"><blockquote lang="zh-Hans" data-src="{esc(cite_src)}" data-url="{url}" data-sep="{'，' if L.code.startswith('zh') else ', '}" data-reads="{esc(json.dumps([[x['zi'], x['pos'], x['du']] for x in g['reads']], ensure_ascii=False))}" data-rl="{esc(L.t('ju_reads'))}" data-hj="{esc(json.dumps(hj_data, ensure_ascii=False))}">{ju_html}</blockquote><figcaption>{L.t("source_line")}</figcaption>{rend_html}<p class="jutip">{L.t("ju_tip")}</p></figure>
{bh_html}
{secs}
{yiwen_html(c)}
{extra}
{vid_html}
<p class="tags">{''.join(f'<span>#{esc(t)}</span>' for t in n['tags'])}</p>{RW.chip_line(D.get("renwu"), c, P) if L.code.startswith("zh") else ""}{GS.footer_line(D.get("gushi"), c, P) if L.code.startswith("zh") else ""}
<nav class="pn">{card(prev_c, L.t("prev"), 'prev')}{card(next_c, L.t("next"), 'next')}</nav>
</article>
<aside><h3>{bname}</h3><ol>{side}</ol></aside>
</main>"""
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
        if st and "video" in ld:
            ld["video"]["hasPart"] = [{"@type": "Clip", "name": f"{c} {title_of(c)}", "startOffset": int(st), "url": f"https://www.youtube.com/watch?v={yt}&t={int(st)}s"}]
        ttl = f"{name}｜原文、白话与读法｜一孔录" if L.code == "zh-Hans" else f"{name} | 一孔录 Yikonglu"
        first = D["first"].get(c, today)
        hj_static = "<ul>" + (f'<li><a href="#zhuben">{L.t("hj_zb")}</a></li>' if zb else "") + (f'<li><a href="#zb-zhuxi">{L.t("hj_cites")}</a></li>' if g["cites"] else "") \
            + (f'<li><a href="https://www.youtube.com/watch?v={yt}&amp;t={st}s" target="_blank" rel="noopener">{L.t("hj_video", t=f"{st//60}:{st%60:02d}")}</a></li>' if st else "") + "</ul>"
        bc = {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "一孔录", "item": f"{DOMAIN}/{L.prefix}"},
            {"@type": "ListItem", "position": 2, "name": L.t("lunyu"), "item": f"{DOMAIN}/{L.prefix}lunyu/"},
            {"@type": "ListItem", "position": 3, "name": bname, "item": f"{DOMAIN}/{L.prefix}lunyu/{slug}/"},
            {"@type": "ListItem", "position": 4, "name": f"{c} {title_of(c)}", "item": url}]}
        ld.pop("@context"); ld["datePublished"] = first
        ld = {"@context": "https://schema.org", "@graph": [ld, bc]}
        cit = "".join(f'<meta name="{k}" content="{esc(v)}">' for k, v in [
            ("citation_title", name), ("citation_author", "一孔录"), ("citation_publisher", "一孔录 yikonglu.com"),
            ("citation_publication_date", first.replace("-", "/")), ("citation_online_date", today.replace("-", "/")),
            ("citation_language", L.hreflang), ("citation_public_url", url),
            ("DC.title", name), ("DC.creator", "一孔录"), ("DC.date", first), ("DC.language", L.hreflang), ("DC.source", SOURCE)])
        write(rel, page(L, ttl, desc, rel, body + JU_JS.replace("@HJH@", L.t("hj_h")).replace("@HJ@", hj_static).replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied")), ld, "pg-chapter", og_img=og_img, head_extra=cit)); urls.append(url)


    # 未讲各章：只出简繁。原文（朱注分章底本）、白话初稿、本句互见、异文、各家注本
    if L.code.startswith("zh"):
        for p_, cs in D["all_by_pian"].items():
            for k, c in enumerate(cs):
                if c in pubset: continue
                q = D["qw"][c]; text = q["text"]; pnum, cnum = c.split("."); pname, slug, pfull, _ = PIAN[pnum]
                rel = rel_of(c); url = f"{DOMAIN}/{L.prefix}{rel}"; bname = L.book(pnum)
                cite_src = f"《论语·{pname}》{c}，一孔录"
                ju_html = "".join(f'<span class="ju" id="s{j}" tabindex="0">{esc(x)}</span>' for j, x in enumerate(split_ju(text), 1))
                pgn = str(q.get("pdf_page", ""))
                pgl = (f'<a class="pg" href="/yuanye/p{int(pgn):03d}.jpg" target="_blank">{pgn}</a>' if pgn in pages_avail else pgn) if pgn else ""
                cap = L.t("wj_src", src=SOURCE, n=pgl) if pgn else L.t("source_line")
                y = D["fz"].get(c)
                if y and y != c: cap += " " + L.t("wj_yang", y=y)
                bh = D["baihua"].get(c)
                bh_html = f'<section class="sec sec-白"><h2><i>白</i>{L.t("baihua")}</h2><p lang="zh-Hans">{esc(bh)}</p><p class="note">{L.t("wj_bh_note")}</p></section>' if bh else ""
                prev_c = cs[k-1] if k > 0 else None; next_c = cs[k+1] if k+1 < len(cs) else None
                pn = "".join(f'<a class="pncard {cl}" href="{href(cc)}"><small>{L.t(lab)}</small><b>{cc}　{esc(ctitle(cc))}</b></a>' if cc else "<span></span>" for cc, lab, cl in ((prev_c, "prev", "prev"), (next_c, "next", "next")))
                body = f"""<div class="chhead"><div class="wrap">
<p class="crumb"><a href="{P}lunyu/">{L.t("lunyu")}</a> › <a href="{P}lunyu/{slug}/">{bname}</a></p>
<h1><span class="no">{L.t("chapter_no", book=pname, n=cnum)} · <em class="wjtag">{L.t("wj_tag")}</em></span>{esc(ctitle(c))}</h1>
</div></div>
<main class="wrap chapter">
<article>
<p class="wjlead">{L.t("wj_lead")}</p>
<figure class="yuanwen"><blockquote lang="zh-Hans" data-src="{esc(cite_src)}" data-url="{url}" data-sep="，" data-reads="[]" data-rl="" data-hj="{esc(json.dumps(hj_of(c), ensure_ascii=False))}">{ju_html}</blockquote><figcaption>{cap}</figcaption><p class="jutip">{L.t("ju_tip")}</p></figure>
{bh_html}
{yiwen_html(c)}
{zb_section(c, url, cite_src)}
<section class="citeit"><p class="mailp">{L.t("report")} {MAIL}</p></section>
<nav class="pn">{pn}</nav>
</article>
<aside><h3>{bname}</h3><ol>{sidebar(pnum, c)}</ol></aside>
</main>"""
                hj_static = "<ul>" + (f'<li><a href="#zhuben">{L.t("hj_zb")}</a></li>' if D["zhuben"].get(c) else "") + "</ul>"
                desc = f"{text[:70]}……《论语·{pname}》第 {cnum} 章原文与白话直译。"
                ld = {"@context": "https://schema.org", "@type": "Article", "headline": f"《论语·{pname}》{c} {ctitle(c)}", "inLanguage": L.hreflang, "url": url,
                      "author": {"@type": "Organization", "name": "一孔录", "url": DOMAIN}, "about": {"@type": "Book", "name": "论语"},
                      "isBasedOn": {"@type": "Book", "name": "论语集注", "author": {"@type": "Person", "name": "朱熹"}}}
                write(rel, page(L, L.t("wj_title", book=pname, c=c), desc, rel, body + JU_JS.replace("@HJH@", L.t("hj_h")).replace("@HJ@", hj_static).replace("@COPY@", L.t("ju_copy")).replace("@LINK@", L.t("ju_link")).replace("@DONE@", L.t("copied")), ld, "pg-chapter pg-wj", codes=["zh-Hans", "zh-Hant"])); urls.append(url)
                search_idx.append({"c": c, "t": ctitle(c), "u": P + rel, "y": text, "x": (bh or "") + " " + " ".join(v["text"] for v in D["zhuben"].get(c, {}).values())})

    def toc(cs):
        def li(c):
            if c in pubset:
                return f'<li><a href="{P}{rel_of(c)}"><em>{c}</em><b>{esc(title_of(c))}</b><span>{esc((field(c, "片里落点")[0] or "").split("；")[0].split(". Today")[0])}</span></a></li>'
            t = D["qw"][c]["text"]
            return f'<li class="wj"><a href="{href(c)}"><em>{c}</em><b>{esc(ctitle(c))}</b><span><i class="wjtag">{L.t("toc_wj")}</i><span lang="zh-Hans">{esc(t[:40] + ("……" if len(t) > 40 else ""))}</span></span></a></li>'
        return '<ol class="toc">' + "".join(li(c) for c in cs) + "</ol>"
    def pcard(p):
        pname, slug, pfull, total = PIAN[p]; done = len(by_pian.get(p, [])); pct = round(done * 100 / total)
        return (f'<a class="pcard" href="{P}lunyu/{slug}/"><b>{pname}</b><small>{L.book(p)}</small><span class="bar"><i style="width:{pct}%"></i></span><em>{L.t("covered", done=done, total=total)}</em></a>')

    toc_all = ""
    ALLP = sorted(set(by_pian) | set(D["all_by_pian"]), key=int)
    for p in ALLP:
        pname, slug, pfull, total = PIAN[p]; cs = D["all_by_pian"].get(p) or by_pian[p]
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}lunyu/">{L.t("lunyu")}</a></p>
<h1><span class="no">{L.t("book_no", n=p, done=len(by_pian.get(p, [])), total=total)}</span>{L.book(p)}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("book_lead")}</p>{toc(cs)}</main>'''
        ttl = f"《论语·{pname}》逐章原文与读法｜一孔录" if L.code == "zh-Hans" else f"{L.t('lunyu')} · {L.book(p)} | 一孔录 Yikonglu"
        write(f"lunyu/{slug}/index.html", page(L, ttl, L.t("book_lead"), f"lunyu/{slug}/", body)); urls.append(f"{DOMAIN}/{L.prefix}lunyu/{slug}/")
        if p in by_pian: toc_all += f'<h2 class="ph"><a href="{P}lunyu/{slug}/">{L.book(p)}</a></h2>{toc(by_pian[p])}'
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("lunyu_sub")}</span>{L.t("lunyu")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("by_chapter")}</p><div class="pcards">{"".join(pcard(p) for p in ALLP)}</div>{toc_all}</main>'''
    write("lunyu/index.html", page(L, ("《论语》逐章原文与读法｜一孔录" if L.code == "zh-Hans" else f"{L.t('lunyu')} | 一孔录 Yikonglu"), L.t("by_chapter"), "lunyu/", body)); urls.append(f"{DOMAIN}/{L.prefix}lunyu/")

    recent = pub[-6:][::-1]
    home = f'''<section class="banner"><picture><source media="(max-width:700px)" srcset="/assets/banner-m3.jpg"><img src="/assets/banner-w.jpg" alt="一孔录片中人物围坐长桌读书" width="3072" height="720"></picture></section>
<main class="home">
<section class="intro wrap narrow">
<h1>一孔录<small>{L.t("tagline")}</small></h1>
<p class="motto">{L.t("motto")}</p>
<p>{L.t("intro")}</p>
<form class="sbox" action="{P}search.html"><input name="q" placeholder="{esc(L.t("search_ph"))}"><button>{L.t("nav_search")}</button></form>
<p class="cta"><a class="btn" href="{P}lunyu/">{L.t("btn_books")}</a><a class="btn ghost" href="{P}kanwu.html">{L.t("btn_errata")}</a></p>
</section>
<section class="pillars wrap">
<div><i>原</i><b>{L.t("p1t")}</b><p>{L.t("p1")}</p></div>
<div><i>注</i><b>{L.t("p2t")}</b><p>{L.t("p2")}</p></div>
<div><i>勘</i><b>{L.t("p3t")}</b><p>{L.t("p3")}</p></div>
</section>
<section class="wrap narrow"><h2 class="ph">{L.t("tools_h")}</h2><div class="tools"><a href="{P}zhuanti/"><b>{L.t("zt_title")}</b><span>{L.t("t_zt")}</span></a><a href="{P}zi.html"><b>{L.t("zi_title")}</b><span>{L.t("t_zi")}</span></a><a href="{P}banben/"><b>{L.t("bb_title")}</b><span>{L.t("t_bb")}</span></a><a href="{P}kaifang.html"><b>{L.t("dt_title")}</b><span>{L.t("t_dt")}</span></a></div></section>
<section class="wrap narrow"><h2 class="ph">{L.t("books")}</h2><h3 class="bookh"><a href="{P}lunyu/">《论语》{" · " + L.t("lunyu") if L.code in ("en", "fr", "es") else ""}</a></h3><div class="pcards">{"".join(pcard(p) for p in ALLP)}</div></section>
<section class="wrap narrow"><h2 class="ph">{L.t("recent")}</h2>{toc(recent)}</section>
</main>'''
    write("index.html", page(L, (f"一孔录｜{TAGLINE}" if L.code == "zh-Hans" else f"一孔录 Yikonglu | {L.t('tagline')}"), L.t("intro"), "", home,
          {"@context": "https://schema.org", "@type": "Organization", "name": "一孔录", "alternateName": "Yikonglu", "url": DOMAIN, "logo": f"{DOMAIN}/assets/seal-180.png", "sameAs": SAME_AS}, "pg-home"))
    urls.insert(0, f"{DOMAIN}/{L.prefix}")
    about = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("tagline")}</span>{L.t("about_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("about_p")}</p>
<h2>{L.t("about_h1")}</h2><p>{L.t("about_site").replace('href="kanwu.html"', f'href="{P}kanwu.html"').replace('href="errata.html"', f'href="{P}kanwu.html"')}</p>
<h2>{L.t("about_h2")}</h2><ul><li>{L.t("about_c1")}</li><li>{L.t("about_c2")}</li><li>{L.t("about_c3")}</li></ul>
<h2>{L.t("about_h3")}</h2><p>{L.t("about_where")}</p><p class="outl"><a class="btn yt" href="https://www.youtube.com/@yikonglu?sub_confirmation=1" target="_blank" rel="noopener">▶ YouTube</a> <a class="btn ghost" href="https://search.bilibili.com/all?keyword=%E4%B8%80%E5%AD%94%E5%BD%95" target="_blank" rel="noopener">Bilibili</a></p></main>'''
    write("about.html", page(L, L.t("about_title"), L.t("about_p")[:120], "about.html", about)); urls.append(f"{DOMAIN}/{L.prefix}about.html")

    if kw:
        trs = "".join(f"<tr><td>{esc(r[0])}</td><td>{esc(r[1])} {esc(r[2])}</td><td>{esc(r[3])}</td><td>{esc(r[4])}</td><td>{esc(r[5])}</td><td>{esc(r[6])}</td><td class=\"who\">{esc(r[7])}</td></tr>" for r in reversed(kw))
        ktable = f'<div class="tw"><table lang="zh-Hans"><thead><tr><th>日期</th><th>集·章</th><th>类别</th><th>原来</th><th>改为</th><th>依据</th><th>勘误者</th></tr></thead><tbody>{trs}</tbody></table></div>'
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
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("search_sub")}</span>{L.t("search_title")}</h1></div></div>
<main class="wrap narrow"><form class="sbox" onsubmit="go();return false"><input id="q" placeholder="{esc(L.t("search_ph2"))}"><button>{L.t("nav_search")}</button></form><div id="res"></div></main>
<script>
let D=null;const q=document.getElementById('q'),R=document.getElementById('res');
const E=s=>s.replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
function cut(s,k){{const i=s.indexOf(k);if(i<0)return E(s.slice(0,60));const a=Math.max(0,i-24);return(a?'…':'')+E(s.slice(a,i))+'<mark>'+E(k)+'</mark>'+E(s.slice(i+k.length,i+k.length+36))+'…'}}
async function go(){{const k=q.value.trim();if(!k){{R.innerHTML='';return}}
if(!D){{try{{D=await (await fetch('{P}search.json')).json()}}catch(e){{R.textContent='…';return}}}}
history.replaceState(null,'','?q='+encodeURIComponent(k));
const hit=D.filter(d=>(d.y+d.t+d.x).includes(k));
R.innerHTML=hit.length?'<p class="lead">'+{json.dumps(L.t("search_n", n="N"))}.replace('N',hit.length)+'</p><ol class="toc">'+hit.map(d=>'<li><a href="'+d.u+'"><em>'+d.c+'</em><b>'+E(d.t)+'</b><span>'+cut(d.y.includes(k)?d.y:d.x,k)+'</span></a></li>').join('')+'</ol>':{json.dumps("<p class=empty>" + L.t("search_none") + "</p>")}}}
const p=new URLSearchParams(location.search).get('q');if(p){{q.value=p;go()}}
</script>'''
    write("search.html", page(L, f'{L.t("search_title")}｜一孔录', L.t("search_sub"), "search.html", body))
    if L.code == "zh-Hans":  # GitHub Pages 只认根目录 404.html
        en = EXTRA_UI["en"]
        body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">404</span>{L.t("nf_h")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("nf_p")}</p><p class="lead" lang="en">{en["nf_h"]}. {en["nf_p"]}</p>
<form class="sbox" action="/search.html"><input name="q" placeholder="{esc(L.t("search_ph"))}"><button>{L.t("nav_search")}</button></form>
<p class="cta"><a class="btn" href="/lunyu/">{L.t("btn_books")}</a><a class="btn ghost" href="/">yikonglu.com</a></p><h2 class="ph">{L.t("recent")}</h2>{toc(recent)}</main>'''
        write("404.html", page(L, f'{L.t("nf_h")}｜一孔录', L.t("nf_p"), "404.html", body, head_extra='<meta name="robots" content="noindex">'))
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
    # 版本与许可
    cards = ""
    for aid, name, rows in BANBEN:
        cards += f'<section class="bbcard" id="{aid}"><h2>{esc(name)}</h2><dl lang="zh-Hans">' + "".join(f"<dt>{L.t(k)}</dt><dd>{v}</dd>" for k, v in rows) + "</dl></section>"
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("bb_sub")}</span>{L.t("bb_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("bb_p")}</p>{cards}</main>'''
    write("banben/index.html", page(L, f'{L.t("bb_title")}｜一孔录', L.t("bb_sub"), "banben/", body)); urls.append(f"{DOMAIN}/{L.prefix}banben/")
    # 专题
    zlist = ""
    for slug, name, terms, intro in ZHUANTI:
        tx = lambda c: yw[c] if c in pubset else D["qw"][c]["text"]
        allc = sorted(pubset | set(D["qw"]), key=lambda c: tuple(map(int, c.split("."))))
        hit = [c for c in allc if any(t in tx(c) for t in terms)]
        def mark(t):
            t = esc(t)
            for w in terms: t = t.replace(esc(w), f"<mark>{esc(w)}</mark>")
            return t
        items = "".join(f'<li{"" if c in pubset else " class=wj"}><a href="{href(c)}"><em>{c}</em><b>{esc(ctitle(c))}</b>{"" if c in pubset else "<i class=wjtag>" + L.t("toc_wj") + "</i>"}</a><p class="zy" lang="zh-Hans">{mark(tx(c))}</p>'
                        + (f'<p class="zd">{esc(field(c, "片里落点")[0])}</p>' if c in pubset and field(c, "片里落点")[0] else "") + "</li>" for c in hit)
        body = f'''<div class="chhead"><div class="wrap"><p class="crumb"><a href="{P}zhuanti/">{L.t("zt_title")}</a></p><h1><span class="no">{L.t("zt_n", n=len(hit))}</span>{esc(name)}</h1></div></div>
<main class="wrap narrow"><p class="lead" lang="zh-Hans">{esc(intro)}</p><p class="note">{L.t("zt_p")}</p>{"<ol class=ztl>" + items + "</ol>" if items else "<p class=empty>" + L.t("zt_none") + "</p>"}</main>'''
        write(f"zhuanti/{slug}.html", page(L, f"《论语》里的“{name}”｜{L.t('zt_title')}｜一孔录" if L.code.startswith("zh") else f"{name} in the Analects | 一孔录 Yikonglu", intro[:110], f"zhuanti/{slug}.html", body)); urls.append(f"{DOMAIN}/{L.prefix}zhuanti/{slug}.html")
        zlist += f'<a class="ztcard" href="{P}zhuanti/{slug}.html"><b>{esc(name)}</b><small>{L.t("zt_n", n=len(hit))}</small></a>'
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("zt_sub")}</span>{L.t("zt_title")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("zt_p")}</p><div class="ztcards">{zlist}</div></main>'''
    write("zhuanti/index.html", page(L, f'{L.t("zt_title")}｜一孔录', L.t("zt_sub"), "zhuanti/", body)); urls.append(f"{DOMAIN}/{L.prefix}zhuanti/")
    if D.get("gushi") and L.code.startswith("zh"):  # “故事”栏：只简繁
        urls += GS.build(L, D, D["gushi"], write, page, P, rel_of, title_of, split_ju, DOMAIN)
    if D.get("renwu") and L.code.startswith("zh"):  # 论语人物：先只简繁
        urls += RW.build(L, D, D["renwu"], write, page, P, rel_of, title_of, DOMAIN)
    # 开放数据（文件只在根目录 /data/，各语种只出说明页）
    rows = "".join(f'<tr><td>{L.book(p)}</td><td><a href="/data/lunyu-{PIAN[p][1]}.json">JSON</a> · <a href="/data/lunyu-{PIAN[p][1]}.csv">CSV</a></td><td>{len(by_pian[p])}</td></tr>' for p in sorted(by_pian, key=int))
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("dt_sub")}</span>{L.t("dt_title")}</h1></div></div>
<main class="wrap narrow prose"><p>{L.t("dt_p")}</p><div class="tw"><table class="zitab"><thead><tr><th>{L.t("lunyu")}</th><th>{L.t("dt_file")}</th><th>{L.t("dt_rows")}</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">{L.t("dt_lic")} · <a href="https://creativecommons.org/licenses/by-nc/4.0/deed.zh-hans" rel="license noopener" target="_blank">CC BY-NC 4.0</a> · <a href="{P}banben/">{L.t("bb_link")}</a></p></main>'''
    write("kaifang.html", page(L, f'{L.t("dt_title")}｜一孔录', L.t("dt_sub"), "kaifang.html", body)); urls.append(f"{DOMAIN}/{L.prefix}kaifang.html")
    # 读音索引
    zi = {}
    for c in pub:
        for x in gao.get(c, {"reads": []})["reads"]:
            zi.setdefault((x["zi"], x["du"]), []).append((c, x["pos"]))
    trs = "".join(f'<tr><td class="zi">{esc(z)}</td><td>{esc(du)}</td><td lang="zh-Hans">' + "<br>".join(f'<a href="{P}{rel_of(c)}">{c}</a> {esc(pos)}' for c, pos in lst) + "</td></tr>"
                  for (z, du), lst in sorted(zi.items(), key=lambda kv: (kv[0][0], kv[0][1])))
    body = f'''<div class="chhead"><div class="wrap"><h1><span class="no">{L.t("zi_sub")}</span>{L.t("zi_title")}</h1></div></div>
<main class="wrap narrow"><p class="lead">{L.t("zi_p")}</p><div class="tw"><table class="zitab"><thead><tr><th>{L.t("th_zi")}</th><th>{L.t("th_du")}</th><th>{L.t("th_ch")} · {L.t("th_pos")}</th></tr></thead><tbody>{trs}</tbody></table></div></main>'''
    write("zi.html", page(L, f'{L.t("zi_title")}｜一孔录', L.t("zi_p"), "zi.html", body)); urls.append(f"{DOMAIN}/{L.prefix}zi.html")
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
        "start_url": P + "?source=pwa", "scope": "/", "display": "standalone", "background_color": "#f6f1e6", "theme_color": "#f6f1e6",
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
    """开放数据：每篇一份 JSON 和 CSV（只含公版原文与古注、一孔录自己的内容；不含现代注本引文）。"""
    os.makedirs(os.path.join(outdir, "data"), exist_ok=True)
    lic = {"license": "CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/); 原文与古注为公版", "attribution": "一孔录 Yikonglu, https://yikonglu.com", "generated": D["today"]}
    for p, cs in D["by_pian"].items():
        rows = []
        for c in cs:
            n = D["notes"][c]; g = D["gao"].get(c, {"cites": [], "reads": []}); h = D["zhuben"].get(c, {}).get("huang")
            rows.append({"chapter": c, "title": n["title"], "url": f"{DOMAIN}/lunyu/{PIAN[p][1]}/{c.split('.')[1]}.html", "text": D["yw"][c],
                         "sentences": split_ju(D["yw"][c]), "baihua": D["baihua"].get(c, ""), "common_reading": n["fields"].get("常见读法", ""),
                         "zhu_keys": n["fields"].get("字眼", ""), "others": n["fields"].get("诸家", ""), "yikonglu_reading": n["fields"].get("片里落点", ""),
                         "citations": [{"text": x["text"], "source": x["src"], "pages": x["pages"], "paraphrase": x["para"]} for x in g["cites"]],
                         "readings": g["reads"], "huangkan_first_line": ({"text": h["text"], "scan_page": h["page"]} if h else None)})
        slug = PIAN[p][1]
        json.dump({**lic, "book": "论语", "pian": PIAN[p][0], "chapters": rows}, open(os.path.join(outdir, "data", f"lunyu-{slug}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        with open(os.path.join(outdir, "data", f"lunyu-{slug}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(["章号", "标题", "原文", "白话", "常见读法", "注里的关键字", "诸家", "一孔录读法", "网址"])
            for r in rows: w.writerow([r["chapter"], r["title"], r["text"], r["baihua"], r["common_reading"], r["zhu_keys"], r["others"], r["yikonglu_reading"], r["url"]])
    open(os.path.join(outdir, "data", "LICENSE.txt"), "w", encoding="utf-8").write("一孔录 Yikonglu 开放数据\n原文与古注：公版。\n一孔录所写内容（白话、读法、引文核对表、读音）：CC BY-NC 4.0，署名“一孔录 yikonglu.com”，不得商用。\nhttps://creativecommons.org/licenses/by-nc/4.0/\n")

def main(zdir, outdir, kanwu=None):
    yw = json.load(open(os.path.join(HERE, "yuanwen.json"), encoding="utf-8"))
    eps = json.load(open(os.path.join(HERE, "episodes.json"), encoding="utf-8"))
    notes = {}
    for f in sorted(os.listdir(zdir)):
        if f.endswith(".md") and f not in ("说明.md", "主题线.md"):
            notes.update(parse_zhaji(os.path.join(zdir, f)))
    gao = {}
    for f in sorted(glob.glob(os.path.join(GAO_DIR, "*", "*稿*.md"))):
        for c, v in parse_gao(f, yw).items():
            gao.setdefault(c, {"cites": [], "reads": []}); gao[c]["cites"] += v["cites"]; gao[c]["reads"] += v["reads"]
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
    ydir = os.path.join(HERE, "yuanye"); os.makedirs(ydir, exist_ok=True)
    for png in sorted(glob.glob(os.path.join(GAO_DIR, "*", "p*.png"))):
        jpg = os.path.join(ydir, os.path.basename(png)[:-4] + ".jpg")
        if not os.path.exists(jpg):
            from PIL import Image
            im = Image.open(png).convert("RGB")
            if im.width > 1400: im = im.resize((1400, int(im.height * 1400 / im.width)))
            im.save(jpg, quality=78, optimize=True, progressive=True)
    shutil.copytree(ydir, os.path.join(outdir, "yuanye"))
    pages_avail = {re.sub(r"\D", "", f).lstrip("0") for f in os.listdir(ydir) if f.endswith(".jpg")}
    zhuben = parse_zhuben(ZB_DIR)
    fsp = os.path.join(HERE, "firstseen.json")  # 每章第一次上网的日期（订阅源、引用元数据用）
    first = json.load(open(fsp, encoding="utf-8")) if os.path.exists(fsp) else {}
    for c in pub: first.setdefault(c, today)
    json.dump(first, open(fsp, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    baihua = {}
    for f in sorted(glob.glob(os.path.join(BH_DIR, "*.md"))):
        for l in open(f, encoding="utf-8"):
            m = re.match(r"^- (\d+\.\d+)[：:]\s*(.+)$", l.strip())
            if m: baihua[m.group(1)] = m.group(2).strip()
    stp = os.path.join(GAO_DIR, "_时间", "章节起点.json")
    starts = {}  # {YouTube ID: {章号: 秒}}，发布线程按集追加
    if os.path.exists(stp):
        for e in json.load(open(stp, encoding="utf-8")).values():
            if isinstance(e, dict) and e.get("youtube"): starts.setdefault(e["youtube"], {}).update({k: int(v) for k, v in e.get("starts", {}).items()})
    hujian = {}  # Codex 互见列：数据/网站素材/_互见/*.csv，列：章号,句,类别(注/本书/他书),内容,出处,链接（链接可写章号如 1.4 或 1.4#s2）
    for f in sorted(glob.glob(os.path.join(GAO_DIR, "_互见", "*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            if r.get("章号") and r.get("内容"):
                hujian.setdefault(r["章号"].strip(), []).append({"ju": (r.get("句") or "1").strip().lstrip("s"), "kind": r.get("类别", "").strip(), "text": r["内容"].strip(), "src": (r.get("出处") or "").strip(), "link": (r.get("链接") or "").strip()})
    # 全书原文（Codex 朱注分章 498 章）：已讲章仍用 yuanwen.json（与视频一致），未讲章用这份
    qf = sorted(glob.glob(os.path.join(YW_DIR, "论语原文-集注分章-v*.json")))
    QW = json.load(open(qf[-1], encoding="utf-8")) if qf else {}
    for c, a, b in (("1.6", "泛爱众", "汎爱众"),):  # Codex JSON 与其异文表不符处，照底本
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
    # 互见的“句”是按 Codex 原文的标点切的；已讲章网站原文标点不全同，按字位换算成网站的句号
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
    D = dict(qw=QW, fz=fz, yiwen=yiwen, all_by_pian=all_by_pian, renwu=RWD, gushi=G, hujian=hujian, starts=starts, first=first, baihua=baihua, zhuben=zhuben, notes=notes, yw=yw, gao=gao, kw=parse_kanwu(kanwu or KANWU_DEFAULT), pub=pub, by_pian=by_pian, ch2ep=ch2ep, pages_avail=pages_avail, today=today)

    def writer(prefix, post=None):
        def write(rel, text):
            p = os.path.join(outdir, prefix, rel); os.makedirs(os.path.dirname(p) or outdir, exist_ok=True)
            open(p, "w", encoding="utf-8").write(post(text) if post else text)
        return write

    # 每章分享图：简体图给简、英、法、西；繁体图给繁、日、韩
    D["og"] = {}
    if OG.available():
        for c in pub:
            pnum, cnum = c.split(".")
            head = f"《论语·{PIAN[pnum][0]}》第 {cnum} 章"
            D["og"][c] = {"hans": OG.make("hans", c, head, yw[c], TAGLINE)}
    else:
        print("没有字体，分享图跳过：", OG.FONT)
    urls = build_lang(Lang("zh-Hans", ZH_UI), D, writer(""))
    write_data(D, outdir)
    # 繁体：由简体页面整页转换，台湾用字；站内链接改前缀
    from opencc import OpenCC
    cc = OpenCC("s2twp")
    keep = ("/assets/", "/yuanye/", "/style.css", "https://", "http://", "#")
    # 古文与人名里不能按今字转的（简繁同形或 OpenCC 会转错），先护住再转
    PROTECT = ["范祖禹", "范氏", "游酢", "游氏", "坐如尸", "尸", "咸", "丑", "干禄", "云：", "云，", "子云", "诗云", "余力", "余，", "余者", "托看"]
    def to_hant(text):
        for i, w in enumerate(PROTECT): text = text.replace(w, f"\ue000{i}\ue001")
        t = cc.convert(text)
        for i, w in enumerate(PROTECT): t = t.replace(f"\ue000{i}\ue001", HANT_FIX.get(w, w))
        t = re.sub(r'(href|action|src)="/(?!zh-hant/)([^"]*)"', lambda m: m.group(0) if m.group(2).startswith(("assets/", "yuanye/", "style.css", "data/", "og/", "gushi/img/")) else f'{m.group(1)}="/zh-hant/{m.group(2)}"', t)
        t = t.replace("fetch('/search.json')", "fetch('/zh-hant/search.json')").replace("&quot;/lunyu/", "&quot;/zh-hant/lunyu/")
        t = t.replace('"u": "/lunyu', '"u": "/zh-hant/lunyu')
        return t
    if OG.available():
        for c in pub:
            pnum, cnum = c.split(".")
            D["og"][c]["hant"] = OG.make("hant", c, to_hant(f"《论语·{PIAN[pnum][0]}》第 {cnum} 章"), to_hant(yw[c]), to_hant(TAGLINE))
        shutil.copytree(os.path.join(HERE, "og"), os.path.join(outdir, "og"), ignore=shutil.ignore_patterns("*.sig"))
    hant_ui = dict(ZH_UI); hant_ui["translated_note"] = ZH_UI["hant_note"]
    urls += build_lang(Lang("zh-Hant", hant_ui), D, writer("zh-hant", to_hant))
    for code in ("en", "ja", "ko", "fr", "es"):
        tr = json.load(open(os.path.join(HERE, "i18n", code + ".json"), encoding="utf-8"))
        ui = dict(EXTRA_UI.get(code, {})); ui.update(tr["ui"])
        urls += build_lang(Lang(code, ui, tr), D, writer(code))

    open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    ver = __import__("hashlib").md5((CSSV + today + str(len(urls))).encode()).hexdigest()[:10]
    open(os.path.join(outdir, "sw.js"), "w", encoding="utf-8").write(open(os.path.join(HERE, "sw.js"), encoding="utf-8").read().replace("@VER@", ver).replace("@PREFIXES@", json.dumps([""] + [LANGS[k][0] for k in LANGS if LANGS[k][0]])))
    open(os.path.join(outdir, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    open(os.path.join(outdir, "CNAME"), "w").write("yikonglu.com\n")
    open(os.path.join(outdir, ".nojekyll"), "w").write("")
    shutil.copy(os.path.join(HERE, "style.css"), os.path.join(outdir, "style.css"))
    print(f"生成 {len(urls)} 页 → {outdir}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
