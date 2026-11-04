# AiDemo

学习 AI —— Gradio / 模型调用 / Agent 示例集合。

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 配置密钥

```powershell
cp .env.example .env
# 编辑 .env，填写 ALI_BAILIAN_* 和/或 DASHSCOPE_API_KEY
```

统一由 `app/common/env_utils.py` 从**项目根**加载 `.env`：

| 场景 | 变量 |
|------|------|
| 百炼 / 通用 OpenAI 兼容 | `DATA_*` 优先，否则 `ALI_BAILIAN_*` |
| DashScope 直连 | `DASHSCOPE_API_KEY`（可选 `DASHSCOPE_BASE_URL`） |

## 运行

```powershell
# 方式一：菜单选择（推荐）
python run.py

# 方式二：直接运行
python app/gradio/01_text_reverse.py
python app/models/03_qwen_chat.py
python app/agents/05_weather_agent.py
```

启动成功后浏览器打开 http://127.0.0.1:7860（Gradio 类示例）。

## 项目结构

```
AiDemo/
├── app/
│   ├── common/             # 统一配置与 LLM 工厂
│   ├── gradio/             # Gradio 基础（不依赖大模型）
│   ├── models/             # 模型调用入门
│   └── agents/             # Agent + tools/
├── docs/                   # 设计文档（与运行代码分层）
├── .env.example
├── run.py
└── requirements.txt
```

## Demo 列表

| 路径 | 功能 |
|------|------|
| `app/gradio/01_text_reverse.py` | 文本反转 |
| `app/gradio/02_image_to_sketch.py` | 图像转铅笔画 |
| `app/models/03_qwen_chat.py` | 通义千问 Chat（DashScope） |
| `app/models/04_test_langchain.py` | LangChain 冒烟 |
| `app/models/05_ali_bailian.py` | 百炼流式（含思考过程） |
| `app/agents/04_qwen_agent.py` | 千问 Agent + Tool Calling |
| `app/agents/05_weather_agent.py` | LangChain 天气 Agent |
