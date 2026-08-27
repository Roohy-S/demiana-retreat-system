from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.period import RetreatPeriod
from app.models.booking import Booking, BookingStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.core.security import require_staff
from app.core.pdf_generator import generate_reception_gate_pdf, generate_final_period_summary_pdf

router = APIRouter(prefix="/reports", tags=["Reporting & PDF Generation"])

@router.get("/gate-pdf/{period_id}")
async def download_gate_reception_pdf(
    period_id: str,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt_p = select(RetreatPeriod).where(RetreatPeriod.id == period_id)
    period = (await db.execute(stmt_p)).scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="فترة الخلوة غير موجودة")

    stmt = select(Booking, Profile, Attendance).join(Profile, Booking.profile_id == Profile.id).outerjoin(Attendance, Booking.id == Attendance.booking_id).where(
        Booking.period_id == period.id,
        Booking.status.in_([BookingStatus.APPROVED, BookingStatus.CHECKED_IN, BookingStatus.COMPLETED, BookingStatus.NO_SHOW])
    ).order_by(Profile.full_name.asc())

    res = await db.execute(stmt)
    retreatants = []
    for b, p, att in res.all():
        retreatants.append({
            "booking_reference": b.booking_reference,
            "full_name": p.full_name,
            "governorate": p.governorate,
            "diocese": p.diocese,
            "church": p.church,
            "phone_number": p.phone_number,
            "attendance_status": att.attendance_status if att else "مقبولة",
            "room_or_cell_number": att.room_or_cell_number if att else ""
        })

    pdf_buffer = generate_reception_gate_pdf(
        period_name=period.period_name,
        start_date_str=period.start_date.strftime("%Y-%m-%d"),
        end_date_str=period.departure_date.strftime("%Y-%m-%d"),
        approved_retreatants=retreatants
    )

    filename = f"gate_sheet_{period.start_date.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

@router.get("/period-summary-pdf/{period_id}")
async def download_period_summary_pdf(
    period_id: str,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    stmt_p = select(RetreatPeriod).where(RetreatPeriod.id == period_id)
    period = (await db.execute(stmt_p)).scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="فترة الخلوة غير موجودة")

    stmt = select(Booking, Profile, Attendance).join(Profile, Booking.profile_id == Profile.id).outerjoin(Attendance, Booking.id == Attendance.booking_id).where(
        Booking.period_id == period.id
    ).order_by(Profile.full_name.asc())

    res = await db.execute(stmt)
    all_rows = res.all()

    approved_count = sum(1 for b, p, att in all_rows if b.status in [BookingStatus.APPROVED, BookingStatus.CHECKED_IN, BookingStatus.COMPLETED])
    checked_in_count = sum(1 for b, p, att in all_rows if att and att.attendance_status in [AttendanceStatus.CHECKED_IN, AttendanceStatus.COMPLETED])
    cancelled_count = sum(1 for b, p, att in all_rows if b.status == BookingStatus.CANCELLED)
    no_show_count = sum(1 for b, p, att in all_rows if att and att.attendance_status == AttendanceStatus.NO_SHOW)

    retreatants_list = []
    for b, p, att in all_rows:
        if b.status in [BookingStatus.APPROVED, BookingStatus.CHECKED_IN, BookingStatus.COMPLETED, BookingStatus.NO_SHOW]:
            retreatants_list.append({
                "booking_reference": b.booking_reference,
                "full_name": p.full_name,
                "governorate": p.governorate,
                "church": p.church,
                "attendance_status": att.attendance_status if att else b.status
            })

    pdf_buffer = generate_final_period_summary_pdf(
        period_name=period.period_name,
        start_date_str=period.start_date.strftime("%Y-%m-%d"),
        end_date_str=period.departure_date.strftime("%Y-%m-%d"),
        capacity=period.capacity,
        stats={
            "approved_count": approved_count,
            "checked_in_count": checked_in_count,
            "cancelled_count": cancelled_count,
            "no_show_count": no_show_count
        },
        retreatants_list=retreatants_list
    )

    filename = f"period_summary_{period.start_date.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

@router.get("/analytics")
async def get_analytics_report(
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    # 1. Bookings by Governorate
    stmt_gov = select(Profile.governorate, func.count(Booking.id)).join(Booking, Profile.id == Booking.profile_id).group_by(Profile.governorate).order_by(desc(func.count(Booking.id)))
    res_gov = await db.execute(stmt_gov)
    gov_stats = [{"governorate": row[0], "count": row[1]} for row in res_gov.all()]

    # 2. Bookings by Diocese
    stmt_dio = select(Profile.diocese, func.count(Booking.id)).join(Booking, Profile.id == Booking.profile_id).group_by(Profile.diocese).order_by(desc(func.count(Booking.id))).limit(15)
    res_dio = await db.execute(stmt_dio)
    dio_stats = [{"diocese": row[0], "count": row[1]} for row in res_dio.all()]

    # 3. Bookings by Church
    stmt_chu = select(Profile.church, func.count(Booking.id)).join(Booking, Profile.id == Booking.profile_id).group_by(Profile.church).order_by(desc(func.count(Booking.id))).limit(15)
    res_chu = await db.execute(stmt_chu)
    chu_stats = [{"church": row[0], "count": row[1]} for row in res_chu.all()]

    # 4. Total metrics
    total_profiles = (await db.execute(select(func.count(Profile.id)))).scalar() or 0
    total_completed = (await db.execute(select(func.count(Attendance.id)).where(Attendance.attendance_status == AttendanceStatus.COMPLETED))).scalar() or 0
    total_no_shows = (await db.execute(select(func.count(Attendance.id)).where(Attendance.attendance_status == AttendanceStatus.NO_SHOW))).scalar() or 0

    return {
        "governorate_breakdown": gov_stats,
        "diocese_breakdown": dio_stats,
        "church_breakdown": chu_stats,
        "total_registered_profiles": total_profiles,
        "total_completed_retreats": total_completed,
        "total_no_shows": total_no_shows
    }
