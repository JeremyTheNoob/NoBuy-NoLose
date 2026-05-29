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

    # 数据稀疏时，优先给出数据提示
    if len(deduped) < 3:
        missing = []
        if not (data.valuation.pe or data.valuation.pb):
            missing.append("估值")
        if not (data.financial.roe_trend or data.financial.debt_ratio):
            missing.append("财务")
        if not data.technical.price:
            missing.append("技术面")
        if not (data.risk.pledge_ratio or data.risk.insider_sells_3m):
            missing.append("风险")

        if missing:
            # 数据提示插在最前面
            deduped.insert(0, {
                "conclusion": f"数据不完整：{', '.join(missing)}维度缺失，建议配置 tushare token",
                "data_support": f"当前仅从 {data.info.name and '新浪财经' or '数据源'} 获取到基础行情。免费注册 tushare.pro 获取 API token 后填入 config.yaml，即可获得完整的估值、财务、风险数据。",
                "impact": "数据不完整时做出的分析结论参考价值有限。完善的データ是理性决策的基础。",
                "severity": "medium",
                "dimension": "数据提示",
            })

    # 如果分析理由太少（数据不足），补充1条统一的提示，不过度堆砌
    if len(deduped) < 3:
        deduped.append({
            "conclusion": "当前可用的分析数据不足，建议配置 tushare token 以获得完整的四维度分析",
            "data_support": "免费注册 tushare.pro 获取 API token，填入 config.yaml 后重新查询，即可获得包含估值、财务质量、技术指标和风险事件的完整报告。",
            "impact": "完善的数据覆盖是做出理性投资决策的前提。",
            "severity": "medium",
            "dimension": "综合",
        })

    return deduped


def make_summary(reasons: list[dict], elapsed: float, provider: str, ai_provider: str | None = None, ai_error: str | None = None) -> dict:
    high = sum(1 for r in reasons if r["severity"] == "high")
    medium = sum(1 for r in reasons if r["severity"] == "medium")
    low = sum(1 for r in reasons if r["severity"] == "low")
    ai_display = ai_provider or "未启用"
    if ai_error:
        ai_display += f" ({ai_error})"
    return {
        "total": len(reasons),
        "high": high,
        "medium": medium,
        "low": low,
        "elapsed_seconds": round(elapsed, 2),
        "provider": provider,
        "ai_provider": ai_display,
    }
