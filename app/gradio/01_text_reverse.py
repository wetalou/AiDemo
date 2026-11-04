"""
案例1：文本反转器
=================
功能：接收用户输入的一段文字，返回该文字的倒序字符串。
学习点：
    1. Gradio 最简单的 Interface 用法（函数 + 输入类型 + 输出类型）
    2. Python 切片语法 text[::-1] 快速反转字符串
依赖：
    pip install gradio
"""

# 导入 Gradio 库，别名为 gr（社区惯例）
import gradio as gr


# ========== 1. 业务逻辑函数 ==========
# 这是 Gradio 的核心：把任何 Python 函数变成一个 Web 应用
def reverse_text(text):
    """
    接收一段文本，返回倒序后的文本。
    参数：
        text (str): 用户在界面输入框中填写的文字
    返回：
        str: 倒序后的文字
    """
    # Python 切片语法 [start:end:step]
    # [::-1] 表示：从头到尾，步长为 -1，即反向遍历整个字符串
    return text[::-1]


# ========== 2. 界面配置 ==========
# gr.Interface 是 Gradio 提供的"快速搭界面"组件
# 只要给它一个函数，它自动帮你生成输入框和输出框
demo = gr.Interface(
    fn=reverse_text,         # fn = function：把上面的 reverse_text 函数绑定到界面上
    inputs="text",           # inputs：输入组件类型，"text" 就是一个简单的文本框
    outputs="text",          # outputs：输出组件类型，同样是文本框
    title="文本反转器",       # 页面标题（显示在浏览器标签和界面顶部）
    description="输入一段文字，我来帮你倒序输出！",  # 页面描述
)

# ========== 3. 启动应用 ==========
# launch() 会在本地启动一个 Web 服务器（默认 http://127.0.0.1:7860）
# 如果想让局域网其他电脑也能访问，可以加参数 server_name="0.0.0.0"
demo.launch()
