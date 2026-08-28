import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token
from app.models.user import User, UserRole
from tests.conftest import TestAsyncSessionLocal

@pytest.mark.asyncio
async def test_admin_bookings_endpoint():
    async with TestAsyncSessionLocal() as session:
        # Create an admin user in DB
        admin_user = User(
            id="test-mother-superior-id",
            email="mother_superior_test_api@demiana.org",
            password_hash="test",
            role=UserRole.MOTHER_SUPERIOR,
            is_active=True
        )
        session.add(admin_user)
        await session.commit()

    token = create_access_token({"sub": "test-mother-superior-id", "role": UserRole.MOTHER_SUPERIOR, "email": "mother_superior_test_api@demiana.org"})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/admin/bookings?skip=0&limit=100", headers={"Authorization": f"Bearer {token}"})
        print("ADMIN BOOKINGS RESPONSE:", res.status_code, res.text)
        assert res.status_code == 200

        # If bookings exist, test /applicant/{profile_id}
        bookings = res.json()
        if bookings:
            first_profile_id = bookings[0]["profile_id"]
            res_dossier = await client.get(f"/api/v1/admin/applicant/{first_profile_id}", headers={"Authorization": f"Bearer {token}"})
            print("ADMIN DOSSIER RESPONSE:", res_dossier.status_code, res_dossier.text)
            assert res_dossier.status_code == 200
            data = res_dossier.json()
            assert "profile" in data
            assert "bookings" in data
            assert "violations" in data
            assert "notes" in data
            assert "audit_trails" in data
