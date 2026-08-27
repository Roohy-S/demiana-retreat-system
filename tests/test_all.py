import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import date, timedelta
from sqlalchemy import select
from app.main import app
from app.database import engine, Base, AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.period import RetreatPeriod, PeriodStatus
from app.models.profile import Profile
from app.models.admin_notes import AdministrativeNote, NoteSeverity
from app.models.booking import Booking, BookingStatus
from app.models.email_verification import EmailVerificationCode
from app.core.security import get_password_hash, create_access_token

from tests.conftest import TestAsyncSessionLocal as AsyncSessionLocal

@pytest.mark.asyncio
async def test_auth_and_gmail_otp_verification_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Invalid Egyptian Phone & Short name should fail validation
        invalid_payload = {
            "email": "test.applicant@gmail.com",
            "password": "Password123!",
            "full_name": "مريم", # Too short
            "national_id_number": "30001151201246",
            "birth_date": "2000-01-15",
            "phone_number": "01999999999", # Invalid Egyptian prefix
            "governorate": "الدقهلية",
            "diocese": "إبراشية بلقاس",
            "church": "كنيسة العذراء",
            "guardian_type": "أب",
            "guardian_name": "أنيس فهيم حنا",
            "guardian_phone": "01223344556",
            "confession_father_name": "أبونا أنطونيوس كمال",
            "confession_father_phone": "01122334455",
            "confession_church": "كنيسة العذراء"
        }
        res_inv = await client.post("/api/v1/auth/register", json=invalid_payload)
        assert res_inv.status_code == 422 # Validation error

        # 2. Register valid applicant
        valid_payload = {
            "email": "test.applicant@gmail.com",
            "password": "Password123!",
            "full_name": "مريم أنيس فهيم حنا",
            "national_id_number": "30001151201246",
            "birth_date": "2000-01-15",
            "phone_number": "01001122334",
            "governorate": "الدقهلية",
            "diocese": "إبراشية بلقاس",
            "church": "كنيسة العذراء",
            "guardian_type": "أب",
            "guardian_name": "أنيس فهيم حنا",
            "guardian_phone": "01223344556",
            "confession_father_name": "أبونا أنطونيوس كمال",
            "confession_father_phone": "01122334455",
            "confession_church": "كنيسة العذراء"
        }
        reg_res = await client.post("/api/v1/auth/register", json=valid_payload)
        assert reg_res.status_code == 200
        reg_data = reg_res.json()
        assert reg_data["requires_verification"] == True
        assert reg_data["email"] == "test.applicant@gmail.com"

        # 3. Attempt to login before OTP verification -> Must be BLOCKED with 403
        login_blocked = await client.post("/api/v1/auth/login", json={
            "email": "test.applicant@gmail.com",
            "password": "Password123!"
        })
        assert login_blocked.status_code == 403
        assert "EMAIL_NOT_VERIFIED" in login_blocked.json()["detail"]

        # 4. Fetch the latest generated OTP code from database
        async with AsyncSessionLocal() as session:
            stmt = select(EmailVerificationCode).where(
                EmailVerificationCode.email == "test.applicant@gmail.com"
            ).order_by(EmailVerificationCode.created_at.desc())
            code_obj = (await session.execute(stmt)).scalars().first()
            assert code_obj is not None
            valid_otp = code_obj.otp_code
            assert len(valid_otp) == 6

        # 5. Submit invalid OTP
        wrong_res = await client.post("/api/v1/auth/verify-email", json={
            "email": "test.applicant@gmail.com",
            "otp_code": "000000"
        })
        assert wrong_res.status_code == 400

        # 6. Submit valid OTP -> MUST succeed and return access token
        verify_res = await client.post("/api/v1/auth/verify-email", json={
            "email": "test.applicant@gmail.com",
            "otp_code": valid_otp
        })
        assert verify_res.status_code == 200
        token_data = verify_res.json()
        assert "access_token" in token_data
        assert token_data["role"] == UserRole.APPLICANT

        # 7. Login now succeeds!
        login_res = await client.post("/api/v1/auth/login", json={
            "email": "test.applicant@gmail.com",
            "password": "Password123!"
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

@pytest.mark.asyncio
async def test_booking_capacity_and_waitlist_engine():
    # Setup Mother Superior and a period with capacity 1
    async with AsyncSessionLocal() as session:
        adm = User(
            email="mother@demiana.org",
            password_hash=get_password_hash("Admin123!"),
            role=UserRole.MOTHER_SUPERIOR,
            is_active=True,
            is_verified=True
        )
        session.add(adm)
        await session.flush()

        period = RetreatPeriod(
            period_name="فترة اختبار السعة",
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=13),
            departure_date=date.today() + timedelta(days=13),
            capacity=1,
            approved_count=0,
            status=PeriodStatus.OPEN
        )
        session.add(period)
        await session.commit()
        period_id = period.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register User 1
        u1_res = await client.post("/api/v1/auth/register", json={
            "email": "user1@example.com",
            "password": "Password123!",
            "full_name": "المتقدمة الأولى سمير حنا",
            "national_id_number": "29805100101248",
            "birth_date": "1998-05-10",
            "phone_number": "01011111111",
            "governorate": "القاهرة",
            "diocese": "مصر الجديدة",
            "church": "مارمرقس",
            "guardian_type": "أب",
            "guardian_name": "سمير حنا بطرس",
            "guardian_phone": "01211111111",
            "confession_father_name": "أبونا يوحنا زكريا",
            "confession_father_phone": "01111111111",
            "confession_church": "مارمرقس"
        })
        
        # Verify User 1
        async with AsyncSessionLocal() as session:
            stmt = select(EmailVerificationCode).where(EmailVerificationCode.email == "user1@example.com")
            otp1 = (await session.execute(stmt)).scalars().first().otp_code
        
        v1 = await client.post("/api/v1/auth/verify-email", json={"email": "user1@example.com", "otp_code": otp1})
        t1 = v1.json()["access_token"]

        # User 1 Submits booking -> Under review
        b1_res = await client.post(
            "/api/v1/bookings/submit",
            json={"period_id": period_id, "agreed_to_rules": True},
            headers={"Authorization": f"Bearer {t1}"}
        )
        assert b1_res.status_code == 200
        b1_data = b1_res.json()
        assert b1_data["status"] == "UNDER_REVIEW"

        # Mother Superior approves booking 1
        admin_token = create_access_token({"sub": adm.id, "role": UserRole.MOTHER_SUPERIOR, "email": adm.email})
        appr_res = await client.post(
            f"/api/v1/admin/bookings/{b1_data['id']}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "APPROVED"

        # Register User 2
        u2_res = await client.post("/api/v1/auth/register", json={
            "email": "user2@example.com",
            "password": "Password123!",
            "full_name": "المتقدمة الثانية فكري خليل",
            "national_id_number": "29906120201244",
            "birth_date": "1999-06-12",
            "phone_number": "01022222222",
            "governorate": "الإسكندرية",
            "diocese": "الإسكندرية",
            "church": "القديسين",
            "guardian_type": "أم",
            "guardian_name": "سامية خليل فكري",
            "guardian_phone": "01222222222",
            "confession_father_name": "أبونا بيشوي رمزي",
            "confession_father_phone": "01122222222",
            "confession_church": "القديسين"
        })
        
        async with AsyncSessionLocal() as session:
            stmt2 = select(EmailVerificationCode).where(EmailVerificationCode.email == "user2@example.com")
            otp2 = (await session.execute(stmt2)).scalars().first().otp_code
        
        v2 = await client.post("/api/v1/auth/verify-email", json={"email": "user2@example.com", "otp_code": otp2})
        t2 = v2.json()["access_token"]

        # User 2 Submits booking -> Capacity full (1 approved) -> MUST GO TO WAITING_LIST
        b2_res = await client.post(
            "/api/v1/bookings/submit",
            json={"period_id": period_id, "agreed_to_rules": True},
            headers={"Authorization": f"Bearer {t2}"}
        )
        assert b2_res.status_code == 200
        b2_data = b2_res.json()
        assert b2_data["status"] == "WAITING_LIST"

@pytest.mark.asyncio
async def test_rebooking_with_administrative_note_alert():
    async with AsyncSessionLocal() as session:
        adm = User(
            email="mother@demiana.org",
            password_hash=get_password_hash("Admin123!"),
            role=UserRole.MOTHER_SUPERIOR,
            is_active=True,
            is_verified=True
        )
        session.add(adm)

        period = RetreatPeriod(
            period_name="فترة التنبيه الإداري",
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=23),
            departure_date=date.today() + timedelta(days=23),
            capacity=20,
            status=PeriodStatus.OPEN
        )
        session.add(period)
        await session.commit()
        period_id = period.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register applicant
        await client.post("/api/v1/auth/register", json={
            "email": "warned.guest@example.com",
            "password": "Password123!",
            "full_name": "سارة عادل نجيب ميخائيل",
            "national_id_number": "29703212101242",
            "birth_date": "1997-03-21",
            "phone_number": "01033333333",
            "governorate": "الجيزة",
            "diocese": "الجيزة",
            "church": "مارمرقس",
            "guardian_type": "أب",
            "guardian_name": "عادل نجيب ميخائيل",
            "guardian_phone": "01233333333",
            "confession_father_name": "أبونا متى مرقس",
            "confession_father_phone": "01133333333",
            "confession_church": "مارمرقس"
        })
        
        async with AsyncSessionLocal() as session:
            stmt = select(EmailVerificationCode).where(EmailVerificationCode.email == "warned.guest@example.com")
            otp = (await session.execute(stmt)).scalars().first().otp_code

        v_res = await client.post("/api/v1/auth/verify-email", json={"email": "warned.guest@example.com", "otp_code": otp})
        token = v_res.json()["access_token"]

        # Mother Superior adds a confidential note
        admin_token = create_access_token({"sub": adm.id, "role": UserRole.MOTHER_SUPERIOR, "email": adm.email})
        
        # Get profile ID
        prof_res = await client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
        profile_id = prof_res.json()["id"]

        note_res = await client.post(
            "/api/v1/admin-notes/notes",
            json={
                "profile_id": profile_id,
                "content": "ملاحظة سلوكية سابقة تتطلب انتباه الإدارة",
                "severity": "HIGH",
                "recommendation": "SUPERVISOR_ATTENTION"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert note_res.status_code == 200

        # Now applicant attempts to submit a booking
        b_res = await client.post(
            "/api/v1/bookings/submit",
            json={"period_id": period_id, "agreed_to_rules": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert b_res.status_code == 200
        # The note MUST NOT be visible to applicant, status is UNDER_REVIEW
        assert "ملاحظة سلوكية" not in str(b_res.json())

        # Check that Mother Superior received an URGENT alert notification
        notifs_res = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert notifs_res.status_code == 200
        notifs = notifs_res.json()
        assert any("تنبيه إداري" in n["title"] for n in notifs)

@pytest.mark.asyncio
async def test_gate_checkin_and_pdf_generation():
    # Setup period, approved booking, and check-in
    async with AsyncSessionLocal() as session:
        adm = User(
            email="reception.staff@demiana.org",
            password_hash=get_password_hash("Staff123!"),
            role=UserRole.RECEPTION_SUPERVISOR,
            is_active=True,
            is_verified=True
        )
        session.add(adm)

        period = RetreatPeriod(
            period_name="فترة فحص البوابة",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            departure_date=date.today() + timedelta(days=3),
            capacity=10,
            approved_count=1,
            status=PeriodStatus.OPEN
        )
        session.add(period)
        await session.commit()
        period_id = period.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/auth/register", json={
            "email": "gate.guest@example.com",
            "password": "Password123!",
            "full_name": "هيلانة فكري شاكر سوريال",
            "national_id_number": "30209091201240",
            "birth_date": "2002-09-09",
            "phone_number": "01099881122",
            "governorate": "الدقهلية",
            "diocese": "بلقاس",
            "church": "دير القديسة دميانة",
            "guardian_type": "أب",
            "guardian_name": "فكري شاكر سوريال",
            "guardian_phone": "01299881122",
            "confession_father_name": "أبونا بولس زكي",
            "confession_father_phone": "01199881122",
            "confession_church": "دير دميانة"
        })
        
        async with AsyncSessionLocal() as session:
            stmt = select(EmailVerificationCode).where(EmailVerificationCode.email == "gate.guest@example.com")
            otp = (await session.execute(stmt)).scalars().first().otp_code

        v_res = await client.post("/api/v1/auth/verify-email", json={"email": "gate.guest@example.com", "otp_code": otp})
        token = v_res.json()["access_token"]
        
        b_res = await client.post(
            "/api/v1/bookings/submit",
            json={"period_id": period_id, "agreed_to_rules": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        booking_id = b_res.json()["id"]

        staff_token = create_access_token({"sub": adm.id, "role": UserRole.RECEPTION_SUPERVISOR, "email": adm.email})
        
        # Approve booking
        await client.post(
            f"/api/v1/admin/bookings/{booking_id}/approve",
            headers={"Authorization": f"Bearer {staff_token}"}
        )

        # Gate Check-in "وصلت"
        checkin_res = await client.post(
            "/api/v1/attendance/check-in",
            json={"booking_id": booking_id, "room_or_cell_number": "قلاية 12"},
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert checkin_res.status_code == 200
        assert checkin_res.json()["attendance_status"] == "CHECKED_IN"
        assert checkin_res.json()["room_or_cell_number"] == "قلاية 12"

        # Download Reception Gate Sheet PDF
        pdf_res = await client.get(
            f"/api/v1/reports/gate-pdf/{period_id}",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert len(pdf_res.content) > 500  # valid binary PDF content
