# A股"不值得买"分析器 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 输入任意 A 股股票代码，基于估值/财务/技术/风险四维度公开数据，生成 10 条详实的"不值得购买"理由。

**Architecture:** 单进程 FastAPI 应用，内嵌静态文件服务。数据层多源自动降级（tushare → akshare → 东方财富），规则引擎四维度独立计算后由聚合器汇总 10 条理由。AI 模块可选，支持 DeepSeek/通义千问/智谱/Ollama 等国内模型。

**Tech Stack:** Python 3.10+ / FastAPI / SQLite / akshare / tushare / vanilla JS 前端

---

### Task 1: 清理旧文件，建立新目录结构

**Files:**
- Remove: `backend/`, `model/`, `frontend/`, `scripts/`, `install_local.sh`, `start_local.sh`, `基础数据/`, `网站/`
- Create: `app/__init__.py`, `app/data/__init__.py`, `app/engine/__init__.py`, `app/ai/__init__.py`, `static/`, `templates/`

- [ ] **Step 1: 删除旧 MVP 代码目录和文件**

```bash
rm -rf backend model frontend scripts "基础数据" "网站"
rm -f install_local.sh start_local.sh api.log model.log frontend.log
```

- [ ] **Step 2: 创建新目录结构**

```bash
mkdir -p app/data app/engine app/ai static templates
touch app/__init__.py app/data/__init__.py app/engine/__init__.py app/ai/__init__.py
```

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "chore: clean old MVP structure, scaffold new app layout"
```

---

### Task 2: 依赖声明 requirements.txt

**Files:**
- Create: `requirements.txt`
- Modify: `model/requirements.txt` → 已删除，无需处理
- Modify: `backend/requirements.txt` → 已删除，无需处理

- [ ] **Step 1: 编写 requirements.txt**

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pyyaml>=6.0
akshare>=1.12.0
tushare>=1.4.0
pandas>=2.0.0
numpy>=1.24.0
ta>=0.11.0
httpx>=0.27.0
openai>=1.0.0
```

- [ ] **Step 2: 提交**

```bash
git add requirements.txt
git commit -m "chore: add project dependencies"
```

---

### Task 3: 配置管理

**Files:**
- Create: `config.yaml.example`
- Create: `app/config.py`

- [ ] **Step 1: 编写配置模板 `config.yaml.example`**

```yaml
# Money-Tracing 配置文件
# 复制为 config.yaml 并填入你的配置

data:
  # 数据源优先级，排前面的优先
  provider_order:
    - tushare
    - akshare
    - eastmoney
  tushare:
    token: ""           # tushare.pro 的 API token，留空自动跳过
  cache_ttl: 3600       # 数据缓存有效期（秒）

ai:
  # provider: deepseek | qwen | zhipu | moonshot | ollama | openai | custom | none
  provider: deepseek

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

  openai:
    api_key: ""
    model: gpt-4o
    base_url: https://api.openai.com/v1

  custom:
    api_key: ""
    base_url: ""
    model: ""

server:
  host: "0.0.0.0"
  port: 8000
```

- [ ] **Step 2: 编写配置加载器 `app/config.py`**

```python
import os
import yaml
from pathlib import Path
from pydantic import BaseModel


class TushareConfig(BaseModel):
    token: str = ""

class DataConfig(BaseModel):
    provider_order: list[str] = ["tushare", "akshare", "eastmoney"]
    tushare: TushareConfig = TushareConfig()
    cache_ttl: int = 3600

class ProviderConfig(BaseModel):
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    host: str = "http://localhost:11434"

class AIConfig(BaseModel):
    provider: str = "none"
    deepseek: ProviderConfig = ProviderConfig(model="deepseek-chat", base_url="https://api.deepseek.com/v1")
    qwen: ProviderConfig = ProviderConfig(model="qwen-plus", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    zhipu: ProviderConfig = ProviderConfig(model="glm-4-flash", base_url="https://open.bigmodel.cn/api/paas/v4")
    moonshot: ProviderConfig = ProviderConfig(model="moonshot-v1-8k", base_url="https://api.moonshot.cn/v1")
    ollama: ProviderConfig = ProviderConfig(model="qwen2.5:7b")
    openai: ProviderConfig = ProviderConfig(model="gpt-4o", base_url="https://api.openai.com/v1")
    custom: ProviderConfig = ProviderConfig()

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000

class AppConfig(BaseModel):
    data: DataConfig = DataConfig()
    ai: AIConfig = AIConfig()
    server: ServerConfig = ServerConfig()


def load_config(config_path: str | None = None) -> AppConfig:
    if config_path is None:
        config_path = os.environ.get("MT_CONFIG", "config.yaml")

    if not Path(config_path).exists():
        return AppConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return AppConfig(**raw)
```

- [ ] **Step 3: 提交**

```bash
git add config.yaml.example app/config.py
git commit -m "feat: add configuration management with YAML support"
```

---

### Task 4: 数据库模型

**Files:**
- Create: `app/models.py`

- [ ] **Step 1: 编写 SQLite 模型 `app/models.py`**

```python
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(String(36), primary_key=True)
    symbol = Column(String(10), index=True, nullable=False)
    stock_name = Column(String(50))
    provider = Column(String(20))
    ai_provider = Column(String(20))
    reasons_json = Column(Text, nullable=False)
    summary = Column(Text)
    elapsed_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db(db_path: str = "data/money_tracing.db"):
    import os
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def get_session(db_path: str = "data/money_tracing.db"):
    Session = init_db(db_path)
    return Session()
```

- [ ] **Step 2: 提交**

```bash
git add app/models.py
git commit -m "feat: add SQLite models for analysis record caching"
```

---

### Task 5: 数据提供者抽象接口

**Files:**
- Create: `app/data/provider.py`

- [ ] **Step 1: 编写抽象基类和数据结构 `app/data/provider.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class StockInfo:
    symbol: str
    name: str = ""
    industry: str = ""

@dataclass
class ValuationData:
    pe: float | None = None
    pe_percentile_5y: float | None = None      # 近5年 PE 分位数 (0-100)
    pe_industry_avg: float | None = None
    pb: float | None = None
    pb_percentile_5y: float | None = None
    pb_industry_avg: float | None = None
    ps: float | None = None

@dataclass
class FinancialData:
    roe_trend: list[float] = field(default_factory=list)       # 近3-5年 ROE
    debt_ratio: float | None = None
    debt_ratio_industry: float | None = None
    operating_cf_trend: list[float] = field(default_factory=list)
    revenue_growth_trend: list[float] = field(default_factory=list)
    profit_growth_trend: list[float] = field(default_factory=list)

@dataclass
class TechnicalData:
    price: float | None = None
    ma_20: float | None = None
    ma_60: float | None = None
    ma_200: float | None = None
    macd_dif: float | None = None
    macd_dea: float | None = None
    macd_histogram: float | None = None
    rsi_14: float | None = None

@dataclass
class RiskData:
    insider_sells_3m: list[dict] = field(default_factory=list)    # [{name, position, amount, date}]
    insider_buys_3m: list[dict] = field(default_factory=list)
    pledge_ratio: float | None = None                              # 股权质押比例 %
    regulatory_inquiries_12m: int = 0                              # 近12月问询次数
    negative_announcements: list[str] = field(default_factory=list)

@dataclass
class StockData:
    info: StockInfo = field(default_factory=StockInfo)
    valuation: ValuationData = field(default_factory=ValuationData)
    financial: FinancialData = field(default_factory=FinancialData)
    technical: TechnicalData = field(default_factory=TechnicalData)
    risk: RiskData = field(default_factory=RiskData)


class DataProvider(ABC):
    """数据提供者抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """检查该数据源是否可用（如 token 是否配置）"""
        ...

    @abstractmethod
    def fetch_stock_info(self, symbol: str) -> StockInfo:
        ...

    @abstractmethod
    def fetch_valuation(self, symbol: str) -> ValuationData:
        ...

    @abstractmethod
    def fetch_financial(self, symbol: str) -> FinancialData:
        ...

    @abstractmethod
    def fetch_technical(self, symbol: str) -> TechnicalData:
        ...

    @abstractmethod
    def fetch_risk(self, symbol: str) -> RiskData:
        ...

    def fetch_all(self, symbol: str) -> StockData:
        return StockData(
            info=self.fetch_stock_info(symbol),
            valuation=self.fetch_valuation(symbol),
            financial=self.fetch_financial(symbol),
            technical=self.fetch_technical(symbol),
            risk=self.fetch_risk(symbol),
        )
```

