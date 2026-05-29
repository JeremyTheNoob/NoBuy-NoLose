# 不买就不会赔

输入 A 股代码，基于估值/财务/技术/风险四维度数据，**AI 生成 10 条不值得购买的理由**。

## 快速开始

```bash
git clone https://github.com/JeremyTheNoob/NoBuy-NoLose.git
cd NoBuy-NoLose
./install.sh
./start.sh
```

浏览器打开 `http://localhost:8000`，输入代码即可。

CLI：
```bash
python analyze.py 000001
```

## 数据源

按 config.yaml 中 `provider_order` 优先级依次尝试，第一个可用即采用：

| 数据源 | 说明 |
|--------|------|
| `custom_api` | 自建数据服务（最稳，22字段全量，需 API Key） |
| `tushare` | tushare.pro 数据（推荐，免费注册获取 token） |
| `akshare` | 免费聚合源（东方财富/同花顺等） |
| `sina` | 新浪财经行情（轻量备选） |
| `eastmoney` | 东方财富直连 |

系统自动降级，无需手动切换。支持本地缓存，同代码 TTL 内秒返。

## AI 模型

支持 DeepSeek / 通义千问 / 智谱 GLM / Moonshot / Ollama / OpenAI 及自定义兼容接口。

配置 `config.yaml` 中 `ai.provider` 和对应的 `api_key` 即可启用。LLM 直接基于原始数据生成 10 条详实理由；未配置 AI 时使用规则引擎兜底。

## 系统要求

Python 3.10+ 或 Docker。macOS / Windows / Linux。

## 许可证

MIT
