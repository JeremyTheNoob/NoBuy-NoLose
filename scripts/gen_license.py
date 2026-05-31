#!/usr/bin/env python3
"""License 生成器 — 卖方工具

用法:
    python scripts/gen_license.py --fingerprint <用户机器指纹>

    生成 License Key，发送给用户。用户放入 data/license.key 即可。
"""

import sys
sys.path.insert(0, ".")
from app.license import generate_license, get_machine_id

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="生成 NoBuy-NoLose License Key")
    p.add_argument("--fingerprint", required=True, help="用户机器指纹（用户运行 python -m app.license 获取）")
    args = p.parse_args()

    key = generate_license(args.fingerprint)
    print()
    print(f"  License Key: {key}")
    print()
    print("  发送给用户，用户执行：")
    print(f"    echo '{key}' > data/license.key")
    print()
