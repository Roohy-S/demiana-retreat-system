import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date
from app.main import app
from app.models.user import User, UserRole
from app.models.period import RetreatPeriod, PeriodStatus
from app.models.profile import Profile
from app.models.booking import Booking, BookingStatus
from app.core.security import create_access_token
from tests.conftest import TestAsyncSessionLocal

@pytest.mark.asyncio
async def test_email_validation_and_disposable_blocking():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test Disposable Email Rejection
        disposable_payload = {
            "email": "applicant@tempmail.com",
            "password": "Password123!",
            "full_name": "سارة جورج فؤاد كامل",
            "national_id_number": "30005121201242",
            "birth_date": "2000-05-12",
            "phone_number": "01055554444",
            "governorate": "الدقهلية",
            "diocese": "بلقاس",
            "church": "دير القديسة دميانة",
            "guardian_type": "أب",
            "guardian_name": "جورج فؤاد كامل",
            "guardian_phone": "01255554444",
            "confession_father_name": "أبونا بطرس",
            "confession_father_phone": "01155554444",
            "confession_church": "دير دميانة"
        }
        res_disp = await client.post("/api/v1/auth/register", json=disposable_payload)
        assert res_disp.status_code == 422
        assert "المؤقت" in str(res_disp.json()) or "غير مسموح" in str(res_disp.json())

        # 2. Test Typo Email Rejection & Correction Suggestion
        typo_payload = {
            **disposable_payload,
            "email": "sarah.george@gmil.com"
        }
        res_typo = await client.post("/api/v1/auth/register", json=typo_payload)
        assert res_typo.status_code == 422
        assert "خطأ إملائي" in str(res_typo.json()) or "gmail.com" in str(res_typo.json())

        # 3. Test check-duplicate preflight endpoint for email
        res_chk_typo = await client.post("/api/v1/auth/check-duplicate", json={
            "field": "email",
            "email": "sarah.george@gmial.com"
        })
        assert res_chk_typo.status_code == 200
        data_chk = res_chk_typo.json()
        assert data_chk["is_available"] == False
        assert "خطأ إملائي" in data_chk["message"] or "gmail.com" in data_chk["message"]

@pytest.mark.asyncio
async def test_national_id_validation_and_cross_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid National ID length
        payload_invalid_len = {
            "email": "valid.person@gmail.com",
            "password": "Password123!",
            "full_name": "ماريا رأفت حليم بولس",
            "national_id_number": "12345",  # Too short
            "birth_date": "2001-08-20",
            "phone_number": "01077778888",
            "governorate": "القاهرة",
            "diocese": "مصر القديمة",
            "church": "مارمينا",
            "guardian_type": "أب",
            "guardian_name": "رأفت حليم بولس",
            "guardian_phone": "01277778888",
            "confession_father_name": "أبونا يوسف",
            "confession_father_phone": "01177778888",
            "confession_church": "مارمينا"
        }
        res1 = await client.post("/api/v1/auth/register", json=payload_invalid_len)
        assert res1.status_code == 422

        # Mismatch between National ID birthdate (2001-08-20 -> 3010820...) and entered birth date
        payload_mismatch = {
            **payload_invalid_len,
            "national_id_number": "30108200101246",  # 2001-08-20
            "birth_date": "1999-01-01"  # Mismatch!
        }
        res2 = await client.post("/api/v1/auth/register", json=payload_mismatch)
        assert res2.status_code == 422
        assert "غير متطابق" in str(res2.json())

