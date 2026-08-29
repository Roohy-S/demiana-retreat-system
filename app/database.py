import os
import ssl
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, select
from app.config import settings

db_url = settings.async_database_url
is_sqlite = "sqlite" in db_url

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / Supabase configuration
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    engine_kwargs["connect_args"] = {
        "ssl": ssl_context,
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 1800

engine = create_async_engine(db_url, **engine_kwargs)

if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            if not os.environ.get("VERCEL"):
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
        except Exception:
            pass

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

_DB_INITIALIZED = False

async def ensure_db_initialized():
    global _DB_INITIALIZED
    if not _DB_INITIALIZED:
        _DB_INITIALIZED = True
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Lazy import models and security helper
            from app.models.settings import SystemSettings
            from app.models.user import User, UserRole
            from app.models.period import RetreatPeriod, PeriodStatus
            from app.core.security import get_password_hash
            from datetime import date, timedelta

            async with AsyncSessionLocal() as session:
                # 1. Seed System Settings
                stmt = select(SystemSettings).limit(1)
                res = await session.execute(stmt)
                if not res.scalar_one_or_none():
                    session.add(SystemSettings())

                # 2. Seed Default Administrative Users
                user_stmt = select(User).where(User.email == "mother.superior@demiana.org")
                user_res = await session.execute(user_stmt)
                if not user_res.scalar_one_or_none():
                    session.add(User(
                        email="mother.superior@demiana.org",
                        password_hash=get_password_hash("Demiana@2026#Monastery"),
                        role=UserRole.MOTHER_SUPERIOR,
                        is_active=True,
                        is_verified=True
                    ))
                    session.add(User(
                        email="mother@stdemiana.org",
                        password_hash=get_password_hash("MotherAdmin@123"),
                        role=UserRole.MOTHER_SUPERIOR,
                        is_active=True,
                        is_verified=True
                    ))
                    session.add(User(
                        email="sister.supervisor@demiana.org",
                        password_hash=get_password_hash("Demiana@2026#Monastery"),
                        role=UserRole.BOOKING_SUPERVISOR,
                        is_active=True,
                        is_verified=True
                    ))
                    session.add(User(
                        email="reception@demiana.org",
                        password_hash=get_password_hash("Demiana@2026#Monastery"),
                        role=UserRole.RECEPTION_SUPERVISOR,
                        is_active=True,
                        is_verified=True
                    ))

                # 3. Seed Upcoming Retreat Periods
                p_stmt = select(RetreatPeriod).limit(1)
                p_res = await session.execute(p_stmt)
                if not p_res.scalar_one_or_none():
                    today = date.today()
                    days_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

                    def make_title(s_date, e_date, nights):
                        s_day = days_ar[s_date.weekday()]
                        e_day = days_ar[e_date.weekday()]
                        return f"فترة خلوة: من {s_day} {s_date.strftime('%d-%m-%Y')} إلى {e_day} {e_date.strftime('%d-%m-%Y')} ({nights} ليالي)"

                    for d_offset in [3, 10, 17, 24]:
                        s_d = today + timedelta(days=d_offset)
                        e_d = s_d + timedelta(days=3)
                        session.add(RetreatPeriod(
                            period_name=make_title(s_d, e_d, 3),
                            start_date=s_d,
                            end_date=e_d,
                            departure_date=e_d,
                            arrival_time_desc="الساعة 12:00 ظهراً",
                            departure_time_desc="قبل الساعة 9:00 صباحاً",
                            nights_count=3,
                            capacity=20,
                            status=PeriodStatus.OPEN
                        ))
                
                await session.commit()
        except Exception as e:
            print(f"[DB AUTO-INIT NOTE] {e}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    await ensure_db_initialized()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
