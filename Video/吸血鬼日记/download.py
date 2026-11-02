# -*- coding: utf-8 -*-
# ============================================================
# 通用剧集下载脚本（适配 dazhikeji.com 这类站点）
#
# 所有剧集相关参数（剧名、保存目录、URL 模板、各季 ID 等）放在独立的
# JSON 配置文件中，默认为脚本同目录下的 config.json，可用 --config 指定其他文件。
# 这样同一个 download.py 可以复用于任意剧集，只需切换配置文件即可。
#
# 配置文件字段说明：
#   series_name      剧集名，用于输出文件名前缀（如 "吸血鬼日记"）
#   save_root        视频保存根目录（脚本会自动在其下创建"第X季"子目录）
#   base_play_url    播放页 URL 模板，支持占位符 {series} {playfrom} {episode}
#   playfrom         线路号（默认 1）
#   series_ids       各季对应的网站条目 ID，形如 {"1": 81217, "2": 81322}
#                    （JSON 的 key 必须是字符串，加载时会自动转 int）
#   referer          (可选)请求 Referer 头
#   max_episodes     (可选)整季下载最大探测集数，默认 30；命令行 --max-episodes 可覆盖
#
# 常用命令（在脚本所在目录执行）:
#   # 用默认 config.json 下载第1季第1集
#   python download.py --season 1 --episode 1
#
#   # 下载第1季整季（连续3集失败自动停止）
#   python download.py --season 1
#
#   # 指定其他配置文件
#   python download.py --config path/to/other.json --season 2 --episode 1
#
#   # 网络好时调高并发到5
#   python download.py --season 1 --workers 5
#
#   # 需要走代理（指定地址）
#   python download.py --season 1 --proxy http://127.0.0.1:7890
#
#   # 用系统代理变量（HTTP_PROXY/HTTPS_PROXY）
#   python download.py --season 1 --use-proxy
#
#   # 强制直连，忽略系统代理变量
#   python download.py --season 1 --no-proxy
# ============================================================
# 代理配置：可在代码顶部 USE_PROXY / PROXY_URL 修改默认值，也可用命令行参数覆盖
#   USE_PROXY = False  # 默认强制直连
#   PROXY_URL = None   # 或 "http://127.0.0.1:7890"
import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urljoin

import requests

# ============== 代理配置 ==============
# 是否使用代理：False=强制直连（忽略系统代理变量），True=使用代理
USE_PROXY = False
# 代理地址：None 时若 USE_PROXY=True 会自动读取系统 HTTP_PROXY/HTTPS_PROXY 变量
# 如："http://127.0.0.1:7890"
PROXY_URL = None
# ====================================

# 默认 UA；Referer 由配置文件 referer 字段提供
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

# 剧集配置，由 main() 从 JSON 文件加载
CONFIG: dict = {}

# 并发分片下载线程数
MAX_WORKERS = 3


def _build_session() -> "requests.Session":
    """根据 USE_PROXY / PROXY_URL / CONFIG.referer 构建 Session"""
    s = requests.Session()
    headers = dict(DEFAULT_HEADERS)
    referer = CONFIG.get("referer") if CONFIG else None
    if referer:
        headers["Referer"] = referer
    s.headers.update(headers)
    if USE_PROXY:
        if PROXY_URL:
            s.proxies = {"http": PROXY_URL, "https": PROXY_URL}
        # PROXY_URL 为 None 时保持 trust_env=True，自动读取系统 env 代理变量
    else:
        # 强制直连：trust_env=False 让 requests 完全忽略系统代理变量
        s.trust_env = False
    return s


# 延迟初始化：CONFIG 加载完成、main 中调用 _build_session 后才会真正使用
_SESSION: "requests.Session | None" = None


def load_config(config_path: Path) -> dict:
    """加载并校验 JSON 配置文件，返回规范化后的配置字典"""
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    required = ["series_name", "save_root", "base_play_url", "series_ids"]
    for k in required:
        if k not in cfg:
            raise ValueError(f"配置文件缺少必需字段: {k}")

    # series_ids 的 key 必须是字符串，加载后转 int 便于按季查找
    raw_ids = cfg["series_ids"]
    cfg["series_ids"] = {int(k): int(v) for k, v in raw_ids.items()}

    # 可选字段默认值
    cfg.setdefault("playfrom", 1)
    cfg.setdefault("max_episodes", 30)
    cfg.setdefault("referer", None)
    return cfg


def season_dir(season: int) -> Path:
    p = Path(CONFIG["save_root"]) / f"第{season}季"
    p.mkdir(parents=True, exist_ok=True)
    return p


