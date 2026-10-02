# -*- coding: utf-8 -*-
# فحص-تعديلات-المالك-v4-2026-10-01.py — برهان ثنائي الاتجاه على v4:
#   (أ) عكس المراسي الأحد عشر على v4 يرجّع بايتيًا v3 الموقّعة (e1689803…dcd7).
#   (ب) لا عودة لأي نص قديم في v4، وكل نص جديد فريد.
# الإخضاع: أي FAIL ⇒ خروج 1.
import hashlib, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
V3 = BASE / 'الدستور-٣٫٠-النهائية-R3-R7-v3-2026-10-01.md'
V4 = BASE / 'الدستور-٣٫٠-النهائية-R3-R7-v4-2026-10-01.md'
V3_HASH = 'e1689803634f27afe3fde230703b2a9a19c18ac35fa84dace56180f6d21fdcd7'

GEN = BASE / 'طبّق-تعديلات-المالك-السبعة-R3-R7-v4-2026-10-01.py'
src = GEN.read_text(encoding='utf-8')
# نستخرج المراسي من المولد نفسه (مصدر وحيد للحقيقة — لا تكرار يدوي)
import re, ast
m = re.search(r'HUNKS\s*=\s*(\[.*?\n\])', src, re.S)
hunks = [(tag, old, new) for tag, old, new in ast.literal_eval(m.group(1))]

fails = []
v3t = V3.read_text(encoding='utf-8')
v4t = V4.read_text(encoding='utf-8')

# (أ) العكس: v4 —[new→old]→ يجب أن يساوي v3 بايتيًا
back = v4t
for tag, old, new in hunks:
    if new not in back:
        fails.append(f'FAIL عكس — نص جديد غائب [{tag}]'); continue
    if back.count(new) != 1:
        fails.append(f'FAIL عكس — نص جديد غير فريد [{tag}]'); continue
    back = back.replace(new, old)
h_back = hashlib.sha256(back.encode('utf-8')).hexdigest()
if h_back != V3_HASH:
    fails.append(f'FAIL عكس — v4 بعد العكس ≠ v3 الموقّعة ({h_back[:12]}…)')

# (ب) صفر قديم + التقديم يساوي v4
for tag, old, new in hunks:
    if old in v4t:
        fails.append(f'FAIL — نص قديم باقٍ في v4 [{tag}]')
fwd = v3t
for tag, old, new in hunks:
    fwd = fwd.replace(old, new)
h_fwd = hashlib.sha256(fwd.encode('utf-8')).hexdigest()
h_v4 = hashlib.sha256(v4t.encode('utf-8')).hexdigest()
if h_fwd != h_v4:
    fails.append(f'FAIL تقديم — v3+مراسي ≠ v4')

print(f'v3 الموقّعة : {V3_HASH}')
print(f'v4 النافذة  : {h_v4}')
print('PASS — عكس كامل إلى بصمة الحبر ✓ · صفر نص قديم ✓ · التقديم يطابق v4 ✓ · ١١ مرساة') if not fails else (print('\n'.join(fails)) or sys.exit(1))
