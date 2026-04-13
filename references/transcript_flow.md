# 逐字稿抓取详细流程

## 整体架构

```
用户请求 (xiaoyuzhoufm URL)
       ↓
解析 episode_id / podcast_id
       ↓
获取小宇宙节目页 HTML
       ↓
正则提取 youzhiyouxing.cn/materials/{id} 链接
       ↓
排除 materials/1037（节目介绍，非逐字稿）
       ↓
取最大 ID 作为主逐字稿
       ↓
markdown-proxy 级联获取:
  → r.jina.ai/{url}  (优先)
  → defuddle.md/{url} (备用)
       ↓
内容清理:
  → 移除图片 ![]...
  → 合并多余空行
  → 保留标题和来源
       ↓
保存为 {title}.md
```

## r.jina.ai vs defuddle.md

| 特性 | r.jina.ai | defuddle.md |
|------|-----------|-------------|
| 速度 | 快 | 稍慢 |
| 稳定性 | 高 | 高 |
| 清理效果 | 好 | 一般 |
| 备用机制 | - | 是 |

r.jina.ai 失败或内容过短时，切换 defuddle.md。

## 降级策略

1. 有知有行逐字稿链接 → 获取主逐字稿
2. 降级 → 直接抓小宇宙节目页（通常是节目介绍/笔记，非完整逐字稿）
3. 都失败 → 返回空内容
