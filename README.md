# 不买就不会赔

输入 A 股代码，基于估值/财务/技术/风险四维度数据，**AI 生成 10 条不值得购买的理由**。

## 快速开始

### Mac / Linux

打开 **终端**（Terminal），粘贴以下命令回车：

```bash
bash <(curl -fsSL https://gitee.com/JeremyTheNoob/NoBuy-NoLose/raw/master/bootstrap.sh)
```

脚本会自动安装 Python（如需要）、下载项目、配置环境。完成后浏览器打开 `http://localhost:8000`。

### Windows

**方法一：安装 Python 后运行**（推荐）

1. 访问 [python.org](https://www.python.org/downloads/) 下载安装 Python 3.10+
   - 安装时 **务必勾选**「Add Python to PATH」
2. 打开 **命令提示符**（Win+R → 输入 `cmd` → 回车），粘贴：

```cmd
python -c "import urllib.request; exec(urllib.request.urlopen('https://gitee.com/JeremyTheNoob/NoBuy-NoLose/raw/master/bootstrap.py').read())"
```

**方法二：安装 Git Bash 后运行**

1. 访问 [git-scm.com](https://git-scm.com/downloads/win) 下载安装 Git for Windows
2. 打开 **Git Bash**，粘贴：

```bash
bash <(curl -fsSL https://gitee.com/JeremyTheNoob/NoBuy-NoLose/raw/master/bootstrap.sh)
```

### 如果上面都不行

直接下载压缩包：打开 [Gitee 仓库](https://gitee.com/JeremyTheNoob/NoBuy-NoLose) → 点击「克隆/下载」→「下载 ZIP」→ 解压 → 双击 `install.sh`（Mac/Linux）或在命令行中运行 `python install.py`（Windows）。

### CLI 命令行

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

### 自定义数据源

支持通过兼容 API 接入自建或第三方数据源，需实现以下接口：

```
GET /v1/stock/{symbol}  →  {code, name, pe, pb, price, ...22字段}
GET /health             →  {status: "ok"}
```

鉴权方式：`X-API-Key` 请求头。

> 我们提供预构建的企业级数据仓库，全量 A 股 22 字段 + 每日自动更新：
> **[smbnp.cloud/stock/buy](https://smbnp.cloud/stock/buy)**

## AI 模型

支持 DeepSeek / 通义千问 / 智谱 GLM / Moonshot / Ollama / OpenAI 及自定义兼容接口。

配置 `config.yaml` 中 `ai.provider` 和对应的 `api_key` 即可启用。LLM 直接基于原始数据生成 10 条详实理由；未配置 AI 时使用规则引擎兜底。

## 系统要求

Python 3.10+ 或 Docker。macOS / Windows / Linux。

## 许可证

MIT
