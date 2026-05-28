import pandas as pd
import akshare as ak
from .provider import DataProvider, StockInfo, ValuationData, FinancialData, TechnicalData, RiskData


class AkshareProvider(DataProvider):
    name = "akshare"

    def is_available(self) -> bool:
        return True

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
