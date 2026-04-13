# Xiaoyuzhou Transcript

小宇宙播客逐字稿抓取 + IMA 知识库同步。

## 配置

### 订阅列表

文件路径：`~/.openclaw/workspace-content/xiaoyuzhou_subscriptions.json`

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

`knowledge_base_id` 可省略，会自动使用 IMA credential 对应的默认知识库。

### 状态文件

路径：`~/.openclaw/workspace-content/xiaoyuzhou_sync/last_check.json`

记录每个播客最新同步的 episode_id，每次 sync 时自动更新。

### IMA 凭证

从 `~/.config/ima/client_id` 和 `~/.config/ima/api_key` 读取。

## 手动运行

```bash
# 单期
python3 scripts/fetch_transcript.py https://www.xiaoyuzhoufm.com/episode/xxx

# 全部（播客主页）
python3 scripts/fetch_transcript.py https://www.xiaoyuzhoufm.com/podcast/xxx --all

# 增量同步（定时任务）
python3 scripts/sync.py
```

## 定时任务

- cron expression: `0 9 * * 6`（每周六 09:00 Asia/Shanghai）
- cron id: `b0d3f7f7-56e5-4f86-811a-1eab40f2898c`
- OpenClaw 会自动 announce 结果到飞书

手动触发：
```bash
openclaw cron run b0d3f7f7-56e5-4f86-811a-1eab40f2898c
```

查看运行历史：
```bash
openclaw cron runs --id b0d3f7f7-56e5-4f86-811a-1eab40f2898c
```

## 更新 skill 后重新推送

```bash
cd ~/.openclaw/skills/xiaoyuzhou-transcript
git add -A && git commit -m "update" && git push
```
