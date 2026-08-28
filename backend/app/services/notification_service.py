import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.notification import Notification, NotificationEventType, NotificationSeverity
from app.models.auth import User
from app.schemas.notification import NotificationFeedResponse, NotificationOut
from app.core.logging import logger


class NotificationService:
    """
    Module 16: Event-Based Notification Service.
    Handles in-app notification feed creation, event-based dispatching, read state tracking,
    and email delivery abstraction (console mock / SMTP ready).
    """

    @classmethod
    async def send_email_notification(cls, to_email: str, subject: str, body: str) -> bool:
        """
        Extensible Email Transport Abstraction.
        In development mode: logs formatted email payload.
        In production mode: connect to SMTP / SendGrid / AWS SES.
        """
        logger.info(f"[EMAIL ADAPTER DISPATCH] To: {to_email} | Subject: {subject} | Body Preview: {body[:100]}...")
        return True

    @classmethod
    async def create_notification(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: NotificationEventType,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        send_email: bool = True
    ) -> Notification:
        """Create and deliver an event-based notification for a user."""
        email_delivered = False
        
        if send_email:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalars().first()
            if user and user.email:
                email_delivered = await cls.send_email_notification(
                    to_email=user.email,
                    subject=f"[NIRVAAN Alert] {title}",
                    body=message
                )

        notif = Notification(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            is_read=False,
            email_sent=email_delivered
        )

        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        logger.info(f"Notification created for user {user_id}: '{title}' (Event: {event_type.value})")
        return notif

    @classmethod
    async def get_user_notifications(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        unread_only: bool = False
    ) -> NotificationFeedResponse:
        """Fetch notification feed for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc())
        res = await db.execute(query)
        notifications = list(res.scalars().all())

        # Count total & unread
        total_res = await db.execute(
            select(func.count(Notification.id)).where(Notification.user_id == user_id)
        )
        total_count = total_res.scalar() or 0

        unread_res = await db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        unread_count = unread_res.scalar() or 0

        items = [NotificationOut.model_validate(n) for n in notifications]

        return NotificationFeedResponse(
            total_count=total_count,
            unread_count=unread_count,
            notifications=items
        )

    @classmethod
    async def mark_as_read(
        cls,
        db: AsyncSession,
        notification_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> NotificationOut:
        """Mark a single notification as read."""
        res = await db.execute(
            select(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == user_id)
        )
        notif = res.scalars().first()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        notif.is_read = True
        notif.read_at = datetime.utcnow()
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        return NotificationOut.model_validate(notif)

    @classmethod
    async def mark_all_read(cls, db: AsyncSession, user_id: uuid.UUID) -> int:
        """Mark all unread notifications for a user as read."""
        now = datetime.utcnow()
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
            .values(is_read=True, read_at=now)
        )
        res = await db.execute(stmt)
        await db.commit()
        count = res.rowcount
        logger.info(f"Marked {count} notifications as read for user {user_id}.")
        return count
