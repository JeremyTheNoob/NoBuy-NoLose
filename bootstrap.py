#!/usr/bin/env python3
"""不买就不会赔 - 一键安装引导脚本

用法（从 Gitee 直接运行）:
    python3 <(curl -fsSL https://gitee.com/<用户>/NoBuy-NoLose/raw/master/bootstrap.py)

或本地运行:
    python3 bootstrap.py
"""

import subprocess, sys, os, tempfile, shutil, urllib.request, platform

# === 仓库地址（按优先级） ===
SOURCES = [
    ("Gitee（国内）", "https://gitee.com/JeremyTheNoob/NoBuy-NoLose.git"),
    ("GitHub", "https://github.com/JeremyTheNoob/NoBuy-NoLose.git"),
]

# === 无 git 时的 zip 下载地址 ===
ZIP_URLS = [
    "https://gitee.com/JeremyTheNoob/NoBuy-NoLose/repository/archive/master.zip",
    "https://github.com/JeremyTheNoob/NoBuy-NoLose/archive/refs/heads/master.zip",
]


def run(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd).returncode == 0


def main():
    print("=" * 55)
    print("  不买就不会赔 - 一键安装")
    print("  输入 A 股代码，AI 生成 10 条不值得购买的理由")
    print("=" * 55)
    print()

    # 检查 Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info < (3, 10):
        print(f"需要 Python 3.10+，当前 {py_ver}")
        sys.exit(1)
    print(f"Python {py_ver} ✓")

    # 选择安装目录
    target = os.path.expanduser("~/NoBuy-NoLose")
    if os.path.exists(target):
        print(f"目录 {target} 已存在，跳过下载")
    else:
        # 方法1: git clone
        has_git = shutil.which("git") is not None
        if has_git:
            cloned = False
            for name, url in SOURCES:
                print(f"尝试从 {name} 下载...")
                if run(f"git clone --depth 1 {url} {target}"):
                    cloned = True
                    print(f"从 {name} 下载成功 ✓")
                    break
                print(f"  {name} 不可用，尝试下一个...")

            if cloned:
                os.chdir(target)
                if os.path.exists("install.sh"):
                    run("bash install.sh")
                print()
                print("安装完成！启动: cd ~/NoBuy-NoLose && ./start.sh")
                return

        # 方法2: 直接下载 zip
        print("Git 不可用，尝试直接下载...")
        for url in ZIP_URLS:
            try:
                print(f"下载 {url}...")
                zip_path = tempfile.mktemp(suffix=".zip")
                urllib.request.urlretrieve(url, zip_path)
                shutil.unpack_archive(zip_path, target)
                os.remove(zip_path)
                print("下载成功 ✓")
                break
            except Exception:
                print("  失败，尝试下一个...")
                continue

    if not os.path.exists(target):
        print("\n无法自动下载。请手动操作：")
        print("  1. 打开 https://gitee.com/JeremyTheNoob/NoBuy-NoLose")
        print('  2. 点击"克隆/下载" → "下载 ZIP"')
        print(f"  3. 解压到 {target}")
        print(f"  4. cd {target} && ./install.sh")
        sys.exit(1)

    os.chdir(target)
    if os.path.exists("install.sh"):
        run("bash install.sh")

    print()
    print("=" * 55)
    print("  安装完成！")
    print(f"  cd {target} && ./start.sh")
    print("  浏览器打开 http://localhost:8000")
    print("=" * 55)


if __name__ == "__main__":
    main()
