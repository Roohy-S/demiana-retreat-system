import os
import sys
import time
import threading
import subprocess

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn

def run_uvicorn():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")

if __name__ == "__main__":
    # Ensure current directory is on python path
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    if cur_dir not in sys.path:
        sys.path.insert(0, cur_dir)

    print("==============================================================================")
    print("  ⛪ نظام بيت الخلوة بدير القديسة دميانة ببراري بلقاس")
    print("  🚀 جاري تشغيل الخادم وإنشاء الرابط العام المباشر...")
    print("==============================================================================")

    # 1. Start FastAPI server in a background daemon thread
    server_thread = threading.Thread(target=run_uvicorn, daemon=True)
    server_thread.start()

    # Wait 2 seconds for FastAPI server to start listening on port 8000
    time.sleep(2)

    # 2. Run Cloudflare Tunnel
    cloudflared_bin = os.path.join(cur_dir, "cloudflared.exe")
    if not os.path.exists(cloudflared_bin):
        print(f"[!] cloudflared.exe not found at {cloudflared_bin}")
        sys.exit(1)

    print("\n[*] السيرفر المحلي يعمل الآن بنجاح على http://127.0.0.1:8000")
    print("[*] جاري توليد الرابط التجريبي العام (HTTPS) خلال ثوانٍ...\n")

    try:
        subprocess.run([cloudflared_bin, "tunnel", "--url", "http://127.0.0.1:8000"])
    except KeyboardInterrupt:
        print("\n[*] تم إيقاف السيرفر بنجاح.")
