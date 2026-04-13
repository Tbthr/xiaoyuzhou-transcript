# 播客源说明

## 小宇宙 (xiaoyuzhoufm.com)

小宇宙是国内播客平台，提供节目和逐字稿。

### URL 格式

- 播客主页: `https://www.xiaoyuzhoufm.com/podcast/{podcast_id}`
- 单期节目: `https://www.xiaoyuzhoufm.com/episode/{episode_id}`

### 逐字稿来源

小宇宙节目页面中会嵌入「有知有行」(youzhiyouxing.cn) 的逐字稿链接。

典型链接模式:
- `https://youzhiyouxing.cn/n/materials/{id}`

其中 `materials/1037` 通常是节目介绍，非逐字稿，应排除。

### 逐字稿获取流程

1. 访问小宇宙节目页
2. 解析 HTML 中的有知有行链接
3. 通过 markdown-proxy 获取逐字稿内容
4. 清理并保存为 Markdown

### 示例

```bash
# 获取单期
python3 scripts/fetch_transcript.py https://www.xiaoyuzhoufm.com/episode/abc123def456

# 获取全部
python3 scripts/fetch_transcript.py https://www.xiaoyuzhoufm.com/podcast/xyz789 --all
```
