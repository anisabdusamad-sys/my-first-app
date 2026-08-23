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
check("adminApiBase -> ба sherи худ (BASE_URL) бармегардад",
      ("function adminApiBase() {" in ha and "return BASE_URL;" in ha))
check("URL-и админ (my-first-app-2) дигар дар клиент сахткор нест", "my-first-app-2-akqv.onrender.com" not in ha)
check("URL-и кӯҳнаи 'localhost:5001' боқӣ намондааст", "localhost:5001" not in ha)
check("Саҳифаи HTML cache-карда намешавад (no-store)", "no-store" in (ra.headers.get("Cache-Control") or ""),
      f"Cache-Control={ra.headers.get('Cache-Control')!r}")

# --- Ҳамин табии "фиристодани заказ аз браузер": POST-и same-origin ба /api/orders/new ---
tmp2 = tempfile.mktemp(suffix=".db")
cn2 = sqlite3.connect(tmp2)
cn2.executescript("""
CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, customer_id TEXT, food TEXT,
 price TEXT, phone TEXT, delivery_type TEXT, tip TEXT, delivery_latitude TEXT, delivery_longitude TEXT,
 delivery_address TEXT, payment_method TEXT, payment_phone TEXT, qabyl INTEGER, omoda INTEGER, dostavka INTEGER,
 estimated_time INTEGER, created TEXT);
CREATE TABLE full_order_history (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, customer_id TEXT,
 food TEXT, price TEXT, phone TEXT, delivery_type TEXT, tip TEXT, payment_method TEXT, created TEXT);
CREATE TABLE revenue_history (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, day TEXT, customer_id TEXT);
""")
cn2.commit(); cn2.close()
orig_db_path = app_module.DB_PATH
app_module.DB_PATH = tmp2

order_payload = '{"customer":"Тест Client","customer_id":"verify-client","food":"Пицца","price":"35","phone":"888888888","delivery_type":"delivery","payment_method":"cash"}'
ro = ac.post("/api/orders/new", data=order_payload, content_type="application/json",
             headers={"X-API-KEY": app_module.TFC_API_KEY})
do = ro.get_json(silent=True)
check("POST /api/orders/new (same-origin, мисли браузер) -> ok=True",
      ro.status_code == 200 and isinstance(do, dict) and do.get("ok") is True,
      f"status={ro.status_code} body={do}")
check("order_id баргаштааст (status-pulling ба кор медарояд)",
      bool(isinstance(do, dict) and do.get("order_id")), f"order_id={do.get('order_id') if isinstance(do, dict) else None}")
r5 = ac.get("/api/orders/since?last_id=0", headers={"X-API-KEY": app_module.TFC_API_KEY})
d5 = r5.get_json(silent=True)
orders_found = isinstance(d5, dict) and any(o.get("customer_id") == "verify-client" for o in d5.get("orders", []))
check("Заказ дар /api/orders/since мавҷуд аст (админ онро мебинад)", orders_found)

app_module.DB_PATH = orig_db_path
try:
    os.remove(tmp2)
except OSError:
    pass

# --- Саҳифаи /admin-и app.py низ API_KEY-и дурустро дорад ---
radm = ac.get("/admin")
hadm = radm.get_data(as_text=True)
check("GET /admin -> 200", radm.status_code == 200, f"status={radm.status_code}")
check("/admin API_KEY аз шаблон меояд", ('const API_KEY = "' + app_module.TFC_API_KEY + '"') in hadm)

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
