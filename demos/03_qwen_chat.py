"""
案例3：通义千问聊天机器人
=========================
功能：与阿里通义千问大模型进行多轮对话聊天。
学习点：
    1. gr.ChatInterface —— Gradio 专为多轮对话设计的聊天界面组件
    2. DashScope 的"OpenAI 兼容模式" —— 用标准 OpenAI SDK 调通义，几乎零学习成本
    3. 环境变量管理 API Key —— 不要把密钥硬编码在代码里！
    4. 多轮对话历史 history 的两种格式兼容处理
依赖：
    pip install gradio openai
前置准备：
    1. 去 https://dashscope.console.aliyun.com/ 开通通义千问，获取 API Key
    2. 设置环境变量 DASHSCOPE_API_KEY
       Windows PowerShell: $env:DASHSCOPE_API_KEY="sk-你的key"
       Windows CMD:       set DASHSCOPE_API_KEY=sk-你的key
"""

# ========== 1. 导入必要的库 ==========
import gradio as gr                     # Gradio：构建 Web 界面
import os                               # os：读取环境变量
from openai import OpenAI               # OpenAI 官方客户端 —— 因为 DashScope 兼容 OpenAI API

# ========== 2. 获取 API Key ==========
# 从环境变量 DASHSCOPE_API_KEY 中读取密钥
# 为什么用环境变量？因为 API Key 相当于密码，硬编码在代码里容易泄露
# 设置环境变量示例（Windows PowerShell）：
#   $env:DASHSCOPE_API_KEY = "sk-xxxxxxxxxxxxxxxx"
api_key = os.getenv("DASHSCOPE_API_KEY")

# 如果没设置 API Key，提供一个友好的错误提示，而不是让程序崩掉
if not api_key:
    print("❌ 未设置 DASHSCOPE_API_KEY 环境变量！")
    print("   请先获取 API Key：https://dashscope.console.aliyun.com/")
    print("   然后设置环境变量再运行。")


# ========== 3. 初始化 OpenAI 客户端 ==========
# DashScope 提供了"OpenAI 兼容模式"的端点，所以我们可以直接用 OpenAI 的 SDK
# 只需要把 base_url 改成阿里云的兼容端点就行
client = OpenAI(
    api_key=api_key,                              # 用 DashScope 的 API Key 来鉴权
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # DashScope 兼容端点
)


# ========== 4. 业务逻辑函数 ==========
# gr.ChatInterface 要求的函数签名：fn(message, history) -> str
#   message 是用户当前这轮发的消息
#   history 是之前的聊天记录列表
def call_qwen(message, history):
    """
    调用通义千问模型生成回复。

    参数：
        message (str): 用户当前输入的消息内容
        history (list): 聊天历史记录，Gradio 支持两种格式
            - 格式1（新版）：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            - 格式2（旧版）：[["用户消息1", "助手回复1"], ["用户消息2", "助手回复2"]]

    返回：
        str: 模型的回复文本，出错时返回错误描述
    """

    # ---- 4.1 检查 API Key 是否可用 ----
    if not api_key:
        return "❌ 错误：未设置 DASHSCOPE_API_KEY 环境变量，请先配置后重试。"

    # ---- 4.2 构建发送给模型的 messages 列表 ----
    # messages 是 OpenAI 兼容格式：[{"role": "user", "content": "..."}, ...]
    messages = []

    if history:
        # 遍历历史记录，把旧对话也加进去，这样模型能"记住"之前聊过什么
        try:
            for msg in history:
                # 新版 ChatInterface 格式：每条是个 dict
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(msg)
                # 旧版格式：每条是个 [user_msg, assistant_msg] 列表或元组
                elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                    user_msg, assistant_msg = msg
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": assistant_msg})
        except Exception as e:
            # 历史记录解析失败不要让整个程序崩掉，打印警告继续执行
            print(f"⚠️ 处理历史记录时出错：{e}")

    # 把当前这轮用户的新消息追加到 messages 末尾
    messages.append({"role": "user", "content": message})

    # ---- 4.3 调用千问大模型 ----
    try:
        # client.chat.completions.create() —— 这就是标准的 ChatCompletion 调用
        response = client.chat.completions.create(
            model="qwen-max",       # 模型名称：qwen-max 是千问系列中性能最强的版本
            messages=messages,      # 传完整的对话历史 + 当前消息，让模型理解上下文
            stream=False,           # False=一次性返回完整回复；True=逐字流式返回（进阶）
        )

        # ---- 4.4 提取回复内容并返回 ----
        # response.choices[0] 是模型的第一个候选回复
        # .message.content 就是最终的回复文本
        return response.choices[0].message.content

    except Exception as e:
        # API 调用失败（比如 Key 不对、网络问题、额度用完），返回友好的错误信息
        return f"❌ 调用失败：{str(e)}"


# ========== 5. 界面配置 ==========
# gr.ChatInterface 是 Gradio 专门给多轮聊天做的组件
# 和 gr.Interface 的区别：
#   - 自动提供"气泡式"聊天界面（左右分布）
#   - 自动管理 history 历史记录
#   - 自带"清除历史"按钮
demo = gr.ChatInterface(
    fn=call_qwen,                       # 绑定我们的聊天函数
    title="通义千问 - Chat",             # 界面标题
    description="基于通义千问 Max 的 AI 聊天机器人。",  # 界面描述
)

# ========== 6. 启动应用 ==========
demo.launch()
