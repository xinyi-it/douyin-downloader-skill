#!/usr/bin/env python3
"""
抖音无水印视频下载器

Usage:
    python douyin.py <url>                    # 下载视频
    python douyin.py <url> --info             # 仅获取信息
    python douyin.py <url> -o ./videos        # 指定输出目录
    python douyin.py <url> --hd               # 下载高清版（如有）

Examples:
    python douyin.py https://v.douyin.com/xxx/
    python douyin.py https://www.douyin.com/video/7652650092314316072
    python douyin.py "7.43 FuL:/ 描述 https://v.douyin.com/xxx/ 复制此链接" --info
"""

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    print("需要 requests 库，请运行: pip install requests", file=sys.stderr)
    sys.exit(1)


# ── 常量 ──────────────────────────────────────────────

DEFAULT_OUTPUT = Path.home() / "Documents" / "douyin_videos"
MOBILE_UA = "Mozilla/5.0 (Linux; Android 12; Pixel 6 Build/SD1A.210817.036) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Mobile Safari/537.36"
PC_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# ── URL 解析 ──────────────────────────────────────────

def extract_url(text: str) -> str:
    """从分享文本中提取抖音URL"""
    # 匹配短链接
    m = re.search(r'https?://v\.douyin\.com/[A-Za-z0-9]+/?', text)
    if m:
        return m.group(0)
    # 匹配完整链接
    m = re.search(r'https?://www\.douyin\.com/video/\d+', text)
    if m:
        return m.group(0)
    # 本身就是URL
    if text.strip().startswith("http"):
        return text.strip()
    raise ValueError(f"无法从文本中提取抖音链接: {text[:50]}...")


def resolve_short_url(url: str) -> str:
    """解析短链接，获取完整URL和视频ID"""
    resp = requests.head(url, headers={"User-Agent": MOBILE_UA}, allow_redirects=True, timeout=10)
    final_url = resp.url
    return final_url


def extract_video_id(url: str) -> Optional[str]:
    """从URL中提取视频ID"""
    m = re.search(r'/video/(\d+)', url)
    if m:
        return m.group(1)
    m = re.search(r'(?:modal_id|vid|item_ids)=(\d+)', url)
    if m:
        return m.group(1)
    return None


# ── 视频信息获取 ──────────────────────────────────────

