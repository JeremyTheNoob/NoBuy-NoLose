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
            df = self.pro.daily_basic(ts_code=self._ts_code(symbol), fields="pe_ttm,pb")
            if df.empty:
                return ValuationData()
            latest = df.iloc[0]  # tushare 默认降序，最新行在第一个
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
