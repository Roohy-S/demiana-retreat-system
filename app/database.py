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
            
            from app.models.settings import SystemSettings
            from app.models.user import User, UserRole
            from app.core.security import get_password_hash
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                # 1. Ensure System Settings exist
                stmt = select(SystemSettings).limit(1)
                res = await session.execute(stmt)
                if not res.scalar_one_or_none():
                    session.add(SystemSettings(
                        retreat_name="بيت الخلوة بدير القديسة دميانة",
                        monastery_location="ببراري بلقاس",
                        default_retreat_nights=3,
                        min_booking_interval_months=3,
                        min_applicant_age_years=15,
                        default_period_capacity=20,
                        allow_waitlist=True,
                        allow_extensions=True,
                        allow_exceptions=True
                    ))

                # 2. Ensure ONLY the Mother Superior Account exists
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
                
                await session.commit()
        except Exception as e:
            print(f"[DB CLEAN INIT NOTE] {e}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    await ensure_db_initialized()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
