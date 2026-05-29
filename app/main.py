import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import load_config
from .data.fallback import fetch_stock_data
from .engine.aggregator import generate_reasons, make_summary
from .ai.providers import build_ai_adapter


app = FastAPI(title="不买就不会赔", description="A股不值得买分析器", version="1.0.0")

_config = load_config()

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class AnalyzeRequest(BaseModel):
    symbol: str

class Reason(BaseModel):
    conclusion: str
    data_support: str
    impact: str
    severity: str
    dimension: str

class AnalyzeResponse(BaseModel):
    symbol: str
    stock_name: str
    reasons: list[Reason]
    summary: dict
    data: dict   # 原始数据: price, pe, pb, industry 等


@app.get("/")
async def index():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "不买就不会赔 API is running. Visit /docs for API documentation."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    symbol = req.symbol.strip()
    if not symbol.isdigit() or len(symbol) != 6:
        raise HTTPException(status_code=400, detail="请输入6位数字的A股代码")

    start = time.time()

    try:
        data, provider_name = fetch_stock_data(symbol, _config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据获取失败: {e}")

    # 先用规则引擎算一遍（兜底）
    rule_reasons = generate_reasons(data, target_count=10)

    ai_provider = None
    ai_error = None
    reasons = rule_reasons

    try:
        adapter, warning = build_ai_adapter(_config)
        if warning:
            ai_error = warning
        if adapter and adapter.is_available():
            # LLM 直接生成 10 条理由
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

    return AnalyzeResponse(
        symbol=symbol,
        stock_name=data.info.name or symbol,
        reasons=[Reason(**r) for r in reasons],
        summary=summary,
        data={
            "price": data.technical.price,
            "pe": data.valuation.pe,
            "pb": data.valuation.pb,
            "industry": data.info.industry or "",
            "ma_20": data.technical.ma_20,
            "ma_60": data.technical.ma_60,
            "ma_200": data.technical.ma_200,
            "rsi_14": data.technical.rsi_14,
            "roe_trend": data.financial.roe_trend,
            "debt_ratio": data.financial.debt_ratio,
        },
    )
