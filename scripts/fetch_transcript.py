#!/usr/bin/env python3
"""
小宇宙播客逐字稿获取脚本
- 支持单期节目和整播客批量获取
- 输出 Markdown 文件
"""

import re, os, sys, json, time, subprocess, argparse

DEFAULT_OUTPUT_DIR = os.path.expanduser("~/podcast_transcripts")

# ---- URL 获取 ----

def fetch_url(url):
    """通过 markdown-proxy 级联获取 URL 内容（返回 Markdown）。"""
    # 优先 r.jina.ai
    try:
        r = subprocess.run(
            ["curl", "-sL", f"https://r.jina.ai/{url}",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
             "-H", "Accept: text/markdown"],
            capture_output=True, text=True, timeout=30
        )
        content = clean_jina(r.stdout)
        if len(content) > 500:
            return content
    except:
        pass

    time.sleep(1)

    # 备用 defuddle.md
    try:
        r = subprocess.run(
            ["curl", "-sL", f"https://defuddle.md/{url}",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"],
            capture_output=True, text=True, timeout=30
        )
        content = clean_defuddle(r.stdout)
        if len(content) > 500:
            return content
    except:
        pass

    return ""


def clean_jina(raw):
    """清理 r.jina.ai 返回内容。"""
    lines = raw.split('\n')
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == 'Markdown Content:':
            start = i + 2
            break
    if start == 0:
        for i, line in enumerate(lines):
            if line.startswith('# ') and i > 2:
                start = i
                break
    content = '\n'.join(lines[start:])
    content = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def clean_defuddle(raw):
    """清理 defuddle.md 返回内容。"""
    if raw.startswith('---'):
        end = raw.find('---', 3)
        if end > 0:
            raw = raw[end+3:].strip()
    raw = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', raw)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    return raw.strip()


# ---- 小宇宙解析 ----

def get_xiaoyuzhou_page(episode_id):
    """获取小宇宙节目页面 HTML。"""
    url = f"https://www.xiaoyuzhoufm.com/episode/{episode_id}"
    result = subprocess.run(
        ["curl", "-sL", url,
         "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"],
        capture_output=True, text=True, timeout=15
    ).stdout
    return result, url


def extract_transcript_link(page_html):
    """
    从小宇宙页面 HTML 中提取有知有行逐字稿链接。
    返回 (transcript_url, is_full_transcript)
    """
    # 查找 youzhiyouxing 逐字稿链接，排除 1037（节目介绍，非逐字稿）
    mat_ids = set(re.findall(r'youzhiyouxing\.cn/(?:n/)?materials/(\d+)', page_html))
    mat_ids.discard('1037')

    if mat_ids:
        # 取最大 ID（通常是主逐字稿）
        mid = sorted(mat_ids)[-1]
        yz_url = f"https://youzhiyouxing.cn/n/materials/{mid}"
        return yz_url, True

    return "", False


def get_episode_transcript(episode_id):
    """
    获取单期节目逐字稿。
    返回 (content, source_url, is_full_transcript)
    """
    page_html, page_url = get_xiaoyuzhou_page(episode_id)

    # 提取有知有行逐字稿链接
    yz_url, is_full = extract_transcript_link(page_html)

    if yz_url:
        content = fetch_url(yz_url)
        if content:
            return content, yz_url, True

    # 降级：直接抓小宇宙页面
    content = fetch_url(page_url)
    if content:
        return content, page_url, False

    return "", "", False


def parse_podcast_page(podcast_url):
    """
    解析播客主页，返回所有 episode 列表。
    返回 [(episode_id, title), ...]
    
    由于页面是 JS 渲染的，从 HTML 提取 episode ID，
    从 JSON-LD 提取标题（两者顺序一致），然后配对。
    """
    result = subprocess.run(
        ["curl", "-sL", podcast_url,
         "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"],
        capture_output=True, text=True, timeout=15
    ).stdout

    # 1. 从 HTML 提取所有 episode ID（顺序）
    html_ids = re.findall(r'href="/episode/([a-f0-9]+)"', result)
    # 去重保持顺序
    seen_ids = []
    for eid in html_ids:
        if eid not in seen_ids:
            seen_ids.append(eid)

    # 2. 从 JSON-LD 提取所有 episode 标题（顺序）
    match = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', result, re.DOTALL)
    json_titles = []
    if match:
        try:
            data = json.loads(match.group(1))
            for ex in data.get('workExample', []):
                name = ex.get('name', '')
                if name:
                    json_titles.append(name)
        except:
            pass

    # 3. 配对（按顺序，HTML ID 数量 >= JSON 标题数量）
    episodes = []
    for i, title in enumerate(json_titles):
        if i < len(seen_ids):
            episodes.append((seen_ids[i], title))

    return episodes


# ---- 文件保存 ----

def save_transcript(content, source_url, title, output_dir):
    """保存逐字稿为 Markdown 文件。"""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r'[|／/:*?"<>\\]', '', title).strip()[:80]
    file_path = os.path.join(output_dir, f"{safe_name}.md")

    header = f"# {title}\n\n**来源:** {source_url}\n\n---\n\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + content)

    return file_path


# ---- 主流程 ----

def fetch_single(episode_url, output_dir=DEFAULT_OUTPUT_DIR):
    """获取单期节目逐字稿。"""
    # 提取 episode_id
    m = re.search(r'/episode/([a-f0-9]+)', episode_url)
    if not m:
        print(f"ERROR: 无法从 URL 解析 episode_id: {episode_url}")
        return None

    episode_id = m.group(1)
    print(f"获取逐字稿: {episode_id}")

    content, source_url, is_full = get_episode_transcript(episode_id)

    if not content or len(content) < 500:
        print(f"⚠️ 获取失败或内容过短")
        return None

    title = f"episode_{episode_id}"
    file_path = save_transcript(content, source_url, title, output_dir)
    print(f"✅ 已保存: {file_path}")
    print(f"   类型: {'完整逐字稿' if is_full else '节目笔记'}")
    print(f"   字数: {len(content)}")

    return file_path


def fetch_all(podcast_url, output_dir=DEFAULT_OUTPUT_DIR):
    """获取播客全部可用逐字稿。"""
    print(f"解析播客: {podcast_url}")
    episodes = parse_podcast_page(podcast_url)

    if not episodes:
        print("ERROR: 未找到任何节目")
        return []

    print(f"共 {len(episodes)} 期节目")

    saved = []
    for i, (eid, title) in enumerate(episodes):
        print(f"\n[{i+1}/{len(episodes)}] {title[:50]}...")

        content, source_url, is_full = get_episode_transcript(eid)

        if not content or len(content) < 500:
            print(f"  ⚠️ 获取失败，跳过")
            time.sleep(2)
            continue

        file_path = save_transcript(content, source_url, title, output_dir)
        print(f"  ✅ {file_path} ({len(content)} chars)")
        saved.append(file_path)
        time.sleep(2)

    return saved


def main():
    parser = argparse.ArgumentParser(description="小宇宙播客逐字稿获取")
    parser.add_argument("url", help="节目链接或播客主页链接")
    parser.add_argument("--all", action="store_true", help="获取全部节目（仅播客主页有效）")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help=f"输出目录（默认: {DEFAULT_OUTPUT_DIR}）")

    args = parser.parse_args()

    if args.all:
        results = fetch_all(args.url, args.output_dir)
        print(f"\n完成，共获取 {len(results)} 期")
    else:
        result = fetch_single(args.url, args.output_dir)
        if result:
            print(f"\n完成: {result}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
