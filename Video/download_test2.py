# -*- coding: utf-8 -*-
"""
吸血鬼日记 视频下载脚本

视频源页面：https://www.dazhukeji.com/vodplay/81217-{季}-{集}.html
保存目录：  D:\\001-视频\\电视剧\\吸血鬼日记\\第X季\\

下载策略：
  1. 优先使用 yt-dlp（对 m3u8/mp4 与多数站点支持良好）
  2. 失败则解析页面 HTML，提取 m3u8/mp4 链接后用 ffmpeg 下载

依赖：
  pip install yt-dlp requests
  ffmpeg 需加入系统 PATH（yt-dlp 合并 m3u8 也需要 ffmpeg）
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

# ============== 配置区 ==============
SERIES_ID = 81217                       # 剧集 ID（URL 中的 81217）
BASE_PLAY_URL = "https://www.dazhukeji.com/vodplay/{series}-{season}-{episode}.html"
SAVE_ROOT = r"D:\001-视频\电视剧\吸血鬼日记"   # 保存根目录
SERIES_NAME = "吸血鬼日记"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.dazhukeji.com/",
}
# ================================


def season_dir(season: int) -> Path:
    """根据季号返回保存目录，并自动创建。"""
    p = Path(SAVE_ROOT) / f"第{season}季"
    p.mkdir(parents=True, exist_ok=True)
    return p


def episode_url(season: int, episode: int) -> str:
    return BASE_PLAY_URL.format(series=SERIES_ID, season=season, episode=episode)


def fetch_page(url: str, timeout: int = 20) -> str:
    """获取播放页 HTML。"""
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.encoding = resp.apparent_encoding or "utf-8"
    resp.raise_for_status()
    return resp.text


def extract_media_source(html: str):
    """
    从播放页 HTML 中提取视频源。
    常见写法：
      - player_aaaa = {"url":"https://xxx/index.m3u8", ...}
      - 变量 url="https://xxx.m3u8"
      - 直接出现的 .m3u8 或 .mp4 链接
    返回 (url, kind) 或 (None, None)。
    """
    # 1. player_aaaa = {...}  JSON 风格
    m = re.search(r"player_aaaa\s*=\s*(\{.*?\})\s*[;<]", html, re.S)
    if m:
        import json
        try:
            data = json.loads(m.group(1))
            u = data.get("url") or data.get("link")
            if u:
                return u, _kind(u)
        except Exception:
            pass

    # 2. var url = "..."
    m = re.search(r"""url\s*[:=]\s*['"]([^'"]+\.m3u8[^'"]*)['"]""", html, re.I)
    if m:
        return m.group(1), "m3u8"
    m = re.search(r"""url\s*[:=]\s*['"]([^'"]+\.mp4[^'"]*)['"]""", html, re.I)
    if m:
        return m.group(1), "mp4"

    # 3. 任意 m3u8 / mp4 直链
    m = re.search(r"https?://[^\s'\"<>]+\.m3u8[^\s'\"<>]*", html, re.I)
    if m:
        return m.group(0), "m3u8"
    m = re.search(r"https?://[^\s'\"<>]+\.mp4[^\s'\"<>]*", html, re.I)
    if m:
        return m.group(0), "mp4"

    return None, None


def _kind(url: str) -> str:
    low = url.lower().split("?")[0]
    if low.endswith(".m3u8"):
        return "m3u8"
    if low.endswith(".mp4"):
        return "mp4"
    return "unknown"


def filename_for(season: int, episode: int, ext: str) -> str:
    return f"{SERIES_NAME}-S{season:02d}E{episode:02d}.{ext}"


# ---------- 下载方式 ----------

def download_with_yt_dlp(url: str, out_path: Path) -> bool:
    """优先方案：yt-dlp。能直接吃播放页或 m3u8/mp4。"""
    try:
        cmd = [
            "yt-dlp",
            "--no-progress",
            "-o", str(out_path),
            "--merge-output-format", "mp4",
            url,
        ]
        print(f"  [yt-dlp] {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    except FileNotFoundError:
        print("  [yt-dlp] 未安装 yt-dlp，跳过此方案。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  [yt-dlp] 失败: {e}")
        return False


def download_with_ffmpeg(url: str, out_path: Path, kind: str) -> bool:
    """后备方案：用 ffmpeg 直接下载 m3u8 或 mp4。"""
    if kind == "unknown":
        print("  [ffmpeg] 未知媒体类型，跳过。")
        return False
    ext = "mp4"
    final = out_path.with_suffix(f".{ext}")
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-headers",
            "\r\n".join(f"{k}: {v}" for k, v in HEADERS.items()) + "\r\n",
            "-i", url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            str(final),
        ]
        print(f"  [ffmpeg] {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    except FileNotFoundError:
        print("  [ffmpeg] 未安装 ffmpeg，跳过此方案。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  [ffmpeg] 失败: {e}")
        return False


def download_episode(season: int, episode: int) -> bool:
    """下载单集。返回是否成功。"""
    play_url = episode_url(season, episode)
    print(f"\n=== 第{season}季 第{episode}集 ===")
    print(f"  播放页: {play_url}")

    out_dir = season_dir(season)
    base_name = filename_for(season, episode, "mp4").rsplit(".", 1)[0]
    out_path = out_dir / (base_name + ".mp4")

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  已存在，跳过: {out_path}")
        return True

    # 方案1：直接给 yt-dlp 播放页（很多站点 yt-dlp 自带解析）
    if download_with_yt_dlp(play_url, out_path):
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"  完成: {out_path}")
            return True

    # 方案2：解析页面拿到媒体直链
    try:
        html = fetch_page(play_url)
    except Exception as e:
        print(f"  获取播放页失败: {e}")
        return False

    media_url, kind = extract_media_source(html)
    if not media_url:
        print("  未在页面中找到 m3u8/mp4 视频源，可能需要更新解析规则。")
        return False
    print(f"  解析到视频源 ({kind}): {media_url}")

    # 2a. yt-dlp 直链
    out_path_yt = out_dir / (base_name + ".%(ext)s")
    if download_with_yt_dlp(media_url, out_path_yt):
        # yt-dlp 会自动生成扩展名，检查任意匹配前缀的文件
        for f in out_dir.glob(f"{base_name}.*"):
            if f.stat().st_size > 0:
                print(f"  完成: {f}")
                return True

    # 2b. ffmpeg 直链
    if download_with_ffmpeg(media_url, out_path, kind):
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"  完成: {out_path}")
            return True

    print(f"  下载失败: 第{season}季 第{episode}集")
    return False


