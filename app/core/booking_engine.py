import random
import uuid
import secrets
from datetime import datetime, date, timedelta, timezone
from typing import Tuple, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status

from app.models.period import RetreatPeriod, PeriodStatus, Waitlist, WaitlistStatus
from app.models.booking import Booking, BookingStatus, BookingStatusHistory, ExtensionRequest, ExtensionStatus, ExceptionStatus
from app.models.profile import Profile
from app.models.admin_notes import AdministrativeNote, Violation, NoteSeverity, NoteRecommendation
from app.models.attendance import Attendance, AttendanceStatus
from app.models.notification import Notification, NotificationType, NotificationSeverity
from app.models.settings import SystemSettings
from app.core.audit import record_audit_log

async def get_system_settings(db: AsyncSession) -> SystemSettings:
    stmt = select(SystemSettings).limit(1)
    result = await db.execute(stmt)
    settings_obj = result.scalar_one_or_none()
    if not settings_obj:
        settings_obj = SystemSettings()
        db.add(settings_obj)
        await db.flush()
    return settings_obj

async def generate_booking_reference(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    for _ in range(10):
        rand_code = secrets.token_hex(2).upper()
        stmt_cnt = select(func.count(Booking.id))
        res_cnt = await db.execute(stmt_cnt)
        count = (res_cnt.scalar() or 0) + 1
        ref = f"DMR-{year}-{count:04d}-{rand_code}"
        
        # Check uniqueness
        stmt_check = select(Booking.id).where(Booking.booking_reference == ref)
        if not (await db.execute(stmt_check)).scalar_one_or_none():
            return ref
    return f"DMR-{year}-{uuid.uuid4().hex[:8].upper()}"

async def check_minimum_booking_interval(
    db: AsyncSession,
    profile: Profile,
    target_start_date: date
) -> Tuple[bool, int, int]:
    """
    Checks whether the applicant has satisfied the minimum booking interval (e.g. 3 months = ~90 days).
    Returns (is_valid, days_since_last_retreat, required_interval_days)
    """
    settings_obj = await get_system_settings(db)
    min_months = settings_obj.min_booking_interval_months
    required_days = min_months * 30

    if not profile.last_retreat_date:
        return True, 9999, required_days

    days_diff = (target_start_date - profile.last_retreat_date).days
    if days_diff >= required_days:
        return True, days_diff, required_days
    return False, max(0, days_diff), required_days

async def check_profile_warnings(
    db: AsyncSession,
    profile_id: str
) -> Tuple[bool, List[str]]:
    """
    Checks if applicant has active high/critical notes, violations or booking restrictions.
    Returns (has_warning, list_of_warning_reasons)
    """
    warnings = []
    
    # Check notes
    stmt_notes = select(AdministrativeNote).where(
        AdministrativeNote.profile_id == profile_id,
        AdministrativeNote.is_active == True,
        or_(
            AdministrativeNote.severity.in_([NoteSeverity.HIGH, NoteSeverity.CRITICAL]),
            AdministrativeNote.recommendation.in_([NoteRecommendation.BAN_BOOKING, NoteRecommendation.SUPERVISOR_ATTENTION])
        )
    )
    res_notes = await db.execute(stmt_notes)
    active_notes = res_notes.scalars().all()
    for n in active_notes:
        warnings.append(f"ملاحظة إدارية ({n.severity}): {n.content[:60]}")

    # Check violations
    stmt_viols = select(Violation).where(
        Violation.profile_id == profile_id,
        Violation.is_resolved == False
    )
    res_viols = await db.execute(stmt_viols)
    viols = res_viols.scalars().all()
    for v in viols:
        warnings.append(f"مخالفة غير مسواة: {v.violation_title}")

    return len(warnings) > 0, warnings

async def submit_new_booking(
    db: AsyncSession,
    profile: Profile,
    period_id: str,
    agreed_to_rules: bool,
    has_interval_exception: bool = False,
    interval_exception_reason: Optional[str] = None
) -> Booking:
    # 1. Fetch Period with lock
    stmt_period = select(RetreatPeriod).where(RetreatPeriod.id == period_id).with_for_update()
    res_period = await db.execute(stmt_period)
    period = res_period.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="فترة الخلوة المحددة غير موجودة")
    if period.status in [PeriodStatus.CLOSED, PeriodStatus.CANCELLED, PeriodStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="الحجز مغلق لهذه الفترة حالياً")

    # 2. Check if already booked
    stmt_existing = select(Booking).where(
        Booking.profile_id == profile.id,
        Booking.period_id == period.id,
        Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.REJECTED])
    )
    res_existing = await db.execute(stmt_existing)
    existing_booking = res_existing.scalar_one_or_none()
    if existing_booking:
        raise HTTPException(status_code=400, detail="لديك حجز مسبق بالفعل في هذه الفترة")

    # 3. Check Minimum Booking Interval
    interval_valid, days_since, required_days = await check_minimum_booking_interval(
        db, profile, period.start_date
    )
    
    if not interval_valid:
        has_interval_exception = True
        if not interval_exception_reason:
            raise HTTPException(
                status_code=400,
                detail=f"لم تنقضِ المدة المحددة بين الخلوات ({required_days // 30} أشهر). آخر خلوة لك كانت منذ {days_since} يوماً. يرجى تقديم سبب الحجز الاستثنائي."
            )

    # 4. Check Administrative Warnings
    has_admin_warning, warning_reasons = await check_profile_warnings(db, profile.id)
    if has_admin_warning:
        profile.has_active_warning = True

    # 5. Determine Initial Booking Status
    booking_ref = await generate_booking_reference(db)
    
    # If period capacity is already reached by approved bookings
    is_period_full = period.approved_count >= period.capacity
    
    if is_period_full:
        # Put on waitlist
        stmt_wl_count = select(func.count(Waitlist.id)).where(Waitlist.period_id == period.id)
        res_wl = await db.execute(stmt_wl_count)
        wl_count = res_wl.scalar() or 0
        queue_num = wl_count + 1

        booking = Booking(
            booking_reference=booking_ref,
            profile_id=profile.id,
            period_id=period.id,
            status=BookingStatus.WAITING_LIST,
            has_interval_exception=has_interval_exception,
            interval_exception_reason=interval_exception_reason,
            interval_exception_status=ExceptionStatus.PENDING if has_interval_exception else ExceptionStatus.NONE,
            agreed_to_rules=agreed_to_rules
        )
        db.add(booking)
        await db.flush()

        waitlist_entry = Waitlist(
            period_id=period.id,
            profile_id=profile.id,
            booking_id=booking.id,
            queue_number=queue_num,
            status=WaitlistStatus.WAITING
        )
        db.add(waitlist_entry)

        # Status History
        history = BookingStatusHistory(
            booking_id=booking.id,
            previous_status=None,
            new_status=BookingStatus.WAITING_LIST,
            change_notes=f"الفترة مكتملة العدد ({period.capacity}). تم إدراج الطلب في قائمة الانتظار برقم {queue_num}."
        )
        db.add(history)

    else:
        # Standard Under Review
        period.pending_count += 1
        booking = Booking(
            booking_reference=booking_ref,
            profile_id=profile.id,
            period_id=period.id,
            status=BookingStatus.UNDER_REVIEW,
            has_interval_exception=has_interval_exception,
            interval_exception_reason=interval_exception_reason,
            interval_exception_status=ExceptionStatus.PENDING if has_interval_exception else ExceptionStatus.NONE,
            agreed_to_rules=agreed_to_rules
        )
        db.add(booking)
        await db.flush()

        # Status History
        history = BookingStatusHistory(
            booking_id=booking.id,
            previous_status=BookingStatus.SUBMITTED,
            new_status=BookingStatus.UNDER_REVIEW,
            change_notes="تم استلام الطلب وبدء المراجعة الإدارية."
        )
        db.add(history)

    # 6. Create User In-App Notification
    user_notification = Notification(
        recipient_user_id=profile.user_id,
        title="تم استلام طلب الخلوة الخاص بك",
        message=f"تم استلام طلبك رقم {booking.booking_reference} لفترة {period.period_name} بنجاح وهو الآن {('في قائمة الانتظار' if is_period_full else 'قيد المراجعة الإدارية')}.",
        notification_type=NotificationType.BOOKING_STATUS,
        severity=NotificationSeverity.INFO,
        related_booking_id=booking.id
    )
    db.add(user_notification)

    # 7. If warning or interval exception, notify Mother Superior
    if has_admin_warning or has_interval_exception:
        # Find mother superior
        from app.models.user import User, UserRole
        stmt_admin = select(User).where(User.role == UserRole.MOTHER_SUPERIOR)
        res_admin = await db.execute(stmt_admin)
        admins = res_admin.scalars().all()
        for adm in admins:
            alert_msg = f"تنبيه إداري: المتقدمة {profile.full_name} تقدمت بطلب حجز رقم {booking.booking_reference}."
            if has_admin_warning:
                alert_msg += f" (توجد ملاحظات أو مخالفات سابقة: {', '.join(warning_reasons)})"
            if has_interval_exception:
                alert_msg += f" (طلب استثناء فاصل زمني: {interval_exception_reason})"
                
            admin_alert = Notification(
                recipient_user_id=adm.id,
                title="تنبيه إداري عاجل - مراجعة طلب خلوة",
                message=alert_msg,
                notification_type=NotificationType.ALERT,
                severity=NotificationSeverity.URGENT,
                related_booking_id=booking.id
            )
            db.add(admin_alert)

    await db.commit()
    await db.refresh(booking)
    return booking