def get_video_info(video_id: str) -> Dict[str, Any]:
    """从iesdouyin移动端页面获取视频信息"""
    url = f"https://www.iesdouyin.com/share/video/{video_id}/"
    headers = {
        "User-Agent": MOBILE_UA,
        "Referer": "https://www.douyin.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    html = resp.text

    # 从HTML中提取SSR数据
    result = _parse_html_data(html, video_id)
    if result:
        return result

    # 备用：从API获取
    return _get_video_info_api(video_id)


def _parse_html_data(html: str, video_id: str) -> Optional[Dict[str, Any]]:
    """从iesdouyin页面HTML中解析视频数据"""
    # 提取play_addr URL列表
    play_urls = re.findall(r'play_addr.*?url_list.*?\["(.*?)"', html)
    download_urls = re.findall(r'download_addr.*?url_list.*?\["(.*?)"', html)

    # 清理URL中的unicode转义
    def clean_url(u: str) -> str:
        return u.replace('\\u002F', '/').replace('\\\\u002F', '/').replace('\\/', '/')

    # 无水印URL：把 /playwm/ 替换为 /play/
    video_url = None
    hd_url = None

    if download_urls:
        hd_url = clean_url(download_urls[0])

    if play_urls:
        raw = clean_url(play_urls[0])
        video_url = raw.replace('/playwm/', '/play/')

    if not video_url:
        return None

    # 提取标题
    title = ""
    m = re.search(r'"desc"\s*:\s*"([^"]+)"', html)
    if m:
        title = m.group(1)

    # 提取作者
    author = ""
    m = re.search(r'"nickname"\s*:\s*"([^"]+)"', html)
    if m:
        author = m.group(1)

    # 提取统计数据
    stats = {}
    for key, pattern in [("likes", r'"digg_count"\s*:\s*(\d+)'),
                          ("comments", r'"comment_count"\s*:\s*(\d+)'),
                          ("shares", r'"share_count"\s*:\s*(\d+)'),
                          ("plays", r'"play_count"\s*:\s*(\d+)')]:
        m = re.search(pattern, html)
        if m:
            stats[key] = int(m.group(1))

    # 提取时长（毫秒），取最大值（HTML中可能有多个duration，视频的是最大的）
    duration = 0
    for m in re.finditer(r'"duration"\s*:\s*(\d+)', html):
        val = int(m.group(1))
        if val > duration:
            duration = val
    # 转换为秒
    duration = duration / 1000 if duration > 1000 else duration

    # 提取封面
    cover_url = ""
    m = re.search(r'cover.*?url_list.*?\["(.*?)"', html)
    if m:
        cover_url = clean_url(m.group(1))

    return {
        "id": video_id,
        "title": title,
        "author": author,
        "cover": cover_url,
        "video_url": video_url,
        "hd_url": hd_url,
        "duration": duration,  # 秒
        "statistics": stats,
    }


def _get_video_info_api(video_id: str) -> Dict[str, Any]:
    """备用：通过iesdouyin API获取视频信息"""
    url = "https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/"
    params = {"item_ids": video_id}
    headers = {"User-Agent": MOBILE_UA, "Referer": "https://www.douyin.com/"}

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("item_list", [])
    if not items:
        raise ValueError(f"API未返回视频数据 (id: {video_id})")

    item = items[0]
    video = item.get("video", {})
    stats = item.get("statistics", {})

    # 提取无水印URL
    play_urls = video.get("play_addr", {}).get("url_list", [])
    video_url = play_urls[0].replace("/playwm/", "/play/") if play_urls else ""

    download_urls = video.get("download_addr", {}).get("url_list", [])
    hd_url = download_urls[0] if download_urls else None

    return {
        "id": item.get("aweme_id", video_id),
        "title": item.get("desc", ""),
        "author": item.get("author", {}).get("nickname", ""),
        "cover": video.get("cover", {}).get("url_list", [""])[0],
        "video_url": video_url,
        "hd_url": hd_url,
        "duration": video.get("duration", 0) / 1000 if video.get("duration", 0) > 1000 else video.get("duration", 0),
        "statistics": {
            "likes": int(stats.get("digg_count", 0)),
            "comments": int(stats.get("comment_count", 0)),
            "shares": int(stats.get("share_count", 0)),
            "plays": int(stats.get("play_count", 0)),
        },
    }


# ── 下载 ──────────────────────────────────────────────

def download_video(url: str, output_path: Path) -> Path:
    """下载视频文件"""
    headers = {
        "User-Agent": MOBILE_UA,
        "Referer": "https://www.douyin.com/",
    }
    resp = requests.get(url, headers=headers, stream=True, timeout=30)
    resp.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return output_path


# ── 主流程 ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="抖音无水印视频下载器",
        epilog="示例: python douyin.py https://v.douyin.com/xxx/ --info",
    )
    parser.add_argument("url", help="抖音视频链接（短链接/完整链接/分享文本）")
    parser.add_argument("-o", "--output", help="输出目录", default=None)
    parser.add_argument("-i", "--info", action="store_true", help="仅显示视频信息，不下载")
    parser.add_argument("--hd", action="store_true", help="下载高清版（如有）")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出信息")
    args = parser.parse_args()

    # Step 1: 提取URL
    try:
        url = extract_url(args.url)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: 解析短链接，获取视频ID
    print(f"解析链接: {url}")
    if "v.douyin.com" in url:
        final_url = resolve_short_url(url)
        video_id = extract_video_id(final_url)
        if not video_id:
            print(f"错误: 无法从重定向URL提取视频ID: {final_url}", file=sys.stderr)
            sys.exit(1)
        print(f"视频ID: {video_id}")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            print(f"错误: 无法从URL提取视频ID", file=sys.stderr)
            sys.exit(1)
        print(f"视频ID: {video_id}")

    # Step 3: 获取视频信息
    print("获取视频信息...")
    try:
        info = get_video_info(video_id)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 4: 输出信息
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    duration_s = info["duration"]
    print(f"\n{'='*50}")
    print(f"  标题:   {info['title']}")
    print(f"  作者:   {info['author']}")
    print(f"  时长:   {duration_s:.1f}秒")
    if info.get("statistics"):
        s = info["statistics"]
        print(f"  点赞:   {s.get('likes', 0):,}")
        print(f"  评论:   {s.get('comments', 0):,}")
        print(f"  播放:   {s.get('plays', 0):,}")
    print(f"  ID:     {info['id']}")
    print(f"{'='*50}")

    if args.info:
        print(f"\n视频URL: {info['video_url']}")
        if info.get("hd_url"):
            print(f"高清URL: {info['hd_url']}")
        return

    # Step 5: 下载
    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT
    output_path = output_dir / f"{info['id']}.mp4"

    dl_url = info["hd_url"] if (args.hd and info.get("hd_url")) else info["video_url"]
    print(f"\n下载中... {'(高清)' if args.hd and info.get('hd_url') else '(无水印)'}")
    try:
        download_video(dl_url, output_path)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✅ 已保存: {output_path} ({size_mb:.1f}MB)")
    except Exception as e:
        print(f"❌ 下载失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
