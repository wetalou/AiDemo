"""
案例：LangChain + 百炼兼容端点冒烟测试
======================================
用 ChatOpenAI 走根目录 .env 中的 ALI_BAILIAN_* / DATA_* 配置。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.common.env_utils import API_KEY
from app.common.init_llm import LlmConfigError, get_chat_openai

try:
    model = get_chat_openai()
except LlmConfigError as e:
    raise SystemExit(str(e)) from e

print("这是 key 前缀：", (API_KEY or "")[:8] + "..." if API_KEY else "(空)")

messages = [
    SystemMessage(content="Translate the following from English into Italian"),
    HumanMessage(content="hi!"),
]

parser = StrOutputParser()
result = model.invoke(messages)
print(parser.invoke(result))