def episode_url(season: int, episode: int) -> str:
    series_id = CONFIG["series_ids"].get(season)
    if series_id is None:
        raise ValueError(
            f"未配置第{season}季的 series ID，请在配置文件 series_ids 中添加。"
            f"已知季: {sorted(CONFIG['series_ids'].keys())}"
        )
    return CONFIG["base_play_url"].format(
        series=series_id,
        playfrom=CONFIG.get("playfrom", 1),
        episode=episode,
    )


def fetch_page(url: str, timeout: int = 30) -> str:
    resp = _SESSION.get(url, timeout=timeout)
    resp.encoding = resp.apparent_encoding or "utf-8"
    resp.raise_for_status()
    return resp.text


def extract_media_source(html: str):
    m = re.search(r"player_aaaa\s*=\s*(\{.*?\})\s*[;<]", html, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            u = data.get("url")
            if u:
                return u, _kind(u)
        except Exception:
            pass

    for pat, label in [
        (r"""url\s*[:=]\s*['"]([^'"]+\.m3u8[^'"]*)['"]""", "m3u8"),
        (r"""url\s*[:=]\s*['"]([^'"]+\.mp4[^'"]*)['"]""", "mp4"),
    ]:
        m = re.search(pat, html, re.I)
        if m:
            return m.group(1), label

    for pat, label in [
        (r"https?://[^\s'\"<>]+\.m3u8[^\s'\"<>]*", "m3u8"),
        (r"https?://[^\s'\"<>]+\.mp4[^\s'\"<>]*", "mp4"),
    ]:
        m = re.search(pat, html, re.I)
        if m:
            return m.group(0), label

    return None, None


def _player_aaaa_empty_url(html: str) -> bool:
    """检测 player_aaaa 存在但 url 为空 —— 网站返回了页面但该集没有视频源（通常表示集不存在）"""
    m = re.search(r"player_aaaa\s*=\s*(\{.*?\})\s*[;<]", html, re.S)
    if not m:
        return False
    try:
        data = json.loads(m.group(1))
        return not data.get("url")
    except Exception:
        return False


def _kind(url: str) -> str:
    low = url.lower().split("?")[0]
    if low.endswith(".m3u8"):
        return "m3u8"
    if low.endswith(".mp4"):
        return "mp4"
    return "unknown"


# ---------- Python 纯代码下载 ----------

def download_mp4_direct(url: str, out_path: Path) -> bool:
    try:
        print("  [mp4] 直接下载...", flush=True)
        with _SESSION.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            if total > 0:
                print(f"  [mp4] 下载完成: {downloaded / 1024 / 1024:.1f} MB", flush=True)
        return True
    except Exception as e:
        print(f"  [mp4] 失败: {e}", flush=True)
        return False


def parse_m3u8(m3u8_text: str, base_url: str):
    segments = []
    for line in m3u8_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        seg_url = urljoin(base_url, line)
        segments.append(seg_url)
    return segments


def _download_one_ts(args):
    seg_url, tmp_dir, idx, total = args
    fname = f"{idx:06d}.ts"
    fpath = tmp_dir / fname
    if fpath.exists() and fpath.stat().st_size > 0:
        return idx, fpath, True
    for attempt in range(1, 4):
        try:
            with _SESSION.get(seg_url, timeout=60) as r:
                r.raise_for_status()
                with open(fpath, "wb") as f:
                    f.write(r.content)
            return idx, fpath, True
        except Exception:
            if attempt == 3:
                return idx, None, False
            import time
            time.sleep(1)
    return idx, None, False


def download_m3u8_python(m3u8_url: str, out_path: Path) -> bool:
    try:
        print("  [m3u8] 拉取 playlist...", flush=True)
        base_url = m3u8_url.rsplit("/", 1)[0] + "/"
        r = _SESSION.get(m3u8_url, timeout=60)
        r.raise_for_status()
        segments = parse_m3u8(r.text, base_url)
        total = len(segments)
        print(f"  [m3u8] 共 {total} 个分片，并发 {MAX_WORKERS} 下载...", flush=True)

        tmp_dir = Path(tempfile.mkdtemp(prefix="m3u8_dl_"))
        args_list = [(segments[i], tmp_dir, i, total) for i in range(total)]

        failed_indices = []

        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(_download_one_ts, a): a for a in args_list}
            for fut in concurrent.futures.as_completed(futures):
                idx, fpath, ok = fut.result()
                if ok:
                    done += 1
                else:
                    failed_indices.append(idx)
                if (done + len(failed_indices)) % 50 == 0 or (done + len(failed_indices)) == total:
                    print(f"  [m3u8] 进度: {done}/{total} (失败 {len(failed_indices)})", flush=True)

        if failed_indices:
            print(f"  [m3u8] 第二轮重试 {len(failed_indices)} 个失败分片 (串行)...", flush=True)
            import time as _time
            still_failed = []
            for idx in failed_indices:
                _time.sleep(0.5)
                _, _, ok = _download_one_ts((segments[idx], tmp_dir, idx, total))
                if ok:
                    done += 1
                else:
                    still_failed.append(idx)

            if still_failed:
                print(f"  [m3u8] 仍有 {len(still_failed)} 个分片失败，中止。", flush=True)
                for f in tmp_dir.iterdir():
                    try:
                        f.unlink()
                    except Exception:
                        pass
                try:
                    tmp_dir.rmdir()
                except Exception:
                    pass
                return False
            print(f"  [m3u8] 第二轮重试全部成功！", flush=True)

        print("  [m3u8] 合并分片...", flush=True)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as out:
            for i in range(len(segments)):
                ts_file = tmp_dir / f"{i:06d}.ts"
                if ts_file.exists():
                    with open(ts_file, "rb") as inp:
                        out.write(inp.read())

        total_mb = out_path.stat().st_size / 1024 / 1024
        print(f"  [m3u8] 完成: {total_mb:.1f} MB", flush=True)

        for f in tmp_dir.iterdir():
            try:
                f.unlink()
            except Exception:
                pass
        try:
            tmp_dir.rmdir()
        except Exception:
            pass

        if out_path.suffix.lower() == ".ts":
            mp4_path = out_path.with_suffix(".mp4")
            try:
                out_path.rename(mp4_path)
                out_path = mp4_path
            except Exception:
                pass

        return True
    except Exception as e:
        print(f"  [m3u8] 失败: {e}", flush=True)
        return False


