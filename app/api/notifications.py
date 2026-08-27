from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationOut
from app.core.security import get_current_active_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationOut])
async def get_my_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(Notification.recipient_user_id == current_user.id).order_by(Notification.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.put("/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(
        Notification.id == notif_id,
        Notification.recipient_user_id == current_user.id
    )
    res = await db.execute(stmt)
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="الإشعار غير موجود")

    notif.is_read = True
    await db.commit()
    return {"message": "تم تحديد الإشعار كمقروء"}

@router.put("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(
        Notification.recipient_user_id == current_user.id,
        Notification.is_read == False
    )
    res = await db.execute(stmt)
    for n in res.scalars().all():
        n.is_read = True
    await db.commit()
    return {"message": "تم تحديد جميع الإشعارات كمقروءة"}
