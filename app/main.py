import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import load_config, save_config
from .data.fallback import fetch_stock_data
from .engine.aggregator import generate_reasons, make_summary
from .ai.providers import build_ai_adapter
from . import warehouse, version


app = FastAPI(title="不买就不会赔", description="A股不值得买分析器", version="1.0.0")

_config = load_config()


@app.on_event("startup")
def _on_startup():
    """启动时自动拉起数据仓库（如果已安装）"""
    try:
        status = warehouse.get_status()
        if status["installed"] and not status["running"]:
            warehouse.start()
    except Exception:
        pass


def _reload_config() -> None:
    global _config
    _config = load_config()


def _config_configured() -> bool:
    cfg = _config
    tushare_ok = bool(cfg.data.tushare.token)
    custom_api_ok = bool(cfg.data.custom_api.url and cfg.data.custom_api.api_key)
    data_ok = tushare_ok or custom_api_ok

    ai = cfg.ai
    provider = ai.provider
    ai_ok = False
    if provider and provider != "none":
        if provider == "ollama":
            ai_ok = True
        elif provider == "custom":
            ai_ok = bool(ai.custom.api_key and ai.custom.base_url)
        else:
            prov_cfg = getattr(ai, provider, None)
            ai_ok = bool(prov_cfg and prov_cfg.api_key)
    return data_ok and ai_ok


def _mask_value(v: str) -> str:
    if not v:
        return ""
    if len(v) > 8:
        return v[:4] + "*" * 8 + v[-4:]
    return "*" * 8

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

class SetupRequest(BaseModel):
    data_source: str = "tushare"  # "tushare" or "custom_api"
    tushare_token: str = ""
    custom_api_url: str = "http://localhost:8001"
    custom_api_key: str = ""
    ai_provider: str = "none"
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    host: str = "http://localhost:11434"


@app.get("/")
async def index():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "不买就不会赔 API is running. Visit /docs for API documentation."}


@app.get("/health")
def health():
    return {"status": "ok", "version": version.CURRENT_VERSION}


@app.get("/api/version")
def get_version():
    return version.check_update()


@app.post("/api/update")
def do_update():
    result = version.perform_update()
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/config")
def get_config():
    cfg = _config
    raw = cfg.model_dump(mode="python")

    # mask secrets
    if raw.get("data", {}).get("tushare", {}).get("token"):
        raw["data"]["tushare"]["token"] = _mask_value(cfg.data.tushare.token)
    if raw.get("data", {}).get("custom_api", {}).get("api_key"):
        raw["data"]["custom_api"]["api_key"] = _mask_value(cfg.data.custom_api.api_key)
    for key in ("deepseek", "qwen", "zhipu", "moonshot", "openai", "custom"):
        prov = getattr(cfg.ai, key, None)
        if prov and prov.api_key:
            raw["ai"][key]["api_key"] = _mask_value(prov.api_key)

    return {"configured": _config_configured(), "config": raw}


@app.post("/api/config")
def save_setup(req: SetupRequest):
    cfg = _config

    if req.data_source == "custom_api":
        if req.custom_api_key and "****" not in req.custom_api_key:
            cfg.data.custom_api.api_key = req.custom_api_key
        if req.custom_api_url:
            cfg.data.custom_api.url = req.custom_api_url
        cfg.data.tushare.token = ""
    else:
        if req.tushare_token and "****" not in req.tushare_token:
            cfg.data.tushare.token = req.tushare_token
        cfg.data.custom_api.api_key = ""

    cfg.ai.provider = req.ai_provider

    if req.ai_provider == "ollama":
        if req.host:
            cfg.ai.ollama.host = req.host
        if req.model:
            cfg.ai.ollama.model = req.model
    elif req.ai_provider == "custom":
        if req.api_key and "****" not in req.api_key:
            cfg.ai.custom.api_key = req.api_key
        if req.model:
            cfg.ai.custom.model = req.model
        if req.base_url:
            cfg.ai.custom.base_url = req.base_url
    elif req.ai_provider in ("deepseek", "qwen", "zhipu", "moonshot", "openai"):
        prov = getattr(cfg.ai, req.ai_provider)
        if req.api_key and "****" not in req.api_key:
            prov.api_key = req.api_key
        if req.model:
            prov.model = req.model
        if req.base_url:
            prov.base_url = req.base_url

    try:
        save_config(cfg)
        _reload_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")

    return {"status": "ok", "message": "配置已保存"}


@app.get("/api/services")
def services_status():
    return warehouse.all_services_status()


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
