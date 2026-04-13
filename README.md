# Xiaoyuzhou Transcript

小宇宙播客逐字稿抓取 + IMA 知识库同步。

## 前置依赖

安装本 skill 前需先安装：

- **`ima-skill`** — 提供 `cos-upload.cjs`
- **`defuddle`** 或 **`markdown-proxy`** — 网页内容抓取

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

## 手动运行

```bash
# 增量同步
python3 scripts/sync.py

# 单期节目
python3 scripts/fetch_transcript.py https://www.xiaoyuzhoufm.com/episode/xxx

# 全部节目（播客主页）
python3 scripts/fetch_transcript.py https://www.xiaoyuzhoufm.com/podcast/xxx --all
```

## 定时任务

- cron expression: `0 9 * * 6`（每周六 09:00 Asia/Shanghai）
- cron id: `b0d3f7f7-56e5-4f86-811a-1eab40f2898c`
- OpenClaw 自动 announce 结果到飞书

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
