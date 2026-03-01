"""User API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.user import (
    BalanceResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserProfile,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return UserProfile(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        title=current_user.title,
        institution=current_user.institution,
        research_field=current_user.research_field,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        token_balance=current_user.token_balance,
        subscription=current_user.subscription,
    )


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新个人信息"""
    updated = await user_service.update_profile(
        db, str(current_user.id), body.model_dump(exclude_unset=True)
    )
    return UserProfile(
        id=str(updated.id),
        name=updated.name,
        email=updated.email,
        phone=updated.phone,
        title=updated.title,
        institution=updated.institution,
        research_field=updated.research_field,
        bio=updated.bio,
        avatar_url=updated.avatar_url,
        token_balance=updated.token_balance,
        subscription=updated.subscription,
    )


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码（需邮箱验证码）"""
    await user_service.change_password(
        db,
        str(current_user.id),
        body.email,
        body.code,
        body.current_password,
        body.new_password,
    )
    return {"success": True}


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 Token 余额"""
    return await user_service.get_balance(db, str(current_user.id))
