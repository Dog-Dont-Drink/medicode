"""Dependencies shared across API endpoints."""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

import jwt as pyjwt

from app.core.config import get_settings
from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import decode_token
from app.db.database import get_db
from app.db.models.user import User
from sqlalchemy import select

settings = get_settings()


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header, return User."""

    if not authorization.startswith("Bearer "):
        raise Unauthorized("无效的 Authorization 头")

    token = authorization[7:]

    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        raise Unauthorized("Token 已过期")
    except pyjwt.PyJWTError:
        raise Unauthorized("无效的 Token")

    if payload.get("type") != "access":
        raise Unauthorized("无效的 Token 类型")

    user_id = payload.get("sub")
    if not user_id:
        raise Unauthorized("无效的 Token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise Unauthorized("用户不存在")
    if not user.is_active:
        raise Unauthorized("账号已禁用")

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure current user is an administrator."""
    if current_user.role != "admin":
        raise Forbidden("仅管理员可访问后台")
    return current_user
