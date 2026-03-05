"""Alipay face-to-face payment integration via the official Python SDK style."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Optional, Type, TypeVar

from Crypto.PublicKey import RSA
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
from alipay.aop.api.exception.Exception import AopException, RequestException, ResponseException
from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest
from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
from alipay.aop.api.response.AlipayResponse import AlipayResponse
from alipay.aop.api.response.AlipayTradePrecreateResponse import AlipayTradePrecreateResponse
from alipay.aop.api.response.AlipayTradeQueryResponse import AlipayTradeQueryResponse
from alipay.aop.api.util.SignatureUtils import get_sign_content, verify_with_rsa

from app.core.config import get_settings
from app.core.exceptions import BadRequest


ResponseT = TypeVar("ResponseT", bound=AlipayResponse)


@dataclass
class AlipayTradeStatus:
    status: str
    trade_no: Optional[str] = None
    total_amount: Optional[str] = None
    paid_at: Optional[str] = None


def _clean_key_material(key_text: str) -> str:
    return key_text.strip().strip('"').replace("\\n", "\n")


def _normalize_private_key(key_text: str) -> str:
    raw = _clean_key_material(key_text)
    candidates = [raw]
    if "BEGIN" not in raw:
        candidates.append(f"-----BEGIN PRIVATE KEY-----\n{raw}\n-----END PRIVATE KEY-----\n")
        candidates.append(f"-----BEGIN RSA PRIVATE KEY-----\n{raw}\n-----END RSA PRIVATE KEY-----\n")
    for candidate in candidates:
        try:
            key = RSA.import_key(candidate)
            pem = key.export_key(format="PEM", pkcs=1).decode("utf-8")
            return "".join(
                line.strip()
                for line in pem.splitlines()
                if line.strip() and "BEGIN " not in line and "END " not in line
            )
        except Exception:
            continue
    raise BadRequest("支付宝应用私钥格式不正确")


def _normalize_public_key(key_text: str) -> str:
    raw = _clean_key_material(key_text)
    candidates = [raw]
    if "BEGIN" not in raw:
        candidates.append(f"-----BEGIN PUBLIC KEY-----\n{raw}\n-----END PUBLIC KEY-----\n")
    for candidate in candidates:
        try:
            key = RSA.import_key(candidate)
            pem = key.public_key().export_key(format="PEM").decode("utf-8")
            return "".join(
                line.strip()
                for line in pem.splitlines()
                if line.strip() and "BEGIN " not in line and "END " not in line
            )
        except Exception:
            continue
    raise BadRequest("支付宝公钥格式不正确")


def _notify_url() -> Optional[str]:
    settings = get_settings()
    value = settings.ALIPAY_NOTIFY_URL.strip()
    if not value or "your-domain.com" in value:
        return None
    return value


@lru_cache
def _client() -> DefaultAlipayClient:
    settings = get_settings()
    if not settings.ALIPAY_APP_ID or not settings.ALIPAY_PRIVATE_KEY or not settings.ALIPAY_PUBLIC_KEY:
        raise BadRequest("支付宝配置未完成，请检查 APP_ID、私钥和支付宝公钥")

    config = AlipayClientConfig(sandbox_debug=settings.ALIPAY_SANDBOX)
    config.app_id = settings.ALIPAY_APP_ID.strip()
    config.sign_type = "RSA2"
    config.app_private_key = _normalize_private_key(settings.ALIPAY_PRIVATE_KEY)
    config.alipay_public_key = _normalize_public_key(settings.ALIPAY_PUBLIC_KEY)
    config.charset = "utf-8"
    config.format = "json"
    #config.server_url = "https://openapi.alipay.com/gateway.do"
    return DefaultAlipayClient(config)


def _parse_response(response_content: str, response_cls: Type[ResponseT]) -> ResponseT:
    response = response_cls()
    response.parse_response_content(response_content)
    if not response.is_success():
        raise BadRequest(response.sub_msg or response.msg or "支付宝接口调用失败")
    return response


async def _execute(request, response_cls: Type[ResponseT]) -> ResponseT:
    client = _client()
    try:
        loop = asyncio.get_running_loop()
        response_content = await loop.run_in_executor(None, client.execute, request)
    except (AopException, RequestException, ResponseException) as exc:
        raise BadRequest(str(exc) or "支付宝接口调用失败")
    except Exception as exc:
        raise BadRequest(f"支付宝接口调用失败: {exc}")
    return _parse_response(response_content, response_cls)


async def run_precreate(
    out_trade_no: str,
    subject: str,
    total_amount: str,
    timeout_express: str,
) -> Dict[str, str]:
    model = AlipayTradePrecreateModel()
    model.out_trade_no = out_trade_no
    model.subject = subject
    model.total_amount = total_amount
    model.timeout_express = timeout_express
    model.product_code = "FACE_TO_FACE_PAYMENT"

    request = AlipayTradePrecreateRequest()
    request.biz_model = model
    notify_url = _notify_url()
    if notify_url:
        request.notify_url = notify_url

    response = await _execute(request, AlipayTradePrecreateResponse)
    return {
        "out_trade_no": response.out_trade_no or out_trade_no,
        "qr_code": response.qr_code or "",
    }


async def query_trade(out_trade_no: str) -> AlipayTradeStatus:
    model = AlipayTradeQueryModel()
    model.out_trade_no = out_trade_no

    request = AlipayTradeQueryRequest()
    request.biz_model = model

    response = await _execute(request, AlipayTradeQueryResponse)
    return AlipayTradeStatus(
        status=response.trade_status or "",
        trade_no=response.trade_no,
        total_amount=response.total_amount,
        paid_at=response.send_pay_date,
    )


def verify_notification_signature(params: Dict[str, str]) -> bool:
    sign = params.get("sign")
    if not sign:
        return False

    unsigned_params = {
        key: value
        for key, value in params.items()
        if value not in (None, "") and key not in {"sign", "sign_type"}
    }
    sign_content = get_sign_content(unsigned_params)
    try:
        return bool(
            verify_with_rsa(
                _normalize_public_key(get_settings().ALIPAY_PUBLIC_KEY),
                sign_content.encode("utf-8"),
                sign,
            )
        )
    except Exception:
        return False
