"""Minimal Alipay precreate smoke test using the current backend .env."""
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.services.alipay_service import run_precreate


async def main() -> int:
    settings = get_settings()
    order_id = str(uuid.uuid4())

    print(json.dumps({
        "sandbox": settings.ALIPAY_SANDBOX,
        "app_id": settings.ALIPAY_APP_ID,
        "notify_url": settings.ALIPAY_NOTIFY_URL,
        "order_id": order_id,
    }, ensure_ascii=False, indent=2))

    try:
        result = await run_precreate(
            out_trade_no=order_id,
            subject="MediCode 支付测试",
            total_amount="0.01",
            timeout_express="1m",
        )
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1

    print("SUCCESS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"QR_CODE={result.get('qr_code', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
