from ..data.provider import FinancialData, StockInfo
from . import load_templates


def analyze(financial: FinancialData, info: StockInfo) -> list[dict]:
    templates = load_templates()["financial"]
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
            "data_support": "高负债企业利息支出大，利润对利率变化敏感。在去杠杆和紧信用环境下经营风险更高。",
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
