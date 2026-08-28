import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from tests.conftest import TestAsyncSessionLocal
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.models.email_verification import EmailVerificationCode
from app.core.security import get_password_hash
from sqlalchemy import select
from datetime import date

@pytest.mark.asyncio
async def test_forgot_and_reset_password_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a verified test user in test DB
        async with TestAsyncSessionLocal() as session:
            test_user = User(
                email="maria@example.com",
                password_hash=get_password_hash("OldPassword123!"),
                role=UserRole.APPLICANT,
                is_active=True,
                is_verified=True
            )
            session.add(test_user)
            await session.flush()

            test_prof = Profile(
                user_id=test_user.id,
                full_name="ماريا فايز حبيب",
                national_id_number="29904120101248",
                birth_date=date(1999, 4, 12),
                phone_number="01012345678",
                governorate="القاهرة",
                diocese="شبرا الخيمة",
                church="مارجرجس"
            )
            session.add(test_prof)
            await session.flush()

            # Add identity document to test serialization
            from app.models.profile import IdentityDocument, Guardian, ConfessionFather
            doc = IdentityDocument(
                profile_id=test_prof.id,
                doc_type="NATIONAL_ID_FRONT",
                file_path="/tmp/nid_front.jpg",
                file_name="nid_front.jpg",
                file_size_bytes=1024,
                mime_type="image/jpeg"
            )
            guardian = Guardian(
                profile_id=test_prof.id,
                guardian_type="أب",
                full_name="فايز حبيب",
                phone_number="01099998888"
            )
            father = ConfessionFather(
                profile_id=test_prof.id,
                father_name="أبونا بيشوي",
                father_phone="01288887777",
                church_name="كنيسة مارجرجس"
            )
            session.add_all([doc, guardian, father])
            await session.commit()

        # 2. Request forgot password using Phone Number
        res_forgot = await client.post("/api/v1/auth/forgot-password", json={
            "identifier": "01012345678"
        })
        assert res_forgot.status_code == 200
        data_forgot = res_forgot.json()
        assert "تم إرسال رمز" in data_forgot["message"]

        # Fetch the generated OTP from DB
        async with TestAsyncSessionLocal() as session:
            stmt = select(EmailVerificationCode.otp_code).where(
                EmailVerificationCode.email == "maria@example.com"
            ).order_by(EmailVerificationCode.created_at.desc())
            otp = (await session.execute(stmt)).scalars().first()
            assert otp is not None
            assert len(otp) == 6

        # 3. Reset password with valid OTP and new password
        res_reset = await client.post("/api/v1/auth/reset-password", json={
            "email": "maria@example.com",
            "otp_code": otp,
            "new_password": "NewSecretPass@2026"
        })
        assert res_reset.status_code == 200
        assert "تم إعادة تعيين كلمة المرور بنجاح" in res_reset.json()["message"]

        # 4. Verify login with the new password via Email
        res_login_email = await client.post("/api/v1/auth/login", json={
            "identifier": "maria@example.com",
            "password": "NewSecretPass@2026"
        })
        assert res_login_email.status_code == 200
        assert "access_token" in res_login_email.json()

        # 5. Verify login with Phone Number
        res_login_phone = await client.post("/api/v1/auth/login", json={
            "identifier": "01012345678",
            "password": "NewSecretPass@2026"
        })
        assert res_login_phone.status_code == 200
        assert "access_token" in res_login_phone.json()

        # 6. Verify login with 14-digit National ID
        res_login_nid = await client.post("/api/v1/auth/login", json={
            "identifier": "29904120101248",
            "password": "NewSecretPass@2026"
        })
        assert res_login_nid.status_code == 200
        assert "access_token" in res_login_nid.json()
        user_token = res_login_nid.json()["access_token"]

        # 7. Verify /profile/me returns profile without lazy load errors
        res_prof = await client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {user_token}"})
        assert res_prof.status_code == 200
        prof_data = res_prof.json()
        assert prof_data["full_name"] == "ماريا فايز حبيب"
        assert len(prof_data["documents"]) == 1
        assert len(prof_data["guardians"]) == 1
        assert len(prof_data["confession_fathers"]) == 1
        assert prof_data["documents"][0]["doc_type"] == "NATIONAL_ID_FRONT"
        assert prof_data["guardians"][0]["full_name"] == "فايز حبيب"
        assert prof_data["confession_fathers"][0]["father_name"] == "أبونا بيشوي"

        # 8. Verify /bookings/my returns list of bookings
        res_my_b = await client.get("/api/v1/bookings/my", headers={"Authorization": f"Bearer {user_token}"})
        assert res_my_b.status_code == 200
        assert isinstance(res_my_b.json(), list)