- [ ] **Step 2: 提交**

```bash
git add app/data/provider.py
git commit -m "feat: define data provider abstract interface and data models"
```

---

### Task 6: akshare 数据提供者

**Files:**
- Create: `app/data/akshare_provider.py`

- [ ] **Step 1: 实现 akshare 提供者 `app/data/akshare_provider.py`**

```python
import pandas as pd
import akshare as ak
from .provider import DataProvider, StockInfo, ValuationData, FinancialData, TechnicalData, RiskData


class AkshareProvider(DataProvider):
    name = "akshare"

    def is_available(self) -> bool:
        return True  # akshare 无需配置即可用

    def fetch_stock_info(self, symbol: str) -> StockInfo:
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            info = StockInfo(symbol=symbol)
            for _, row in df.iterrows():
                if row["item"] == "股票简称":
                    info.name = str(row["value"])
                elif row["item"] == "行业":
                    info.industry = str(row["value"])
            return info
        except Exception:
            return StockInfo(symbol=symbol)

    def fetch_valuation(self, symbol: str) -> ValuationData:
        try:
            df = ak.stock_a_lg_indicator(symbol=symbol)
            if df.empty:
                return ValuationData()
            latest = df.iloc[-1]
            pe_col = [c for c in df.columns if "市盈率" in c and "PE" in c.upper()]
            pb_col = [c for c in df.columns if "市净率" in c and "PB" in c.upper()]
            return ValuationData(
                pe=float(latest[pe_col[0]]) if pe_col and pd.notna(latest[pe_col[0]]) else None,
                pb=float(latest[pb_col[0]]) if pb_col and pd.notna(latest[pb_col[0]]) else None,
            )
        except Exception:
            return ValuationData()

    def fetch_financial(self, symbol: str) -> FinancialData:
        try:
            df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按年度")
            if df.empty:
                return FinancialData()
            # 取最近5年
            recent = df.head(5)
            roe_trend = []
            for _, row in recent.iterrows():
                for col in ["净资产收益率", "ROE", "加权净资产收益率"]:
                    if col in df.columns and pd.notna(row.get(col)):
                        roe_trend.append(float(row[col]))
                        break
            debt_col = next((c for c in ["资产负债率", "负债合计/资产总计"] if c in df.columns), None)
            debt = float(recent.iloc[0][debt_col]) if debt_col and pd.notna(recent.iloc[0][debt_col]) else None
            return FinancialData(roe_trend=roe_trend, debt_ratio=debt)
        except Exception:
            return FinancialData()

    def fetch_technical(self, symbol: str) -> TechnicalData:
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if df.empty or len(df) < 200:
                return TechnicalData()
            close = df["收盘"].astype(float)
            latest_price = float(close.iloc[-1])
            ma_20 = float(close.tail(20).mean())
            ma_60 = float(close.tail(60).mean()) if len(close) >= 60 else None
            ma_200 = float(close.tail(200).mean()) if len(close) >= 200 else None
            # RSI-14
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
            rs = gain / loss
            rsi = float(100 - (100 / (1 + rs.iloc[-1]))) if loss.iloc[-1] != 0 else 50.0
            # MACD
            ema_12 = close.ewm(span=12).mean()
            ema_26 = close.ewm(span=26).mean()
            dif = ema_12 - ema_26
            dea = dif.ewm(span=9).mean()
            macd_hist = 2 * (dif - dea)
            return TechnicalData(
                price=latest_price, ma_20=ma_20, ma_60=ma_60, ma_200=ma_200,
                macd_dif=float(dif.iloc[-1]), macd_dea=float(dea.iloc[-1]),
                macd_histogram=float(macd_hist.iloc[-1]), rsi_14=rsi,
            )
        except Exception:
            return TechnicalData()

    def fetch_risk(self, symbol: str) -> RiskData:
        try:
            pledge_df = ak.stock_gpzy_pledge_ratio_em()
            pledge_ratio = None
            if not pledge_df.empty:
                col = next((c for c in pledge_df.columns if "比例" in c or "ratio" in c.lower()), pledge_df.columns[-1])
                pledge_ratio = float(pledge_df.iloc[0][col]) if pd.notna(pledge_df.iloc[0][col]) else None
            return RiskData(pledge_ratio=pledge_ratio)
        except Exception:
            return RiskData()
```

- [ ] **Step 2: 提交**

```bash
git add app/data/akshare_provider.py
git commit -m "feat: implement akshare data provider"
```

---

### Task 7: tushare 数据提供者

**Files:**
- Create: `app/data/tushare_provider.py`

- [ ] **Step 1: 实现 tushare 提供者 `app/data/tushare_provider.py`**

```python
import pandas as pd
import tushare as ts
from .provider import DataProvider, StockInfo, ValuationData, FinancialData, TechnicalData, RiskData


class TushareProvider(DataProvider):
    name = "tushare"

    def __init__(self, token: str):
        self.token = token
        self._pro = None

    def is_available(self) -> bool:
        return bool(self.token)

    @property
    def pro(self):
        if self._pro is None and self.token:
            ts.set_token(self.token)
            self._pro = ts.pro_api()
        return self._pro

    def _ts_code(self, symbol: str) -> str:
        """将纯数字代码转换为 tushare 格式"""
        if "." in symbol:
            return symbol
        if symbol.startswith("6"):
            return f"{symbol}.SH"
        return f"{symbol}.SZ"

    def fetch_stock_info(self, symbol: str) -> StockInfo:
        if not self.pro:
            return StockInfo(symbol=symbol)
        try:
            df = self.pro.stock_basic(ts_code=self._ts_code(symbol), fields="name,industry")
            if not df.empty:
                row = df.iloc[0]
                return StockInfo(symbol=symbol, name=row["name"], industry=row.get("industry", ""))
        except Exception:
            pass
        return StockInfo(symbol=symbol)

    def fetch_valuation(self, symbol: str) -> ValuationData:
        if not self.pro:
            return ValuationData()
        try:
            df = self.pro.daily_basic(ts_code=self._ts_code(symbol), fields="pe,pb,pe_ttm,pb")
            if df.empty:
                return ValuationData()
            latest = df.iloc[-1]
            return ValuationData(
                pe=float(latest["pe_ttm"]) if pd.notna(latest.get("pe_ttm")) else None,
                pb=float(latest["pb"]) if pd.notna(latest.get("pb")) else None,
            )
        except Exception:
            return ValuationData()

    def fetch_financial(self, symbol: str) -> FinancialData:
        if not self.pro:
            return FinancialData()
        try:
            df = self.pro.fina_indicator(ts_code=self._ts_code(symbol), fields="roe,debt_to_assets")
            if df.empty:
                return FinancialData()
            recent = df.head(5)
            roe_trend = [float(r["roe"]) for _, r in recent.iterrows() if pd.notna(r["roe"])]
            debt = float(recent.iloc[0]["debt_to_assets"]) if pd.notna(recent.iloc[0].get("debt_to_assets")) else None
            return FinancialData(roe_trend=roe_trend, debt_ratio=debt)
        except Exception:
            return FinancialData()

    def fetch_technical(self, symbol: str) -> TechnicalData:
        # tushare 不直接提供技术指标，返回空数据
        return TechnicalData()

    def fetch_risk(self, symbol: str) -> RiskData:
        if not self.pro:
            return RiskData()
        try:
            df = self.pro.pledge_stat(ts_code=self._ts_code(symbol))
            pledge_ratio = float(df.iloc[0]["pledge_ratio"]) if not df.empty and pd.notna(df.iloc[0].get("pledge_ratio")) else None
            return RiskData(pledge_ratio=pledge_ratio)
        except Exception:
            return RiskData()
```

