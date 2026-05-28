# 不买就不会赔

输入任意 A 股股票代码，基于估值、财务、技术、风险四个维度，生成 **10 条详实的"不值得买"理由**。

每条理由包含：**结论** + **数据支撑** + **影响解读**，让你在做投资决策前看到硬币的另一面。

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/JeremyTheNoob/NoBuy-NoLose.git
cd NoBuy-NoLose

# 2. 一键安装
./install.sh

# 3. （推荐）编辑 config.yaml，填入 tushare token 提高数据稳定性

# 4. 一键启动
./start.sh
```

启动后访问 `http://localhost:8000` 使用 Web 界面，或使用命令行：

```bash
python analyze.py 000001
```

## 功能

- **多维度分析**: 估值（PE/PB分位数）、财务（ROE/负债/现金流）、技术面（均线/MACD/RSI）、风险事件（减持/质押/问询）
- **多数据源**: tushare → akshare → 新浪财经 → 东方财富，自动降级
- **本地缓存**: 同一代码在 TTL 内不重复拉取，无网络时用过期缓存兜底
- **AI 增强（可选）**: 支持 DeepSeek、通义千问、智谱 GLM、Moonshot、Ollama 本地模型
- **双界面**: Web 界面 + 命令行工具
- **一键部署**: 自动检测 Docker，无 Docker 则走 venv 本地部署

## 提高数据稳定性（推荐）

免费注册 tushare 可大幅提高数据获取的稳定性：

1. 访问 https://tushare.pro 注册账号
2. 登录后进入"个人主页" → "接口TOKEN" 复制 token
3. 编辑 `config.yaml`：

```yaml
data:
  tushare:
    token: "你的token"
```

## 配置

```yaml
data:
  # 数据源优先级（排前面的优先，留空 token 自动跳过）
  provider_order: [tushare, akshare, sina, eastmoney]
  tushare:
    token: "你的tushare token"
  cache_ttl: 3600       # 缓存有效期（秒）

ai:
  provider: deepseek    # 可选: deepseek/qwen/zhipu/moonshot/ollama/none
  deepseek:
    api_key: "你的API key"
```

## 系统要求

- Python 3.10+（推荐）或 Docker
- macOS / Windows / Linux

## 许可证

MIT