async def approve_booking_action(
    db: AsyncSession,
    booking_id: str,
    admin_user,
    notes: Optional[str] = None
) -> Booking:
    stmt = select(Booking).where(Booking.id == booking_id).with_for_update()
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")

    stmt_period = select(RetreatPeriod).where(RetreatPeriod.id == booking.period_id).with_for_update()
    res_period = await db.execute(stmt_period)
    period = res_period.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="الفترة غير موجودة")

    if booking.status == BookingStatus.APPROVED:
        return booking

    # Check capacity limit
    if period.approved_count >= period.capacity:
        raise HTTPException(status_code=400, detail="لا يمكن قبول الطلب لاكتمال سعة الفترة القصوى")

    old_status = booking.status
    if old_status in [BookingStatus.UNDER_REVIEW, BookingStatus.SUBMITTED]:
        period.pending_count = max(0, period.pending_count - 1)
    
    period.approved_count += 1
    booking.status = BookingStatus.APPROVED
    if booking.has_interval_exception and booking.interval_exception_status == ExceptionStatus.PENDING:
        booking.interval_exception_status = ExceptionStatus.APPROVED

    # If was on waitlist, mark promoted
    if booking.waitlist_item:
        booking.waitlist_item.status = WaitlistStatus.PROMOTED
        booking.waitlist_item.promoted_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Record history
    history = BookingStatusHistory(
        booking_id=booking.id,
        previous_status=old_status,
        new_status=BookingStatus.APPROVED,
        changed_by_user_id=admin_user.id,
        change_notes=notes or "تمت الموافقة على طلب الخلوة من قبل إدارة بيت الخلوة."
    )
    db.add(history)

    # Initialize Attendance record
    stmt_att = select(Attendance).where(Attendance.booking_id == booking.id)
    res_att = await db.execute(stmt_att)
    existing_att = res_att.scalar_one_or_none()
    if not existing_att:
        attendance = Attendance(
            booking_id=booking.id,
            period_id=period.id,
            profile_id=booking.profile_id,
            attendance_status=AttendanceStatus.EXPECTED
        )
        db.add(attendance)

    # In-App Notification to User
    if booking.profile and booking.profile.user_id:
        notif = Notification(
            recipient_user_id=booking.profile.user_id,
            title="تمت الموافقة على طلب الخلوة الخاص بك",
            message=f"بركة دير القديسة دميانة. تمت الموافقة على حجزك رقم {booking.booking_reference} لفترة {period.period_name}. موعد الوصول: {period.arrival_time_desc} يوم {period.start_date.strftime('%Y-%m-%d')}.",
            notification_type=NotificationType.BOOKING_STATUS,
            severity=NotificationSeverity.SUCCESS,
            related_booking_id=booking.id
        )
        db.add(notif)

    await record_audit_log(
        db,
        action="APPROVE_BOOKING",
        target_entity="BOOKING",
        target_entity_id=booking.id,
        user=admin_user,
        details={"booking_reference": booking.booking_reference, "period_id": period.id, "notes": notes}
    )

    await db.commit()
    await db.refresh(booking)
    return booking