- [ ] **Step 2: 提交**

```bash
git add app/data/tushare_provider.py
git commit -m "feat: implement tushare data provider"
```

---

### Task 8: 东方财富数据提供者 + 降级编排

**Files:**
- Create: `app/data/eastmoney_provider.py`
- Create: `app/data/fallback.py`

- [ ] **Step 1: 编写东方财富提供者 `app/data/eastmoney_provider.py`**

```python
import httpx
from .provider import DataProvider, StockInfo, ValuationData, FinancialData, TechnicalData, RiskData


class EastmoneyProvider(DataProvider):
    name = "eastmoney"

    def is_available(self) -> bool:
        return True

    def _market_code(self, symbol: str) -> str:
        if symbol.startswith("6"):
            return f"1.{symbol}"
        return f"0.{symbol}"

    def fetch_stock_info(self, symbol: str) -> StockInfo:
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {"secid": self._market_code(symbol), "fields": "f57,f58,f100"}
            resp = httpx.get(url, params=params, timeout=10)
            data = resp.json().get("data", {})
            return StockInfo(symbol=symbol, name=data.get("f58", ""), industry=data.get("f100", ""))
        except Exception:
            return StockInfo(symbol=symbol)

    def fetch_valuation(self, symbol: str) -> ValuationData:
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {"secid": self._market_code(symbol), "fields": "f9,f23,f162,f167"}
            resp = httpx.get(url, params=params, timeout=10)
            data = resp.json().get("data", {})
            return ValuationData(
                pe=data.get("f9"),       # PE-TTM
                pb=data.get("f23"),       # PB
            )
        except Exception:
            return ValuationData()

    def fetch_financial(self, symbol: str) -> FinancialData:
        return FinancialData()  # 东方财富 API 不直接暴露财报摘要

    def fetch_technical(self, symbol: str) -> TechnicalData:
        return TechnicalData()  # 历史行情需要单独的 kline API，这里让 akshare 承担

    def fetch_risk(self, symbol: str) -> RiskData:
        return RiskData()
```

- [ ] **Step 2: 编写降级编排 `app/data/fallback.py`**

```python
from .provider import DataProvider, StockData, StockInfo
from .akshare_provider import AkshareProvider
from .tushare_provider import TushareProvider
from .eastmoney_provider import EastmoneyProvider
from ..config import AppConfig


def _build_providers(config: AppConfig) -> list[DataProvider]:
    providers: list[DataProvider] = []
    for name in config.data.provider_order:
        if name == "tushare" and config.data.tushare.token:
            providers.append(TushareProvider(token=config.data.tushare.token))
        elif name == "akshare":
            providers.append(AkshareProvider())
        elif name == "eastmoney":
            providers.append(EastmoneyProvider())
    if not providers:
        providers.append(AkshareProvider())
    return providers


def fetch_stock_data(symbol: str, config: AppConfig) -> tuple[StockData, str]:
    """
    按配置的优先级依次尝试数据源。
    返回 (StockData, 实际使用的 provider_name)。
    若全部失败则抛出 RuntimeError。
    """
    providers = _build_providers(config)
    last_error = None

    for p in providers:
        if not p.is_available():
            continue
        try:
            data = p.fetch_all(symbol)
            if data.info.name or data.valuation.pe is not None:
                return data, p.name
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise RuntimeError(f"所有数据源均获取失败，最后错误: {last_error}")
    raise RuntimeError("没有可用的数据源，请在 config.yaml 中配置 tushare token 或检查网络连接")
```

- [ ] **Step 3: 提交**

```bash
git add app/data/eastmoney_provider.py app/data/fallback.py
git commit -m "feat: add eastmoney provider and multi-source fallback orchestration"
```

---

### Task 9: 理由模板

**Files:**
- Create: `templates/reasons_zh.json`

- [ ] **Step 1: 编写理由模板 `templates/reasons_zh.json`**

```json
{
  "valuation": {
    "pe_high_percentile": {
      "severity": "high",
      "conclusion": "当前 PE {pe:.1f}，处于近5年历史 {percentile:.0f}% 分位",
      "data_support": "近5年 PE 中位数为 {pe_median:.1f}，当前值高出中位数 {premium:.0f}%。同行业（{industry}）PE 均值仅 {pe_industry:.1f}，{name} 已显著偏离行业中枢。",
      "impact": "高估值意味着市场已充分定价甚至过度乐观。一旦业绩不及预期或市场情绪转向，面临较大的估值回归压力。"
    },
    "pb_high": {
      "severity": "medium",
      "conclusion": "当前 PB {pb:.1f}，高于行业均值 {pb_industry:.1f}",
      "data_support": "同行业（{industry}）PB 均值 {pb_industry:.1f}，{name} 溢价 {pb_premium:.0f}%。",
      "impact": "市净率偏高暗示市场对公司资产质量给予了较高预期，若 ROE 不能匹配该溢价，股价存在回调风险。"
    }
  },
  "financial": {
    "roe_declining": {
      "severity": "high",
      "conclusion": "ROE 连续 {years} 年下滑，从 {roe_first:.1f}% 降至 {roe_last:.1f}%",
      "data_support": "近 {years} 年 ROE 变化: {roe_sequence}。累计下滑幅度 {roe_decline:.1f} 个百分点。",
      "impact": "ROE 持续下滑表明公司盈利能力在恶化。资本回报率的下降往往先于股价下跌，是基本面向弱的重要先行指标。"
    },
    "debt_high": {
      "severity": "medium",
      "conclusion": "资产负债率 {debt:.1f}%，显著高于行业均值 {debt_industry:.1f}%",
      "data_support": "行业平均资产负债率 {debt_industry:.1f}%，{name} 高出 {debt_gap:.1f} 个百分点。",
      "impact": "高杠杆意味着更高的财务风险和利息负担。在经济下行或利率上升周期中，高负债企业面临更大的经营压力。"
    },
    "cashflow_negative": {
      "severity": "high",
      "conclusion": "经营现金流连续 {cf_negative_years} 年为负",
      "data_support": "近 {cf_negative_years} 年经营现金流分别为: {cf_sequence}。",
      "impact": "经营现金流持续为负说明公司主营业务不产生真正的现金流入，利润可能依赖应收款项或投资收��支撑，盈利质量堪忧。"
    },
    "revenue_declining": {
      "severity": "medium",
      "conclusion": "营收增速连续放缓，近 {years} 年复合增长率仅 {cagr:.1f}%",
      "data_support": "近 {years} 年营收增速分别为: {revenue_sequence}。",
      "impact": "营收增长乏力可能反映市场空间见顶或竞争力下降。在成本刚性的情况下，营收放缓将直接拖累利润。"
    }
  },
  "technical": {
    "below_ma200": {
      "severity": "high",
      "conclusion": "股价 {price:.2f} 跌破 200 日均线 {ma200:.2f}，中期趋势偏弱",
      "data_support": "当前股价处于 200 日均线下方 {below_pct:.1f}%，属于技术性熊市区域。",
      "impact": "200 日均线被视为牛熊分界线。股价持续运行在 200 日线下方向往预示着中长期资金正在流出，趋势逆转需要时间。"
    },
    "below_ma60": {
      "severity": "medium",
      "conclusion": "股价 {price:.2f} 低于 60 日均线 {ma60:.2f}，短期动能不足",
      "data_support": "当前股价低于 60 日均线 {below_pct:.1f}%。",
      "impact": "60 日均线反映季度级别的持仓成本。股价持续低于此线表明大多数近期买入者处于亏损状态，反弹时将面临解套抛压。"
    },
    "macd_death_cross": {
      "severity": "medium",
      "conclusion": "MACD 周线 DIF 下穿 DEA，动能转弱",
      "data_support": "当前 DIF {dif:.3f}，DEA {dea:.3f}，柱状图 {hist:.3f}。",
      "impact": "MACD 死叉是趋势交易中常用的卖出信号。虽然并非每次死叉都会下跌，但结合当前基本面状况，技术面的走弱增加了短期风险。"
    },
    "rsi_overbought": {
      "severity": "low",
      "conclusion": "RSI(14) 为 {rsi:.1f}，接近超买区间",
      "data_support": "RSI 高于 70 通常被视为超买信号，当前值为 {rsi:.1f}。",
      "impact": "RSI 超买提示短期可能存在回调需求。虽然强势股可以维持超买状态较长时间，但追高买入的风险收益比不佳。"
    }
  },
  "risk": {
    "insider_selling": {
      "severity": "high",
      "conclusion": "近3月高管累计减持 {amount:.1f} 万元，存在内部人卖出压力",
      "data_support": "近期减持记录: {insider_details}。",
      "impact": "高管作为最了解公司经营状况的人，其减持行为值得重视。大规模的��部人卖出可能暗示他们对短期前景的担忧。"
    },
    "pledge_high": {
      "severity": "high",
      "conclusion": "股权质押比例达 {pledge:.1f}%，远高于 30% 的警戒线",
      "data_support": "当前质押比例 {pledge:.1f}%，大股东质押融资在股价大幅下跌时可能触发强制平仓。",
      "impact": "高质押比例是潜在的黑天鹅风险源。一旦股价跌破平仓线，大股东若无法补仓或还款，将面临被动减持，进一步打压股价形成负反馈。"
    },
    "regulatory_inquiry": {
      "severity": "medium",
      "conclusion": "近12个月收到 {inquiry_count} 次交易所问询函，合规风险值得关注",
      "data_support": "交易所问询通常涉及财务数据异常、关联交易、信息披露等问题。频繁收函往往意味着公司治理或财务披露存在问题。",
      "impact": "监管关注增加公司未来面临处罚或在融资、重组等事项上受阻的风险，对股价构成潜在利空。"
    },
    "no_insider_buying": {
      "severity": "low",
      "conclusion": "近 3 月无高管增持记录，内部人缺乏信心信号",
      "data_support": "在近期股价区间内，无任何高管或大股东主动增持行为。",
      "impact": "如果连最了解公司的人都���愿意在当前价位买入，普通投资者更应该三思。"
    }
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add templates/reasons_zh.json
git commit -m "feat: add Chinese reason templates with three-part structure"
```

