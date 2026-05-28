# A股"不值得买"分析器 — 设计文档

## 概述

输入任意 A 股股票代码，基于多维度的公开数据，生成 10 条详实的"不值得购买"理由。每条理由包含结论、数据支撑和影响解读。通过 CLI 和 Web 两种方式使用，支持一键本地部署。

## 架构

从当前 MVP 的多服务架构（FastAPI + 独立 model 服务 + Postgres + nginx）精简为**单进程架构**，降低部署复杂度：

```
用户输入 000001
    │
    ├── CLI:  python analyze.py 000001
    └── Web:  浏览器 → localhost:8000
                    │
            ┌───────▼────────┐
            │  FastAPI 后端   │  单进程，端口 8000
            │  + 静态文件托管 │
            └───────┬────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌──────────┐
   │ 数据层   │ │ 规则引擎 │ │ AI 适配器 │
   │ 多源降级 │ │ 四维度   │ │ 可选启用  │
   └─────────┘ └─────────┘ └──────────┘
                    │
                    ▼
              ┌──────────┐
              │ SQLite   │  缓存历史查询
              └──────────┘
```

## 技术栈

- **后端**: Python 3.10+ / FastAPI / uvicorn
- **前端**: 静态 HTML + vanilla JS（无框架依赖）
- **数据库**: SQLite（单文件，零配置）
- **数据源**: akshare、tushare、东方财富 API，多源自动降级
- **AI（可选）**: DeepSeek / 通义千问 / 智谱 GLM / Moonshot / Ollama / 自定义 OpenAI 兼容接口
- **部署**: Docker Compose + 纯脚本双方案

## 目录结构

```
Money-Tracing/
├── analyze.py              # CLI 入口
├── app/
│   ├── main.py             # FastAPI 应用 + 静态文件
│   ├── data/               # 数据获取层
│   │   ├── __init__.py
│   │   ├── provider.py         # 抽象基类
│   │   ├── akshare_provider.py
│   │   ├── tushare_provider.py
│   │   ├── eastmoney_provider.py
│   │   └── fallback.py         # 多源降级与优先级
│   ├── engine/              # 规则引擎
│   │   ├── __init__.py
│   │   ├── valuation.py        # 估值维度
│   │   ├── financial.py        # 财务质量维度
│   │   ├── technical.py        # 技术面维度
│   │   ├── risk.py             # 风险事件维度
│   │   └── aggregator.py       # 汇总10条理由
│   ├── ai/                  # AI 可选模块
│   │   ├── __init__.py
│   │   ├── base.py             # 适配器接口
│   │   ├── deepseek.py
│   │   ├── qwen.py
│   │   ├── zhipu.py
│   │   ├── moonshot.py
│   │   ├── ollama.py
│   │   └── custom.py           # OpenAI 兼容接口
│   ├── models.py            # SQLite ORM
│   └── config.py            # 配置加载
├── static/                  # Web 前端
│   ├── index.html
│   ├── style.css
│   └── app.js
├── templates/               # 理由模板库
│   └── reasons_zh.json
├── config.yaml.example      # 配置模板
├── install.sh               # 一键安装
├── start.sh                 # 一键启动
├── requirements.txt
└── README.md
```

## 数据源策略

### 优先级

用户可在 `config.yaml` 中配置数据源优先级。默认：tushare（有 token）> akshare > 东方财富。

```yaml
data:
  provider_order: [tushare, akshare, eastmoney]
  tushare:
    token: ""           # 留空则自动跳过
  cache_ttl: 3600       # 缓存有效期（秒）
```

### 降级逻辑

查询时按 `provider_order` 依次尝试，成功即停止。若全部失败，返回错误提示。

## 四维度分析引擎

每个维度生成 2-3 条理由，总计 10 条。某维度数据缺失时用备选理由补充。

### 估值维度（valuation）
- PE 当前值 / 历史分位数 / 行业对比
- PB 当前值 / 历史分位数 / 行业对比
- PS 估值参考

### 财务质量维度（financial）
- ROE 趋势（近3-5年）
- 资产负债率及行业对比
- 经营现金流（是否持续为负）
- 营收/利润增速趋势

### 技术面维度（technical）
- 均线位置（股价 vs 20/60/200 日均线）
- MACD 周线/日线信号
- RSI 超买超卖

### 风险事件维度（risk）
- 高管增减持记录
- 股权质押比例
- 监管问询/处罚记录
- 近期负面公告

## 理由详实度

每条理由包含三段式结构：

```
🔴 高估值 | 当前 PE 85.3，处于近5年历史 92% 分位

  数据支撑：近5年 PE 中位数为 32.1，当前值高出中位数 166%。
  同行业（银行板块）PE 均值仅 6.8，平安银行显著偏离行业中枢。

  影响解读：高估值意味着市场已充分定价甚至过度乐观，
  一旦业绩不及预期或市场情绪转向，面临较大的估值回归压力。

  数据来源: akshare (2026Q1财报) | 严重程度: 高
```

CLI 用颜色标签（🔴🟡🟢），Web 用对应色卡。

## AI 模块

### 角色
- **润色**：将规则引擎的结构化数据转为自然语言
- **深度分析**：解读财报附注、商业模式风险等定性内容
- 用户可自由开关，不启用时纯规则引擎也能完整工作

### 支持的 Provider

```yaml
ai:
  provider: deepseek       # 默认推荐
  # 可选: deepseek | qwen | zhipu | moonshot | ollama | openai | custom | none

  deepseek:
    api_key: ""
    model: deepseek-chat
    base_url: https://api.deepseek.com/v1

  qwen:
    api_key: ""
    model: qwen-plus
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1

  zhipu:
    api_key: ""
    model: glm-4-flash
    base_url: https://open.bigmodel.cn/api/paas/v4

  moonshot:
    api_key: ""
    model: moonshot-v1-8k
    base_url: https://api.moonshot.cn/v1

  ollama:
    host: http://localhost:11434
    model: qwen2.5:7b

  custom:
    api_key: ""
    base_url: ""
    model: ""
```

优先推荐国产模型（中文金融文本理解更好），Ollama 默认推荐 qwen2.5 系列。

## 部署方案

### install.sh 逻辑

1. 检测 OS（macOS / Windows Git Bash / Linux）
2. 检测 Python 3.10+
3. 检测 Docker → 有则走 Docker，无则走 venv
4. 创建 venv，pip install requirements.txt
5. 从 `config.yaml.example` 拷贝 `config.yaml`，引导用户填写

### start.sh 逻辑

1. Docker 模式 → `docker compose up -d`
2. 本地模式 → 激活 venv，`uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 输出格式

### CLI
```
$ python analyze.py 000001

🔍 平安银行 (000001) — 不值得买的 10 个理由
═══════════════════════════════════════════════

🔴 高估值 | 当前 PE 85.3，处于近5年历史 92% 分位
  数据支撑：...
  影响解读：...
  数据来源: akshare | 严重程度: 高

（共10条）

💡 总结: 高风险 4 条，中等风险 4 条，低风险 2 条。
⏱ 分析耗时: 3.2s | 数据源: akshare | AI: deepseek-chat
```

### Web API
- `POST /analyze` — `{"symbol": "000001"}` → 返回 10 条理由 JSON
- `GET /health` — 健康检查
- `GET /` — 静态前端页面

## 许可证

MIT — 完全本地运行，不上传用户数据。

## 非目标（本期不做）

- 实时行情推送
- 用户账户/登录系统
- 历史数据回测
- 股票对比功能
- 移动端 App
