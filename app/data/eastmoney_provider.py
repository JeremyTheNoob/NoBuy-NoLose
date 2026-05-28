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
                pe=data.get("f9"),
                pb=data.get("f23"),
            )
        except Exception:
            return ValuationData()

    def fetch_financial(self, symbol: str) -> FinancialData:
        return FinancialData()

    def fetch_technical(self, symbol: str) -> TechnicalData:
        return TechnicalData()

    def fetch_risk(self, symbol: str) -> RiskData:
        return RiskData()
