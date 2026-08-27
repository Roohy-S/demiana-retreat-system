from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.notification import CommunicationLog
from app.schemas.notification import CommunicationSend, CommunicationLogOut
from app.core.security import require_staff
from app.core.whatsapp_bridge import dispatch_whatsapp_message, WHATSAPP_TEMPLATES

router = APIRouter(prefix="/communication", tags=["WhatsApp & Communication"])

@router.get("/templates")
async def get_message_templates(current_user: User = Depends(require_staff)):
    return {
        "templates": [
            {"key": k, "text": v} for k, v in WHATSAPP_TEMPLATES.items()
        ]
    }

@router.post("/send-whatsapp")
async def send_whatsapp_to_applicant(
    payload: CommunicationSend,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Profile).where(Profile.id == payload.profile_id)
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="الملف الشخصي للمتقدمة غير موجود")

    result = await dispatch_whatsapp_message(
        db=db,
        profile=profile,
        admin_user=current_user,
        template_name=payload.template_name,
        custom_message=payload.custom_message
    )
    await db.commit()
    return result

@router.get("/logs/{profile_id}", response_model=List[CommunicationLogOut])
async def get_profile_communication_logs(
    profile_id: str,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CommunicationLog).where(CommunicationLog.profile_id == profile_id).order_by(CommunicationLog.sent_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()
