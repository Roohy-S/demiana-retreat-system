from typing import List, Optional
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.period import RetreatPeriod, PeriodStatus, Waitlist, WaitlistStatus
from app.models.profile import Profile
from app.schemas.period import PeriodCreate, PeriodUpdate, PeriodOut, WaitlistOut
from app.core.security import get_current_active_user, require_staff, require_mother_superior
from app.core.audit import record_audit_log

router = APIRouter(prefix="/periods", tags=["Retreat Periods"])

@router.get("", response_model=List[PeriodOut])
@router.get("/", response_model=List[PeriodOut])
async def list_open_periods(db: AsyncSession = Depends(get_db)):
    """
    Public/Applicant endpoint to view open retreat periods.
    """
    stmt = select(RetreatPeriod).where(
        RetreatPeriod.status.in_([PeriodStatus.OPEN, PeriodStatus.EXCEPTIONAL, PeriodStatus.FULL]),
        RetreatPeriod.start_date >= date.today()
    ).order_by(RetreatPeriod.start_date.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/admin/all", response_model=List[PeriodOut])
async def list_all_periods_admin(
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to view all historical and upcoming periods.
    """
    stmt = select(RetreatPeriod).order_by(RetreatPeriod.start_date.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=PeriodOut)
async def create_period(
    payload: PeriodCreate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    period = RetreatPeriod(
        period_name=payload.period_name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        departure_date=payload.departure_date,
        arrival_time_desc=payload.arrival_time_desc,
        departure_time_desc=payload.departure_time_desc,
        nights_count=payload.nights_count,
        capacity=payload.capacity,
        status=PeriodStatus.OPEN,
        is_special_period=payload.is_special_period,
        allows_extension_requests=payload.allows_extension_requests,
        allows_exception_requests=payload.allows_exception_requests,
        admin_notes=payload.admin_notes
    )
    db.add(period)
    await db.flush()

    await record_audit_log(
        db,
        action="CREATE_PERIOD",
        target_entity="RETREAT_PERIOD",
        target_entity_id=period.id,
        user=current_user,
        details={"period_name": period.period_name, "start_date": str(period.start_date), "capacity": period.capacity}
    )
    await db.commit()
    await db.refresh(period)
    return period

@router.put("/{period_id}", response_model=PeriodOut)
async def update_period(
    period_id: str,
    payload: PeriodUpdate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RetreatPeriod).where(RetreatPeriod.id == period_id)
    res = await db.execute(stmt)
    period = res.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="فترة الخلوة غير موجودة")

    data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    for field, val in data.items():
        if val is not None:
            setattr(period, field, val)

    period.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await record_audit_log(
        db,
        action="UPDATE_PERIOD",
        target_entity="RETREAT_PERIOD",
        target_entity_id=period.id,
        user=current_user,
        details=payload.dict(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(period)
    return period

@router.get("/{period_id}/waitlist", response_model=List[WaitlistOut])
async def get_period_waitlist(
    period_id: str,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Waitlist, Profile).join(Profile, Waitlist.profile_id == Profile.id).where(
        Waitlist.period_id == period_id,
        Waitlist.status == WaitlistStatus.WAITING
    ).order_by(Waitlist.queue_number.asc())
    
    res = await db.execute(stmt)
    items = []
    for wl, prof in res.all():
        items.append(WaitlistOut(
            id=wl.id,
            period_id=wl.period_id,
            profile_id=wl.profile_id,
            booking_id=wl.booking_id,
            queue_number=wl.queue_number,
            priority_score=wl.priority_score,
            status=wl.status,
            created_at=wl.created_at,
            profile_name=prof.full_name,
            profile_phone=prof.phone_number,
            governorate=prof.governorate,
            church=prof.church
        ))
    return items
