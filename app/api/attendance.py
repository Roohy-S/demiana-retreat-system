from typing import List, Optional
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.period import RetreatPeriod
from app.models.booking import Booking, BookingStatus, BookingStatusHistory
from app.models.attendance import Attendance, AttendanceStatus
from app.schemas.attendance import CheckinCreate, AttendanceStatusUpdate, AttendanceOut, GateSheetItem
from app.core.security import require_staff
from app.core.audit import record_audit_log

router = APIRouter(prefix="/attendance", tags=["Attendance & Gate Check-in"])

@router.get("/period/{period_id}", response_model=List[GateSheetItem])
async def get_period_gate_sheet(
    period_id: str,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking, Profile, Attendance).join(Profile, Booking.profile_id == Profile.id).outerjoin(Attendance, Booking.id == Attendance.booking_id).where(
        Booking.period_id == period_id,
        Booking.status.in_([BookingStatus.APPROVED, BookingStatus.CHECKED_IN, BookingStatus.COMPLETED, BookingStatus.NO_SHOW])
    ).order_by(Profile.full_name.asc())
    
    res = await db.execute(stmt)
    items = []
    for b, p, att in res.all():
        att_status = att.attendance_status if att else AttendanceStatus.EXPECTED
        checked_time = att.checked_in_at if att else None
        room_num = att.room_or_cell_number if att else None

        items.append(GateSheetItem(
            booking_id=b.id,
            booking_reference=b.booking_reference,
            profile_name=p.full_name,
            national_id=p.national_id_number,
            phone_number=p.phone_number,
            governorate=p.governorate,
            diocese=p.diocese,
            church=p.church,
            status=b.status,
            attendance_status=att_status,
            checked_in_at=checked_time,
            room_or_cell_number=room_num,
            companion_name=p.companion_name if p.is_minor else None
        ))
    return items

@router.post("/check-in", response_model=AttendanceOut)
async def checkin_guest(
    payload: CheckinCreate,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt_b = select(Booking).where(Booking.id == payload.booking_id).with_for_update()
    booking = (await db.execute(stmt_b)).scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")

    stmt_att = select(Attendance).where(Attendance.booking_id == booking.id).with_for_update()
    att = (await db.execute(stmt_att)).scalar_one_or_none()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not att:
        att = Attendance(
            booking_id=booking.id,
            period_id=booking.period_id,
            profile_id=booking.profile_id,
            checked_in_at=now,
            checked_in_by_user_id=current_user.id,
            attendance_status=AttendanceStatus.CHECKED_IN,
            room_or_cell_number=payload.room_or_cell_number,
            reception_notes=payload.reception_notes
        )
        db.add(att)
    else:
        att.checked_in_at = now
        att.checked_in_by_user_id = current_user.id
        att.attendance_status = AttendanceStatus.CHECKED_IN
        if payload.room_or_cell_number:
            att.room_or_cell_number = payload.room_or_cell_number
        if payload.reception_notes:
            att.reception_notes = payload.reception_notes

    booking.status = BookingStatus.CHECKED_IN

    # Record history
    history = BookingStatusHistory(
        booking_id=booking.id,
        previous_status=BookingStatus.APPROVED,
        new_status=BookingStatus.CHECKED_IN,
        changed_by_user_id=current_user.id,
        change_notes=f"تم تسجيل الوصول في الاستقبال (الغرفة/القلاية: {payload.room_or_cell_number or 'غير محدد'})."
    )
    db.add(history)

    await record_audit_log(
        db,
        action="CHECKIN_ATTENDANCE",
        target_entity="ATTENDANCE",
        target_entity_id=booking.id,
        user=current_user,
        details={"booking_reference": booking.booking_reference, "room": payload.room_or_cell_number}
    )

    await db.commit()
    await db.refresh(att)
    return att

@router.put("/{attendance_id}", response_model=AttendanceOut)
async def update_attendance_status(
    attendance_id: str,
    payload: AttendanceStatusUpdate,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Attendance).where(Attendance.id == attendance_id).with_for_update()
    att = (await db.execute(stmt)).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail="سجل الحضور غير موجود")

    stmt_b = select(Booking).where(Booking.id == att.booking_id).with_for_update()
    booking = (await db.execute(stmt_b)).scalar_one_or_none()

    att.attendance_status = payload.attendance_status
    if payload.room_or_cell_number is not None:
        att.room_or_cell_number = payload.room_or_cell_number
    if payload.reception_notes is not None:
        att.reception_notes = payload.reception_notes

    # If completed, update profile last retreat date
    if payload.attendance_status == AttendanceStatus.COMPLETED:
        att.checked_out_at = datetime.now(timezone.utc).replace(tzinfo=None)
        was_already_completed = booking and booking.status == BookingStatus.COMPLETED
        if booking:
            booking.status = BookingStatus.COMPLETED
        stmt_prof = select(Profile).where(Profile.id == att.profile_id).with_for_update()
        prof = (await db.execute(stmt_prof)).scalar_one_or_none()
        if prof:
            prof.last_retreat_date = date.today()
            if not was_already_completed:
                prof.total_retreats_count += 1
    elif payload.attendance_status == AttendanceStatus.NO_SHOW:
        if booking:
            booking.status = BookingStatus.NO_SHOW

    await db.commit()
    await db.refresh(att)
    return att
