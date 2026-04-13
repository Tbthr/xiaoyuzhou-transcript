#!/usr/bin/env python3
"""
小宇宙播客逐字稿 → IMA 知识库同步脚本
- 对比本地记录的 latest_episode_id 与小宇宙页面最新 episode ID
- 若有更新，抓取新节目的逐字稿直接上传 IMA 知识库
- 不在本地存储 .md 文件
- 上传完成后更新本地记录的 latest_episode_id
"""

import re, os, sys, json, time, subprocess, tempfile

# ---- 配置 ----
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_SCRIPT = os.path.join(SKILL_DIR, "scripts", "fetch_transcript.py")
COS_UPLOAD_SCRIPT = os.path.expanduser("~/.openclaw/skills/ima/scripts/cos-upload.cjs")
SUBSCRIPTIONS_PATH = os.path.expanduser("~/xiaoyuzhou-transcript/subscriptions.json")
STATE_PATH = os.path.expanduser("~/xiaoyuzhou-transcript/state.json")

# IMA 凭证
def load_ima_creds():
    client_id = os.environ.get("IMA_OPENAPI_CLIENTID", "")
    api_key = os.environ.get("IMA_OPENAPI_APIKEY", "")
    if not client_id:
        try:
            client_id = open(os.path.expanduser("~/.config/ima/client_id")).read().strip()
        except:
            pass
    if not api_key:
        try:
            api_key = open(os.path.expanduser("~/.config/ima/api_key")).read().strip()
        except:
            pass
    return client_id, api_key

def ima_api(path, body, client_id, api_key):
    """调用 IMA OpenAPI。"""
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"https://ima.qq.com/{path}",
         "-H", f"ima-openapi-clientid: {client_id}",
         "-H", f"ima-openapi-apikey: {api_key}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body, ensure_ascii=False)],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except:
        return {"code": -1, "msg": result.stdout or result.stderr}

def upload_to_ima(kb_id, content, file_name, client_id, api_key):
    """
    将内容作为临时 .md 文件上传到 IMA 知识库。
    返回 (ok, msg)
    """
    file_ext = "md"
    content_type = "text/markdown"

    # Step 1: 获取 COS 上传凭证
    tmp_path = os.path.join(tempfile.gettempdir(), f"ima_upload_{time.time()}.md")
    header = f"# {file_name}\n\n**来源:** 小宇宙\n\n---\n\n"
    full_content = header + content
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    file_size = len(full_content.encode("utf-8"))  # bytes, not chars

    create = ima_api("openapi/wiki/v1/create_media", {
        "file_name": file_name,
        "file_size": file_size,
        "content_type": content_type,
        "knowledge_base_id": kb_id,
        "file_ext": file_ext
    }, client_id, api_key)

    if create.get("code") != 0:
        os.remove(tmp_path)
        return False, f"create_media failed: {create.get('msg')}"

    cos_cred = create.get("data", {}).get("cos_credential", {})
    media_id = create.get("data", {}).get("media_id", "")

    if not cos_cred or not media_id:
        os.remove(tmp_path)
        return False, "No cos_credential or media_id in create_media response"

    # Step 2: 上传到 COS
    upload_result = subprocess.run(
        ["node", COS_UPLOAD_SCRIPT,
         "--file", tmp_path,
         "--secret-id", cos_cred.get("secret_id", ""),
         "--secret-key", cos_cred.get("secret_key", ""),
         "--token", cos_cred.get("token", ""),
         "--bucket", cos_cred.get("bucket_name", ""),
         "--region", cos_cred.get("region", ""),
         "--cos-key", cos_cred.get("cos_key", ""),
         "--content-type", content_type],
        capture_output=True, text=True, timeout=60
    )
    os.remove(tmp_path)

    if upload_result.returncode != 0:
        return False, f"COS upload failed: {upload_result.stderr}"

    # Step 3: 添加知识
    add = ima_api("openapi/wiki/v1/add_knowledge", {
        "media_type": 7,
        "media_id": media_id,
        "title": file_name.replace(".md", ""),
        "knowledge_base_id": kb_id,
        "file_info": {
            "cos_key": cos_cred.get("cos_key", ""),
            "file_size": len(full_content.encode("utf-8")),
            "last_modify_time": int(time.time()),
            "file_name": file_name
        }
    }, client_id, api_key)

    if add.get("code") != 0:
        return False, f"add_knowledge failed: {add.get('msg')}"

    return True, media_id


# ---- 小宇宙解析 ----

def parse_podcast_page(podcast_url):
    """解析播客主页，返回 [(episode_id, title), ...]，按最新排序。"""
    result = subprocess.run(
        ["curl", "-sL", podcast_url,
         "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"],
        capture_output=True, text=True, timeout=15
    ).stdout

    html_ids = re.findall(r'href="/episode/([a-f0-9]+)"', result)
    seen_ids = []
    for eid in html_ids:
        if eid not in seen_ids:
            seen_ids.append(eid)

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

    episodes = []
    for i, title in enumerate(json_titles):
        if i < len(seen_ids):
            episodes.append((seen_ids[i], title))
    return episodes