---

### Task 10: 估值引擎

**Files:**
- Create: `app/engine/valuation.py`

- [ ] **Step 1: 实现估值分析引擎 `app/engine/valuation.py`**

```python
import json
from pathlib import Path
from ..data.provider import ValuationData, StockInfo


_TEMPLATES = None

def _load_templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        tmpl_path = Path(__file__).parent.parent.parent / "templates" / "reasons_zh.json"
        with open(tmpl_path, "r", encoding="utf-8") as f:
            _TEMPLATES = json.load(f)
    return _TEMPLATES


def analyze(valuation: ValuationData, info: StockInfo) -> list[dict]:
    """
    基于估值数据生成 2-3 条理由。
    返回格式: [{"conclusion": str, "data_support": str, "impact": str, "severity": str, "dimension": "估值"}]
    """
    templates = _load_templates()["valuation"]
    reasons = []

    # PE 高估
    if valuation.pe is not None and valuation.pe_percentile_5y is not None:
        if valuation.pe_percentile_5y >= 80:
            t = templates["pe_high_percentile"]
            pe_median_est = valuation.pe / (1 + (valuation.pe_percentile_5y - 50) / 100)
            reasons.append({
                "conclusion": t["conclusion"].format(
                    pe=valuation.pe, percentile=valuation.pe_percentile_5y),
                "data_support": t["data_support"].format(
                    pe=valuation.pe, percentile=valuation.pe_percentile_5y,
                    pe_median=pe_median_est,
                    premium=((valuation.pe / pe_median_est - 1) * 100) if pe_median_est else 0,
                    pe_industry=valuation.pe_industry_avg or "暂无",
                    industry=info.industry or "全市场",
                    name=info.name or valuation.pe),
                "impact": t["impact"],
                "severity": t["severity"],
                "dimension": "估值",
            })
    elif valuation.pe is not None and valuation.pe > 50:
        reasons.append({
            "conclusion": f"当前 PE {valuation.pe:.1f}，绝对估值水平较高",
            "data_support": f"一般而言 PE 超过 50 意味着市场给予了很高的成长预期。同行业（{info.industry or '全市场'}）参考 PE 为 {valuation.pe_industry_avg or '暂无数据'}。",
            "impact": "高 PE 需要未来业绩高速增长来消化，一旦增速不达预期，估值和盈利双杀的风险不容忽视。",
            "severity": "medium",
            "dimension": "估值",
        })

    # PB 高估
    if valuation.pb is not None and valuation.pb_industry_avg is not None:
        if valuation.pb > valuation.pb_industry_avg * 1.3:
            t = templates["pb_high"]
            reasons.append({
                "conclusion": t["conclusion"].format(pb=valuation.pb, pb_industry=valuation.pb_industry_avg),
                "data_support": t["data_support"].format(
                    pb=valuation.pb, pb_industry=valuation.pb_industry_avg,
                    name=info.name or "该股票", industry=info.industry or "全市场",
                    pb_premium=((valuation.pb / valuation.pb_industry_avg - 1) * 100)),
                "impact": t["impact"],
                "severity": t["severity"],
                "dimension": "估值",
            })

    # 如果还不够2条，补充一条估值的通用提醒
    if len(reasons) < 2 and valuation.pe is not None:
        reasons.append({
            "conclusion": f"当前 PE {valuation.pe:.1f}，在同行业中不具估值优势",
            "data_support": f"行业均值 PE 约 {valuation.pe_industry_avg or '暂无'}。考虑到 A 股市场整体估值水平，该股票的性价比有待商榷。",
            "impact": "投资的核心是买得便宜。在估值缺乏安全边际的情况下，任何负面消息都可能引发较大幅度的回调。",
            "severity": "low",
            "dimension": "估值",
        })

    return reasons
```

- [ ] **Step 2: 提交**

```bash
git add app/engine/valuation.py
git commit -m "feat: implement valuation analysis engine"
```

---

### Task 11: 财务质量引擎

**Files:**
- Create: `app/engine/financial.py`

- [ ] **Step 1: 实现财务分析引擎 `app/engine/financial.py`**

