# AiDemo

学习 AI —— Gradio 快速上手示例集合。

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 运行

```powershell
# 方式一：菜单选择运行哪个 Demo（推荐）
python run.py

# 方式二：直接运行某个 Demo
python demos/01_text_reverse.py
python demos/02_image_to_sketch.py
python demos/03_qwen_chat.py
```

### Demo3 前置准备（调用千问模型）

```powershell
# 1. 在阿里云开通 DashScope，获取 API Key：https://dashscope.console.aliyun.com/
# 2. 设置环境变量（PowerShell，只在当前终端生效）
$env:DASHSCOPE_API_KEY = "sk-你的APIKey"

# 3. 然后运行
python demos/03_qwen_chat.py
```

启动成功后浏览器打开 http://127.0.0.1:7860

## 项目结构

```
AiDemo/
├── run.py                        # 快速选择器，输入编号即可切换 Demo
├── requirements.txt              # 统一依赖清单
├── aiDemo001.py                  # 入口提示（历史文件，可忽略）
└── demos/                        # 所有 Demo 按编号放在这里
    ├── 01_text_reverse.py        # 文本反转器（最简单的 Gradio 入门）
    ├── 02_image_to_sketch.py     # 图像转铅笔画（OpenCV + Gradio）
    └── 03_qwen_chat.py           # 通义千问聊天机器人（ChatInterface + DashScope）
```

## Demo 列表

| 编号 | 文件 | 功能 | 学习点 |
|------|------|------|--------|
| 01 | `01_text_reverse.py` | 输入文字 → 倒序输出 | `gr.Interface` 基础用法、Python 切片语法 |
| 02 | `02_image_to_sketch.py` | 上传图片 → 铅笔画效果 | `gr.Image` 组件、OpenCV 图像处理 |
| 03 | `03_qwen_chat.py` | 多轮对话聊天机器人 | `gr.ChatInterface`、API 调用、历史记录管理 |
