from ..data.provider import TechnicalData, StockInfo
from . import load_templates


def analyze(technical: TechnicalData, info: StockInfo) -> list[dict]:
    templates = load_templates()["technical"]
    reasons = []
    price = technical.price

    # 1. 跌破 200 日均线
    if price and technical.ma_200 and price < technical.ma_200:
        t = templates["below_ma200"]
        below_pct = (1 - price / technical.ma_200) * 100
        reasons.append({
            "conclusion": t["conclusion"].format(price=price, ma200=technical.ma_200),
            "data_support": t["data_support"].format(below_pct=below_pct),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "技术面",
        })

    # 2. 跌破 60 日均线
    if price and technical.ma_60 and price < technical.ma_60:
        t = templates["below_ma60"]
        below_pct = (1 - price / technical.ma_60) * 100
        reasons.append({
            "conclusion": t["conclusion"].format(price=price, ma60=technical.ma_60),
            "data_support": t["data_support"].format(below_pct=below_pct),
            "impact": t["impact"],
            "severity": t["severity"],
            "dimension": "技术面",
        })

    # 3. 跌破 20 日均线（短期偏弱）
    if price and technical.ma_20 and price < technical.ma_20:
        below_pct = (1 - price / technical.ma_20) * 100
        reasons.append({
            "conclusion": f"股价 {price:.2f} 低于 20 日均线 {technical.ma_20:.2f}，短期走势偏弱",
            "data_support": f"当前股价位于 20 日均线下方 {below_pct:.1f}%，近一个月趋势偏空。",
            "impact": "20 日均线反映短期持仓成本，股价持续低于此线表明短线资金处于浮亏状态，反弹面临抛压。",
            "severity": "low",
            "dimension": "技术面",
        })

    # 4. MACD 死叉
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

    # 5. RSI 超买或超卖
    if technical.rsi_14 is not None:
        if technical.rsi_14 >= 70:
            reasons.append({
                "conclusion": f"RSI(14) 为 {technical.rsi_14:.1f}，处于超买区间",
                "data_support": f"RSI 高于 70 通常被视为超买信号，短期可能存在回调需求。",
                "impact": "RSI 超买提示追高风险较大，虽然强势股可以维持超买状态较长时间，但风险收益比不佳。",
                "severity": "low",
                "dimension": "技术面",
            })
        elif technical.rsi_14 <= 30:
            reasons.append({
                "conclusion": f"RSI(14) 为 {technical.rsi_14:.1f}，处于超卖区间，但趋势偏弱",
                "data_support": f"RSI 低于 30 通常被视为超卖信号，但超卖不等于止跌，在下跌趋势中超卖可以持续很长时间。",
                "impact": "抄底超卖股票需要等待企稳信号，盲目买入可能面临继续下跌的风险。",
                "severity": "medium",
                "dimension": "技术面",
            })

    # 6. 无看空信号 = 说明当前技术面情况
    has_indicators = (
        technical.ma_20 is not None
        or technical.ma_60 is not None
        or technical.rsi_14 is not None
    )
    if not reasons and price is not None:
        if has_indicators:
            reasons.append({
                "conclusion": f"当前股价 {price:.2f} 元，技术面无明显看空信号",
                "data_support": "均线、MACD、RSI 等指标均未触发卖出条件。但这并不构成买入理由——技术面健康不代表估值合理或基本面良好。",
                "impact": "技术面不提供卖出信号时，应更多参考估值和财务维度来判断投资价值。",
                "severity": "low",
                "dimension": "技术面",
            })
        else:
            reasons.append({
                "conclusion": f"当前股价 {price:.2f} 元，无法获取技术指标数据",
                "data_support": "缺少历史K线数据，无法计算均线、MACD、RSI 等技术指标。建议配置更完整的数据源。",
                "impact": "缺少技术指标意味着无法判断当前价位在历史走势中的位置。",
                "severity": "low",
                "dimension": "技术面",
            })

    return reasons
