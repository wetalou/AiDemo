"""
tools/registry.py —— AI Agent 工具注册表
========================================
管理所有可供大模型调用的工具（Tools）。
"""

from typing import Any, Callable

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
