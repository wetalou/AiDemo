"""
加载项目根目录 .env，并导出常用模型配置常量。

变量优先级（OpenAI 兼容 / 百炼）：
    DATA_*  >  ALI_BAILIAN_*

DashScope 直连场景单独读 DASHSCOPE_API_KEY；
base_url 缺省为官方兼容端点。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# app/common/env_utils.py → 上溯两级到仓库根
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

_ENV_LOADED = False


def ensure_env_loaded(*, override: bool = True) -> Path:
    """从仓库根加载 .env；可重复调用，默认只真正加载一次。"""
    global _ENV_LOADED
    env_path = ROOT_DIR / ".env"
    if not _ENV_LOADED:
        load_dotenv(env_path, override=override)
        _ENV_LOADED = True
    return env_path


def _first(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value is not None and str(value).strip() != "":
            return value
    return default


ensure_env_loaded()

# ---- 百炼 / 通用 OpenAI 兼容（DATA_* 优先）----
API_KEY = _first("DATA_API_KEY", "ALI_BAILIAN_API_KEY")
BASE_URL = _first("DATA_BASE_URL", "ALI_BAILIAN_BASE_URL")
MODEL = _first("DATA_MODEL", "ALI_BAILIAN_MODEL")

# ---- DashScope ----
DASHSCOPE_API_KEY = _first("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = _first("DASHSCOPE_BASE_URL", default=DEFAULT_DASHSCOPE_BASE_URL)

# 兼容旧脚本直接引用的别名
ALI_BAILIAN_API_KEY = _first("ALI_BAILIAN_API_KEY")
ALI_BAILIAN_BASE_URL = _first("ALI_BAILIAN_BASE_URL")
ALI_BAILIAN_MODEL = _first("ALI_BAILIAN_MODEL")
DATA_API_KEY = _first("DATA_API_KEY")
DATA_BASE_URL = _first("DATA_BASE_URL")
DATA_MODEL = _first("DATA_MODEL")


def missing_bailian_config() -> list[str]:
    """返回百炼/通用兼容通道缺失的配置项名称。"""
    missing: list[str] = []
    if not API_KEY:
        missing.append("DATA_API_KEY 或 ALI_BAILIAN_API_KEY")
    if not BASE_URL:
        missing.append("DATA_BASE_URL 或 ALI_BAILIAN_BASE_URL")
    if not MODEL:
        missing.append("DATA_MODEL 或 ALI_BAILIAN_MODEL")
    return missing


def missing_dashscope_config() -> list[str]:
    """返回 DashScope 通道缺失的配置项名称。"""
    if DASHSCOPE_API_KEY:
        return []
    return ["DASHSCOPE_API_KEY"]


def config_hint() -> str:
    return (
        f"请复制 .env.example 为 .env 并填写密钥（路径：{ROOT_DIR / '.env.example'}）"
    )
