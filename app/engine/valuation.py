from ..data.provider import ValuationData, StockInfo
from . import load_templates


def _fmt(val: float, precision: int = 1) -> str:
    return f"{val:.{precision}f}"


def analyze(valuation: ValuationData, info: StockInfo) -> list[dict]:
    """基于估值数据生成 3-5 条理由"""
    reasons = []

    industry = info.industry or "全市场"
    name = info.name or "该股票"

    # 1. PE 分位
    if valuation.pe is not None:
        if valuation.pe_percentile_5y is not None and valuation.pe_percentile_5y >= 80:
            pe_median_est = valuation.pe / (1 + (valuation.pe_percentile_5y - 50) / 100) if valuation.pe_percentile_5y > 50 else valuation.pe
            reasons.append({
                "conclusion": f"当前 PE {valuation.pe:.1f}，处于近5年历史 {valuation.pe_percentile_5y:.0f}% 分位",
                "data_support": f"近5年 PE 中位数为 {pe_median_est:.1f}，当前值高出中位数 {((valuation.pe/pe_median_est-1)*100):.0f}%。"
                               f"同行业（{industry}）PE 均值仅 {valuation.pe_industry_avg or '暂无'}。",
                "impact": "高估值意味着市场已充分定价甚至过度乐观。一旦业绩不及预期或市场情绪转向，面临较大的估值回归压力。",
                "severity": "high",
                "dimension": "估值",
            })
        elif valuation.pe_percentile_5y is not None and valuation.pe_percentile_5y >= 60:
            reasons.append({
                "conclusion": f"当前 PE {valuation.pe:.1f}，处于近5年历史 {valuation.pe_percentile_5y:.0f}% 分位，估值偏高",
                "data_support": f"近5年 PE 分布中，当前值高于 {valuation.pe_percentile_5y:.0f}% 的历史交易日。",
                "impact": "处于历史中高估区域，安全边际有限。若业绩增速放缓，估值回调压力较大。",
                "severity": "medium",
                "dimension": "估值",
            })
        elif valuation.pe > 50:
            reasons.append({
                "conclusion": f"当前 PE {valuation.pe:.1f}，绝对估值水平较高",
                "data_support": f"PE 超过 50 意味着市场给予了很高的成长预期。同行业参考 PE 为 {valuation.pe_industry_avg or '暂无数据'}。",
                "impact": "高 PE 需要未来业绩高速增长来消化，一旦增速不达预期，估值和盈利双杀的风险不容忽视。",
                "severity": "medium",
                "dimension": "估值",
            })

    # 2. PE vs 行业
    if (valuation.pe is not None and valuation.pe_industry_avg is not None
            and valuation.pe > 0 and valuation.pe_industry_avg > 0):
        ratio = valuation.pe / valuation.pe_industry_avg
        if ratio >= 2:
            reasons.append({
                "conclusion": f"PE 为行业均值 {valuation.pe_industry_avg:.1f} 的 {ratio:.1f} 倍，显著高于同行业水平",
                "data_support": f"同属{industry}的上市公司 PE 均值 {valuation.pe_industry_avg:.1f}，{name} 当前 PE {valuation.pe:.1f}。",
                "impact": "远超行业均值的估值意味着市场对公司寄予了远超同行的期望，一旦这种乐观情绪消退，回调幅度往往更大。",
                "severity": "high" if ratio >= 3 else "medium",
                "dimension": "估值",
            })

    # 3. PB 高估
    if valuation.pb is not None:
        if valuation.pb_industry_avg is not None and valuation.pb > valuation.pb_industry_avg * 1.3:
            premium = (valuation.pb / valuation.pb_industry_avg - 1) * 100
            reasons.append({
                "conclusion": f"当前 PB {valuation.pb:.1f}，高于行业均值 {valuation.pb_industry_avg:.1f}",
                "data_support": f"同行业（{industry}）PB 均值 {valuation.pb_industry_avg:.1f}，{name} 溢价 {premium:.0f}%。",
                "impact": "市净率偏高暗示市场对公司资产质量给予了较高预期，若 ROE 不能匹配该溢价，股价存在回调风险。",
                "severity": "medium",
                "dimension": "估值",
            })
        if valuation.pb_percentile_5y is not None and valuation.pb_percentile_5y >= 85:
            reasons.append({
                "conclusion": f"当前 PB 处于近5年 {valuation.pb_percentile_5y:.0f}% 分位，接近历史高位",
                "data_support": f"近5年 PB 数据表明当前估值水平高于 {valuation.pb_percentile_5y:.0f}% 的历史交易日。",
                "impact": "PB 处于历史高位区域时，下跌风险大于上涨空间，历史规律表明均值回归是大概率事件。",
                "severity": "high" if valuation.pb_percentile_5y >= 95 else "medium",
                "dimension": "估值",
            })

    # 4. PS 估值参考
    if valuation.ps is not None and valuation.ps > 10:
        reasons.append({
            "conclusion": f"市销率(PS)为 {valuation.ps:.1f}，对于非成长型公司而言偏高",
            "data_support": f"PS > 10 通常适用于高增长、高毛利的科技公司，对于传统行业可能意味着估值泡沫。",
            "impact": "PS 过高表明市场为每一元营收支付了过高的溢价，一旦营收增长放缓，估值支撑将迅速瓦解。",
            "severity": "low",
            "dimension": "估值",
        })

    return reasons
