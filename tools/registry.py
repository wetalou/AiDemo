"""
tools/registry.py —— AI Agent 工具注册表
========================================
管理所有可供大模型调用的工具（Tools）。
每个工具包含：
    - name:        工具名称（大模型通过这个名字调用）
    - description: 工具功能描述（大模型据此判断什么时候用这个工具）
    - parameters:  JSON Schema 格式的参数定义
    - handler:     实际执行函数

使用方式：
    1. 在 tools/ 下新建一个 .py 文件，定义 handler 函数和 schema
    2. 调用 register_tool(schema, handler) 注册
    3. 在 agent 中调用 get_all_tools() 拿到 tools 列表传给大模型
    4. 大模型返回 tool_calls 后，用 dispatch(tool_call) 执行
"""

from typing import Callable, Any

_TOOLS: dict[str, dict] = {}


def register_tool(schema: dict, handler: Callable[..., Any]):
    name = schema["function"]["name"]
    _TOOLS[name] = {
        "schema": schema,
        "handler": handler,
    }


def get_all_tools() -> list[dict]:
    return [t["schema"] for t in _TOOLS.values()]


def dispatch(tool_call) -> str:
    name = tool_call.function.name
    arguments = tool_call.function.arguments

    import json
    args = json.loads(arguments) if isinstance(arguments, str) else arguments

    if name not in _TOOLS:
        return f"❌ 未知工具: {name}"

    handler = _TOOLS[name]["handler"]
    try:
        result = handler(**args)
        return str(result)
    except Exception as e:
        return f"❌ 工具 {name} 执行失败: {e}"
