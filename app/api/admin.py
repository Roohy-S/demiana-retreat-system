from typing import List, Optional
from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.period import RetreatPeriod, PeriodStatus, Waitlist, WaitlistStatus
from app.models.booking import Booking, BookingStatus, BookingStatusHistory, ExtensionRequest, ExtensionStatus, ExceptionStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.admin_notes import AdministrativeNote, Violation
from app.models.notification import Notification, NotificationType, NotificationSeverity, CommunicationLog
from app.models.audit import AuditLog
from app.schemas.booking import (
    BookingOut, BookingStatusUpdate, BookingTransfer,
    ExtensionRequestDecision, ExceptionRequestDecision
)
from app.schemas.profile import ProfileOut
from app.core.security import require_staff, require_mother_superior
from app.core.booking_engine import approve_booking_action, reject_booking_action
from app.core.audit import record_audit_log

router = APIRouter(prefix="/admin", tags=["Admin & Mother Superior Dashboard"])

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()

    # 1. Booking Status Counts
    total_bookings = (await db.execute(select(func.count(Booking.id)))).scalar() or 0
    under_review = (await db.execute(select(func.count(Booking.id)).where(Booking.status == BookingStatus.UNDER_REVIEW))).scalar() or 0
    approved = (await db.execute(select(func.count(Booking.id)).where(Booking.status == BookingStatus.APPROVED))).scalar() or 0
    rejected = (await db.execute(select(func.count(Booking.id)).where(Booking.status == BookingStatus.REJECTED))).scalar() or 0
    waiting_list = (await db.execute(select(func.count(Waitlist.id)).where(Waitlist.status == WaitlistStatus.WAITING))).scalar() or 0
    checked_in = (await db.execute(select(func.count(Attendance.id)).where(Attendance.attendance_status == AttendanceStatus.CHECKED_IN))).scalar() or 0
    no_show = (await db.execute(select(func.count(Attendance.id)).where(Attendance.attendance_status == AttendanceStatus.NO_SHOW))).scalar() or 0
    
    # 2. Action Items
    pending_extensions = (await db.execute(select(func.count(ExtensionRequest.id)).where(ExtensionRequest.status == ExtensionStatus.PENDING))).scalar() or 0
    pending_exceptions = (await db.execute(select(func.count(Booking.id)).where(
        Booking.has_interval_exception == True,
        Booking.interval_exception_status == ExceptionStatus.PENDING
    ))).scalar() or 0
    urgent_alerts = (await db.execute(select(func.count(Notification.id)).where(
        Notification.recipient_user_id == current_user.id,
        Notification.severity == NotificationSeverity.URGENT,
        Notification.is_read == False
    ))).scalar() or 0

    # 3. Today's Actions (Arrivals & Departures)
    stmt_arrivals = select(Booking, Profile, RetreatPeriod).join(Profile, Booking.profile_id == Profile.id).join(RetreatPeriod, Booking.period_id == RetreatPeriod.id).where(
        RetreatPeriod.start_date == today,
        Booking.status.in_([BookingStatus.APPROVED, BookingStatus.CHECKED_IN])
    )
    res_arrivals = await db.execute(stmt_arrivals)
    arrivals_today = []
    for b, p, per in res_arrivals.all():
        arrivals_today.append({
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "full_name": p.full_name,
            "phone_number": p.phone_number,
            "church": p.church,
            "diocese": p.diocese,
            "governorate": p.governorate,
            "status": b.status,
            "arrival_time": per.arrival_time_desc
        })

    stmt_departures = select(Booking, Profile, RetreatPeriod).join(Profile, Booking.profile_id == Profile.id).join(RetreatPeriod, Booking.period_id == RetreatPeriod.id).where(
        RetreatPeriod.departure_date == today,
        Booking.status == BookingStatus.CHECKED_IN
    )
    res_departures = await db.execute(stmt_departures)
    departures_today = []
    for b, p, per in res_departures.all():
        departures_today.append({
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "full_name": p.full_name,
            "phone_number": p.phone_number,
            "church": p.church,
            "status": b.status,
            "departure_time": per.departure_time_desc
        })

    # 4. Current / Next Period Summary
    stmt_cur = select(RetreatPeriod).where(
        RetreatPeriod.start_date <= today,
        RetreatPeriod.departure_date >= today
    ).order_by(RetreatPeriod.start_date.desc()).limit(1)
    current_period = (await db.execute(stmt_cur)).scalar_one_or_none()

    stmt_next = select(RetreatPeriod).where(
        RetreatPeriod.start_date > today,
        RetreatPeriod.status.in_([PeriodStatus.OPEN, PeriodStatus.FULL])
    ).order_by(RetreatPeriod.start_date.asc()).limit(1)
    next_period = (await db.execute(stmt_next)).scalar_one_or_none()

    return {
        "summary": {
            "total_bookings": total_bookings,
            "under_review": under_review,
            "approved": approved,
            "rejected": rejected,
            "waiting_list": waiting_list,
            "checked_in": checked_in,
            "no_show": no_show,
            "pending_extensions": pending_extensions,
            "pending_exceptions": pending_exceptions,
            "urgent_alerts": urgent_alerts
        },
        "today_actions": {
            "arrivals_count": len(arrivals_today),
            "arrivals": arrivals_today,
            "departures_count": len(departures_today),
            "departures": departures_today
        },
        "current_period": {
            "id": current_period.id,
            "name": current_period.period_name,
            "capacity": current_period.capacity,
            "approved_count": current_period.approved_count,
            "remaining": current_period.remaining_spots
        } if current_period else None,
        "next_period": {
            "id": next_period.id,
            "name": next_period.period_name,
            "start_date": str(next_period.start_date),
            "capacity": next_period.capacity,
            "approved_count": next_period.approved_count,
            "remaining": next_period.remaining_spots
        } if next_period else None
    }

