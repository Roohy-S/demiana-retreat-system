from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.api import api_router
from app.models.settings import SystemSettings
import app.models # Ensure all models are loaded

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize default settings if not exists
    async with AsyncSessionLocal() as session:
        stmt = select(SystemSettings).limit(1)
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            session.add(SystemSettings())
            await session.commit()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="منصة حجز وإدارة بيت الخلوة بدير القديسة دميانة العامر ببراري بلقاس",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include API Endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", response_class=HTMLResponse)
async def get_index_page(request: Request):
    html_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
  <meta name="theme-color" content="#0B0F17">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="بيت الخلوة">
  <title>بيت الخلوة – دير القديسة دميانة – ببراري بلقاس</title>
  <meta name="description" content="النظام الإلكتروني الرسمي لحجز وإدارة بيت الخلوة بدير القديسة دميانة ببراري بلقاس">
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="icon" href="/static/images/cross.png" type="image/png">
  <link rel="apple-touch-icon" href="/static/images/cross.png">
</head>
<body>
  <!-- Monastic Background Overlays -->
  <div class="monastery-bg-overlay"></div>
  <div class="monastery-vignette"></div>

  <!-- Top Navigation Bar -->
  <header class="navbar">
    <div class="container navbar-container">
      <div class="brand-section" onclick="navigate('landing')">
        <img src="/static/images/cross.png" alt="الصليب القبطي" class="brand-cross-icon" />
        <div class="brand-titles">
          <span class="brand-main-title">بيت الخلوة بدير القديسة دميانة</span>
          <span class="brand-sub-title">ببراري بلقاس – محافظة الدقهلية</span>
        </div>
      </div>

      <div class="nav-actions" id="nav-actions">
        <!-- Injected via app.js -->
      </div>
    </div>
  </header>

  <!-- Main View Container -->
  <main id="main-content">
    <!-- Injected dynamically via Router (landing, guest_dashboard, admin_dashboard, register_wizard, login) -->
  </main>

  <!-- Global Toast Notification Container -->
  <div id="toast-container" style="position:fixed; bottom:20px; right:20px; z-index:9999;"></div>

  <!-- Scripts -->
  <script src="/static/js/app.js"></script>
  <script src="/static/js/landing.js"></script>
  <script src="/static/js/registration.js"></script>
  <script src="/static/js/guest_dashboard.js"></script>
  <script src="/static/js/admin_dashboard.js"></script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
