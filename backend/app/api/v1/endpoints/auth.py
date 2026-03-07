"""Auth API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendCodeRequest,
    TokenResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from app.services import auth_service
from app.core.security import decode_token, create_access_token
from app.core.exceptions import Unauthorized, Forbidden
from app.db.models.user import User
from sqlalchemy import select
import jwt as pyjwt

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/send-code", response_model=MessageResponse)
async def send_code(body: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    """发送邮箱验证码"""
    result = await auth_service.send_code(db, body.email, body.purpose)
    return result


@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(body: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    """校验验证码"""
    await auth_service.verify_code(db, body.email, body.code, body.purpose)
    return {"verified": True}


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册（邮箱必须已通过验证）"""
    return await auth_service.register(db, body.name, body.email, body.password, body.code)


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    try:
        result = await auth_service.login(db, body.email, body.password)
        return result
    except Forbidden:
        # 邮箱未验证的特殊响应
        return {"error": "邮箱未验证", "need_verify": True, "email": body.email}


@router.post("/admin-login", response_model=TokenResponse)
async def admin_login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """管理员登录"""
    return await auth_service.admin_login(db, body.email, body.password)


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """重置密码"""
    await auth_service.reset_password(db, body.email, body.code, body.new_password)
    return {"success": True}


@router.post("/refresh-token")
async def refresh_token(body: RefreshTokenRequest):
    """刷新 Access Token"""
    try:
        payload = decode_token(body.refresh_token)
    except pyjwt.ExpiredSignatureError:
        raise Unauthorized("Refresh Token 已过期")
    except pyjwt.PyJWTError:
        raise Unauthorized("无效的 Refresh Token")

    if payload.get("type") != "refresh":
        raise Unauthorized("无效的 Token 类型")

    new_access = create_access_token(payload["sub"])
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """退出登录（客户端清除 token 即可）"""
    return {"message": "已退出"}
