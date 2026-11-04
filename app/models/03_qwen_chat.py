"""
案例3：通义千问聊天机器人
=========================
功能：与阿里通义千问大模型进行多轮对话聊天。
学习点：
    1. gr.ChatInterface —— Gradio 专为多轮对话设计的聊天界面组件
    2. DashScope 的"OpenAI 兼容模式" —— 用标准 OpenAI SDK 调通义
    3. app.common.init_llm —— 统一从根目录 .env 读取密钥并创建客户端
    4. 多轮对话历史 history 的两种格式兼容处理
依赖：
    pip install gradio openai python-dotenv
前置准备：
    在 .env 中设置 DASHSCOPE_API_KEY（见 .env.example）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import gradio as gr
from app.common.env_utils import DASHSCOPE_API_KEY, config_hint
from app.common.init_llm import LlmConfigError, get_openai_client

try:
    client = get_openai_client(provider="dashscope")
    api_key = DASHSCOPE_API_KEY
except LlmConfigError as e:
    print(f"❌ {e}")
    client = None
    api_key = None


def call_qwen(message, history):
    """
    调用通义千问模型生成回复。

    参数：
        message (str): 用户当前输入的消息内容
        history (list): 聊天历史记录，Gradio 支持两种格式
            - 格式1（新版）：[{"role": "user", "content": "..."}, ...]
            - 格式2（旧版）：[["用户消息1", "助手回复1"], ...]

    返回：
        str: 模型的回复文本，出错时返回错误描述
    """
    if not api_key or client is None:
        return f"❌ 错误：未设置 DASHSCOPE_API_KEY。{config_hint()}"

    messages = []

    if history:
        try:
            for msg in history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(msg)
                elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                    user_msg, assistant_msg = msg
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": assistant_msg})
        except Exception as e:
            print(f"⚠️ 处理历史记录时出错：{e}")

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 调用失败：{str(e)}"


demo = gr.ChatInterface(
    fn=call_qwen,
    title="通义千问 - Chat",
    description="基于通义千问 Max 的 AI 聊天机器人。",
)

demo.launch()
