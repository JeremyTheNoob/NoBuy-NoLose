import uuid
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


app = FastAPI(title="Money-Tracing", description="A股不值得买分析器", version="1.0.0")

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


@app.get("/")
async def index():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Money-Tracing API is running. Visit /docs for API documentation."}


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

    reasons = generate_reasons(data, target_count=10)

    ai_provider = None
    try:
        adapter = build_ai_adapter(_config)
        if adapter and adapter.is_available():
            reasons = adapter.enhance(reasons, data.info.name or symbol, symbol)
            ai_provider = adapter.name
    except Exception:
        pass

    elapsed = time.time() - start
    summary = make_summary(reasons, elapsed, provider_name, ai_provider)

    return AnalyzeResponse(
        symbol=symbol,
        stock_name=data.info.name or symbol,
        reasons=[Reason(**r) for r in reasons],
        summary=summary,
    )
