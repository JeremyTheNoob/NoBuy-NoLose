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
