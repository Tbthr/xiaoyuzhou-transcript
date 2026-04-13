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
播客主页 → 解析 episode_id → 提取有知有行逐字稿链接
    → defuddle.md / r.jina.ai 获取内容
    → 上传到 IMA 知识库（通过 ima-skill）
    → 更新本地 episode_id 记录
```

## 核心脚本

### `scripts/fetch_transcript.py`

获取单期或全部节目逐字稿：

```bash
python3 scripts/fetch_transcript.py <episode_url> [--output-dir <dir>]
python3 scripts/fetch_transcript.py <podcast_url> --all [--output-dir <dir>]
```

### `scripts/sync.py`

增量同步脚本，对比本地记录与最新节目，只上传新增期：

```bash
python3 scripts/sync.py
```

依赖配置目录 `~/xiaoyuzhou-transcript/`（见 README.md）。

## 前置依赖

- **`ima-skill`** — 提供 COS 上传脚本 `cos-upload.cjs`
- **`defuddle`** 或 **`markdown-proxy`** — 网页内容抓取

## 参考资料

- `references/podcast_sources.md` — 播客源 URL 格式说明
- `references/transcript_flow.md` — 详细抓取流程
- `README.md` — 配置说明、定时任务设置