async def reject_booking_action(
    db: AsyncSession,
    booking_id: str,
    admin_user,
    reason: str,
    show_to_user: bool = False
) -> Booking:
    stmt = select(Booking).where(Booking.id == booking_id).with_for_update()
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")

    stmt_period = select(RetreatPeriod).where(RetreatPeriod.id == booking.period_id).with_for_update()
    res_period = await db.execute(stmt_period)
    period = res_period.scalar_one_or_none()

    old_status = booking.status
    if old_status == BookingStatus.APPROVED and period:
        period.approved_count = max(0, period.approved_count - 1)
    elif old_status in [BookingStatus.UNDER_REVIEW, BookingStatus.SUBMITTED] and period:
        period.pending_count = max(0, period.pending_count - 1)

    booking.status = BookingStatus.REJECTED
    booking.rejection_reason = reason
    booking.show_rejection_reason_to_user = show_to_user
    if booking.has_interval_exception:
        booking.interval_exception_status = ExceptionStatus.REJECTED

    if booking.waitlist_item:
        booking.waitlist_item.status = WaitlistStatus.REJECTED

    # History
    history = BookingStatusHistory(
        booking_id=booking.id,
        previous_status=old_status,
        new_status=BookingStatus.REJECTED,
        changed_by_user_id=admin_user.id,
        change_notes=f"تم رفض الطلب: {reason}"
    )
    db.add(history)

    # In-app notification
    if booking.profile and booking.profile.user_id:
        user_msg = f"نعتذر، لم تتم الموافقة على طلب الخلوة رقم {booking.booking_reference}."
        if show_to_user and reason:
            user_msg += f" السبب: {reason}"
        notif = Notification(
            recipient_user_id=booking.profile.user_id,
            title="حالة طلب الخلوة",
            message=user_msg,
            notification_type=NotificationType.BOOKING_STATUS,
            severity=NotificationSeverity.WARNING,
            related_booking_id=booking.id
        )
        db.add(notif)

    await record_audit_log(
        db,
        action="REJECT_BOOKING",
        target_entity="BOOKING",
        target_entity_id=booking.id,
        user=admin_user,
        details={"booking_reference": booking.booking_reference, "reason": reason, "show_to_user": show_to_user}
    )

    await db.commit()
    await db.refresh(booking)
    return booking

