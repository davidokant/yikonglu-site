-- 一孔书院·书友圈 雏形（Workers + D1）。结构借鉴 MIT 开源 cf-bbs Nexus、企鹅窝，代码自写。
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,                 -- 网名
  pw TEXT,                            -- PBKDF2 哈希（角色账号为空，不能登录）
  salt TEXT,
  role TEXT NOT NULL DEFAULT 'guest', -- guest 注册未入会 | member 会员 | admin 管理 | char 原创角色
  avatar TEXT, tag TEXT,              -- 角色账号的头像与小标
  ident TEXT,                         -- 书院世界里的身份：shusheng youxia shanglv yizhe jiangren fangwai
  ident_at INTEGER,                   -- 上次改身份的时间（每 30 天可改一次）
  posts INTEGER DEFAULT 0,            -- 发言数，算学籍
  created INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS u_name ON users (lower(name));
CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS invites (
  code TEXT PRIMARY KEY, kind TEXT NOT NULL,   -- member 入会 | reset 重置密码
  for_name TEXT, note TEXT, created INTEGER NOT NULL, used_by INTEGER, used_at INTEGER
);
CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  descr TEXT, sort INTEGER DEFAULT 0, members_only INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS threads (
  id INTEGER PRIMARY KEY AUTOINCREMENT, board_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
  title TEXT NOT NULL, chapter TEXT, pinned INTEGER DEFAULT 0, answered INTEGER DEFAULT 0, open INTEGER DEFAULT 0, -- open: 会员区里“本周公开”给免费书友看的一帖
  replies INTEGER DEFAULT 0, created INTEGER NOT NULL, last_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS t_board ON threads (board_id, pinned DESC, last_at DESC);
CREATE INDEX IF NOT EXISTS t_chapter ON threads (chapter);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
  body TEXT NOT NULL, created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS p_thread ON posts (thread_id, id);
CREATE TABLE IF NOT EXISTS scheduled (           -- 角色定时帖：到点由 Cron 发出
  id INTEGER PRIMARY KEY AUTOINCREMENT, as_user INTEGER NOT NULL, board_slug TEXT, thread_id INTEGER,
  title TEXT, body TEXT NOT NULL, run_at INTEGER NOT NULL, done INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS hits (k TEXT PRIMARY KEY, n INTEGER, until INTEGER);  -- 简单限流

INSERT OR IGNORE INTO boards (slug, name, descr, sort, members_only) VALUES
 ('menkou', '山门', '书院公告、院规、新人报到。谁都能看，免费书友可发一帖报到。', 1, 0),
 ('lunyu', '共读堂 · 论语', '按篇开帖，一篇一帖。孔照今每周一发进度，周五点名。', 2, 1),
 ('shiyong', '明用斋 · 这句话怎么用', '每周会员片一帖，下面聊自己的处境。', 3, 1),
 ('shuhou', '藏书阁 · 书后面的事', '每月加餐：注家怎么争、一孔按展开、跨章串读。', 4, 1),
 ('wen', '问津亭 · 问一孔', '书友提问，保证有答；答了标“已答”。', 5, 1),
 ('xiantan', '茶寮 · 闲谈', '读书之外的话。', 6, 1);
INSERT OR IGNORE INTO users (name, role, avatar, tag, created) VALUES
 ('上官有理', 'char', 'https://img.yikonglu.com/gushi/img/youli-head.png', '一孔录原创角色·智器主持', 0),
 ('孔照今', 'char', 'https://img.yikonglu.com/gushi/img/zhaojin-head.png', '一孔录原创角色·智器主持', 0),
 ('林守拙', 'char', 'https://img.yikonglu.com/gushi/img/shouzhuo-head.png', '一孔录原创角色·智器主持', 0),
 ('陆川', 'char', 'https://img.yikonglu.com/gushi/img/luchuan-head.png', '一孔录原创角色·智器主持', 0),
 ('阮流绮', 'char', 'https://img.yikonglu.com/gushi/img/liuqi-head.png', '一孔录原创角色·智器主持', 0),
 ('莎赫拉', 'char', 'https://img.yikonglu.com/gushi/img/shahela-head.png', '一孔录原创角色·智器主持', 0);