```python
import json
from pathlib import Path
from ..data.provider import FinancialData, StockInfo


_TEMPLATES = None

def _load_templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        tmpl_path = Path(__file__).parent.parent.parent / "templates" / "reasons_zh.json"
        with open(tmpl_path, "r", encoding="utf-8") as f:
            _TEMPLATES = json.load(f)
    return _TEMPLATES


def analyze(financial: FinancialData, info: StockInfo) -> list[dict]:
    templates = _load_templates()["financial"]
    reasons = []

    # ROE 下滑
    if len(financial.roe_trend) >= 3:
        roe_first = financial.roe_trend[0]
        roe_last = financial.roe_trend[-1]
        if roe_first > roe_last * 1.1 and roe_last < roe_first:
            t = templates["roe_declining"]
            roe_seq = " → ".join(f"{v:.1f}%" for v in financial.roe_trend)
            reasons.append({
                "conclusion": t["conclusion"].format(
                    years=len(financial.roe_trend), roe_first=roe_first, roe_last=roe_last),
                "data_support": t["data_support"].format(
                    years=len(financial.roe_trend), roe_sequence=roe_seq,
                    roe_decline=roe_first - roe_last),
                "impact": t["impact"],
                "severity": t["severity"],
                "dimension": "财务质量",
            })

    # 资产负债率过高
    if financial.debt_ratio is not None and financial.debt_ratio_industry is not None:
        if financial.debt_ratio > financial.debt_ratio_industry * 1.2:
            t = templates["debt_high"]
            reasons.append({
                "conclusion": t["conclusion"].format(
                    debt=financial.debt_ratio, debt_industry=financial.debt_ratio_industry),
                "data_support": t["data_support"].format(
                    name=info.name or "该股票",
                    debt=financial.debt_ratio, debt_industry=financial.debt_ratio_industry,
                    debt_gap=financial.debt_ratio - financial.debt_ratio_industry),
                "impact": t["impact"],
                "severity": t["severity"],
                "dimension": "财务质量",
            })
    elif financial.debt_ratio is not None and financial.debt_ratio > 70:
        reasons.append({
            "conclusion": f"资产负债率 {financial.debt_ratio:.1f}%，超过 70% 的安全线",
            "data_support": f"高负债企业利息支出大，利润对利率变化敏感。在去杠杆和紧信用环境下经营风险更高。",
            "impact": "过高的杠杆会在行业下行时放大亏损，严重时甚至引发流动性危机。保守投资者应规避高杠杆标的。",
            "severity": "medium",
            "dimension": "财务质量",
        })

    # 经营现金流为负
    negative_cf = [cf for cf in financial.operating_cf_trend if cf < 0]
    if len(negative_cf) >= 2:
        t = templates["cashflow_negative"]
        cf_seq = "、".join(f"{v:.1f}亿" for v in financial.operating_cf_trend[-3:])
        reasons.append({
            "conclusion": t["conclusion"].format(cf_negative_years=len(negative_cf)),
            "data_support": t["data_support"].format(
                cf_negative_years=len(negative_cf), cf_sequence=cf_seq),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "财务质量",
        })

    # 营收下滑
    if len(financial.revenue_growth_trend) >= 3:
        recent_growth = financial.revenue_growth_trend[-3:]
        if all(g < 10 for g in recent_growth) and sum(recent_growth) / 3 < 5:
            t = templates["revenue_declining"]
            growth_seq = " → ".join(f"{g:.1f}%" for g in recent_growth)
            reasons.append({
                "conclusion": t["conclusion"].format(years=3, cagr=sum(recent_growth) / 3),
                "data_support": t["data_support"].format(years=3, revenue_sequence=growth_seq),
                "impact": t["impact"],
                "severity": t["severity"],
                "dimension": "财务质量",
            })

    return reasons
```

- [ ] **Step 2: 提交**

```bash
git add app/engine/financial.py
git commit -m "feat: implement financial quality analysis engine"
```

---

### Task 12: 技术面 + 风险事件引擎

**Files:**
- Create: `app/engine/technical.py`
- Create: `app/engine/risk.py`

- [ ] **Step 1: 实现技术面引擎 `app/engine/technical.py`**

```python
import json
from pathlib import Path
from ..data.provider import TechnicalData, StockInfo


_TEMPLATES = None

def _load_templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        tmpl_path = Path(__file__).parent.parent.parent / "templates" / "reasons_zh.json"
        with open(tmpl_path, "r", encoding="utf-8") as f:
            _TEMPLATES = json.load(f)
    return _TEMPLATES


def analyze(technical: TechnicalData, info: StockInfo) -> list[dict]:
    templates = _load_templates()["technical"]
    reasons = []

    # 跌破 200 日均线
    if technical.price and technical.ma_200 and technical.price < technical.ma_200:
        t = templates["below_ma200"]
        below_pct = (1 - technical.price / technical.ma_200) * 100
        reasons.append({
            "conclusion": t["conclusion"].format(price=technical.price, ma200=technical.ma_200),
            "data_support": t["data_support"].format(below_pct=below_pct),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "技术面",
        })

    # 跌破 60 日均线
    if technical.price and technical.ma_60 and technical.price < technical.ma_60:
        t = templates["below_ma60"]
        below_pct = (1 - technical.price / technical.ma_60) * 100
        reasons.append({
            "conclusion": t["conclusion"].format(price=technical.price, ma60=technical.ma_60),
            "data_support": t["data_support"].format(below_pct=below_pct),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "技术面",
        })

    # MACD 死叉
    if (technical.macd_dif is not None and technical.macd_dea is not None
            and technical.macd_dif < technical.macd_dea):
        t = templates["macd_death_cross"]
        reasons.append({
            "conclusion": t["conclusion"].format(
                dif=technical.macd_dif, dea=technical.macd_dea,
                hist=technical.macd_histogram or 0),
            "data_support": t["data_support"].format(
                dif=technical.macd_dif, dea=technical.macd_dea,
                hist=technical.macd_histogram or 0),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "技术面",
        })

    # RSI 超买
    if technical.rsi_14 is not None and technical.rsi_14 >= 65:
        t = templates["rsi_overbought"]
        reasons.append({
            "conclusion": t["conclusion"].format(rsi=technical.rsi_14),
            "data_support": t["data_support"].format(rsi=technical.rsi_14),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "技术面",
        })

    return reasons
```

- [ ] **Step 2: 实现风险事件引擎 `app/engine/risk.py`**

```python
import json
from pathlib import Path
from ..data.provider import RiskData, StockInfo


_TEMPLATES = None

def _load_templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        tmpl_path = Path(__file__).parent.parent.parent / "templates" / "reasons_zh.json"
        with open(tmpl_path, "r", encoding="utf-8") as f:
            _TEMPLATES = json.load(f)
    return _TEMPLATES


def analyze(risk: RiskData, info: StockInfo) -> list[dict]:
    templates = _load_templates()["risk"]
    reasons = []

    # 高管减持
    if risk.insider_sells_3m:
        total_amount = sum(s.get("amount", 0) for s in risk.insider_sells_3m)
        if total_amount > 0:
            t = templates["insider_selling"]
            details = "; ".join(
                f"{s.get('name','某人')}减持{s.get('amount',0):.0f}万元({s.get('date','未知日期')})"
                for s in risk.insider_sells_3m[:3]
            )
            reasons.append({
                "conclusion": t["conclusion"].format(amount=total_amount),
                "data_support": t["data_support"].format(insider_details=details),
                "impact": t["impact"],
                "severity": t["severity"],
                "dimension": "风险事件",
            })

    # 质押比例高
    if risk.pledge_ratio is not None and risk.pledge_ratio > 30:
        t = templates["pledge_high"]
        reasons.append({
            "conclusion": t["conclusion"].format(pledge=risk.pledge_ratio),
            "data_support": t["data_support"].format(pledge=risk.pledge_ratio),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "风险事件",
        })

    # 监管问询
    if risk.regulatory_inquiries_12m >= 1:
        t = templates["regulatory_inquiry"]
        reasons.append({
            "conclusion": t["conclusion"].format(inquiry_count=risk.regulatory_inquiries_12m),
            "data_support": t["data_support"],
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "风险事件",
        })

    # 无高管增持（仅在其他风险信号存在时才加入）
    if not risk.insider_buys_3m and risk.insider_sells_3m:
        t = templates["no_insider_buying"]
        reasons.append({
            "conclusion": t["conclusion"],
            "data_support": t["data_support"],
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "风险事件",
        })

    return reasons
```

- [ ] **Step 3: 提交**

```bash
git add app/engine/technical.py app/engine/risk.py
git commit -m "feat: implement technical and risk analysis engines"
```

---

### Task 13: 聚合器

**Files:**
- Create: `app/engine/aggregator.py`

- [ ] **Step 1: 实现理由聚合器 `app/engine/aggregator.py`**