@pytest.mark.asyncio
async def test_multi_level_duplicate_detection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register base person
        base_payload = {
            "email": "veronica.samir@gmail.com",
            "password": "Password123!",
            "full_name": "فيرونيكا سمير رشدي كامل",
            "national_id_number": "29910151201246",  # 1999-10-15
            "birth_date": "1999-10-15",
            "phone_number": "01099887766",
            "governorate": "الدقهلية",
            "diocese": "المنصورة",
            "church": "مارجرجس",
            "guardian_type": "أب",
            "guardian_name": "سمير رشدي كامل",
            "guardian_phone": "01299887766",
            "confession_father_name": "أبونا مينا",
            "confession_father_phone": "01199887766",
            "confession_church": "مارجرجس"
        }
        res_init = await client.post("/api/v1/auth/register", json=base_payload)
        assert res_init.status_code == 200

        # Verify email to make account active
        async with TestAsyncSessionLocal() as session:
            from app.models.email_verification import EmailVerificationCode
            from sqlalchemy import select
            stmt = select(EmailVerificationCode.otp_code).where(EmailVerificationCode.email == "veronica.samir@gmail.com")
            otp = (await session.execute(stmt)).scalars().first()

        v_res = await client.post("/api/v1/auth/verify-email", json={"email": "veronica.samir@gmail.com", "otp_code": otp})
        assert v_res.status_code == 200
        token_veronica = v_res.json()["access_token"]

        # 2. Attempt duplicate: Same phone number with different email and different name
        dup_phone_payload = {
            **base_payload,
            "email": "different.email@gmail.com",
            "full_name": "تريزا صبحي عازر جرجس",
            "national_id_number": "30104051201248",
            "birth_date": "2001-04-05",
            "phone_number": "01099887766"  # Duplicate phone!
        }
        res_dup_phone = await client.post("/api/v1/auth/register", json=dup_phone_payload)
        assert res_dup_phone.status_code == 400
        assert "رقم الهاتف" in res_dup_phone.json()["detail"] and "مسجل بالفعل" in res_dup_phone.json()["detail"]

        # 3. Attempt duplicate: Same National ID with different email and phone
        dup_nid_payload = {
            **base_payload,
            "email": "another.email@gmail.com",
            "full_name": "تريزا صبحي عازر جرجس",
            "phone_number": "01011223344",
            "national_id_number": "29910151201246"  # Duplicate National ID!
        }
        res_dup_nid = await client.post("/api/v1/auth/register", json=dup_nid_payload)
        assert res_dup_nid.status_code == 400
        assert "الرقم القومي" in res_dup_nid.json()["detail"] and "مسجل بالفعل" in res_dup_nid.json()["detail"]

        # 4. Attempt duplicate: Same Arabic Name + Birth Date with different email, phone, and national ID
        dup_identity_payload = {
            "email": "fake.new.account@gmail.com",
            "password": "Password123!",
            "full_name": "فيرونيكا سمير رشدي كامل",  # Same person
            "national_id_number": "29910151601248",  # Different ID, same birth date (1999-10-15)
            "birth_date": "1999-10-15",
            "phone_number": "01066554433",
            "governorate": "الغربية",
            "diocese": "طنطا",
            "church": "مارجرجس",
            "guardian_type": "أب",
            "guardian_name": "سمير رشدي كامل",
            "guardian_phone": "01266554433",
            "confession_father_name": "أبونا مينا",
            "confession_father_phone": "01166554433",
            "confession_church": "مارجرجس"
        }
        res_dup_identity = await client.post("/api/v1/auth/register", json=dup_identity_payload)
        assert res_dup_identity.status_code == 400
        assert "بيانات مسجلة بالفعل" in res_dup_identity.json()["detail"] or "تطابق" in res_dup_identity.json()["detail"]

        # 5. Test updating profile with a phone number that is already used
        res_update_dup = await client.put(
            "/api/v1/profile/me",
            json={"phone_number": "01099887766"},  # Same phone for self is OK
            headers={"Authorization": f"Bearer {token_veronica}"}
        )
        assert res_update_dup.status_code == 200

@pytest.mark.asyncio
async def test_admin_duplicates_audit_and_notes_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Mother Superior
        async with TestAsyncSessionLocal() as session:
            admin_user = User(
                email="mother.audit@demiana.org",
                password_hash="hashedpass",
                role=UserRole.MOTHER_SUPERIOR,
                is_active=True,
                is_verified=True
            )
            session.add(admin_user)
            await session.commit()
            token_admin = create_access_token({"sub": admin_user.id, "role": admin_user.role, "email": admin_user.email})

        # Test Duplicates Audit Endpoint
        res_audit = await client.get("/api/v1/admin/duplicates/audit", headers={"Authorization": f"Bearer {token_admin}"})
        assert res_audit.status_code == 200
        data = res_audit.json()
        assert "total_duplicates_flagged" in data
        assert "audit_items" in data

        # Test Note Lifecycle: Create note -> check warning -> deactivate -> check warning cleared
        async with TestAsyncSessionLocal() as session:
            u_test = User(email="noted.user@demiana.org", password_hash="pass", role=UserRole.APPLICANT, is_active=True, is_verified=True)
            session.add(u_test)
            await session.flush()
            p_test = Profile(user_id=u_test.id, full_name="نادية كمال شحاتة", birth_date=date(1995, 3, 10), phone_number="01099880011", governorate="القاهرة", diocese="المعادي", church="العذراء")
            session.add(p_test)
            await session.commit()
            prof_id = p_test.id

        # Mother adds note
        res_add_note = await client.post(
            "/api/v1/admin-notes/notes",
            json={"profile_id": prof_id, "content": "ملاحظة تدقيق", "severity": "HIGH", "recommendation": "SUPERVISOR_ATTENTION"},
            headers={"Authorization": f"Bearer {token_admin}"}
        )
        assert res_add_note.status_code == 200
        note_id = res_add_note.json()["id"]

        # Deactivate note
        res_deact = await client.put(f"/api/v1/admin-notes/notes/{note_id}/deactivate", headers={"Authorization": f"Bearer {token_admin}"})
        assert res_deact.status_code == 200
        assert res_deact.json()["is_active"] == False
