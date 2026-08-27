from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.periods import router as periods_router
from app.api.bookings import router as bookings_router
from app.api.admin import router as admin_router
from app.api.admin_notes import router as admin_notes_router
from app.api.attendance import router as attendance_router
from app.api.reports import router as reports_router
from app.api.notifications import router as notifications_router
from app.api.communication import router as communication_router
from app.api.staff import router as staff_router
from app.api.settings import router as settings_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(periods_router)
api_router.include_router(bookings_router)
api_router.include_router(admin_router)
api_router.include_router(admin_notes_router)
api_router.include_router(attendance_router)
api_router.include_router(reports_router)
api_router.include_router(notifications_router)
api_router.include_router(communication_router)
api_router.include_router(staff_router)
api_router.include_router(settings_router)
