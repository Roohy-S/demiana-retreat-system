import os
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as fastapi_app

async def app(scope, receive, send):
    if scope["type"] == "http":
        headers = dict(scope.get("headers", []))
        raw_matched = (
            headers.get(b"x-matched-path")
            or headers.get(b"x-vercel-matched-path")
            or headers.get(b"x-forwarded-uri")
            or headers.get(b"x-invoke-path")
        )
        if raw_matched:
            p = unquote(raw_matched.decode("utf-8")).split("?")[0]
            if p and p not in ("/api/index.py", "/index.py", "/api/index", "/api"):
                scope["path"] = p
                scope["raw_path"] = p.encode("utf-8")
            elif scope.get("path") in ("/api/index.py", "/index.py", "/api/index", "/api") and scope.get("method") == "GET":
                scope["path"] = "/"
                scope["raw_path"] = b"/"

    await fastapi_app(scope, receive, send)
