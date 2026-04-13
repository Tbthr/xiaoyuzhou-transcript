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

## 工作流程

```
小宇宙页面 → 解析 episode_id → 提取有知有行逐字稿链接
    → r.jina.ai / defuddle.md 获取内容
    → 上传到 IMA 知识库（使用 ima-skill）
    → 更新本地 latest_episode_id 记录
```

## 定时任务

- 触发：`cron 0 9 * * 6`（每周六 09:00 Asia/Shanghai）
- 脚本：`~/.openclaw/workspace-content/xiaoyuzhou_sync/sync.py`
- 配置：`~/.openclaw/workspace-content/xiaoyuzhou_subscriptions.json`

## 核心脚本

### `scripts/fetch_transcript.py`

获取单期或全部节目逐字稿：

```bash
# 单期
python3 scripts/fetch_transcript.py <episode_url> [--output-dir <dir>]

# 全部（播客主页）
python3 scripts/fetch_transcript.py <podcast_url> --all [--output-dir <dir>]
```

## 依赖 Skills

- `markdown-proxy` 或 `defuddle` — URL → Markdown 内容获取
- `ima-skill` — IMA 知识库上传

## 参考资料

- `references/podcast_sources.md` — 播客源说明和 URL 格式
- `references/transcript_flow.md` — 详细抓取流程和降级策略
