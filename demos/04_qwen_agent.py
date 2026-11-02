"""
案例4：通义千问 Agent（带 Tool Calling）
==========================================
功能：与通义千问大模型多轮对话，并让模型自动调用工具（Tools）来回答问题。
学习点：
    1. OpenAI SDK 的 tools 参数 —— 把工具 JSON Schema 告诉大模型
    2. tool_calls 响应解析 —— 判断大模型是要调用工具还是直接回答
    3. 工具执行循环 —— 调用函数 → 结果回传 → 再请求模型 → 直到最终回复
    4. tools/ 目录的工具注册机制 —— 新增工具只需在 tools/ 下加文件
可用工具：
    - get_weather(city)  查询城市天气
依赖：
    pip install gradio openai requests
前置准备：
    设置环境变量 DASHSCOPE_API_KEY
    $env:DASHSCOPE_API_KEY = "sk-你的key"
"""

import gradio as gr
import os
import json
from openai import OpenAI
from tools import get_all_tools, dispatch

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("未设置 DASHSCOPE_API_KEY 环境变量！")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

MODEL = "qwen-max"
MAX_TOOL_ROUNDS = 5


def _build_messages(message, history):
    messages = [{"role": "system", "content": "你是一个智能助手，可以调用工具来帮助用户解决问题。"}]

    if history:
        for msg in history:
            if isinstance(msg, dict) and "role" in msg:
                messages.append(msg)
            elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                messages.append({"role": "user", "content": msg[0]})
                messages.append({"role": "assistant", "content": msg[1]})

    messages.append({"role": "user", "content": message})
    return messages


def _call_model(messages):
    tools = get_all_tools()
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    return client.chat.completions.create(**kwargs)


def _do_tool_calls(messages, assistant_message):
    tool_calls = assistant_message.tool_calls
    if not tool_calls:
        return messages

    messages.append({
        "role": "assistant",
        "content": assistant_message.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ],
    })

    for tc in tool_calls:
        result = dispatch(tc)
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })

    return messages


def agent_chat(message, history):
    if not api_key:
        return "未设置 DASHSCOPE_API_KEY 环境变量，请先配置后重试。"

    messages = _build_messages(message, history)

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            response = _call_model(messages)
        except Exception as e:
            return f"调用失败：{e}"

        choice = response.choices[0]
        assistant_message = choice.message

        if not assistant_message.tool_calls:
            return assistant_message.content or "(模型未返回内容)"

        messages = _do_tool_calls(messages, assistant_message)

    return "已达到最大工具调用轮数。"


available_tools = get_all_tools()
tool_names = ", ".join(t["function"]["name"] for t in available_tools) if available_tools else "无"

demo = gr.ChatInterface(
    fn=agent_chat,
    title="通义千问 - Agent (Tool Calling)",
    description=f"智能助手可以自动调用工具来回答问题。当前可用工具：{tool_names}",
)

demo.launch()
