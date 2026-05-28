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
