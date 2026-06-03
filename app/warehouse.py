"""云端数据仓库连接状态检查"""

import httpx
from pathlib import Path
from .config import load_config


def check_cloud_health() -> dict:
    """检查云端数据仓库是否可达"""
    config = load_config()
    url = config.data.custom_api.url.rstrip("/")
    api_key = config.data.custom_api.api_key

    if not api_key:
        return {"reachable": False, "detail": "未配置"}

    try:
        resp = httpx.get(
            f"{url}/health",
            headers={"X-API-Key": api_key},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "reachable": True,
                "detail": data.get("time", "connected"),
                "license": data.get("license", "unknown"),
            }
        return {"reachable": False, "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"reachable": False, "detail": "无法连接"}


def all_services_status() -> dict:
    """返回所有服务状态，供前端仪表盘使用"""
    config = load_config()
    cloud_ok = False
    cloud_detail = "未配置"

    if config.data.custom_api.api_key:
        health = check_cloud_health()
        cloud_ok = health["reachable"]
        cloud_detail = health["detail"]

    api_url = config.data.custom_api.url.rstrip("/") if config.data.custom_api.api_key else ""

    return {
        "services": {
            "analyzer": {
                "name": "分析引擎", "running": True,
                "detail": "localhost:8000",
            },
            "warehouse": {
                "name": "数据仓库", "running": cloud_ok,
                "installed": bool(config.data.custom_api.api_key),
                "detail": api_url if cloud_ok else cloud_detail,
            },
            "database": {
                "name": "数据源", "available": cloud_ok,
                "detail": config.data.tushare.token and "Tushare" or (api_url and "云端数据仓库" or "免费数据源"),
                "hint": None if (api_url and cloud_ok) else True,
            },
        },
        "all_running": cloud_ok,
        "need_action": [] if cloud_ok else (["warehouse"] if config.data.custom_api.api_key else []),
    }
