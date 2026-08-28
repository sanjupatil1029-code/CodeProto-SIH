import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User
from app.schemas.notification import NotificationFeedResponse, NotificationOut
from app.services.auth_service import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notification System"])


@router.get("/feed", response_model=NotificationFeedResponse)
async def get_notification_feed(
    unread_only: bool = Query(False, description="Filter unread notifications only"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 16: Retrieve in-app notification feed for current user.
    """
    return await NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only
    )


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 16: Mark a specific notification as read.
    """
    return await NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )


@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 16: Mark all unread notifications as read for current user.
    """
    count = await NotificationService.mark_all_read(db=db, user_id=current_user.id)
    return {"status": "success", "marked_read_count": count}