@router.get("/bookings", response_model=List[BookingOut])
async def search_and_filter_bookings(
    q: Optional[str] = None,
    period_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    governorate: Optional[str] = None,
    has_warning: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking).join(Profile, Booking.profile_id == Profile.id)
    
    if q:
        search_pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Booking.booking_reference.ilike(search_pattern),
                Profile.full_name.ilike(search_pattern),
                Profile.phone_number.ilike(search_pattern),
                Profile.church.ilike(search_pattern),
                Profile.diocese.ilike(search_pattern),
                Profile.governorate.ilike(search_pattern)
            )
        )
    if period_id:
        stmt = stmt.where(Booking.period_id == period_id)
    if status_filter:
        stmt = stmt.where(Booking.status == status_filter)
    if governorate:
        stmt = stmt.where(Profile.governorate == governorate)
    if has_warning is not None:
        stmt = stmt.where(Profile.has_active_warning == has_warning)

    stmt = stmt.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/applicant/{profile_id}")
async def get_applicant_full_dossier(
    profile_id: str,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt_prof = select(Profile).where(Profile.id == profile_id)
    res_prof = await db.execute(stmt_prof)
    profile = res_prof.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="ملف المتقدمة غير موجود")

    # Bookings History
    stmt_b = select(Booking).where(Booking.profile_id == profile.id).order_by(Booking.created_at.desc())
    bookings = (await db.execute(stmt_b)).scalars().all()

    # Notes (Confidential)
    notes = []
    if current_user.is_mother_superior():
        stmt_n = select(AdministrativeNote).where(AdministrativeNote.profile_id == profile.id).order_by(AdministrativeNote.created_at.desc())
        notes = (await db.execute(stmt_n)).scalars().all()

    # Violations
    stmt_v = select(Violation).where(Violation.profile_id == profile.id).order_by(Violation.occurred_at.desc())
    violations = (await db.execute(stmt_v)).scalars().all()

    # Communication Logs
    stmt_c = select(CommunicationLog).where(CommunicationLog.profile_id == profile.id).order_by(CommunicationLog.sent_at.desc())
    comm_logs = (await db.execute(stmt_c)).scalars().all()

    # Audit Trail
    stmt_a = select(AuditLog).where(
        AuditLog.target_entity.in_(["PROFILE", "BOOKING"]),
        AuditLog.target_entity_id.in_([profile.id] + [b.id for b in bookings])
    ).order_by(AuditLog.created_at.desc()).limit(30)
    audit_trails = (await db.execute(stmt_a)).scalars().all()

    return {
        "profile": ProfileOut.model_validate(profile),
        "bookings_count": len(bookings),
        "bookings": [BookingOut.model_validate(b) for b in bookings],
        "notes": notes,
        "violations": violations,
        "communication_logs": comm_logs,
        "audit_trails": audit_trails
    }

