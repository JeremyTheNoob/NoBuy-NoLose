#!/usr/bin/env bash
# 不买就不会赔 - 一键安装（纯 bash，无需 Python/Git）
#
# 用法:
#   bash <(curl -fsSL https://gitee.com/JeremyTheNoob/NoBuy-NoLose/raw/master/bootstrap.sh)
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
TARGET="$HOME/NoBuy-NoLose"

echo "========================================"
echo "  不买就不会赔 - 一键安装"
echo "========================================"
echo ""

# --- 平台检测 ---
OS="$(uname -s)"
case "$OS" in
    Darwin)  OS_NAME="macOS" ;;
    Linux)   OS_NAME="Linux" ;;
    MINGW*|MSYS*|CYGWIN*) OS_NAME="Windows" ;;
    *)       OS_NAME="$OS" ;;
esac
echo "系统: $OS_NAME"

# --- Python 检测与安装指引 ---
PY_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0")
        major=$(echo "$ver" | cut -d. -f1)
        if [ "$major" -ge 3 ]; then
            PY_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PY_CMD" ]; then
    echo ""
    echo -e "${YELLOW}未检测到 Python 3，请先安装：${NC}"
    echo ""
    case "$OS" in
        Darwin)
            echo "  macOS:"
            echo "    1. 安装 Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "    2. brew install python@3.12"
            ;;
        Linux)
            echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv -y"
            echo "  CentOS/RHEL:   sudo yum install python3 python3-pip -y"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "  Windows:"
            echo "    访问 https://www.python.org/downloads/ 下载安装包"
            echo "    安装时勾选 'Add Python to PATH'"
            ;;
    esac
    echo ""
    echo "  安装完成后，重新运行本脚本即可。"
    exit 1
fi
echo -e "Python: $("$PY_CMD" --version) ${GREEN}✓${NC}"

# --- 下载项目 ---
if [ -d "$TARGET" ]; then
    echo "目录 $TARGET 已存在，跳过下载"
else
    # 方法1: git clone
    if command -v git &>/dev/null; then
        echo "尝试 Git 下载..."
        CLONED=false
        for url in \
            "https://gitee.com/JeremyTheNoob/NoBuy-NoLose.git" \
            "https://github.com/JeremyTheNoob/NoBuy-NoLose.git"; do
            echo "  尝试 $url ..."
            if git clone --depth 1 "$url" "$TARGET" 2>/dev/null; then
                CLONED=true
                echo -e "  ${GREEN}下载成功 ✓${NC}"
                break
            fi
            echo "  不可用，尝试下一个..."
        done

        if $CLONED; then
            cd "$TARGET"
            if [ -f install.sh ]; then
                bash install.sh
            fi
            echo ""
            echo "========================================"
            echo "  安装完成！"
            echo "  启动: cd ~/NoBuy-NoLose && ./start.sh"
            echo "  浏览器打开 http://localhost:8000"
            echo "========================================"
            exit 0
        fi
    fi

    # 方法2: 直接下载 zip
    echo "Git 不可用，尝试直接下载 zip..."
    for url in \
        "https://gitee.com/JeremyTheNoob/NoBuy-NoLose/repository/archive/master.zip" \
        "https://github.com/JeremyTheNoob/NoBuy-NoLose/archive/refs/heads/master.zip"; do
        echo "  $url ..."
        TMP_ZIP="/tmp/nobl_install_$$.zip"
        if curl -fsSL --connect-timeout 10 -o "$TMP_ZIP" "$url" 2>/dev/null; then
            mkdir -p "$TARGET"
            if command -v unzip &>/dev/null; then
                unzip -qo "$TMP_ZIP" -d /tmp/nobl_extract_$$
                EXTRACTED=$(ls -d /tmp/nobl_extract_$$/*/ 2>/dev/null | head -1)
                if [ -n "$EXTRACTED" ]; then
                    cp -r "$EXTRACTED"* "$TARGET/"
                fi
                rm -rf /tmp/nobl_extract_$$
            elif "$PY_CMD" -c "import zipfile; zipfile.ZipFile('$TMP_ZIP').extractall('/tmp/nobl_extract_$$')" 2>/dev/null; then
                EXTRACTED=$(ls -d /tmp/nobl_extract_$$/*/ 2>/dev/null | head -1)
                if [ -n "$EXTRACTED" ]; then
                    cp -r "$EXTRACTED"* "$TARGET/"
                fi
                rm -rf /tmp/nobl_extract_$$
            fi
            rm -f "$TMP_ZIP"
            if [ -f "$TARGET/install.sh" ]; then
                echo -e "  ${GREEN}下载成功 ✓${NC}"
                cd "$TARGET"
                bash install.sh
                echo ""
                echo "========================================"
                echo "  安装完成！"
                echo "  启动: cd ~/NoBuy-NoLose && ./start.sh"
                echo "  浏览器打开 http://localhost:8000"
                echo "========================================"
                exit 0
            fi
            break
        fi
        echo "  不可用，尝试下一个..."
    done
fi

# 兜底：手动指引
echo ""
echo -e "${YELLOW}自动下载失败。请手动操作：${NC}"
echo "  1. 浏览器打开 https://gitee.com/JeremyTheNoob/NoBuy-NoLose"
echo "  2. 点击「克隆/下载」→「下载 ZIP」"
echo "  3. 解压到 $TARGET"
echo "  4. cd $TARGET && ./install.sh && ./start.sh"
