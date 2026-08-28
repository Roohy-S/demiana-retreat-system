import os
import sys
from pathlib import Path

# Add project root and current dir to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from app.main import app
except Exception as e:
    import traceback
    print(f"[FATAL VERCEL BOOT ERROR] {e}")
    traceback.print_exc()
    raise e