@router.post("/bookings/{booking_id}/approve", response_model=BookingOut)
async def approve_booking(
    booking_id: str,
    payload: Optional[BookingStatusUpdate] = None,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    notes = payload.admin_notes if payload else None
    return await approve_booking_action(db, booking_id, current_user, notes)

@router.post("/bookings/{booking_id}/reject", response_model=BookingOut)
async def reject_booking(
    booking_id: str,
    payload: BookingStatusUpdate,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    return await reject_booking_action(
        db, booking_id, current_user,
        reason=payload.rejection_reason or "اعتذار من إدارة بيت الخلوة",
        show_to_user=payload.show_rejection_reason_to_user
    )

@router.post("/bookings/{booking_id}/transfer", response_model=BookingOut)
async def transfer_booking_to_period(
    booking_id: str,
    payload: BookingTransfer,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking).where(Booking.id == booking_id).with_for_update()
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")

    stmt_target_period = select(RetreatPeriod).where(RetreatPeriod.id == payload.new_period_id).with_for_update()
    res_tp = await db.execute(stmt_target_period)
    target_period = res_tp.scalar_one_or_none()
    if not target_period:
        raise HTTPException(status_code=404, detail="الفترة المراد النقل إليها غير موجودة")

    if target_period.approved_count >= target_period.capacity:
        raise HTTPException(status_code=400, detail="الفترة المراد النقل إليها مكتملة العدد")

    old_period_id = booking.period_id
    
    # Adjust old period count if was approved
    if booking.status == BookingStatus.APPROVED:
        stmt_old_p = select(RetreatPeriod).where(RetreatPeriod.id == old_period_id)
        old_p = (await db.execute(stmt_old_p)).scalar_one_or_none()
        if old_p:
            old_p.approved_count = max(0, old_p.approved_count - 1)
        target_period.approved_count += 1

    booking.original_period_id = old_period_id
    booking.period_id = target_period.id
    booking.transferred_by_user_id = current_user.id
    booking.transfer_reason = payload.transfer_reason

    # Record history
    history = BookingStatusHistory(
        booking_id=booking.id,
        previous_status=booking.status,
        new_status=booking.status,
        changed_by_user_id=current_user.id,
        change_notes=f"تم نقل الحجز إلى فترة {target_period.period_name}. السبب: {payload.transfer_reason}"
    )
    db.add(history)

    # Notify applicant
    if booking.profile and booking.profile.user_id:
        notif = Notification(
            recipient_user_id=booking.profile.user_id,
            title="تعديل موعد فترة الخلوة",
            message=f"تم نقل حجزك رقم {booking.booking_reference} إلى فترة {target_period.period_name} (تبدأ {target_period.start_date.strftime('%Y-%m-%d')}).",
            notification_type=NotificationType.BOOKING_STATUS,
            severity=NotificationSeverity.INFO,
            related_booking_id=booking.id
        )
        db.add(notif)

    await record_audit_log(
        db,
        action="TRANSFER_BOOKING",
        target_entity="BOOKING",
        target_entity_id=booking.id,
        user=current_user,
        details={"old_period_id": old_period_id, "new_period_id": target_period.id, "reason": payload.transfer_reason}
    )

    await db.commit()
    await db.refresh(booking)
    return booking

@router.post("/waitlist/{waitlist_id}/promote", response_model=BookingOut)
async def promote_waitlist_item(
    waitlist_id: str,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Waitlist).where(Waitlist.id == waitlist_id)
    res = await db.execute(stmt)
    wl = res.scalar_one_or_none()
    if not wl or wl.status != WaitlistStatus.WAITING:
        raise HTTPException(status_code=404, detail="عنصر قائمة الانتظار غير صالح للترقية")

    return await approve_booking_action(db, wl.booking_id, current_user, notes="تمت ترقية الحجز من قائمة الانتظار بناءً على قرار الإدارة.")

@router.post("/extensions/{extension_id}/decide")
async def decide_extension(
    extension_id: str,
    payload: ExtensionRequestDecision,
    current_user: User = Depends(require_mother_superior),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ExtensionRequest).where(ExtensionRequest.id == extension_id)
    res = await db.execute(stmt)
    ext = res.scalar_one_or_none()
    if not ext:
        raise HTTPException(status_code=404, detail="طلب التمديد غير موجود")

    stmt_b = select(Booking).where(Booking.id == ext.booking_id)
    booking = (await db.execute(stmt_b)).scalar_one_or_none()

    ext.status = payload.status
    ext.admin_response_notes = payload.admin_response_notes
    ext.decided_by_user_id = current_user.id
    ext.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if booking:
        if payload.status == ExtensionStatus.APPROVED:
            booking.status = BookingStatus.EXTENSION_APPROVED
            notif_msg = f"تمت الموافقة على طلب تمديد إقامتك ببيت الخلوة لمدة {ext.requested_additional_days} أيام إضافية."
            notif_sev = NotificationSeverity.SUCCESS
        else:
            booking.status = BookingStatus.EXTENSION_REJECTED
            notif_msg = f"نعتذر، لم تتم الموافقة على طلب تمديد الإقامة. {payload.admin_response_notes or ''}"
            notif_sev = NotificationSeverity.WARNING

        if booking.profile and booking.profile.user_id:
            notif = Notification(
                recipient_user_id=booking.profile.user_id,
                title="قرار بخصوص طلب التمديد",
                message=notif_msg,
                notification_type=NotificationType.EXTENSION,
                severity=notif_sev,
                related_booking_id=booking.id
            )
            db.add(notif)

    await record_audit_log(
        db,
        action="DECIDE_EXTENSION",
        target_entity="EXTENSION_REQUEST",
        target_entity_id=ext.id,
        user=current_user,
        details={"status": payload.status, "notes": payload.admin_response_notes}
    )
    await db.commit()
    return {"message": "تم تسجيل القرار بنجاح", "status": ext.status}

@router.get("/duplicates/audit")
async def audit_duplicates(
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Audit potential duplicate accounts, matching phone numbers, or correlated identities.
    """
    # Fetch all profiles
    stmt = select(Profile)
    res = await db.execute(stmt)
    profiles = res.scalars().all()

    phone_map = {}
    name_birth_map = {}
    duplicates_found = []

    for p in profiles:
        # Check phone duplicates
        if p.phone_number:
            phone_map.setdefault(p.phone_number, []).append(p)

        # Check name + birthdate duplicates
        from app.core.duplicate_detector import normalize_arabic_text
        norm_name = normalize_arabic_text(p.full_name)
        key = f"{norm_name}_{p.birth_date}"
        name_birth_map.setdefault(key, []).append(p)

    # Correlate phone duplicates
    for phone, group in phone_map.items():
        if len(group) > 1:
            duplicates_found.append({
                "type": "SHARED_PHONE",
                "label": f"اشتراك في رقم الهاتف ({phone})",
                "count": len(group),
                "profiles": [
                    {
                        "id": pr.id,
                        "full_name": pr.full_name,
                        "phone_number": pr.phone_number,
                        "national_id": pr.national_id_number,
                        "church": pr.church,
                        "governorate": pr.governorate,
                        "created_at": pr.created_at.strftime("%Y-%m-%d") if pr.created_at else ""
                    }
                    for pr in group
                ]
            })

    # Correlate identity duplicates
    for key, group in name_birth_map.items():
        if len(group) > 1:
            duplicates_found.append({
                "type": "SHARED_IDENTITY",
                "label": f"تطابق الاسم وتاريخ الميلاد ({group[0].full_name} - {group[0].birth_date})",
                "count": len(group),
                "profiles": [
                    {
                        "id": pr.id,
                        "full_name": pr.full_name,
                        "phone_number": pr.phone_number,
                        "national_id": pr.national_id_number,
                        "church": pr.church,
                        "governorate": pr.governorate,
                        "created_at": pr.created_at.strftime("%Y-%m-%d") if pr.created_at else ""
                    }
                    for pr in group
                ]
            })

    return {
        "total_duplicates_flagged": len(duplicates_found),
        "audit_items": duplicates_found
    }

