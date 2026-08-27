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