# ---------- 备选：yt-dlp / ffmpeg ----------

def download_with_yt_dlp(url: str, out_path: Path) -> bool:
    try:
        cmd = [
            "yt-dlp",
            "--no-progress",
            "--proxy", "",  # 强制不走代理
            "-o", str(out_path),
            "--merge-output-format", "mp4",
        ]
        cmd.append(url)
        print(f"  [yt-dlp] {' '.join(cmd)}", flush=True)
        subprocess.run(cmd, check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError as e:
        print(f"  [yt-dlp] 失败: {e}", flush=True)
        return False


def download_with_ffmpeg(url: str, out_path: Path, kind: str) -> bool:
    if kind == "unknown":
        return False
    final = out_path.with_suffix(".mp4")
    try:
        # 用 _SESSION.headers（含 Referer）作为请求头
        cmd = [
            "ffmpeg", "-y",
            "-headers", "\r\n".join(f"{k}: {v}" for k, v in _SESSION.headers.items()) + "\r\n",
            "-i", url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            str(final),
        ]
        print(f"  [ffmpeg] {' '.join(cmd)}", flush=True)
        subprocess.run(cmd, check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError as e:
        print(f"  [ffmpeg] 失败: {e}", flush=True)
        return False


# ---------- 主流程 ----------

TEMP_SUFFIXES = (".part", ".ytdl", ".frag", ".download", ".tmp", ".ts")


def _cleanup_temp_files(out_dir: Path, base_name: str):
    for f in out_dir.glob(f"{base_name}.*"):
        if f.suffix.lower() in TEMP_SUFFIXES or ".part" in f.name:
            try:
                f.unlink()
            except Exception:
                pass


def download_episode(season: int, episode: int) -> bool:
    try:
        play_url = episode_url(season, episode)
    except ValueError as e:
        print(f"  {e}", flush=True)
        return False
    print(f"\n=== 第{season}季 第{episode}集 ===", flush=True)
    print(f"  播放页: {play_url}", flush=True)

    out_dir = season_dir(season)
    base_name = f"{CONFIG['series_name']}-S{season:02d}E{episode:02d}"
    out_path = out_dir / f"{base_name}.mp4"

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  已存在，跳过: {out_path}", flush=True)
        return True

    _cleanup_temp_files(out_dir, base_name)

    try:
        html = fetch_page(play_url)
    except Exception as e:
        print(f"  获取播放页失败: {e}", flush=True)
        return False

    media_url, kind = extract_media_source(html)
    if not media_url:
        if _player_aaaa_empty_url(html):
            print(f"  该集不存在或暂无视频源（player_aaaa.url 为空）。", flush=True)
        else:
            print("  未在页面中找到 m3u8/mp4 视频源。", flush=True)
        return False
    print(f"  解析到视频源 ({kind}): {media_url}", flush=True)

    ok = False
    if kind == "mp4":
        ok = download_mp4_direct(media_url, out_path)
    elif kind == "m3u8":
        ok = download_m3u8_python(media_url, out_path)
        if not ok:
            print("  Python下载失败，尝试 yt-dlp...", flush=True)
            ok = download_with_yt_dlp(media_url, out_dir / f"{base_name}.%(ext)s")
            if not ok:
                print("  尝试 ffmpeg...", flush=True)
                ok = download_with_ffmpeg(media_url, out_path, kind)
    else:
        ok = download_mp4_direct(media_url, out_path) or \
             download_with_yt_dlp(media_url, out_dir / f"{base_name}.%(ext)s")

    if ok and out_path.exists() and out_path.stat().st_size > 0:
        print(f"  完成: {out_path}", flush=True)
        _cleanup_temp_files(out_dir, base_name)
        return True

    if ok:
        for f in out_dir.glob(f"{base_name}.*"):
            if f.stat().st_size > 0 and f.suffix.lower() not in TEMP_SUFFIXES and ".part" not in f.name:
                print(f"  完成: {f}", flush=True)
                _cleanup_temp_files(out_dir, base_name)
                return True

    _cleanup_temp_files(out_dir, base_name)
    print(f"  下载失败: 第{season}季 第{episode}集", flush=True)
    return False


def download_season(season: int, max_episodes: int = 30):
    if season not in CONFIG["series_ids"]:
        print(
            f"\n未配置第{season}季的 series ID，无法下载。"
            f"已知季: {sorted(CONFIG['series_ids'].keys())}"
            f"\n请在配置文件 series_ids 中添加第{season}季对应的条目 ID。",
            flush=True,
        )
        return
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
                print(f"\n连续 {fail_streak} 集失败，认为第{season}季已结束。", flush=True)
                break
    print(f"\n第{season}季下载完成，成功 {success} 集。", flush=True)


def _resolve_config_path(raw: str) -> Path:
    """相对路径相对脚本所在目录解析"""
    p = Path(raw)
    if not p.is_absolute():
        p = Path(__file__).parent / p
    return p


def main():
    global MAX_WORKERS, USE_PROXY, PROXY_URL, _SESSION, CONFIG

    parser = argparse.ArgumentParser(
        description="通用剧集下载脚本（通过 JSON 配置文件指定剧集参数）"
    )
    parser.add_argument("--config", default="config.json",
                        help="配置文件路径，默认脚本同目录下 config.json")
    parser.add_argument("--season", type=int, default=1, help="季号，默认 1")
    parser.add_argument("--episode", type=int, default=0, help="集号；不填则下载整季")
    parser.add_argument("--max-episodes", type=int, default=0,
                        help="整季下载最大探测集数；0 表示使用配置文件中的 max_episodes")
    parser.add_argument("--workers", type=int, default=3, help="并发下载分片数，默认 3")
    parser.add_argument("--proxy", default=None,
                        help="代理地址，如 http://127.0.0.1:7890；传了就走该代理，不传按代码里 USE_PROXY/PROXY_URL 配置")
    parser.add_argument("--use-proxy", action="store_true",
                        help="使用系统代理变量（HTTP_PROXY/HTTPS_PROXY）；等价于代码里设 USE_PROXY=True")
    parser.add_argument("--no-proxy", action="store_true",
                        help="强制直连，忽略系统代理变量；等价于代码里设 USE_PROXY=False")
    args = parser.parse_args()

    # 1) 加载配置文件
    config_path = _resolve_config_path(args.config)
    try:
        CONFIG = load_config(config_path)
    except Exception as e:
        print(f"加载配置失败 ({config_path}): {e}", flush=True)
        sys.exit(1)

    # 2) 命令行覆盖代理配置：优先级 --proxy > --use-proxy/--no-proxy > 代码内 USE_PROXY
    if args.proxy:
        USE_PROXY = True
        PROXY_URL = args.proxy
    elif args.use_proxy:
        USE_PROXY = True
    elif args.no_proxy:
        USE_PROXY = False
    _SESSION = _build_session()

    # 3) max_episodes 优先级：命令行 > 配置文件 > 默认 30
    max_eps = args.max_episodes if args.max_episodes > 0 else CONFIG.get("max_episodes", 30)

    MAX_WORKERS = args.workers

    # 4) 打印运行信息
    print(f"配置文件: {config_path}", flush=True)
    print(f"剧集: {CONFIG['series_name']}", flush=True)
    print(f"保存根目录: {CONFIG['save_root']}", flush=True)
    if USE_PROXY:
        print(f"代理: 启用（{PROXY_URL or '读取系统env变量'}）", flush=True)
    else:
        print(f"代理: 无（强制直连，忽略系统代理变量）", flush=True)
    print(f"并发: {MAX_WORKERS}", flush=True)
    print(f"已知季: {sorted(CONFIG['series_ids'].keys())}", flush=True)
    os.makedirs(CONFIG["save_root"], exist_ok=True)

    if args.episode > 0:
        download_episode(args.season, args.episode)
    else:
        download_season(args.season, max_eps)


if __name__ == "__main__":
    main()