```python
from ..data.provider import StockData
from . import valuation, financial, technical, risk


def generate_reasons(data: StockData, target_count: int = 10) -> list[dict]:
    """
    汇总四维度分析结果，生成 target_count 条理由。
    优先级：估值 ≥ 财务 ≥ 风险 ≥ 技术面
    每维度至少贡献 1 条，不足时用其他维度的备选理由补充。
    """
    all_reasons: list[dict] = []

    val_reasons = valuation.analyze(data.valuation, data.info)
    fin_reasons = financial.analyze(data.financial, data.info)
    tech_reasons = technical.analyze(data.technical, data.info)
    risk_reasons = risk.analyze(data.risk, data.info)

    # 按严重程度排序: high > medium > low
    severity_order = {"high": 0, "medium": 1, "low": 2}

    all_candidates = val_reasons + fin_reasons + risk_reasons + tech_reasons
    all_candidates.sort(key=lambda r: (severity_order.get(r["severity"], 99)))

    # 取前 target_count 条
    selected = all_candidates[:target_count]

    # 去重: 如果同一维度超过4条，只保留前4条
    dimension_counts: dict[str, int] = {}
    deduped = []
    for r in selected:
        dim = r["dimension"]
        cnt = dimension_counts.get(dim, 0)
        if cnt < 4:
            deduped.append(r)
            dimension_counts[dim] = cnt + 1

    # 如果还不够 target_count，补充通用理由
    while len(deduped) < target_count:
        deduped.append({
            "conclusion": "该股票无法通过基础数据验证获得足够的安全边际",
            "data_support": "在估值、财务、技术、风险四个维度中，多个关键指标缺失或表现不佳，无法形成完整的投资价值评估。",
            "impact": "信息不充分本身就是一种风险。在关键数据缺失的情况下买入，等于在不完全信息下做决策。",
            "severity": "medium",
            "dimension": "综合",
        })

    return deduped


def make_summary(reasons: list[dict], elapsed: float, provider: str, ai_provider: str | None = None) -> dict:
    high = sum(1 for r in reasons if r["severity"] == "high")
    medium = sum(1 for r in reasons if r["severity"] == "medium")
    low = sum(1 for r in reasons if r["severity"] == "low")
    return {
        "total": len(reasons),
        "high": high,
        "medium": medium,
        "low": low,
        "elapsed_seconds": round(elapsed, 2),
        "provider": provider,
        "ai_provider": ai_provider or "未启用",
    }
```

- [ ] **Step 2: 提交**

```bash
git add app/engine/aggregator.py
git commit -m "feat: implement reason aggregator with priority and dedup"
```

---

### Task 14: AI 适配器

**Files:**
- Create: `app/ai/base.py`
- Create: `app/ai/providers.py`

- [ ] **Step 1: 编写 AI 抽象接口 `app/ai/base.py`**

```python
from abc import ABC, abstractmethod


class AIAdapter(ABC):
    """AI 服务适配器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def enhance(self, reasons: list[dict], stock_name: str, symbol: str) -> list[dict]:
        """
        接收规则引擎生成的理由列表，返回润色/增强后的理由列表。
        保持原有结构 (conclusion, data_support, impact, severity, dimension)。
        """
        ...


def build_prompt(reasons: list[dict], stock_name: str, symbol: str) -> str:
    lines = [
        f"你是专业的A股投资分析师。请针对股票 {stock_name}({symbol}) 的分析结果进行润色和深化。",
        f"",
        f"以下是规则引擎生成的 {len(reasons)} 条\"不值得购买\"理由：",
    ]
    for i, r in enumerate(reasons, 1):
        lines.append(f"{i}. [{r['dimension']}] {r['conclusion']}")
        lines.append(f"   数据支撑: {r['data_support']}")
        lines.append(f"   影响解读: {r['impact']}")

    lines.extend([
        "",
        "请对每条理由做以下处理（保持 JSON 数组格式输出）：",
        "1. 让语言更流畅、更自然，避免套话",
        "2. 补充你了解的相关背景知识或行业洞察",
        "3. 保持原有的 severity 和 dimension 字段不变",
        "4. 每条理由保持 conclusion / data_support / impact 三段式结构",
        "",
        '输出格式: [{"conclusion": "...", "data_support": "...", "impact": "...", "severity": "high/medium/low", "dimension": "估值/财务质量/技术面/风险事件/综合"}]',
    ])
    return "\n".join(lines)
```

- [ ] **Step 2: 编写各 Provider 适配器 `app/ai/providers.py`**

```python
import json
import httpx
from openai import OpenAI
from .base import AIAdapter, build_prompt


class DeepSeekAdapter(AIAdapter):
    name = "deepseek"

    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    def is_available(self) -> bool:
        return bool(self.api_key)

    def enhance(self, reasons: list[dict], stock_name: str, symbol: str) -> list[dict]:
        if not self.client:
            return reasons
        prompt = build_prompt(reasons, stock_name, symbol)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            content = resp.choices[0].message.content or ""
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            enhanced = json.loads(content)
            if isinstance(enhanced, list):
                return enhanced
        except Exception:
            pass
        return reasons


class OllamaAdapter(AIAdapter):
    name = "ollama"

    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.host = host
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = httpx.get(f"{self.host}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def enhance(self, reasons: list[dict], stock_name: str, symbol: str) -> list[dict]:
        prompt = build_prompt(reasons, stock_name, symbol)
        try:
            resp = httpx.post(
                f"{self.host}/api/chat",
                json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "stream": False},
                timeout=120,
            )
            content = resp.json()["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            enhanced = json.loads(content)
            if isinstance(enhanced, list):
                return enhanced
        except Exception:
            pass
        return reasons


def create_openai_compatible_adapter(name: str, api_key: str, model: str, base_url: str) -> type[AIAdapter]:
    """工厂函数：创建任意 OpenAI 兼容接口的适配器类"""
    class Adapter(AIAdapter):
        _name = name
        def __init__(self):
            self.api_key = api_key
            self.model = model
            self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None
        @property
        def name(self) -> str:
            return self._name
        def is_available(self) -> bool:
            return bool(self.api_key)
        def enhance(self, reasons, stock_name, symbol):
            if not self.client:
                return reasons
            prompt = build_prompt(reasons, stock_name, symbol)
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                content = resp.choices[0].message.content or ""
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]
                enhanced = json.loads(content)
                if isinstance(enhanced, list):
                    return enhanced
            except Exception:
                pass
            return reasons
    return Adapter


def build_ai_adapter(config) -> AIAdapter | None:
    """根据配置创建 AI 适配器，返回 None 表示禁用"""
    from ..config import AppConfig
    if not isinstance(config, AppConfig):
        return None
    ai = config.ai
    if ai.provider == "none" or not ai.provider:
        return None

    provider_map = {
        "deepseek": ai.deepseek,
        "qwen": ai.qwen,
        "zhipu": ai.zhipu,
        "moonshot": ai.moonshot,
        "openai": ai.openai,
    }

    if ai.provider == "ollama":
        return OllamaAdapter(host=ai.ollama.host, model=ai.ollama.model)

    if ai.provider == "custom":
        if ai.custom.api_key and ai.custom.base_url:
            return create_openai_compatible_adapter(
                "custom", ai.custom.api_key, ai.custom.model, ai.custom.base_url)()
        return None

    if ai.provider in provider_map:
        cfg = provider_map[ai.provider]
        if cfg.api_key:
            return create_openai_compatible_adapter(
                ai.provider, cfg.api_key, cfg.model, cfg.base_url)()

    return None
```

- [ ] **Step 3: 提交**

```bash
git add app/ai/base.py app/ai/providers.py
git commit -m "feat: implement AI adapter with multiple Chinese LLM providers"
```

---

### Task 15: FastAPI 主应用

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: 实现 FastAPI 应用 `app/main.py`**

