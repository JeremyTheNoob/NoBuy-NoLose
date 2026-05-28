from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class StockInfo:
    symbol: str
    name: str = ""
    industry: str = ""

@dataclass
class ValuationData:
    pe: float | None = None
    pe_percentile_5y: float | None = None
    pe_industry_avg: float | None = None
    pb: float | None = None
    pb_percentile_5y: float | None = None
    pb_industry_avg: float | None = None
    ps: float | None = None

@dataclass
class FinancialData:
    roe_trend: list[float] = field(default_factory=list)
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
    insider_sells_3m: list[dict] = field(default_factory=list)
    insider_buys_3m: list[dict] = field(default_factory=list)
    pledge_ratio: float | None = None
    regulatory_inquiries_12m: int = 0
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
