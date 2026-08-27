from typing import List
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.settings import SystemSettings, GeneralAnnouncement
from app.schemas.settings import SystemSettingsOut, SystemSettingsUpdate, AnnouncementOut, AnnouncementCreate
from app.core.security import require_mother_superior, get_current_user
from app.core.audit import record_audit_log

router = APIRouter(prefix="/settings", tags=["Settings & Announcements"])

@router.get("", response_model=SystemSettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db)):
    stmt = select(SystemSettings).limit(1)
    res = await db.execute(stmt)
    settings_obj = res.scalar_one_or_none()
    if not settings_obj:
        settings_obj = SystemSettings()
        db.add(settings_obj)
        await db.commit()
        await db.refresh(settings_obj)
    return settings_obj

@router.put("", response_model=SystemSettingsOut)
async def update_settings(
    payload: SystemSettingsUpdate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SystemSettings).limit(1)
    res = await db.execute(stmt)
    settings_obj = res.scalar_one_or_none()
    if not settings_obj:
        settings_obj = SystemSettings()
        db.add(settings_obj)

    data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    for field, val in data.items():
        if val is not None:
            setattr(settings_obj, field, val)

    settings_obj.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await record_audit_log(
        db,
        action="UPDATE_SYSTEM_SETTINGS",
        target_entity="SYSTEM_SETTINGS",
        target_entity_id=settings_obj.id,
        user=current_user,
        details=payload.dict(exclude_unset=True)
    )

    await db.commit()
    await db.refresh(settings_obj)
    return settings_obj

@router.get("/announcements", response_model=List[AnnouncementOut])
async def list_announcements(db: AsyncSession = Depends(get_db)):
    stmt = select(GeneralAnnouncement).where(GeneralAnnouncement.is_active == True).order_by(GeneralAnnouncement.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/announcements", response_model=AnnouncementOut)
async def create_announcement(
    payload: AnnouncementCreate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    ann = GeneralAnnouncement(
        title=payload.title,
        content=payload.content,
        target_audience=payload.target_audience,
        is_active=payload.is_active,
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann
