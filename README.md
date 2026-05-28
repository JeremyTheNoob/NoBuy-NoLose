# 不买就不会赔

输入任意 A 股股票代码，基于估值、财务、技术、风险四个维度，生成 **10 条详实的"不值得买"理由**。

每条理由包含：**结论** + **数据支撑** + **影响解读**，让你在做投资决策前看到硬币的另一面。

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/buymai-jiu-buhui-pei.git
cd buymai-jiu-buhui-pei

# 2. 一键安装
./install.sh

# 3. （可选）编辑 config.yaml，填入 AI API key 启用智能分析

# 4. 一键启动
./start.sh
```

启动后访问 `http://localhost:8000` 使用 Web 界面，或使用命令行：

```bash
python analyze.py 000001
```

## 功能

- **多维度分析**: 估值（PE/PB分位数）、财务（ROE/负债/现金流）、技术面（均线/MACD/RSI）、风险事件（减持/质押/问询）
- **多数据源**: tushare → akshare → 东方财富，自动降级
- **AI 增强（可选）**: 支持 DeepSeek、通义千问、智谱 GLM、Moonshot、Ollama 本地模型
- **双界面**: Web 界面 + 命令行工具
- **一键部署**: 自动检测 Docker，无 Docker 则走 venv 本地部署

## 配置

复制 `config.yaml.example` 为 `config.yaml`:

```yaml
data:
  tushare:
    token: "你的tushare token"   # 可选，不填则自动跳过

ai:
  provider: deepseek              # 可选: deepseek/qwen/zhipu/moonshot/ollama/none
  deepseek:
    api_key: "你的API key"
```

## 系统要求

- Python 3.10+（推荐）或 Docker
- macOS / Windows / Linux

## 许可证

MIT
