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

## 工作流程（AI 编排）

```
用户触发 skill（手动或 cron）
    ↓
AI 读取 SKILL.md 了解播客解析流程
    ↓
AI 解析播客主页 → 获取 episode_id 列表
    ↓
对于每个需要处理的 episode:
    → AI 调用 markdown-proxy skill 获取逐字稿 URL 内容
    → AI 处理内容（移除图片、清理格式）
    → AI 调用 ima-skill 上传到知识库
    ↓
AI 更新状态文件 ~/xiaoyuzhou-transcript/state.json
```

**关键**：URL 获取由 AI 调用 markdown-proxy skill，脚本只做解析和状态管理。

## 核心脚本

### `scripts/fetch_transcript.py`

解析播客主页，返回 episode 列表（不做网络获取）：

```bash
python3 scripts/fetch_transcript.py <podcast_url> --list
# 输出: [(episode_id, title), ...] JSON
```

### `scripts/sync.py`

状态管理脚本，对比本地记录与最新节目，只处理新增期：

```bash
python3 scripts/sync.py
```

依赖配置目录 `~/xiaoyuzhou-transcript/`（见 README.md）。

## AI 编排示例

当用户说 "获取这个播客的逐字稿" 时：

1. AI 运行 `fetch_transcript.py --list` 获取 episode 列表
2. 对于每个 episode，AI 读取 `markdown-proxy` SKILL.md，按其描述的工作流获取内容：
   - 优先：`curl -sL "https://r.jina.ai/{url}"`
   - 备用：`curl -sL "https://defuddle.md/{url}"`
3. AI 清理内容（移除图片 `![]...`、合并空行）
4. AI 调用 ima-skill 上传
5. AI 更新 `~/xiaoyuzhou-transcript/state.json`

## 前置依赖

- **`ima-skill`** — 提供 COS 上传脚本和 IMA API 调用
- **`markdown-proxy`** — AI 调用此 skill 获取 URL 内容（不是脚本直接调用）

## 参考资料

- `references/podcast_sources.md` — 播客源 URL 格式说明
- `references/transcript_flow.md` — 详细抓取流程
- `README.md` — 配置说明、定时任务设置
