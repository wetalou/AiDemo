"""
run.py —— Demo 快速选择器
==========================
运行方式：python run.py
功能：列出 demos/ 目录下所有示例，输入编号即可运行对应的 Demo。
     新增 demo 时只要往 demos/ 里放一个 .py 文件，自动出现在菜单中。
"""

import os
import subprocess
import sys

# demos/ 目录路径（相对于本文件所在位置）
DEMOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demos")


def list_demos():
    """扫描 demos/ 目录，返回按文件名排序的 .py 文件列表"""
    demos = []
    if os.path.isdir(DEMOS_DIR):
        # 取所有 .py 文件，排除 __开头 的（比如 __pycache__）
        files = sorted(f for f in os.listdir(DEMOS_DIR) if f.endswith(".py") and not f.startswith("__"))
        demos = [os.path.join(DEMOS_DIR, f) for f in files]
    return demos


def show_menu(demos):
    """打印菜单列表"""
    print("\n" + "=" * 50)
    print("  Gradio Demo 快速选择器")
    print("=" * 50)
    for idx, path in enumerate(demos, 1):
        name = os.path.basename(path)  # 只取文件名
        print(f"  [{idx}] {name}")
    print(f"  [q]  退出")
    print("-" * 50)


def main():
    demos = list_demos()

    if not demos:
        print(f"❌ 在 {DEMOS_DIR} 下没有找到任何 demo 文件！")
        print("   请创建一些 .py 文件，比如 demos/01_text_reverse.py")
        return

    while True:
        show_menu(demos)
        choice = input("请输入编号运行 Demo（q 退出）：").strip().lower()

        if choice == "q":
            print("👋 再见！")
            break

        try:
            idx = int(choice)
            if 1 <= idx <= len(demos):
                target = demos[idx - 1]
                print(f"\n🚀 启动 {os.path.basename(target)} ...\n")
                # 在新进程中运行，这样可以 Ctrl+C 退出后回到菜单
                subprocess.run([sys.executable, target])
            else:
                print(f"⚠️  请输入 1 ~ {len(demos)} 之间的数字")
        except ValueError:
            print("⚠️  无效输入，请输入数字或 q")


if __name__ == "__main__":
    main()
