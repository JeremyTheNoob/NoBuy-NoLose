#!/usr/bin/env python3
"""A股不值得买分析器 - CLI 入口

用法: python analyze.py 000001
"""

import sys
import time
from app.config import load_config
from app.data.fallback import fetch_stock_data
from app.engine.aggregator import generate_reasons, make_summary
from app.ai.providers import build_ai_adapter


SEVERITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}
SEVERITY_LABELS = {"high": "高风险", "medium": "中等风险", "low": "低风险"}


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze.py <股票代码>")
        print("示例: python analyze.py 000001")
        sys.exit(1)

    symbol = sys.argv[1].strip()
    if not symbol.isdigit() or len(symbol) != 6:
        print("错误: 请输入6位数字的A股代码")
        sys.exit(1)

    print(f"\n🔍 正在分析 {symbol} ...\n")

    config = load_config()
    start = time.time()

    try:
        data, provider_name = fetch_stock_data(symbol, config)
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        sys.exit(1)

    reasons = generate_reasons(data, target_count=10)

    ai_provider = None
    ai_error = None
    try:
        adapter, warning = build_ai_adapter(config)
        if warning:
            ai_error = warning
        if adapter and adapter.is_available():
            print("🤖 正在使用 AI 生成分析结果...\n")
            llm_reasons = adapter.generate(data)
            if llm_reasons and len(llm_reasons) >= 3:
                reasons = llm_reasons
                ai_provider = adapter.name
            else:
                ai_error = "AI 未生成足够理由，使用规则引擎结果"
                ai_provider = adapter.name
    except Exception as e:
        ai_error = f"AI 调用异常: {e}"

    elapsed = time.time() - start
    summary = make_summary(reasons, elapsed, provider_name, ai_provider, ai_error)

    # 输出
    stock_display = f"{data.info.name}({symbol})" if data.info.name else symbol
    print(f"{'='*60}")
    print(f"  {stock_display} — 不值得买的 {len(reasons)} 个理由")
    print(f"{'='*60}\n")

    for i, r in enumerate(reasons, 1):
        icon = SEVERITY_ICONS.get(r["severity"], "⚪")
        label = SEVERITY_LABELS.get(r["severity"], "未知")
        print(f"{icon} {r['dimension']} | {r['conclusion']}")
        print(f"  数据支撑: {r['data_support']}")
        print(f"  影响解读: {r['impact']}")
        print(f"  严重程度: {label}\n")

    print(f"{'='*60}")
    print(f"💡 总结: 高风险 {summary['high']} 条，中等风险 {summary['medium']} 条，低风险 {summary['low']} 条")
    print(f"⏱ 分析耗时: {summary['elapsed_seconds']}s | 数据源: {summary['provider']} | AI: {summary['ai_provider']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
