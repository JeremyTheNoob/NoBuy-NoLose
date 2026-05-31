"""License 验证 + 试用计数"""

import os
import json
import time
import hashlib
import hmac
from pathlib import Path

# ====== 私钥（分发时混淆处理） ======
_SECRET = b"nbl-888-premium-2026-secret-key-v2"
# =====================================

TRIAL_FILE = Path(__file__).parent.parent / "data" / ".trial"
LICENSE_PATHS = [
    Path(__file__).parent.parent / "data" / "license.key",
    Path.home() / ".nbl_license",
]
TRIAL_LIMIT = 3


def get_machine_id() -> str:
    """本机标识"""
    import uuid, socket, platform
    parts = []
    try:
        parts.append(f"mac:{uuid.getnode()}")
    except Exception:
        pass
    try:
        parts.append(f"host:{socket.gethostname()}")
    except Exception:
        pass
    try:
        parts.append(f"os:{platform.system()}-{platform.release()}")
    except Exception:
        pass
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def generate_license(machine_id: str) -> str:
    """生成 License Key（卖方工具调用）"""
    sig = hmac.new(_SECRET, machine_id.encode(), hashlib.sha256).hexdigest()[:12]
    return f"NB-{machine_id[:4]}-{sig}".upper()


def validate_license(key: str) -> bool:
    """验证 License 是否有效"""
    if not key or not key.startswith("NB-"):
        return False
    try:
        parts = key.split("-")
        fp_prefix = parts[1].lower()
        sig = parts[2].lower()
    except Exception:
        return False

    mid = get_machine_id()
    if not mid.startswith(fp_prefix):
        return False
    expected = hmac.new(_SECRET, mid.encode(), hashlib.sha256).hexdigest()[:12]
    return sig == expected


def load_license() -> str | None:
    """读取 License 文件"""
    for p in LICENSE_PATHS:
        if p.exists():
            key = p.read_text().strip()
            if validate_license(key):
                return key
    return None


def _sign_counter(count: int) -> str:
    return hmac.new(_SECRET, f"trial-{count}".encode(), hashlib.sha256).hexdigest()[:8]


def get_trial_count() -> int:
    """读取已用试用次数"""
    if not TRIAL_FILE.exists():
        return 0
    try:
        data = json.loads(TRIAL_FILE.read_text())
        count = data.get("count", 0)
        sig = data.get("sig", "")
        if _sign_counter(count) == sig:
            return count
    except Exception:
        pass
    return 0


def increment_trial() -> int:
    """试用+1，返回当前次数"""
    count = get_trial_count() + 1
    TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    sig = _sign_counter(count)
    TRIAL_FILE.write_text(json.dumps({"count": count, "sig": sig, "ts": time.time()}))
    return count


def check_access() -> dict:
    """
    检查访问权限。返回:
        {"allowed": True/False, "trial": int, "remaining": int, "reason": str}
    """
    # 1. 是否有有效 License？
    if load_license():
        return {"allowed": True, "trial": 0, "remaining": -1, "reason": "licensed"}

    # 2. 试用计数
    used = get_trial_count()
    remaining = TRIAL_LIMIT - used
    if remaining > 0:
        return {"allowed": True, "trial": used, "remaining": remaining, "reason": "trial"}

    return {"allowed": False, "trial": used, "remaining": 0, "reason": "trial_exhausted"}
