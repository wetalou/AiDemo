"""
案例2：图像转铅笔画
=================
功能：上传一张图片，自动转换成铅笔画风格后输出。
学习点：
    1. Gradio 的 Image 组件（支持上传图片）
    2. OpenCV 的铅笔素描效果算法（反色 → 高斯模糊 → 颜色减淡）
    3. 在同一行代码中组合多个图像处理步骤
依赖：
    pip install gradio numpy opencv-python pillow
"""

# NumPy：科学计算库，这里用来把图片转成数组做像素运算
import numpy as np
# OpenCV：计算机视觉库，这里用来做高斯模糊等图像处理
import cv2
# Gradio：Web 界面库
import gradio as gr


# ========== 1. 业务逻辑函数 ==========
def image_to_sketch(image):
    """
    接收一张 PIL 图片，返回铅笔画效果的图片。
    算法原理（经典的"反色 + 模糊 + 颜色减淡"三步法）：
        1. 把原图转灰度 → 黑白两色
        2. 灰度图反色     → 黑变白、白变黑
        3. 反色图高斯模糊 → 柔化边缘，让笔触过渡自然
        4. 再反色回来     → 得到"笔画底色"
        5. 原图 ÷ 底色 × 256 → 模拟 Photoshop 的"颜色减淡"混合模式
           线条密集的地方颜色深，稀疏的地方颜色浅 → 就像素描的明暗层次

    参数：
        image (PIL.Image): 上传的图片（Gradio 用 type="pil" 即可自动转成 PIL 格式）
    返回：
        numpy.ndarray: 铅笔画效果的图片（Gradio 能自动识别并显示）
    """
    # ---- 第一步：转灰度 ----
    # image.convert('L') 把彩色图片转成灰度图（只有黑白，没有颜色）
    gray_image = image.convert('L')

    # ---- 第二步：反色 ----
    # 把灰度图转成 NumPy 数组后用 255 去减每个像素值
    # 像素值范围是 0~255，所以 255 - 原值 就相当于"底片效果"
    # （白变黑，黑变白，灰也变相反的灰）
    inverted_image = 255 - np.array(gray_image)

    # ---- 第三步：高斯模糊 ----
    # cv2.GaussianBlur 对反色图做高斯模糊
    # (21, 21) 是模糊核的大小，奇数越大模糊越强
    # 0 是标准差，OpenCV 会自动根据核大小算一个合适的值
    blurred = cv2.GaussianBlur(inverted_image, (21, 21), 0)

    # ---- 第四步：模糊图再反色 ----
    # 让模糊的边缘回到正常的明暗方向，用来做"颜色减淡"的底色层
    inverted_blurred = 255 - blurred

    # ---- 第五步：颜色减淡合成 ----
    # cv2.divide 是逐像素除法
    # 公式：原图 ÷ 底色 × 256，相当于 Photoshop 的"颜色减淡"混合模式
    # scale=256.0 用来控制对比度，数值越大线条感越强
    pencil_sketch = cv2.divide(np.array(gray_image), inverted_blurred, scale=256.0)

    # 返回处理好的铅笔画（NumPy 数组，Gradio 能直接显示）
    return pencil_sketch


# ========== 2. 界面配置 ==========
demo = gr.Interface(
    fn=image_to_sketch,                     # 绑定图片处理函数
    # gr.Image() 是图片组件：支持上传，自动识别是输入还是输出
    inputs=gr.Image(label="上传图片", type="pil"),   # 输入：上传图片，自动转成 PIL 格式传给函数
    outputs=gr.Image(label="铅笔画"),                # 输出：图片
    title="图像转铅笔画",
    description="将上传的图片转为铅笔画风格。",
)

# ========== 3. 启动应用 ==========
demo.launch()
