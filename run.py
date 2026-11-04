"""
run.py —— Demo 快速选择器
==========================
运行方式：python run.py
功能：扫描 app/gradio、app/models、app/agents 顶层示例，输入编号即可运行。
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT, "app")

# 主题目录（相对 app/，顺序即菜单分组顺序）
TOPIC_DIRS = ("gradio", "models", "agents")


def list_demos():
    """扫描各主题目录顶层 .py（排除 __init__.py）。"""
    demos = []
    for topic in TOPIC_DIRS:
        topic_path = os.path.join(APP_DIR, topic)
        if not os.path.isdir(topic_path):
            continue
        files = sorted(
            f
            for f in os.listdir(topic_path)
            if f.endswith(".py") and not f.startswith("__")
        )
        for name in files:
            demos.append({
                "label": f"app/{topic}/{name}",
                "path": os.path.join(topic_path, name),
            })
    return demos


def show_menu(demos):
    print("\n" + "=" * 50)
    print("  AiDemo 快速选择器")
    print("=" * 50)
    for idx, item in enumerate(demos, 1):
        print(f"  [{idx}] {item['label']}")
    print("  [q]  退出")
    print("-" * 50)


def main():
    demos = list_demos()

    if not demos:
        print("❌ 未找到任何示例脚本！")
        print("   请确认存在 app/gradio、app/models、app/agents 目录。")
        return

    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = ROOT if not existing else ROOT + os.pathsep + existing

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
                print(f"\n🚀 启动 {target['label']} ...\n")
                subprocess.run([sys.executable, target["path"]], env=env, cwd=ROOT)
            else:
                print(f"⚠️  请输入 1 ~ {len(demos)} 之间的数字")
        except ValueError:
            print("⚠️  无效输入，请输入数字或 q")


if __name__ == "__main__":
    main()
