#!/usr/bin/env python3
"""
小宇宙播客逐字稿获取脚本
- 支持单期节目和整播客批量获取
- 输出 Markdown 文件
- URL 获取由 AI 调用 markdown-proxy skill 负责
"""

import re, os, sys, json, subprocess, argparse

DEFAULT_OUTPUT_DIR = os.path.expanduser("~/podcast_transcripts")

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
    """
    获取单期节目逐字稿信息（URL）。
    URL 获取由 AI 调用 markdown-proxy skill 负责。
    返回 (episode_id, transcript_url, source_url, is_full_transcript)
    """
    # 提取 episode_id
    m = re.search(r'/episode/([a-f0-9]+)', episode_url)
    if not m:
        print(f"ERROR: 无法从 URL 解析 episode_id: {episode_url}")
        return None, None, None, False

    episode_id = m.group(1)
    page_html, page_url = get_xiaoyuzhou_page(episode_id)

    # 提取有知有行逐字稿链接
    yz_url, is_full = extract_transcript_link(page_html)

    if yz_url:
        return episode_id, yz_url, yz_url, True

    # 降级：返回小宇宙页面
    return episode_id, page_url, page_url, False


def fetch_all(podcast_url, output_dir=DEFAULT_OUTPUT_DIR):
    """
    解析播客主页，返回所有 episode 列表。
    返回 [(episode_id, title, transcript_url, is_full), ...]
    """
    print(f"解析播客: {podcast_url}")
    episodes = parse_podcast_page(podcast_url)

    if not episodes:
        print("ERROR: 未找到任何节目")
        return []

    print(f"共 {len(episodes)} 期节目")

    results = []
    for i, (eid, title) in enumerate(episodes):
        print(f"\n[{i+1}/{len(episodes)}] {title[:50]}...")

        page_html, page_url = get_xiaoyuzhou_page(eid)
        yz_url, is_full = extract_transcript_link(page_html)

        transcript_url = yz_url if yz_url else page_url
        results.append((eid, title, transcript_url, is_full))

        if not yz_url:
            print(f"  ⚠️ 未找到有知有行逐字稿，使用节目页")

    return results


def list_episodes(podcast_url):
    """列出播客所有 episode，仅解析不获取内容。"""
    episodes = parse_podcast_page(podcast_url)
    for eid, title in episodes:
        print(f"{eid}\t{title}")
    return episodes


def main():
    parser = argparse.ArgumentParser(description="小宇宙播客逐字稿解析")
    parser.add_argument("url", help="节目链接或播客主页链接")
    parser.add_argument("--list", action="store_true", help="仅列出 episode（不获取内容）")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help=f"输出目录（默认: {DEFAULT_OUTPUT_DIR}）")

    args = parser.parse_args()

    if args.list:
        # 仅列出 episode，供 AI 调用 markdown-proxy 用
        list_episodes(args.url)
    elif '/episode/' in args.url:
        # 单期模式
        episode_id, transcript_url, source_url, is_full = fetch_single(args.url, args.output_dir)
        if episode_id:
            print(f"episode_id: {episode_id}")
            print(f"transcript_url: {transcript_url}")
            print(f"is_full: {is_full}")
        else:
            sys.exit(1)
    else:
        # 批量模式 - 返回 episode 列表（内容获取由 AI 调用 markdown-proxy）
        results = fetch_all(args.url, args.output_dir)
        print(f"\n完成，共解析 {len(results)} 期")


if __name__ == "__main__":
    main()
