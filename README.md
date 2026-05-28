# Money-Tracing MVP

这是一个最小可运行的样板，用于演示云 Postgres -> 本地模型服务 -> 本地后端 -> 前端 展示的数据流。

主要组件：
- `db` : Postgres（用于保存分析结果示例）
- `model` : 模拟模型服务（HTTP /infer）
- `api` : FastAPI 后端，提供 `/predict` 和 `/results`
- `frontend` : 静态页面，通过 `/predict` 发起请求并展示结果

快速启动：

```bash
docker-compose up -d --build
# 等待服务启动，然后初始化 DB（可选）
curl -s http://localhost:8000/health
``` 

前端访问: http://localhost:8080

说明：本示例为最小 demo，JWT 授权尚未集成；模型为占位实现，后续可替换为真实推理容器或 ONNX 服务。
