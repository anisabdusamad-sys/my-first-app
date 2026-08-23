# -*- coding: utf-8 -*-
"""
Таҳрири автоматии ислоҳот: CORS + Admin API URL + интиқоли api_key.
Бе оғози серверҳо — танҳо Flask test_client истифода мешавад.
Иҷро:  python verify_fix.py   (натиҷа дар verify_result.txt ҳам сабт мешавад)
"""
import os
import sys
import io
import sqlite3
import tempfile

# Дар Windows-консоль (cp1251) эмодзиҳо боиси UnicodeEncodeError мешаванд
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG = io.open(os.path.join(BASE_DIR, "verify_result.txt"), "w", encoding="utf-8")
failures = []

def out(*args):
    line = " ".join(str(a) for a in args)
    print(line)
    LOG.write(line + "\n")

def check(name, cond, extra=""):
    out(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" | {extra}" if extra else ""))
    if not cond:
        failures.append(name)

CLIENT_ORIGIN = "https://my-first-app-1-4t5v.onrender.com"
ADMIN_ORIGIN = "https://my-first-app-2-akqv.onrender.com"

out("=" * 70)
out("1) Тафтиши bilol.py (админ-панел)")
out("=" * 70)

import bilol  # noqa: E402

check("CORS домени клиенти Render-ро дорад", CLIENT_ORIGIN in bilol.LOCAL_ORIGINS, f"origins={bilol.LOCAL_ORIGINS}")
check("CORS домени админро низ дорад", ADMIN_ORIGIN in bilol.LOCAL_ORIGINS)

client = bilol.app.test_client()
# Дар тестҳо app.py дастрас набояд бошад — роҳи fallback санҷида мешавад
bilol.API_BASE_URL = "http://127.0.0.1:9"
bilol.DEFAULT_API_URL = "http://127.0.0.1:9"

# 1a. CORS preflight барои фиристодани заказ аз сайти клиент
r = client.options("/api/orders/new", headers={
    "Origin": CLIENT_ORIGIN,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type,x-api-key",
})
acao = r.headers.get("Access-Control-Allow-Origin", "")
aach = (r.headers.get("Access-Control-Allow-Headers", "") or "").upper()
check("OPTIONS preflight /api/orders/new -> 204/200", r.status_code in (200, 204), f"status={r.status_code}")
check("Access-Control-Allow-Origin == домени клиент", acao == CLIENT_ORIGIN, f"got={acao!r}")
check("Allow-Headers Content-Type/X-API-KEY", ("X-API-KEY" in aach and "CONTENT-TYPE" in aach), f"got={aach!r}")

# 1b. GET customer-status аз домени клиент (proxy + fallback)
r2 = client.get("/api/orders/customer-status?customer_id=verify-test", headers={"Origin": CLIENT_ORIGIN})
check("GET customer-status -> 200", r2.status_code == 200, f"status={r2.status_code}")
check("ACOA дар GET", r2.headers.get("Access-Control-Allow-Origin") == CLIENT_ORIGIN,
      f"got={r2.headers.get('Access-Control-Allow-Origin')!r}")

# 1c. POST /api/orders/new — fallback (app.py дастрас нест) бо базаи муваққатӣ
tmp = tempfile.mktemp(suffix=".db")
conn = sqlite3.connect(tmp)
conn.executescript("""
CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, customer_id TEXT, food TEXT,
 price TEXT, phone TEXT, delivery_type TEXT, delivery_latitude TEXT, delivery_longitude TEXT,
 delivery_address TEXT, payment_method TEXT, qabyl INTEGER, omoda INTEGER, created TEXT);
CREATE TABLE full_order_history (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, customer_id TEXT,
 food TEXT, price TEXT, phone TEXT, delivery_type TEXT, payment_method TEXT, created TEXT);
CREATE TABLE revenue_history (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, day TEXT, customer_id TEXT);
""")
conn.commit(); conn.close()
bilol.DB_PATH = tmp

payload = '{"customer":"Тест","customer_id":"verify-test","food":"Паста","price":"25","phone":"999999999","delivery_type":"pickup","payment_method":"online"}'
r3 = client.post("/api/orders/new", data=payload, content_type="application/json",
                 headers={"Origin": CLIENT_ORIGIN, "X-API-KEY": bilol.API_KEY})
d3 = r3.get_json(silent=True)
check("POST /api/orders/new (fallback) -> ok=True",
      r3.status_code == 200 and isinstance(d3, dict) and d3.get("ok") is True,
      f"status={r3.status_code} body={d3}")
check("order_id дар ҷавоб мавҷуд аст", bool(isinstance(d3, dict) and d3.get("order_id")),
      f"order_id={d3.get('order_id') if isinstance(d3, dict) else None}")
check("ACOA дар POST", r3.headers.get("Access-Control-Allow-Origin") == CLIENT_ORIGIN,
      f"got={r3.headers.get('Access-Control-Allow-Origin')!r}")

# 1d. Шаблони админ: API_BASE_URL ва api_key бояд интиқол ёфта бошанд
r4 = client.get("/", headers={"Origin": ADMIN_ORIGIN})
html = r4.get_data(as_text=True)
check("GET / (админ) -> 200", r4.status_code == 200, f"status={r4.status_code}")
check("API_BASE_URL дар шаблон дуруст аст", ("const API_BASE_URL = '" + bilol.API_BASE_URL + "'") in html)
check("API_KEY дар шаблон холӣ нест", ("const API_KEY = '" + bilol.API_KEY + "'") in html)

try:
    os.remove(tmp)
except OSError:
    pass

out()
out("=" * 70)
out("2) Тафтиши app.py (сайти клиент)")
out("=" * 70)

import app as app_module  # noqa: E402

ac = app_module.app.test_client()

ra = ac.get("/")
ha = ra.get_data(as_text=True)
check("GET / (клиент) -> 200", ra.status_code == 200, f"status={ra.status_code}")
check("{{ api_key }} интиқол ёфтааст (холӣ нест)", ('const API_KEY = "' + app_module.TFC_API_KEY + '"') in ha)
check("adminApiBase -> домени Render мавҷуд аст", ADMIN_ORIGIN in ha)
check("adminApiBase -> 127.0.0.1:5001 барои localhost", "127.0.0.1:5001" in ha)
check("URL-и кӯҳнаи 'localhost:5001' боқӣ намондааст", "localhost:5001" not in ha)

rb = ac.options("/api/orders/new", headers={
    "Origin": ADMIN_ORIGIN,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type,x-api-key",
})
check("app.py CORS preflight", rb.headers.get("Access-Control-Allow-Origin") in ("*", ADMIN_ORIGIN),
      f"got={rb.headers.get('Access-Control-Allow-Origin')!r}")

out()
out("=" * 70)
out("НАТИҶА: " + ("Ҳама тафтишот муваффақ шуданд ✅" if not failures else f"{len(failures)} хато ❌ -> {failures}"))
out("=" * 70)
LOG.close()
sys.exit(0 if not failures else 1)
