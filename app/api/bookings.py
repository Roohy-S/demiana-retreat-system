from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.booking import Booking, BookingStatus, BookingStatusHistory, ExtensionRequest, ExtensionStatus
from app.models.period import RetreatPeriod
from app.models.notification import Notification, NotificationType, NotificationSeverity
from app.schemas.booking import BookingSubmit, BookingOut, ExtensionRequestCreate, ExtensionRequestOut
from app.core.security import get_current_active_user
from app.core.booking_engine import submit_new_booking, cancel_booking_by_guest

router = APIRouter(prefix="/bookings", tags=["Guest Bookings"])

@router.post("/submit", response_model=BookingOut)
async def submit_booking(
    payload: BookingSubmit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Profile).where(Profile.user_id == current_user.id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="يرجى استكمال بيانات الملف الشخصي أولاً قبل تقديم الحجز")

    if not payload.agreed_to_rules:
        raise HTTPException(status_code=400, detail="يجب قراءة لائحة بيت الخلوة والموافقة عليها أولاً")

    booking = await submit_new_booking(
        db=db,
        profile=profile,
        period_id=payload.period_id,
        agreed_to_rules=payload.agreed_to_rules,
        has_interval_exception=payload.has_interval_exception,
        interval_exception_reason=payload.interval_exception_reason
    )
    return BookingOut.model_validate(booking)

@router.get("/my", response_model=List[BookingOut])
async def get_my_bookings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_prof = select(Profile).where(Profile.user_id == current_user.id)
    res_prof = await db.execute(stmt_prof)
    profile = res_prof.scalar_one_or_none()
    if not profile:
        return []

    stmt = (
        select(Booking)
        .where(Booking.profile_id == profile.id)
        .options(
            selectinload(Booking.profile),
            selectinload(Booking.period),
            selectinload(Booking.history),
            selectinload(Booking.extension_requests)
        )
        .order_by(Booking.created_at.desc())
    )
    res = await db.execute(stmt)
    bookings = res.scalars().all()
    return [BookingOut.model_validate(b) for b in bookings]

@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking_details(
    booking_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            selectinload(Booking.profile),
            selectinload(Booking.period),
            selectinload(Booking.history),
            selectinload(Booking.extension_requests)
        )
    )
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")

    # If applicant, must own booking
    if not current_user.is_staff():
        stmt_prof = select(Profile).where(Profile.user_id == current_user.id)
        res_prof = await db.execute(stmt_prof)
        my_prof = res_prof.scalar_one_or_none()
        if not my_prof or my_prof.id != booking.profile_id:
            raise HTTPException(status_code=403, detail="ليس لديك صلاحية لعرض هذا الحجز")

    return BookingOut.model_validate(booking)

@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await cancel_booking_by_guest(db, booking_id, current_user)

@router.post("/{booking_id}/request-extension", response_model=ExtensionRequestOut)
async def request_extension(
    booking_id: str,
    payload: ExtensionRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking).where(Booking.id == booking_id)
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")

    # If applicant, verify ownership
    if not current_user.is_staff():
        stmt_prof = select(Profile).where(Profile.user_id == current_user.id)
        res_prof = await db.execute(stmt_prof)
        my_prof = res_prof.scalar_one_or_none()
        if not my_prof or my_prof.id != booking.profile_id:
            raise HTTPException(status_code=403, detail="ليس لديك صلاحية لطلب تمديد لهذا الحجز")

    if booking.status not in [BookingStatus.APPROVED, BookingStatus.CHECKED_IN]:
        raise HTTPException(status_code=400, detail="يمكن طلب التمديد فقط للحجوزات المقبولة أو الحاضرة")

    ext_req = ExtensionRequest(
        booking_id=booking.id,
        profile_id=booking.profile_id,
        requested_additional_days=payload.requested_additional_days,
        reason=payload.reason,
        detailed_explanation=payload.detailed_explanation,
        status=ExtensionStatus.PENDING
    )
    db.add(ext_req)
    booking.status = BookingStatus.EXTENSION_REQUESTED

    # History
    history = BookingStatusHistory(
        booking_id=booking.id,
        previous_status=booking.status,
        new_status=BookingStatus.EXTENSION_REQUESTED,
        changed_by_user_id=current_user.id,
        change_notes=f"طلب تمديد إقامة لمدة {payload.requested_additional_days} أيام إضافية. السبب: {payload.reason}"
    )
    db.add(history)

    # Notify Mother Superior
    from app.models.user import UserRole
    stmt_admin = select(User).where(User.role == UserRole.MOTHER_SUPERIOR)
    res_admin = await db.execute(stmt_admin)
    admins = res_admin.scalars().all()
    for adm in admins:
        notif = Notification(
            recipient_user_id=adm.id,
            title="طلب تمديد مدة خلوة جديد",
            message=f"تقدمت النزيلة {booking.profile.full_name if booking.profile else ''} بطلب تمديد خلوة لمدة {payload.requested_additional_days} أيام إضافية. السبب: {payload.reason}",
            notification_type=NotificationType.EXTENSION,
            severity=NotificationSeverity.INFO,
            related_booking_id=booking.id
        )
        db.add(notif)

    await db.commit()
    await db.refresh(ext_req)
    return ext_req
