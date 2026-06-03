"""服务管理：数据仓库、每日更新调度器、数据库状态"""

import os
import sqlite3
import subprocess
import zipfile
import httpx
import time
from pathlib import Path

WAREHOUSE_DIR = Path(__file__).parent.parent / "data" / "warehouse"
HEALTH_URL = "http://127.0.0.1:8001/health"

_proc: subprocess.Popen | None = None
_scheduler_proc: subprocess.Popen | None = None


def get_status() -> dict:
    """返回数据仓库状态"""
    installed = (WAREHOUSE_DIR / "start.sh").exists()

    if not installed:
        return {"status": "not_installed", "installed": False, "running": False}

    running = _check_health()
    return {"status": "running" if running else "stopped", "installed": True, "running": running}


def _check_health() -> bool:
    try:
        resp = httpx.get(HEALTH_URL, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def install(license_key: str, download_url: str, progress_callback=None) -> dict:
    """下载并安装数据仓库"""
    if not download_url:
        return {"ok": False, "error": "下载地址未配置"}

    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    zip_path = WAREHOUSE_DIR / "warehouse.zip"

    try:
        # 下载
        if progress_callback:
            progress_callback("downloading", "正在下载数据仓库...")

        with httpx.stream(
            "GET", download_url,
            headers={"X-License-Key": license_key},
            timeout=600, follow_redirects=True,
        ) as resp:
            if resp.status_code != 200:
                return {"ok": False, "error": f"下载失败 (HTTP {resp.status_code})，请检查 License Key"}
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_bytes(65536):
                    f.write(chunk)

        # 解压
        if progress_callback:
            progress_callback("extracting", "正在解压...")

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(WAREHOUSE_DIR)

        zip_path.unlink()

        # 启动
        if progress_callback:
            progress_callback("starting", "正在启动数据仓库服务...")

        result = start()
        if result["ok"]:
            return {"ok": True, "message": "安装完成，数据仓库已启动"}
        else:
            return {"ok": True, "message": "安装完成，但启动失败: " + result.get("error", "未知错误")}

    except Exception as e:
        return {"ok": False, "error": f"安装失败: {e}"}


def start() -> dict:
    """启动数据仓库服务"""
    global _proc

    if _check_health():
        return {"ok": True, "message": "数据仓库已在运行"}

    start_script = WAREHOUSE_DIR / "start.sh"
    if not start_script.exists():
        return {"ok": False, "error": "数据仓库未安装"}

    try:
        _proc = subprocess.Popen(
            ["bash", str(start_script)],
            cwd=str(WAREHOUSE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # 等它启动
        for _ in range(30):
            time.sleep(0.5)
            if _check_health():
                return {"ok": True, "message": "数据仓库已启动"}
        return {"ok": True, "message": "数据仓库正在启动中，请稍后刷新"}
    except Exception as e:
        return {"ok": False, "error": f"启动失败: {e}"}


def stop() -> dict:
    """停止数据仓库服务"""
    global _proc
    if _proc and _proc.poll() is None:
        _proc.terminate()
        try:
            _proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _proc.kill()
        _proc = None
        return {"ok": True, "message": "数据仓库已停止"}
    return {"ok": True, "message": "数据仓库未在运行"}


# ====== 每日更新调度器 ======

def _scheduler_script() -> Path | None:
    """找到调度器脚本路径"""
    candidates = [
        WAREHOUSE_DIR / "scripts" / "scheduler.py",
        Path("/Users/liuweihua/Downloads/stock-data-api/scripts/scheduler.py"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def scheduler_status() -> dict:
    """调度器状态"""
    global _scheduler_proc
    running = _scheduler_proc is not None and _scheduler_proc.poll() is None
    installed = _scheduler_script() is not None
    return {"running": running, "installed": installed}


def scheduler_start() -> dict:
    """启动每日更新调度器"""
    global _scheduler_proc

    if _scheduler_proc and _scheduler_proc.poll() is None:
        return {"ok": True, "message": "调度器已在运行"}

    script = _scheduler_script()
    if not script:
        return {"ok": False, "error": "调度器脚本未找到"}

    try:
        _scheduler_proc = subprocess.Popen(
            ["python3", str(script)],
            cwd=str(script.parent.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"ok": True, "message": "调度器已启动（每日凌晨2:00更新）"}
    except Exception as e:
        return {"ok": False, "error": f"启动失败: {e}"}


def scheduler_stop() -> dict:
    """停止调度器"""
    global _scheduler_proc
    if _scheduler_proc and _scheduler_proc.poll() is None:
        _scheduler_proc.terminate()
        try:
            _scheduler_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _scheduler_proc.kill()
        _scheduler_proc = None
        return {"ok": True, "message": "调度器已停止"}
    return {"ok": True, "message": "调度器未在运行"}


# ====== 数据库状态 ======

def _db_paths() -> list[Path]:
    """找到所有可能的数据库路径"""
    paths = []
    candidates = [
        WAREHOUSE_DIR / "data" / "stock.db",
        Path("/Users/liuweihua/Downloads/stock-data-api/data/stock.db"),
    ]
    for p in candidates:
        if p.exists():
            paths.append(p)
    return paths


def db_status() -> dict:
    """数据库状态"""
    paths = _db_paths()
    if not paths:
        return {"available": False}

    db_path = str(paths[0])
    try:
        conn = sqlite3.connect(db_path)
        stocks = conn.execute("SELECT COUNT(*) FROM stocks").fetchone()[0]
        latest = conn.execute(
            "SELECT MAX(date) FROM daily_prices WHERE date != 'date'"
        ).fetchone()[0]
        conn.close()
        return {
            "available": True,
            "stocks": stocks,
            "latest_date": latest,
        }
    except Exception:
        return {"available": False}


# ====== 统一服务状态 ======

def all_services_status() -> dict:
    """返回所有服务状态，供前端仪表盘使用"""
    wh = get_status()
    sch = scheduler_status()
    db = db_status()

    # 判断哪些需要启动
    need_action = []
    if wh["installed"] and not wh["running"]:
        need_action.append("warehouse")
    if sch["installed"] and not sch["running"]:
        need_action.append("scheduler")

    all_running = not need_action

    return {
        "services": {
            "analyzer": {"name": "分析引擎", "running": True, "port": 8000, "detail": "localhost:8000"},
            "warehouse": {"name": "数据仓库", "running": wh["running"], "installed": wh["installed"], "port": 8001, "detail": "全量 A 股数据 API"},
            "scheduler": {"name": "每日更新", "running": sch["running"], "installed": sch["installed"], "detail": "凌晨 2:00 自动更新" if sch["running"] else "未启动"},
            "database": {"name": "数据库", "available": db["available"], "detail": f"{db.get('stocks', 0)} 只股票, 最新 {db.get('latest_date', 'N/A')}" if db["available"] else "未检测到"},
        },
        "all_running": all_running,
        "need_action": need_action,
    }


def start_all() -> dict:
    """一键启动所有服务"""
    results = {"started": [], "failed": [], "already": []}

    # 数据仓库
    wh = get_status()
    if wh["installed"]:
        if not wh["running"]:
            r = start()
            if r["ok"]:
                results["started"].append("warehouse")
            else:
                results["failed"].append({"service": "warehouse", "error": r.get("error", "")})
        else:
            results["already"].append("warehouse")

    # 调度器
    sch = scheduler_status()
    if sch["installed"]:
        if not sch["running"]:
            r = scheduler_start()
            if r["ok"]:
                results["started"].append("scheduler")
            else:
                results["failed"].append({"service": "scheduler", "error": r.get("error", "")})
        else:
            results["already"].append("scheduler")

    return results
