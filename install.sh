#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"
echo "不买就不会赔 一键安装脚本"
echo "检测到系统: $OS"
echo ""

# --- Python check ---
if ! command -v python3 &>/dev/null; then
    echo "未检测到 Python 3。请先安装 Python 3.10+"
    echo "   macOS: brew install python@3.12"
    echo "   Windows: https://www.python.org/downloads/"
    exit 1
fi

PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo "Python 版本过低: $PY_MAJOR.$PY_MINOR，需要 3.10 或以上"
    echo "   macOS: brew install python@3.12"
    echo "   Windows: https://www.python.org/downloads/"
    exit 1
fi
PY_VER="$PY_MAJOR.$PY_MINOR"
echo "Python $PY_VER"

# --- Check Docker ---
USE_DOCKER=false
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    USE_DOCKER=true
    echo "Docker 可用，将使用 Docker 部署"
else
    echo "Docker 未检测到，将使用本地 venv 部署"
fi

# --- Ensure config.yaml ---
if [ ! -f config.yaml ]; then
    cp config.yaml.example config.yaml
    echo ""
    echo "已创建 config.yaml，请编辑填入你的 tushare token 和 AI API key（可选）"
    echo "   配置文件路径: $(pwd)/config.yaml"
fi

# --- 数据源提示 ---
echo ""
echo "============================================"
echo "  数据源选择"
echo "============================================"
echo ""
echo "  1. tushare（免费）"
echo "     → 访问 tushare.pro 注册获取 token，填入 config.yaml"
echo "     → 稳定但需 200 积分/年（免费注册可得）"
echo ""
echo "  2. 数据仓库包（付费 149 元）"
echo "     → 预构建 22 字段全量数据库，本地运行，0 延迟"
echo "     → 含自动更新 + License 绑定本机"
echo "     → 获取方式: <你的网站>"
echo ""
echo "  3. akshare / 新浪（免费备选）"
echo "     → 无需配置，自动使用"
echo "     → 网络不稳定，数据可能不完整"
echo ""
echo "============================================"
echo ""

if $USE_DOCKER; then
    echo ""
    echo "Docker 模式安装完成。启动请运行: ./start.sh"
else
    echo ""
    echo "正在创建 Python 虚拟环境..."
    python3 -m venv .venv
    . .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    mkdir -p data
    echo ""
    echo "本地安装完成。启动请运行: ./start.sh"
fi
