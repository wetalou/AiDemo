"""
统一初始化 OpenAI 兼容客户端与 LangChain ChatOpenAI。
"""

from __future__ import annotations

from typing import Any, Literal

from openai import OpenAI

from app.common import env_utils

Provider = Literal["bailian", "dashscope"]


class LlmConfigError(RuntimeError):
    """模型配置缺失或无效。"""


def _require_bailian() -> tuple[str, str, str]:
    missing = env_utils.missing_bailian_config()
    if missing:
        raise LlmConfigError(
            "缺少模型配置：" + "；".join(missing) + "。\n" + env_utils.config_hint()
        )
    assert env_utils.API_KEY and env_utils.BASE_URL and env_utils.MODEL
    return env_utils.API_KEY, env_utils.BASE_URL, env_utils.MODEL


def _require_dashscope() -> tuple[str, str]:
    missing = env_utils.missing_dashscope_config()
    if missing:
        raise LlmConfigError(
            "缺少模型配置：" + "；".join(missing) + "。\n" + env_utils.config_hint()
        )
    assert env_utils.DASHSCOPE_API_KEY and env_utils.DASHSCOPE_BASE_URL
    return env_utils.DASHSCOPE_API_KEY, env_utils.DASHSCOPE_BASE_URL


def get_openai_client(
    *,
    provider: Provider = "bailian",
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAI:
    """
    返回 openai.OpenAI 客户端。

    provider:
        - bailian：DATA_* / ALI_BAILIAN_*
        - dashscope：DASHSCOPE_*（缺省兼容端点）
    """
    env_utils.ensure_env_loaded()
    if provider == "dashscope":
        key, url = _require_dashscope()
        return OpenAI(api_key=api_key or key, base_url=base_url or url)

    key, url, _model = _require_bailian()
    return OpenAI(api_key=api_key or key, base_url=base_url or url)


def get_chat_openai(
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0,
    **kwargs: Any,
):
    """返回 langchain_openai.ChatOpenAI（走百炼/通用兼容配置）。"""
    from langchain_openai import ChatOpenAI

    env_utils.ensure_env_loaded()
    key, url, default_model = _require_bailian()
    return ChatOpenAI(
        model=model or default_model,
        api_key=api_key or key,
        base_url=base_url or url,
        temperature=temperature,
        **kwargs,
    )


def resolve_bailian_model(override: str | None = None) -> str:
    env_utils.ensure_env_loaded()
    _key, _url, default_model = _require_bailian()
    return override or default_model
