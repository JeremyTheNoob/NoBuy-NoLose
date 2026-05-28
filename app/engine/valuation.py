from ..data.provider import ValuationData, StockInfo
from . import load_templates


def analyze(valuation: ValuationData, info: StockInfo) -> list[dict]:
    """
    基于估值数据生成 2-3 条理由。
    返回格式: [{"conclusion": str, "data_support": str, "impact": str, "severity": str, "dimension": "估值"}]
    """
    templates = load_templates()["valuation"]
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