def fetch_transcript(episode_id):
    """获取单期逐字稿内容。返回 (content, source_url, is_full)。"""
    xiaoyuzhou_url = f"https://www.xiaoyuzhoufm.com/episode/{episode_id}"
    page = subprocess.run(
        ["curl", "-sL", xiaoyuzhou_url,
         "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"],
        capture_output=True, text=True, timeout=15
    ).stdout

    mat_ids = set(re.findall(r'youzhiyouxing\.cn/(?:n/)?materials/(\d+)', page))
    mat_ids.discard('1037')

    if mat_ids:
        mid = sorted(mat_ids)[-1]
        yz_url = f"https://youzhiyouxing.cn/n/materials/{mid}"
        content = fetch_url(yz_url)
        if content:
            return content, yz_url, True

    content = fetch_url(xiaoyuzhou_url)
    if content:
        return content, xiaoyuzhou_url, False
    return "", "", False


def fetch_url(url):
    """通过 markdown-proxy 级联获取内容（返回 Markdown）。"""
    # 优先 defuddle.md
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

    time.sleep(1)

    # 备用 r.jina.ai
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
    return ""


def clean_jina(raw):
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
    if raw.startswith('---'):
        end = raw.find('---', 3)
        if end > 0:
            raw = raw[end+3:].strip()
    raw = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', raw)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    return raw.strip()


# ---- 主流程 ----

def load_subscriptions():
    if not os.path.exists(SUBSCRIPTIONS_PATH):
        return []
    with open(SUBSCRIPTIONS_PATH) as f:
        return json.load(f).get("subscriptions", [])


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    client_id, api_key = load_ima_creds()
    if not client_id or not api_key:
        print("ERROR: IMA 凭证未配置")
        sys.exit(1)

    subs = load_subscriptions()
    state = load_state()

    if not subs:
        print("WARNING: 订阅列表为空")
        return [], state

    all_results = []

    for sub in subs:
        name = sub["name"]
        url = sub["url"]
        kb_id = sub.get("knowledge_base_id", "")

        if not kb_id:
            try:
                config_path = os.path.expanduser("~/.openclaw/workspace-content/投资ABC_sync/config.json")
                with open(config_path) as f:
                    config = json.load(f)
                kb_id = config.get("knowledge_base_id", "")
            except:
                pass

        print(f"\n=== {name} ===")

        episodes = parse_podcast_page(url)
        if not episodes:
            print("  ⚠️ 未找到节目")
            all_results.append({"name": name, "status": "PARSE_FAILED", "new_count": 0})
            continue

        latest_id, latest_title = episodes[0]
        print(f"  最新: {latest_title[:50]}")
        print(f"  共 {len(episodes)} 期")

        last_recorded_id = state.get(name, {}).get("latest_episode_id", "")

        if latest_id == last_recorded_id:
            print("  无新增，跳过")
            all_results.append({"name": name, "status": "NO_NEW", "new_count": 0})
            continue

        last_idx = next((i for i, (eid, _) in enumerate(episodes) if eid == last_recorded_id), len(episodes))
        new_episodes = episodes[:last_idx]

        print(f"  新增 {len(new_episodes)} 期，开始上传 IMA...")

        uploaded = []
        for i, (eid, title) in enumerate(new_episodes):
            print(f"  [{i+1}/{len(new_episodes)}] {title[:40]}...")

            content, source_url, is_full = fetch_transcript(eid)

            if not content or len(content) < 500:
                print(f"    ⚠️ 逐字稿获取失败")
                time.sleep(2)
                continue

            safe_name = re.sub(r'[|／/:*?"<>\\]', '', title).strip()[:80] + ".md"

            ok, msg = upload_to_ima(kb_id, content, safe_name, client_id, api_key)

            if ok:
                uploaded.append(eid)
                print(f"    ✅ media_id: {msg}")
            else:
                print(f"    ❌ {msg}")

            time.sleep(2)

        state[name] = {
            "latest_episode_id": latest_id,
            "latest_episode_title": latest_title,
            "last_check": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        all_results.append({
            "name": name,
            "status": "OK",
            "new_count": len(uploaded),
            "latest_title": latest_title
        })

    save_state(state)

    print("\n" + "="*50)
    print("摘要:")
    has_update = False
    for r in all_results:
        if r["status"] == "OK" and r["new_count"] > 0:
            print(f"  ✅ {r['name']}: 新增 {r['new_count']} 期 → 已上传 IMA")
            has_update = True
        elif r["status"] == "NO_NEW":
            print(f"  ➖ {r['name']}: 无更新")
        else:
            print(f"  ⚠️ {r['name']}: {r['status']}")

    if not has_update:
        print("  本次无新增节目")

    return all_results, state


if __name__ == "__main__":
    main()
    print(f"\n完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
