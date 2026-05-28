from ..data.provider import RiskData, StockInfo
from . import load_templates


def analyze(risk: RiskData, info: StockInfo) -> list[dict]:
    templates = load_templates()["risk"]
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
