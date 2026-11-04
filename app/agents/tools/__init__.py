"""
app/agents/tools/ —— AI Agent 工具包
====================================
在此目录下放置各种可供大模型调用的工具模块。

新增工具的步骤：
    1. 在本目录下新建一个 .py 文件（如 time_tool.py）
    2. 在文件末尾调用 register_tool(schema, handler) 注册
    3. 在本 __init__.py 中 import 该模块（触发注册）

可用工具：
    - get_weather(city)  天气查询
"""

from app.agents.tools.registry import dispatch, get_all_tools, register_tool

import app.agents.tools.weather  # noqa: F401  触发注册

__all__ = ["register_tool", "get_all_tools", "dispatch"]
