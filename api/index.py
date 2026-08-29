import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as fastapi_app

async def app(scope, receive, send):
    if scope["type"] == "http":
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        path_param = params.get("__path", [None])[0]

        final_path = "/"
        if path_param is not None:
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
            raw_matched = (
                headers.get(b"x-matched-path")
                or headers.get(b"x-vercel-matched-path")
                or headers.get(b"x-forwarded-uri")
                or headers.get(b"x-invoke-path")
            )
            if raw_matched:
                p = unquote(raw_matched.decode("utf-8")).split("?")[0]
                if p and p not in ("/api/index.py", "/index.py", "/api/index", "/api"):
                    final_path = p
                else:
                    final_path = "/"
            else:
                cur_p = scope.get("path", "/")
                if cur_p not in ("/api/index.py", "/index.py", "/api/index", "/api"):
                    final_path = cur_p
                else:
                    final_path = "/"

        scope["path"] = final_path
        scope["raw_path"] = final_path.encode("utf-8")

    await fastapi_app(scope, receive, send)