```python
import uuid
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import load_config
from .data.fallback import fetch_stock_data
from .engine.aggregator import generate_reasons, make_summary
from .ai.providers import build_ai_adapter


app = FastAPI(title="Money-Tracing", description="A股不值得买分析器", version="1.0.0")

_config = load_config()

# 挂载静态文件
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class AnalyzeRequest(BaseModel):
    symbol: str

class Reason(BaseModel):
    conclusion: str
    data_support: str
    impact: str
    severity: str
    dimension: str

class AnalyzeResponse(BaseModel):
    symbol: str
    stock_name: str
    reasons: list[Reason]
    summary: dict


@app.get("/")
async def index():
    from fastapi.responses import FileResponse
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Money-Tracing API is running. Visit /docs for API documentation."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    symbol = req.symbol.strip()
    if not symbol.isdigit() or len(symbol) != 6:
        raise HTTPException(status_code=400, detail="请输入6位数字的A股代码")

    start = time.time()

    try:
        data, provider_name = fetch_stock_data(symbol, _config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据获取失败: {e}")

    reasons = generate_reasons(data, target_count=10)

    # AI 增强（可选）
    ai_provider = None
    try:
        adapter = build_ai_adapter(_config)
        if adapter and adapter.is_available():
            reasons = adapter.enhance(reasons, data.info.name or symbol, symbol)
            ai_provider = adapter.name
    except Exception:
        pass

    elapsed = time.time() - start
    summary = make_summary(reasons, elapsed, provider_name, ai_provider)

    return AnalyzeResponse(
        symbol=symbol,
        stock_name=data.info.name or symbol,
        reasons=[Reason(**r) for r in reasons],
        summary=summary,
    )
```

- [ ] **Step 2: 提交**

```bash
git add app/main.py
git commit -m "feat: implement FastAPI main application with /analyze endpoint"
```

---

### Task 16: CLI 入口

**Files:**
- Create: `analyze.py`

- [ ] **Step 1: 实现命令行入口 `analyze.py`**

```python
#!/usr/bin/env python3
"""A股不值得买分析器 - CLI 入口

用法: python analyze.py 000001
"""

import sys
import time
from app.config import load_config
from app.data.fallback import fetch_stock_data
from app.engine.aggregator import generate_reasons, make_summary
from app.ai.providers import build_ai_adapter


SEVERITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}
SEVERITY_LABELS = {"high": "高风险", "medium": "中等风险", "low": "低风险"}


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze.py <股票代码>")
        print("示例: python analyze.py 000001")
        sys.exit(1)

    symbol = sys.argv[1].strip()
    if not symbol.isdigit() or len(symbol) != 6:
        print("错误: 请输入6位数字的A股代码")
        sys.exit(1)

    print(f"\n🔍 正在分析 {symbol} ...\n")

    config = load_config()
    start = time.time()

    try:
        data, provider_name = fetch_stock_data(symbol, config)
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        sys.exit(1)

    reasons = generate_reasons(data, target_count=10)

    ai_provider = None
    try:
        adapter = build_ai_adapter(config)
        if adapter and adapter.is_available():
            print("🤖 正在使用 AI 增强分析结果...\n")
            reasons = adapter.enhance(reasons, data.info.name or symbol, symbol)
            ai_provider = adapter.name
    except Exception:
        pass

    elapsed = time.time() - start
    summary = make_summary(reasons, elapsed, provider_name, ai_provider)

    # 输出
    stock_display = f"{data.info.name}({symbol})" if data.info.name else symbol
    print(f"{'='*60}")
    print(f"  {stock_display} — 不值得买的 {len(reasons)} 个理由")
    print(f"{'='*60}\n")

    for i, r in enumerate(reasons, 1):
        icon = SEVERITY_ICONS.get(r["severity"], "⚪")
        label = SEVERITY_LABELS.get(r["severity"], "未知")
        print(f"{icon} {r['dimension']} | {r['conclusion']}")
        print(f"  数据支撑: {r['data_support']}")
        print(f"  影响解读: {r['impact']}")
        print(f"  严重程度: {label}\n")

    print(f"{'='*60}")
    print(f"💡 总结: 高风险 {summary['high']} 条，中等风险 {summary['medium']} 条，低风险 {summary['low']} 条")
    print(f"⏱ 分析耗时: {summary['elapsed_seconds']}s | 数据源: {summary['provider']} | AI: {summary['ai_provider']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 设置可执行权限并提交**

```bash
chmod +x analyze.py
git add analyze.py
git commit -m "feat: implement CLI entry point with colored output"
```

---

### Task 17: Web 前端

**Files:**
- Create: `static/index.html`
- Create: `static/style.css`
- Create: `static/app.js`

- [ ] **Step 1: 编写 HTML `static/index.html`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Money-Tracing — A股不值得买分析器</title>
    <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Money-Tracing</h1>
            <p class="subtitle">A股"不值得买"分析器 — 输入代码，获取 10 个理性拒绝的理由</p>
        </header>

        <div class="search-box">
            <input id="symbolInput" type="text" placeholder="输入6位股票代码，如 000001" maxlength="6" autofocus />
            <button id="analyzeBtn">开始分析</button>
        </div>

        <div id="loading" class="hidden">
            <div class="spinner"></div>
            <p>正在获取数据并分析中...</p>
        </div>

        <div id="error" class="hidden"></div>

        <div id="result" class="hidden">
            <div id="stockHeader"></div>
            <div id="reasons"></div>
            <div id="summary"></div>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 编写样式 `static/style.css`**

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
}
.container { max-width: 800px; margin: 0 auto; padding: 24px 16px; }
header { text-align: center; margin-bottom: 32px; }
header h1 { font-size: 28px; color: #d32f2f; margin-bottom: 8px; }
.subtitle { color: #666; font-size: 14px; }

.search-box { display: flex; gap: 12px; justify-content: center; margin-bottom: 24px; }
.search-box input {
    width: 260px; padding: 12px 16px; font-size: 18px;
    border: 2px solid #ddd; border-radius: 8px; outline: none;
    text-align: center; letter-spacing: 4px;
}
.search-box input:focus { border-color: #d32f2f; }
.search-box button {
    padding: 12px 24px; font-size: 16px; background: #d32f2f;
    color: white; border: none; border-radius: 8px; cursor: pointer;
    font-weight: 600;
}
.search-box button:hover { background: #b71c1c; }
.search-box button:disabled { background: #ccc; cursor: not-allowed; }

.hidden { display: none !important; }

#loading { text-align: center; padding: 40px; }
.spinner {
    width: 40px; height: 40px; border: 4px solid #eee;
    border-top-color: #d32f2f; border-radius: 50%;
    animation: spin 0.8s linear infinite; margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

#error { background: #ffebee; color: #c62828; padding: 16px; border-radius: 8px; margin-bottom: 16px; }

#stockHeader { text-align: center; margin-bottom: 24px; }
#stockHeader h2 { font-size: 22px; }
#stockHeader .meta { color: #888; font-size: 13px; margin-top: 4px; }

.reason-card {
    background: white; border-radius: 10px; padding: 20px;
    margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-left: 4px solid #ddd;
}
.reason-card.severity-high { border-left-color: #d32f2f; }
.reason-card.severity-medium { border-left-color: #f57c00; }
.reason-card.severity-low { border-left-color: #388e3c; }

.reason-card .card-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 10px;
}
.reason-card .dimension-tag {
    font-size: 12px; padding: 2px 8px; border-radius: 4px;
    background: #f0f0f0; color: #666;
}
.reason-card .severity-tag {
    font-size: 12px; padding: 2px 8px; border-radius: 4px;
}
.severity-tag.high { background: #ffebee; color: #c62828; }
.severity-tag.medium { background: #fff3e0; color: #e65100; }
.severity-tag.low { background: #e8f5e9; color: #2e7d32; }

.reason-card .conclusion { font-size: 16px; font-weight: 600; color: #222; margin-bottom: 8px; }
.reason-card .data-support { font-size: 13px; color: #555; margin-bottom: 8px; padding-left: 12px; border-left: 2px solid #eee; }
.reason-card .impact { font-size: 13px; color: #777; font-style: italic; }

#summary {
    background: white; border-radius: 10px; padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center;
}
#summary .stats { display: flex; justify-content: center; gap: 24px; margin-bottom: 12px; }
#summary .stat { text-align: center; }
#summary .stat .num { font-size: 32px; font-weight: 700; }
#summary .stat .num.high { color: #d32f2f; }
#summary .stat .num.medium { color: #f57c00; }
#summary .stat .num.low { color: #388e3c; }
#summary .stat .label { font-size: 13px; color: #888; }
#summary .meta { font-size: 12px; color: #aaa; }
```

