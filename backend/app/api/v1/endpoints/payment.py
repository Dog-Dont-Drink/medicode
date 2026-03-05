"""Payment API endpoints."""
from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.payment import (
    OrderRecord,
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentPackage,
    PaymentStatusResponse,
)
from app.services import payment_service

router = APIRouter(prefix="/payment", tags=["支付"])


@router.get("/packages", response_model=List[PaymentPackage])
async def get_payment_packages():
    """List token packages configured on the backend."""
    return [
        PaymentPackage(
            id=package.id,
            name=package.name,
            price=float(package.amount),
            tokens=package.tokens,
            unitPrice=package.unit_price,
            badge=package.badge,
            features=list(package.features),
        )
        for package in payment_service.list_packages()
    ]


@router.post("/precreate", response_model=PaymentCreateResponse)
async def create_payment_order(
    body: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an Alipay precreate order."""
    order = await payment_service.create_order(db, current_user, body)
    return PaymentCreateResponse(
        orderId=str(order.id),
        qrCodeUrl=order.qr_code_url or "",
        totalAmount=f"{order.amount:.2f}",
        expireTime=(order.expire_at.isoformat() if order.expire_at else ""),
    )


@router.get("/query/{order_id}", response_model=PaymentStatusResponse)
async def query_payment_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query the payment status for an order."""
    order = await payment_service.sync_order_status(db, current_user, order_id)
    return PaymentStatusResponse(
        orderId=str(order.id),
        status=order.status,
        paidAt=(order.paid_at.isoformat() if order.paid_at else None),
        tokensAdded=(order.tokens if order.status == "paid" else None),
    )


@router.get("/orders", response_model=List[OrderRecord])
async def get_payment_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's payment orders."""
    orders = await payment_service.list_orders(db, current_user)
    return [
        OrderRecord(
            orderId=str(order.id),
            packageName=order.package_name,
            amount=float(order.amount),
            tokens=order.tokens,
            status=order.status,
            createdAt=order.created_at.isoformat(),
            paidAt=(order.paid_at.isoformat() if order.paid_at else None),
        )
        for order in orders
    ]


@router.post("/notify")
async def alipay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive asynchronous Alipay payment notifications."""
    form = await request.form()
    payload: Dict[str, str] = {key: str(value) for key, value in form.items()}
    try:
        await payment_service.handle_notification(db, payload)
    except Exception:
        return PlainTextResponse("failure", status_code=400)
    return PlainTextResponse("success")
