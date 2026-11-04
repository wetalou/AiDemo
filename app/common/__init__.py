"""AiDemo 公共层：环境变量与 LLM 初始化。"""

from app.common.env_utils import ROOT_DIR, ensure_env_loaded
from app.common.init_llm import get_chat_openai, get_openai_client

__all__ = [
    "ROOT_DIR",
    "ensure_env_loaded",
    "get_openai_client",
    "get_chat_openai",
]
