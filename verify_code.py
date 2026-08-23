# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import bilol
c = bilol.app.test_client()
h = c.get('/').get_data(as_text=True)
needle = "code === '159951.tfc'"
ok1 = needle in h
ok2 = "code === correctCode" in h
ok3 = "async function verifyHistoryCode" in h
print("HARDCODE_159951_TFC_IN_ADMIN_TEMPLATE:", ok1)
print("ALSO_ACCEPTS_STORED_PASSWORD:", ok2)
print("VERIFY_FUNCTION_PRESENT:", ok3)
assert ok1 and ok2 and ok3
print("RESULT: ALL_OK")