# -*- coding: utf-8 -*-
"""Verify app.py imports and /api/host-info returns public URL."""
import os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

os.environ["RENDER_EXTERNAL_URL"] = "https://my-first-app-1-4t5v.onrender.com"
import app as module
c = module.app.test_client()
r = c.get("/api/host-info")
d = r.get_json(silent=True)
print("HOST_INFO_STATUS:", r.status_code)
print("HOST_INFO_DATA  :", d)
print("PUBLIC_URL_FIX  :", bool(d and d.get("host") == "https://my-first-app-1-4t5v.onrender.com"))