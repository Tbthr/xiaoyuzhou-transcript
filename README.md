# Xiaoyuzhou Transcript

小宇宙播客逐字稿抓取 + IMA 知识库同步。

## 前置依赖

安装本 skill 前需先安装：

- **`ima-skill`** — 提供 COS 上传脚本和 IMA API 调用
- **`markdown-proxy`** — AI 调用此 skill 获取 URL 内容

## 工作流

```
用户触发 skill（手动或 cron）
    ↓
AI 解析播客主页 → 获取 episode_id 列表
    ↓
对于每个需要处理的 episode:
    → AI 调用 markdown-proxy skill 获取逐字稿
    → AI 处理内容并上传到 IMA
    ↓
AI 更新状态文件 ~/xiaoyuzhou-transcript/state.json
```

**注意**：URL 获取由 AI 调用 markdown-proxy skill，脚本只做解析和状态管理。

## 配置目录

所有配置文件统一放在 `~/xiaoyuzhou-transcript/`：

```
~/xiaoyuzhou-transcript/
├── subscriptions.json   # 订阅播客列表
└── state.json           # 增量同步状态（自动管理）
```

### subscriptions.json

```json
{
  "subscriptions": [
    {
      "name": "投资ABC",
      "url": "https://www.xiaoyuzhoufm.com/podcast/64b0bfde585daadfc82f3b12",
      "knowledge_base_id": "IMA_KB_ID"
    }
  ]
}
```

`knowledge_base_id` 可省略，使用 IMA credential 对应的默认知识库。

### IMA 凭证

从 `~/.config/ima/client_id` 和 `~/.config/ima/api_key` 读取。

## AI 编排模式

当用户说 "获取逐字稿" 时，AI 会：

1. 运行 `scripts/fetch_transcript.py --list` 获取 episode 列表
2. 对每个 episode，调用 markdown-proxy skill 获取内容：
   ```bash
   bash ~/.claude/skills/qiaomu-markdown-proxy/scripts/fetch.sh "https://youzhiyouxing.cn/n/materials/{id}"
   ```
3. AI 清理内容（移除图片、合并空行）
4. AI 调用 ima-skill 上传到 IMA
5. AI 更新 `~/xiaoyuzhou-transcript/state.json`

## 手动运行

### 解析播客（供 AI 调用 markdown-proxy）

```bash
# 列出 episode（不获取内容）
python3 scripts/fetch_transcript.py <podcast_url> --list

# 单期解析
python3 scripts/fetch_transcript.py https://www.xiaoyuzhoufm.com/episode/xxx
```

### 增量同步

```bash
python3 scripts/sync.py
```

## 定时任务

- cron expression: `0 9 * * 6`（每周六 09:00 Asia/Shanghai）
- cron id: `b0d3f7f7-56e5-4f86-811a-1eab40f2898c`
- OpenClaw 自动 announce 结果到飞书
- cron 触发时 AI 也参与编排

手动触发：
```bash
openclaw cron run b0d3f7f7-56e5-4f86-811a-1eab40f2898c
```

查看运行历史：
```bash
openclaw cron runs --id b0d3f7f7-56e5-4f86-811a-1eab40f2898c
```

## 更新后推送

```bash
git add -A && git commit -m "update" && git push
```
