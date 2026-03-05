"""Payment-related request and response schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    packageId: str = Field(min_length=1)


class PaymentCreateResponse(BaseModel):
    orderId: str
    qrCodeUrl: str
    totalAmount: str
    expireTime: str


class PaymentStatusResponse(BaseModel):
    orderId: str
    status: str
    paidAt: str | None = None
    tokensAdded: int | None = None


class OrderRecord(BaseModel):
    orderId: str
    packageName: str
    amount: float
    tokens: int
    status: str
    createdAt: str
    paidAt: str | None = None


class PaymentPackage(BaseModel):
    id: str
    name: str
    price: float
    tokens: int
    unitPrice: str
    badge: str
    features: list[str]