def download_season(season: int, max_episodes: int = 30):
    """下载整季，遇到连续失败则停止。"""
    success = 0
    fail_streak = 0
    for ep in range(1, max_episodes + 1):
        ok = download_episode(season, ep)
        if ok:
            success += 1
            fail_streak = 0
        else:
            fail_streak += 1
            if fail_streak >= 3:
                print(f"\n连续 {fail_streak} 集失败，认为第{season}季已结束。")
                break
    print(f"\n第{season}季下载完成，成功 {success} 集。")


def main():
    parser = argparse.ArgumentParser(description="下载《吸血鬼日记》视频")
    parser.add_argument("--season", type=int, default=1, help="季号，默认 1")
    parser.add_argument("--episode", type=int, default=0,
                        help="集号；不填则下载整季")
    parser.add_argument("--max-episodes", type=int, default=30,
                        help="整季下载时最大集数探测，默认 30")
    args = parser.parse_args()

    print(f"保存根目录: {SAVE_ROOT}")
    if not os.path.isdir(SAVE_ROOT):
        os.makedirs(SAVE_ROOT, exist_ok=True)
        print(f"已创建目录: {SAVE_ROOT}")

    if args.episode > 0:
        download_episode(args.season, args.episode)
    else:
        download_season(args.season, args.max_episodes)


if __name__ == "__main__":
    sys.exit(0)

