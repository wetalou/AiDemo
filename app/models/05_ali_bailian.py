"""
案例：阿里百炼流式调用（含思考过程）
==================================
从 app.common 读取 ALI_BAILIAN_* / DATA_*，用 OpenAI 兼容 SDK 流式输出。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.common.init_llm import LlmConfigError, get_openai_client, resolve_bailian_model

try:
    client = get_openai_client(provider="bailian")
    model_name = resolve_bailian_model()
except LlmConfigError as e:
    raise SystemExit(str(e)) from e

messages = [{"role": "user", "content": "你是谁"}]
completion = client.chat.completions.create(
    model=model_name,
    messages=messages,
    extra_body={"enable_thinking": True, "reasoning_effort": "max"},
    stream=True,
)

is_answering = False
print("\n" + "=" * 20 + "思考过程" + "=" * 20)
for chunk in completion:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
        if not is_answering:
            print(delta.reasoning_content, end="", flush=True)
    if hasattr(delta, "content") and delta.content:
        if not is_answering:
            print("\n" + "=" * 20 + "完整回复" + "=" * 20)
            is_answering = True
        print(delta.content, end="", flush=True)
