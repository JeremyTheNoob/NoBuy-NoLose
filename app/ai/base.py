from abc import ABC, abstractmethod


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
    def enhance(self, reasons: list[dict], stock_name: str, symbol: str) -> list[dict]:
        """
        接收规则引擎生成的理由列表，返回润色/增强后的理由列表。
        保持原有结构 (conclusion, data_support, impact, severity, dimension)。
        """
        ...


def build_prompt(reasons: list[dict], stock_name: str, symbol: str) -> str:
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
        "1. 让语言更流畅、更自然，避免套话",
        "2. 补充你了解的相关背景知识或行业洞察",
        "3. 保持原有的 severity 和 dimension 字段不变",
        "4. 每条理由保持 conclusion / data_support / impact 三段式结构",
        "",
        '输出格式: [{"conclusion": "...", "data_support": "...", "impact": "...", "severity": "high/medium/low", "dimension": "估值/财务质量/技术面/风险事件/综合"}]',
    ])
    return "\n".join(lines)
