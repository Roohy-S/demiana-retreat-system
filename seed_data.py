import asyncio
from datetime import datetime, date, timedelta, timezone
from app.database import AsyncSessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.profile import Profile, Guardian, ConfessionFather
from app.models.period import RetreatPeriod, PeriodStatus, Waitlist, WaitlistStatus
from app.models.booking import Booking, BookingStatus, BookingStatusHistory, ExtensionRequest, ExtensionStatus, ExceptionStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.admin_notes import AdministrativeNote, Violation, NoteSeverity, NoteRecommendation
from app.models.notification import Notification, NotificationType, NotificationSeverity, CommunicationLog
from app.models.settings import SystemSettings
from app.core.security import get_password_hash

async def seed_database():
    print("[*] Initializing Database Schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("[*] Seeding System Settings...")
        settings = SystemSettings(
            retreat_name="بيت الخلوة بدير القديسة دميانة",
            monastery_location="ببراري بلقاس",
            default_retreat_nights=3,
            min_booking_interval_months=3,
            min_applicant_age_years=15,
            default_period_capacity=20,
            allow_waitlist=True,
            allow_extensions=True,
            allow_exceptions=True,
            whatsapp_official_number="201012345678",
            reception_contact_phone="201098765432"
        )
        session.add(settings)

        print("[*] Seeding Administrative & Staff Accounts...")
        # 1. Mother Superior (Official from docs: mother@stdemiana.org / MotherAdmin@123)
        mother_official = User(
            email="mother@stdemiana.org",
            password_hash=get_password_hash("MotherAdmin@123"),
            role=UserRole.MOTHER_SUPERIOR,
            is_active=True,
            is_verified=True
        )
        session.add(mother_official)

        mother_user = User(
            email="mother.superior@demiana-monastery.org",
            password_hash=get_password_hash("MotherSuperior2026!"),
            role=UserRole.MOTHER_SUPERIOR,
            is_active=True,
            is_verified=True
        )
        session.add(mother_user)

        # 2. Supervisor (Official from docs: supervisor@stdemiana.org / Supervisor@123)
        supervisor_official = User(
            email="supervisor@stdemiana.org",
            password_hash=get_password_hash("Supervisor@123"),
            role=UserRole.BOOKING_SUPERVISOR,
            is_active=True,
            is_verified=True
        )
        session.add(supervisor_official)

        # 3. Reception Staff
        reception_user = User(
            email="reception@demiana-monastery.org",
            password_hash=get_password_hash("Reception2026!"),
            role=UserRole.RECEPTION_SUPERVISOR,
            is_active=True,
            is_verified=True
        )
        session.add(reception_user)

        # 4. Booking Supervisor
        booking_staff_user = User(
            email="booking.staff@demiana-monastery.org",
            password_hash=get_password_hash("BookingStaff2026!"),
            role=UserRole.BOOKING_SUPERVISOR,
            is_active=True,
            is_verified=True
        )
        session.add(booking_staff_user)
        await session.flush()

        print("[*] Seeding Retreat Periods...")
        today = date.today()

        # Period 1: Open upcoming period (Arrival in 5 days)
        period1 = RetreatPeriod(
            period_name="فترة خلوة 1 يونيو - 4 يونيو (الأولى)",
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=8),
            departure_date=today + timedelta(days=8),
            arrival_time_desc="الساعة 12:00 ظهراً",
            departure_time_desc="قبل الساعة 9:00 صباحاً",
            nights_count=3,
            capacity=20,
            approved_count=3,
            pending_count=2,
            status=PeriodStatus.OPEN
        )
        session.add(period1)

        # Period 2: Full period with active waitlist (Arrival in 12 days)
        period2 = RetreatPeriod(
            period_name="فترة خلوة 10 يونيو - 13 يونيو (المكتملة)",
            start_date=today + timedelta(days=12),
            end_date=today + timedelta(days=15),
            departure_date=today + timedelta(days=15),
            nights_count=3,
            capacity=2,  # Small capacity for waitlist demonstration
            approved_count=2,
            pending_count=0,
            status=PeriodStatus.FULL
        )
        session.add(period2)

        # Period 3: Current ongoing period (Arrived today!)
        period3 = RetreatPeriod(
            period_name="فترة خلوة النصف الأخير من الشهر (الحالية)",
            start_date=today,
            end_date=today + timedelta(days=3),
            departure_date=today + timedelta(days=3),
            nights_count=3,
            capacity=15,
            approved_count=2,
            pending_count=0,
            status=PeriodStatus.OPEN
        )
        session.add(period3)

        # Period 4: Completed Historical Period
        period4 = RetreatPeriod(
            period_name="فترة خلوة شهر مارس (أرشيف)",
            start_date=today - timedelta(days=60),
            end_date=today - timedelta(days=57),
            departure_date=today - timedelta(days=57),
            nights_count=3,
            capacity=20,
            approved_count=18,
            status=PeriodStatus.COMPLETED
        )
        session.add(period4)
        await session.flush()

        print("[*] Seeding Applicant Profiles & Booking Scenarios...")
        
        # Doc Guest 1: Maria Fayez (Approved in Period 1)
        u_maria = User(
            email="maria@example.com",
            password_hash=get_password_hash("Guest@12345"),
            role=UserRole.APPLICANT,
            is_active=True,
            is_verified=True
        )
        session.add(u_maria)
        await session.flush()

        p_maria = Profile(
            user_id=u_maria.id,
            full_name="ماريا فايز حبيب",
            national_id_number="29904120101248",
            birth_date=date(1999, 4, 12),
            phone_number="01012345678",
            governorate="القاهرة",
            diocese="إبراشية شبرا الخيمة",
            church="كنيسة الشهيد مارجرجس",
            total_retreats_count=2,
            last_retreat_date=today - timedelta(days=150)
        )
        session.add(p_maria)
        await session.flush()

        b_maria = Booking(
            booking_reference="DMR-2026-000100",
            profile_id=p_maria.id,
            period_id=period1.id,
            status=BookingStatus.APPROVED,
            agreed_to_rules=True
        )
        session.add(b_maria)
        await session.flush()

        att_maria = Attendance(
            booking_id=b_maria.id,
            period_id=period1.id,
            profile_id=p_maria.id,
            attendance_status=AttendanceStatus.EXPECTED
        )
        session.add(att_maria)

        # Doc Guest 2: Laila Abdelmassih (Has Active Warning / Note)
        u_laila = User(
            email="laila@example.com",
            password_hash=get_password_hash("Guest@12345"),
            role=UserRole.APPLICANT,
            is_active=True,
            is_verified=True
        )
        session.add(u_laila)
        await session.flush()

        p_laila = Profile(
            user_id=u_laila.id,
            full_name="ليلى عبد المسيح",
            national_id_number="30010050201242",
            birth_date=date(2000, 10, 5),
            phone_number="01223344556",
            governorate="الإسكندرية",
            diocese="إبراشية الإسكندرية",
            church="كنيسة المرقسية الكبرى",
            has_active_warning=True,
            total_retreats_count=1,
            last_retreat_date=today - timedelta(days=120)
        )
        session.add(p_laila)
        await session.flush()

        note_laila = AdministrativeNote(
            profile_id=p_laila.id,
            author_user_id=mother_official.id,
            author_name_cache="الأم المسؤولة",
            note_type="BEHAVIOR",
            severity=NoteSeverity.HIGH,
            content="المتقدمة تأخرت سابقاً عن موعد إطفاء الأنوار واستخدمت الهاتف بالقلاية. تتطلب موافقة خاصة.",
            recommendation=NoteRecommendation.SUPERVISOR_ATTENTION,
            is_active=True
        )
        session.add(note_laila)

        b_laila = Booking(
            booking_reference="DMR-2026-000101",
            profile_id=p_laila.id,
            period_id=period1.id,
            status=BookingStatus.UNDER_REVIEW,
            agreed_to_rules=True
        )
        session.add(b_laila)

        # Doc Guest 3: Rania Girgis (Cooldown Interval Exception Request)
        u_rania = User(
            email="rania@example.com",
            password_hash=get_password_hash("Guest@12345"),
            role=UserRole.APPLICANT,
            is_active=True,
            is_verified=True
        )
        session.add(u_rania)
        await session.flush()

        p_rania = Profile(
            user_id=u_rania.id,
            full_name="رانيا جرجس أسعد",
            national_id_number="29706202401244",
            birth_date=date(1997, 6, 20),
            phone_number="01144556677",
            governorate="المنيا",
            diocese="إبراشية المنيا وأبوقرقاص",
            church="كنيسة الأمير تادرس بالمنيا",
            total_retreats_count=3,
            last_retreat_date=today - timedelta(days=40)
        )
        session.add(p_rania)
        await session.flush()

        b_rania = Booking(
            booking_reference="DMR-2026-000102",
            profile_id=p_rania.id,
            period_id=period1.id,
            status=BookingStatus.UNDER_REVIEW,
            has_interval_exception=True,
            interval_exception_reason="قادمة من المنيا مع مجموعة من خدام كنيستها وتطلب استثناء الفاصل الزمني (40 يوماً فقط).",
            interval_exception_status=ExceptionStatus.PENDING,
            agreed_to_rules=True
        )
        session.add(b_rania)

        # Doc Guest 4: Church Test Account
        u_test = User(
            email="church-test@example.com",
            password_hash=get_password_hash("TestPass@123"),
            role=UserRole.APPLICANT,
            is_active=True,
            is_verified=True
        )
        session.add(u_test)
        await session.flush()

        p_test = Profile(
            user_id=u_test.id,
            full_name="حساب اختباري كنيسة",
            national_id_number="29501011201246",
            birth_date=date(1995, 1, 1),
            phone_number="01099998888",
            governorate="الدقهلية",
            diocese="إبراشية المنصورة",
            church="كنيسة العذراء بالمنصورة",
            total_retreats_count=0
        )
        session.add(p_test)
        await session.flush()

        # Guest 5: Sandra (Waitlist in Period 2)
        u_sandra = User(
            email="sandra.mounir@example.com",
            password_hash=get_password_hash("Sandra123456!"),
            role=UserRole.APPLICANT,
            is_active=True,
            is_verified=True
        )
        session.add(u_sandra)
        await session.flush()

        p_sandra = Profile(
            user_id=u_sandra.id,
            full_name="ساندرا منير يوسف",
            national_id_number="30303180201248",
            birth_date=date(2003, 3, 18),
            phone_number="01077889900",
            governorate="الإسكندرية",
            diocese="إبراشية الإسكندرية",
            church="كنيسة القديسين مارمرقس والبابا بطرس",
            total_retreats_count=0
        )
        session.add(p_sandra)
        await session.flush()

        b_sandra = Booking(
            booking_reference="DMR-2026-000104",
            profile_id=p_sandra.id,
            period_id=period2.id,
            status=BookingStatus.WAITING_LIST,
            agreed_to_rules=True
        )
        session.add(b_sandra)
        await session.flush()

        wl_sandra = Waitlist(
            period_id=period2.id,
            profile_id=p_sandra.id,
            booking_id=b_sandra.id,
            queue_number=1,
            status=WaitlistStatus.WAITING
        )
        session.add(wl_sandra)

        # Guest 6: Verena (Checked-in today in Period 3 & requested extension)
        u_verena = User(
            email="verena.nabil@example.com",
            password_hash=get_password_hash("Verena123456!"),
            role=UserRole.APPLICANT,
            is_active=True,
            is_verified=True
        )
        session.add(u_verena)
        await session.flush()

        p_verena = Profile(
            user_id=u_verena.id,
            full_name="فيرينا نبيل عزمي",
            national_id_number="29909091601240",
            birth_date=date(1999, 9, 9),
            phone_number="01133221100",
            governorate="الغربية",
            diocese="إبراشية طنطا وتوابعها",
            church="كنيسة مارجرجس بطنطا",
            total_retreats_count=1
        )
        session.add(p_verena)
        await session.flush()

        b_verena = Booking(
            booking_reference="DMR-2026-000105",
            profile_id=p_verena.id,
            period_id=period3.id,
            status=BookingStatus.EXTENSION_REQUESTED,
            agreed_to_rules=True
        )
        session.add(b_verena)
        await session.flush()

        att_verena = Attendance(
            booking_id=b_verena.id,
            period_id=period3.id,
            profile_id=p_verena.id,
            checked_in_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3),
            checked_in_by_user_id=reception_user.id,
            attendance_status=AttendanceStatus.CHECKED_IN,
            room_or_cell_number="قلاية رقم 7"
        )
        session.add(att_verena)

        ext_verena = ExtensionRequest(
            booking_id=b_verena.id,
            profile_id=p_verena.id,
            requested_additional_days=1,
            reason="ظروف مواصلات وسفر طويل",
            detailed_explanation="أرغب في مد الخلوة يوماً إضافياً لإنهاء قراءة المزامير والتأمل في هدوء الدير.",
            status=ExtensionStatus.PENDING
        )
        session.add(ext_verena)

        await session.commit()
        print("[SUCCESS] Database successfully seeded with all production accounts and scenarios!")

if __name__ == "__main__":
    asyncio.run(seed_database())
