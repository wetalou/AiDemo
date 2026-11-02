"""
tools/weather.py —— 天气查询工具
================================
调用免费的 wttr.in 接口查询实时天气，无需 API Key。
"""

import requests
from tools.registry import register_tool


def get_weather(city: str) -> str:
    """查询指定城市的当前天气，包括温度、天气状况、湿度、风速。"""
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "curl/7.68.0"})
        resp.raise_for_status()
        data = resp.json()

        cur = data["current_condition"][0]
        area = data["nearest_area"][0]

        return (
            f"{area['areaName'][0]['value']} 天气，"
            f"{cur['weatherDesc'][0]['value']}。"
            f"{cur['temp_C']}°C（体感{cur['FeelsLikeC']}°C）。"
            f"湿度{cur['humidity']}%，风速{cur['windspeedKmph']}km/h"
        )
    except Exception:
        return f"【{city}】（模拟数据）晴，28°C，体感30°C，湿度65%"


_WEATHER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的当前天气，包括温度、天气状况、湿度、风速。当用户问某个城市天气、气温、冷不冷、热不热、下不下雨时用这个工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如：北京、上海、深圳、New York",
                }
            },
            "required": ["city"],
        },
    },
}

register_tool(_WEATHER_SCHEMA, get_weather)
