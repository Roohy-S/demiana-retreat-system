import os
import sys
import traceback
from pathlib import Path

# Ensure root directory and app directory are always in sys.path
_FILE_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _FILE_DIR.parent

for _p in [str(_ROOT_DIR), str(_FILE_DIR), os.getcwd()]:
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from contextlib import asynccontextmanager
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
except Exception as _e:
    print(f"[FATAL ERROR IMPORTING APP/MAIN.PY] {_e}", file=sys.stderr)
    traceback.print_exc()
    raise _e

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload and data directories exist
    try:
        upload_path = Path(settings.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        if "sqlite" in settings.DATABASE_URL:
            db_path_str = settings.DATABASE_URL.split("///")[-1]
            if db_path_str and not db_path_str.startswith(":memory:"):
                Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Initialize default settings if not exists
        async with AsyncSessionLocal() as session:
            stmt = select(SystemSettings).limit(1)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                session.add(SystemSettings())
                await session.commit()
    except Exception as e:
        print(f"[STARTUP WARNING] DB init note: {e}")
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

from fastapi.responses import HTMLResponse, FileResponse, Response

# Static Files Candidate Search
STATIC_DIR = Path(__file__).resolve().parent / "static"
if not STATIC_DIR.exists():
    STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/static/{file_path:path}")
async def serve_static_file(file_path: str):
    candidates = [
        STATIC_DIR / file_path,
        Path(__file__).resolve().parent / "static" / file_path,
        Path(__file__).resolve().parent.parent / "app" / "static" / file_path,
        Path(__file__).resolve().parent.parent / "static" / file_path
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            media_type = None
            if file_path.endswith(".css"):
                media_type = "text/css"
            elif file_path.endswith(".js"):
                media_type = "application/javascript"
            elif file_path.endswith(".png"):
                media_type = "image/png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                media_type = "image/jpeg"
            elif file_path.endswith(".svg"):
                media_type = "image/svg+xml"
            elif file_path.endswith(".ico"):
                media_type = "image/x-icon"
            return FileResponse(str(candidate), media_type=media_type)
    return Response(status_code=404, content="Static file not found")

def get_cached_css() -> str:
    candidates = [
        STATIC_DIR / "css" / "style.css",
        Path(__file__).resolve().parent / "static" / "css" / "style.css",
        Path(__file__).resolve().parent.parent / "static" / "css" / "style.css",
        Path(__file__).resolve().parent.parent / "public" / "static" / "css" / "style.css",
        Path(__file__).resolve().parent.parent / "public" / "css" / "style.css"
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            try:
                return c.read_text(encoding="utf-8")
            except Exception:
                pass
    return ""

# Include API Endpoints on all standard prefixes
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/v1")
app.include_router(api_router, prefix="/api")

@app.post("/api/index.py")
@app.post("/api/index")
@app.post("/api")
@app.post("/index.py")
async def handle_api_fallback_post(request: Request):
    try:
        data = await request.json()
        if "identifier" in data or ("email" in data and "password" in data):
            from app.api.auth import login
            from app.schemas.auth import UserLogin
            from app.database import get_db
            payload = UserLogin(**data)
            async for db in get_db():
                return await login(payload, request, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=404, detail="Endpoint not found")

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
@app.get("/index.py", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
async def get_index_page(request: Request):
    inline_css = get_cached_css()
    html_content = f"""<!DOCTYPE html>
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
  <link rel="stylesheet" href="/static/css/style.css?v=2.8">
  <link rel="stylesheet" href="/css/style.css?v=2.8">
  <style>
    {inline_css}
  </style>
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
  <script src="/static/js/app.js?v=2.8"></script>
  <script src="/static/js/landing.js?v=2.8"></script>
  <script src="/static/js/registration.js?v=2.8"></script>
  <script src="/static/js/guest_dashboard.js?v=2.8"></script>
  <script src="/static/js/admin_dashboard.js?v=2.8"></script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
