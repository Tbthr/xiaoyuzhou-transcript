---
name: xiaoyuzhou-transcript
description: >
  Fetch podcast transcripts from Xiaoyuzhou (小宇宙) and upload to IMA knowledge base.
  Use when user provides a xiaoyuzhoufm.com podcast or episode link and wants to:
  (1) fetch transcripts and upload to IMA knowledge base;
  (2) check for new episodes and sync.
  Trigger phrases: "获取逐字稿", "下载播客文稿", "抓取小宇宙", "播客逐字稿", "小宇宙 transcript", "同步播客".
---

# Xiaoyuzhou Transcript

从小宇宙获取播客逐字稿并上传到 IMA 知识库。

## 脚本说明

### `scripts/fetch_transcript.py`

获取单期或全部节目逐字稿：

```bash
# 单期
python3 scripts/fetch_transcript.py <episode_url> [--output-dir <dir>]

# 全部（播客主页）
python3 scripts/fetch_transcript.py <podcast_url> --all [--output-dir <dir>]
```

### `scripts/sync.py`

增量同步脚本，对比本地记录的 latest_episode_id 与小宇宙最新节目，只上传新增期：

```bash
python3 scripts/sync.py
```

依赖 `~/.openclaw/workspace-content/xiaoyuzhou_subscriptions.json` 配置订阅列表。

## 定时任务

每周六 09:00（Asia/Shanghai），cron id：`b0d3f7f7-56e5-4f86-811a-1eab40f2898c`

## 依赖 Skills

- `markdown-proxy` 或 `defuddle` — URL → Markdown 内容获取
- `ima-skill` — IMA 知识库上传（需要 cos-upload.cjs）

## 参考资料

- `references/podcast_sources.md` — 播客源说明和 URL 格式
- `references/transcript_flow.md` — 详细抓取流程和降级策略
- `README.md` — 配置说明（订阅列表格式、状态文件路径）
