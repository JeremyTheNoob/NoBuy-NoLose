"""版本检测与自动更新"""

import subprocess
import json
from pathlib import Path
import httpx

CURRENT_VERSION = "1.1.0"
GITHUB_API = "https://api.github.com/repos/JeremyTheNoob/NoBuy-NoLose/releases/latest"
GITHUB_RELEASES = "https://github.com/JeremyTheNoob/NoBuy-NoLose/releases"

PROJECT_DIR = Path(__file__).parent.parent


def check_update() -> dict:
    """检查是否有新版本"""
    try:
        resp = httpx.get(GITHUB_API, timeout=10, headers={"Accept": "application/vnd.github+json"})
        if resp.status_code != 200:
            return {"current": CURRENT_VERSION, "latest": None, "has_update": False, "error": "无法连接 GitHub"}
        release = resp.json()
        latest = release.get("tag_name", "").lstrip("v")
        has_update = _compare_versions(latest, CURRENT_VERSION) > 0
        return {
            "current": CURRENT_VERSION,
            "latest": latest,
            "has_update": has_update,
            "release_url": release.get("html_url", GITHUB_RELEASES),
            "release_notes": release.get("body", "")[:500] if has_update else "",
        }
    except Exception as e:
        return {"current": CURRENT_VERSION, "latest": None, "has_update": False, "error": str(e)}


def perform_update() -> dict:
    """执行 git pull 更新"""
    if not (PROJECT_DIR / ".git").exists():
        return {"ok": False, "error": "未检测到 Git 仓库，请手动下载新版本: " + GITHUB_RELEASES}

    try:
        # fetch
        subprocess.run(
            ["git", "fetch", "origin", "--tags"],
            cwd=str(PROJECT_DIR), capture_output=True, timeout=30,
        )
        # get latest tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", "origin/master"],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=15,
        )
        latest_tag = result.stdout.strip().lstrip("v")

        if _compare_versions(latest_tag, CURRENT_VERSION) <= 0:
            return {"ok": True, "message": f"已是最新版本 {CURRENT_VERSION}"}

        # pull
        result = subprocess.run(
            ["git", "pull", "origin", "master", "--ff-only"],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return {"ok": False, "error": f"更新失败: {result.stderr.strip()}"}

        # reinstall dependencies
        pip_result = subprocess.run(
            ["pip", "install", "-r", "requirements.txt", "-q"],
            cwd=str(PROJECT_DIR), capture_output=True, text=True, timeout=120,
        )

        return {"ok": True, "message": f"已更新到 {latest_tag}，请重启服务"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "更新超时，请检查网络后重试"}
    except Exception as e:
        return {"ok": False, "error": f"更新异常: {e}"}


def _compare_versions(a: str, b: str) -> int:
    """比较版本号，a > b 返回 1，a == b 返回 0，a < b 返回 -1"""
    try:
        parts_a = [int(x) for x in a.split(".")]
        parts_b = [int(x) for x in b.split(".")]
        for pa, pb in zip(parts_a, parts_b):
            if pa > pb: return 1
            if pa < pb: return -1
        return 1 if len(parts_a) > len(parts_b) else (-1 if len(parts_a) < len(parts_b) else 0)
    except Exception:
        return 0
