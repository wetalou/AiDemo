from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载 .env 配置文件
load_dotenv()

client = OpenAI(
    api_key=os.getenv("ALI_BAILIAN_API_KEY"),
    base_url=os.getenv("ALI_BAILIAN_BASE_URL"),
)

# completion = client.chat.completions.create(
#     model=os.getenv("ALI_BAILIAN_MODEL"),
#     messages=[{"role": "user", "content": "你是谁"}],
#     extra_body={"enable_thinking": True, "reasoning_effort": "max"},
#     stream=True,
# )

messages = [{"role": "user", "content": "你是谁"}]
completion = client.chat.completions.create(
    model=os.getenv("ALI_BAILIAN_MODEL"),  # 您可以按需更换为其它深度思考模型
    messages=messages,
    extra_body={"enable_thinking": True, "reasoning_effort": "max"},
    stream=True
)
is_answering = False  # 是否进入回复阶段
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