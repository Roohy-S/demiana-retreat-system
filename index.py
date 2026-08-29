import os
import sys
from pathlib import Path
from urllib.parse import parse_qs

ROOT_DIR = Path(__file__).resolve().parent
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
            
            final_path = "/"
            if path_param:
                clean_p = path_param.strip("/")
                if not clean_p or clean_p == "/":
                    final_path = "/"
                elif clean_p.startswith("api/"):
                    final_path = "/" + clean_p
                elif clean_p.startswith("v1/"):
                    final_path = "/api/" + clean_p
                else:
                    final_path = "/" + clean_p
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
                        final_path = orig_path
                    else:
                        final_path = "/"
                else:
                    cur_path = scope.get("path", "/")
                    if cur_path in ("/api/index.py", "/index.py", "/api/index", "/api"):
                        final_path = "/"
                    else:
                        final_path = cur_path

            scope["path"] = final_path
            scope["raw_path"] = final_path.encode("utf-8")

        await self.app(scope, receive, send)

app = VercelEntrypointMiddleware(fastapi_app)