async def cancel_booking_by_guest(
    db: AsyncSession,
    booking_id: str,
    guest_user
) -> Booking:
    stmt = select(Booking).where(Booking.id == booking_id).with_for_update()
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")

    # Strict ownership check for non-staff
    if not guest_user.is_staff():
        stmt_prof = select(Profile).where(Profile.user_id == guest_user.id)
        res_prof = await db.execute(stmt_prof)
        my_prof = res_prof.scalar_one_or_none()
        if not my_prof or my_prof.id != booking.profile_id:
            raise HTTPException(status_code=403, detail="ليس لديك صلاحية لإلغاء هذا الحجز")

    stmt_period = select(RetreatPeriod).where(RetreatPeriod.id == booking.period_id).with_for_update()
    res_period = await db.execute(stmt_period)
    period = res_period.scalar_one_or_none()

    old_status = booking.status
    if old_status == BookingStatus.APPROVED and period:
        period.approved_count = max(0, period.approved_count - 1)
    elif old_status in [BookingStatus.UNDER_REVIEW, BookingStatus.SUBMITTED] and period:
        period.pending_count = max(0, period.pending_count - 1)

    booking.status = BookingStatus.CANCELLED

    if booking.waitlist_item:
        booking.waitlist_item.status = WaitlistStatus.CANCELLED

    history = BookingStatusHistory(
        booking_id=booking.id,
        previous_status=old_status,
        new_status=BookingStatus.CANCELLED,
        changed_by_user_id=guest_user.id,
        change_notes="اعتذرت المتقدمة عن موعد الخلوة وتم إلغاء الحجز."
    )
    db.add(history)

    # Notify Mother Superior of cancellation & available spot
    from app.models.user import User, UserRole
    stmt_admin = select(User).where(User.role == UserRole.MOTHER_SUPERIOR)
    res_admin = await db.execute(stmt_admin)
    admins = res_admin.scalars().all()
    for adm in admins:
        admin_alert = Notification(
            recipient_user_id=adm.id,
            title="اعتذار عن حجز وتوفر مكان شاغر",
            message=f"اعتذرت المتقدمة {booking.profile.full_name if booking.profile else ''} عن حجزها رقم {booking.booking_reference} لفترة {period.period_name if period else ''}. تتوفر الآن إمكانية ترقية متقدمة من قائمة الانتظار.",
            notification_type=NotificationType.ALERT,
            severity=NotificationSeverity.INFO,
            related_booking_id=booking.id
        )
        db.add(admin_alert)

    await db.commit()
    await db.refresh(booking)
    return booking
