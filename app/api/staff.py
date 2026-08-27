from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.schemas.auth import UserOut
from app.core.security import require_mother_superior, get_password_hash
from app.core.audit import record_audit_log

router = APIRouter(prefix="/staff", tags=["Staff & Supervisors Management"])

class StaffCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # BOOKING_SUPERVISOR, RECEPTION_SUPERVISOR, REPORT_SUPERVISOR, CUSTOM_STAFF

class StaffUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("", response_model=List[UserOut])
async def list_staff(
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.role.in_(list(UserRole.ALL_STAFF_ROLES))).order_by(User.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=UserOut)
async def create_staff_user(
    payload: StaffCreate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    if payload.role not in UserRole.ALL_STAFF_ROLES:
        raise HTTPException(status_code=400, detail="الدور الوظيفي المحدد غير صالح")

    stmt_exists = select(User).where(User.email == payload.email)
    if (await db.execute(stmt_exists)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل مسبقاً")

    staff = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        is_active=True,
        is_verified=True
    )
    db.add(staff)
    await db.flush()

    await record_audit_log(
        db,
        action="CREATE_STAFF",
        target_entity="USER",
        target_entity_id=staff.id,
        user=current_user,
        details={"email": staff.email, "role": staff.role}
    )

    await db.commit()
    await db.refresh(staff)
    return staff

@router.put("/{staff_id}", response_model=UserOut)
async def update_staff_user(
    staff_id: str,
    payload: StaffUpdate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == staff_id)
    staff = (await db.execute(stmt)).scalar_one_or_none()
    if not staff or staff.role == UserRole.MOTHER_SUPERIOR:
        raise HTTPException(status_code=404, detail="حساب المشرف غير موجود أو لا يمكن تعديله")

    if payload.role:
        if payload.role not in UserRole.ALL_STAFF_ROLES:
            raise HTTPException(status_code=400, detail="الدور الوظيفي غير صالح")
        staff.role = payload.role
    if payload.is_active is not None:
        staff.is_active = payload.is_active

    staff.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await record_audit_log(
        db,
        action="UPDATE_STAFF",
        target_entity="USER",
        target_entity_id=staff.id,
        user=current_user,
        details={"role": staff.role, "is_active": staff.is_active}
    )

    await db.commit()
    await db.refresh(staff)
    return staff

@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = 100,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