- [ ] **Step 3: 编写 JavaScript `static/app.js`**

```javascript
const SEVERITY_LABELS = { high: "高风险", medium: "中等风险", low: "低风险" };

document.getElementById("analyzeBtn").addEventListener("click", runAnalysis);
document.getElementById("symbolInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") runAnalysis();
});

async function runAnalysis() {
    const symbol = document.getElementById("symbolInput").value.trim();
    if (!/^\d{6}$/.test(symbol)) {
        showError("请输入6位数字的A股代码");
        return;
    }

    const btn = document.getElementById("analyzeBtn");
    btn.disabled = true;

    hide("error");
    hide("result");
    show("loading");

    try {
        const resp = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol }),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "分析失败");
        }

        const data = await resp.json();
        renderResult(data);
    } catch (e) {
        showError(e.message);
    } finally {
        hide("loading");
        btn.disabled = false;
    }
}

function renderResult(data) {
    document.getElementById("stockHeader").innerHTML = `
        <h2>${data.stock_name} (${data.symbol})</h2>
        <p class="meta">数据源: ${data.summary.provider} | AI: ${data.summary.ai_provider} | 耗时: ${data.summary.elapsed_seconds}s</p>
    `;

    const reasonsDiv = document.getElementById("reasons");
    reasonsDiv.innerHTML = data.reasons.map((r, i) => `
        <div class="reason-card severity-${r.severity}">
            <div class="card-header">
                <span class="dimension-tag">${r.dimension}</span>
                <span class="severity-tag ${r.severity}">${SEVERITY_LABELS[r.severity] || r.severity}</span>
            </div>
            <div class="conclusion">${i + 1}. ${r.conclusion}</div>
            <div class="data-support">📊 ${r.data_support}</div>
            <div class="impact">💡 ${r.impact}</div>
        </div>
    `).join("");

    document.getElementById("summary").innerHTML = `
        <div class="stats">
            <div class="stat">
                <div class="num high">${data.summary.high}</div>
                <div class="label">高风险</div>
            </div>
            <div class="stat">
                <div class="num medium">${data.summary.medium}</div>
                <div class="label">中等风险</div>
            </div>
            <div class="stat">
                <div class="num low">${data.summary.low}</div>
                <div class="label">低风险</div>
            </div>
        </div>
        <div class="meta">
            ⏱ ${data.summary.elapsed_seconds}s | 📡 ${data.summary.provider} | 🤖 ${data.summary.ai_provider}
        </div>
    `;

    hide("error");
    show("result");
    window.scrollTo({ top: document.getElementById("result").offsetTop - 20, behavior: "smooth" });
}

function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden"); }

function showError(msg) {
    hide("result");
    const el = document.getElementById("error");
    el.textContent = "❌ " + msg;
    show("error");
}
```

- [ ] **Step 4: 提交**

```bash
git add static/
git commit -m "feat: implement web frontend with search, cards, and summary"
```

---

### Task 18: 部署脚本

**Files:**
- Create: `install.sh`
- Create: `start.sh`
- Modify: `docker-compose.yml`

- [ ] **Step 1: 编写 install.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"
echo "Money-Tracing 一键安装脚本"
echo "检测到系统: $OS"
echo ""

# --- Python check ---
if ! command -v python3 &>/dev/null; then
    echo "❌ 未检测到 Python 3。请先安装 Python 3.10+"
    echo "   macOS: brew install python@3.12"
    echo "   Windows: https://www.python.org/downloads/"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PY_VER"

# --- Check Docker ---
USE_DOCKER=false
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    USE_DOCKER=true
    echo "✅ Docker 可用，将使用 Docker 部署"
else
    echo "ℹ️ Docker 未检测到，将使用本地 venv 部署"
fi

# --- Ensure config.yaml ---
if [ ! -f config.yaml ]; then
    cp config.yaml.example config.yaml
    echo ""
    echo "📝 已创建 config.yaml，请编辑填入你的 tushare token 和 AI API key（可选）"
    echo "   配置文件路径: $(pwd)/config.yaml"
fi

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
    echo "✅ 本地安装完成。启动请运行: ./start.sh"
fi
```

- [ ] **Step 2: 编写 start.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    echo "🐳 使用 Docker 模式启动..."
    docker compose up -d --build
    echo ""
    echo "✅ 服务已启动"
    echo "   Web 界面: http://localhost:8000"
    echo "   API 文档: http://localhost:8000/docs"
    echo "   停止服务: docker compose down"
else
    if [ ! -f .venv/bin/activate ]; then
        echo "❌ 虚拟环境未找到，请先运行 ./install.sh"
        exit 1
    fi

    echo "🐍 使用本地模式启动..."
    . .venv/bin/activate
    echo "启动服务 on http://localhost:8000 ..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
```

- [ ] **Step 3: 更新 docker-compose.yml**

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data:/app/data
    environment:
      - MT_CONFIG=/app/config.yaml
    restart: unless-stopped
```

- [ ] **Step 4: 创建 Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 5: 设置权限并提交**

```bash
chmod +x install.sh start.sh
git add install.sh start.sh docker-compose.yml Dockerfile
git commit -m "feat: add one-click install/start scripts and Docker support"
```

---

### Task 19: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 重写 README.md**

```markdown
# Money-Tracing 📊

输入任意 A 股股票代码，基于估值、财务、技术、风险四个维度，生成 **10 条详实的"不值得买"理由**。

每条理由包含：**结论** + **数据支撑** + **影响解读**，让你在做投资决策前看到硬币的另一面。

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/Money-Tracing.git
cd Money-Tracing

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
```

- [ ] **Step 2: 创建 .gitignore**

```gitignore
.venv/
__pycache__/
*.pyc
data/
*.log
config.yaml
.DS_Store
```

- [ ] **Step 3: 提交**

```bash
git add README.md .gitignore
git commit -m "docs: rewrite README with project overview and quickstart"
```

---

### Task 20: 端到端测试

**Files:**
- Create: `test_analyze.py`

- [ ] **Step 1: 编写集成测试 `test_analyze.py`**

```python
"""端到端冒烟测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_analyze_valid_symbol():
    resp = client.post("/analyze", json={"symbol": "000001"})
    assert resp.status_code == 200
    data = resp.json()
    assert "reasons" in data
    assert len(data["reasons"]) >= 1
    assert "summary" in data
    for r in data["reasons"]:
        assert "conclusion" in r
        assert "data_support" in r
        assert "impact" in r
        assert "severity" in r
        assert "dimension" in r


def test_analyze_invalid_symbol():
    resp = client.post("/analyze", json={"symbol": "123"})
    assert resp.status_code == 400


def test_analyze_nonexistent_symbol():
    """不存在的股票代码应该能优雅处理"""
    resp = client.post("/analyze", json={"symbol": "999999"})
    # 可能返回 200（拿到了部分数据）或 500（数据源完全失败）
    # 两者都是可接受的行为
    assert resp.status_code in (200, 500)
```

- [ ] **Step 2: 运行测试**

```bash
pip install pytest httpx
python -m pytest test_analyze.py -v
```

Expected: 至少 `test_health` 和 `test_analyze_invalid_symbol` 通过。`test_analyze_valid_symbol` 依赖外部数据源，可能因网络问题失败，不计入必须通过。

- [ ] **Step 3: 提交**

```bash
git add test_analyze.py
git commit -m "test: add end-to-end smoke tests"
```

---
