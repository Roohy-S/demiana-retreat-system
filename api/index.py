import os
import sys
from pathlib import Path
from urllib.parse import parse_qs

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as fastapi_app

class VercelEntrypointMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(query_string)
            path_param = params.get("__path", [None])[0]
            
            if path_param:
                clean_p = path_param.strip("/")
                if not clean_p or clean_p == "/":
                    scope["path"] = "/"
                elif clean_p.startswith("api/"):
                    scope["path"] = "/" + clean_p
                elif clean_p.startswith("v1/"):
                    scope["path"] = "/api/" + clean_p
                else:
                    scope["path"] = "/" + clean_p
            else:
                headers = dict(scope.get("headers", []))
                raw_orig = (
                    headers.get(b"x-matched-path")
                    or headers.get(b"x-vercel-matched-path")
                    or headers.get(b"x-invoke-path")
                    or headers.get(b"x-forwarded-uri")
                )
                if raw_orig:
                    orig_path = raw_orig.decode("utf-8").split("?")[0]
                    if orig_path not in ("/api/index.py", "/index.py", "/api/index", "/api"):
                        scope["path"] = orig_path
                elif scope.get("path") in ("/api/index.py", "/index.py", "/api/index", "/api"):
                    scope["path"] = "/"

        await self.app(scope, receive, send)

app = VercelEntrypointMiddleware(fastapi_app)
