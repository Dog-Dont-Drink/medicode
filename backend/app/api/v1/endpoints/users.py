"""User API endpoints."""

import os
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import BadRequest
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.user import (
    BalanceResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserProfile,
)
from app.services.resource_service import resource_fields
from app.services import user_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/users", tags=["用户"])

ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return UserProfile(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        title=current_user.title,
        institution=current_user.institution,
        research_field=current_user.research_field,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        **resource_fields(int(current_user.token_balance or 0)),
        subscription=current_user.subscription,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
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
        role=updated.role,
        phone=updated.phone,
        title=updated.title,
        institution=updated.institution,
        research_field=updated.research_field,
        bio=updated.bio,
        avatar_url=updated.avatar_url,
        **resource_fields(int(updated.token_balance or 0)),
        subscription=updated.subscription,
        is_verified=updated.is_verified,
        is_active=updated.is_active,
    )


@router.post("/avatar", response_model=UserProfile)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传用户头像"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise BadRequest("头像仅支持 JPG、PNG 或 WEBP 格式")

    content = await file.read()
    if not content:
        raise BadRequest("请选择要上传的头像文件")
    if len(content) > MAX_AVATAR_SIZE:
        raise BadRequest("头像大小不能超过 2MB")

    object_key = f"avatars/{current_user.id}/{uuid.uuid4()}{ext}"
    content_type = file.content_type or "application/octet-stream"

    await storage_service.upload(
        object_key=object_key,
        content=content,
        content_type=content_type,
    )

    old_object_key = storage_service.extract_object_key(current_user.avatar_url or "")
    public_url = await storage_service.get_public_url(object_key)

    try:
        updated = await user_service.update_profile(
            db,
            str(current_user.id),
            {"avatar_url": public_url},
        )
    except Exception:
        await storage_service.delete(object_key)
        raise

    if old_object_key and old_object_key != object_key:
        await storage_service.delete(old_object_key)

    return UserProfile(
        id=str(updated.id),
        name=updated.name,
        email=updated.email,
        role=updated.role,
        phone=updated.phone,
        title=updated.title,
        institution=updated.institution,
        research_field=updated.research_field,
        bio=updated.bio,
        avatar_url=updated.avatar_url,
        **resource_fields(int(updated.token_balance or 0)),
        subscription=updated.subscription,
        is_verified=updated.is_verified,
        is_active=updated.is_active,
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
    """获取资源余额"""
    return await user_service.get_balance(db, str(current_user.id))
