"""AI 适配器基类 + Prompt 模板"""

from abc import ABC, abstractmethod
from ..data.provider import StockData


class AIAdapter(ABC):
    """AI 服务适配器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def generate(self, data: StockData) -> list[dict]:
        """
        直接由 LLM 生成 10 条理由，返回结构化列表。
        每项包含: conclusion, data_support, impact, severity, dimension
        """
        ...

    def enhance(self, reasons: list[dict], stock_name: str, symbol: str) -> tuple[list[dict], str | None]:
        """（保留兼容）润色已有理由，返回 (reasons, error)"""
        return reasons, None


def build_analysis_prompt(data: StockData) -> str:
    """将 StockData 全部字段格式化为 LLM prompt"""

    name = data.info.name or data.info.symbol
    industry = data.info.industry or "未知"

    lines = [
        f"你是专业的A股投资分析师。请基于以下数据，针对 {name}（{data.info.symbol}，{industry}行业），",
        f"生成 10 条「不值得购买」的理由。每条理由需包含 conclusion（结论）、data_support（数据支撑）、impact（影响解读）、severity（严重程度：high/medium/low）、dimension（维度：估值/财务质量/技术面/风险事件/综合）。",
        f"",
        f"## 基本信息",
        f"- 股票: {name} ({data.info.symbol})",
        f"- 行业: {industry}",
        f"",
        f"## 行情数据",
    ]

    v = data.valuation
    if v.pe or v.pb:
        lines.append(f"- 最新 PE(TTM): {v.pe or '无'}")
        lines.append(f"- 最新 PB: {v.pb or '无'}")
        lines.append(f"- PE 近5年分位: {v.pe_percentile_5y or '无'}%")
        lines.append(f"- PB 近5年分位: {v.pb_percentile_5y or '无'}%")
        lines.append(f"- 行业 PE 均值: {v.pe_industry_avg or '无'}")
        lines.append(f"- 行业 PB 均值: {v.pb_industry_avg or '无'}")

    t = data.technical
    lines.append(f"")
    lines.append(f"## 技术指标")
    if t.price:
        lines.append(f"- 最新价: {t.price}")
    if t.ma_20 or t.ma_60 or t.ma_200:
        lines.append(f"- MA20: {t.ma_20 or '无'}, MA60: {t.ma_60 or '无'}, MA200: {t.ma_200 or '无'}")
    if t.macd_dif is not None:
        lines.append(f"- MACD DIF: {t.macd_dif:.4f}, DEA: {t.macd_dea:.4f}")
    if t.rsi_14:
        lines.append(f"- RSI(14): {t.rsi_14}")

    f = data.financial
    if f.roe_trend or f.debt_ratio:
        lines.append(f"")
        lines.append(f"## 财务数据")
        if f.roe_trend:
            trend = " → ".join(f"{x:.1f}%" for x in f.roe_trend)
            lines.append(f"- ROE 趋势（近{len(f.roe_trend)}年）: {trend}")
        if f.debt_ratio:
            lines.append(f"- 资产负债率: {f.debt_ratio:.1f}%")
        if f.revenue_growth_trend:
            trend = " → ".join(f"{x:.1f}%" for x in f.revenue_growth_trend)
            lines.append(f"- 营收增速趋势: {trend}")
        if f.operating_cf_trend:
            trend = " → ".join(f"{x:.1f}亿" for x in f.operating_cf_trend)
            lines.append(f"- 经营现金流: {trend}")

    r = data.risk
    if r.pledge_ratio or r.insider_sells_3m or r.regulatory_inquiries_12m:
        lines.append(f"")
        lines.append(f"## 风险数据")
        if r.pledge_ratio:
            lines.append(f"- 股权质押比例: {r.pledge_ratio:.1f}%")
        if r.insider_sells_3m:
            lines.append(f"- 近3月高管减持 {len(r.insider_sells_3m)} 笔")
        if r.regulatory_inquiries_12m:
            lines.append(f"- 近12月交易所问询: {r.regulatory_inquiries_12m} 次")

    lines.extend([
        "",
        "## 要求",
        "1. 生成恰好 10 条理由，覆盖估值、财务质量、技术面、风险事件四个维度",
        "2. 每条理由详实有据，包含具体数字",
        "3. 严重程度 (severity) 合理分布: 3-4条high, 3-4条medium, 2-4条low",
        "4. 如果某维度数据缺失，从其他维度补足，确保始终有10条",
        "5. 使用中文，语言流畅自然",
        "",
        "输出严格的 JSON 数组格式（不要markdown代码块）：",
        '[{"conclusion":"...","data_support":"...","impact":"...","severity":"high","dimension":"估值"}, ...]',
    ])

    return "\n".join(lines)


def build_prompt(reasons: list[dict], stock_name: str, symbol: str) -> str:
    """（保留兼容）润色已有理由的 prompt"""
    lines = [
        f"你是专业的A股投资分析师。请针对股票 {stock_name}({symbol}) 的分析结果进行润色和深化。",
        "",
        f"以下是规则引擎生成的 {len(reasons)} 条\"不值得购买\"理由：",
    ]
    for i, r in enumerate(reasons, 1):
        lines.append(f"{i}. [{r['dimension']}] {r['conclusion']}")
        lines.append(f"   数据支撑: {r['data_support']}")
        lines.append(f"   影响解读: {r['impact']}")
    lines.extend([
        "",
        "请对每条理由做以下处理（保持 JSON 数组格式输出）：",
        "1. 让语言更流畅、更自然",
        "2. 补充相关背景知识",
        "3. 保持 severity 和 dimension 字段不变",
        "",
        '输出格式: [{"conclusion": "...", "data_support": "...", "impact": "...", "severity": "high/medium/low", "dimension": "..."}]',
    ])
    return "\n".join(lines)
