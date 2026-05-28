#!/usr/bin/env bash
set -euo pipefail

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    echo "使用 Docker 模式启动..."
    docker compose up -d --build
    echo ""
    echo "服务已启动"
    echo "   Web 界面: http://localhost:8000"
    echo "   API 文档: http://localhost:8000/docs"
    echo "   停止服务: docker compose down"
else
    if [ ! -f .venv/bin/activate ]; then
        echo "虚拟环境未找到，请先运行 ./install.sh"
        exit 1
    fi

    echo "使用本地模式启动..."
    . .venv/bin/activate
    echo "启动服务 on http://localhost:8000 ..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
