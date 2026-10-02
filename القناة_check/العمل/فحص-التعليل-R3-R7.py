#!/usr/bin/env python3
# فحص-التعليل-R3-R4.py — فاحص عدم-الفراغ لجدول التعليل (R-10): وسوم ↔ صفوف ↔ expected_count
# قتلتان: حذف وسم ⇒ فشل · حذف صف ⇒ فشل
import re, sys, tempfile, pathlib

DOC = pathlib.Path(__file__).resolve().parent / 'الدستور-٣٫٠-النهائية-R3-R7-2026-10-01.md'

def check(text: str) -> tuple[bool, str]:
    tags = re.findall(r'<!-- rationale: (R-\d{2}) -->', text)
    rows = re.findall(r'^\| (R-\d{2}) \|', text, re.M)
    exp = re.search(r'<!-- expected_count: (\d+) -->', text)
    if not exp:
        return False, 'لا إعلان expected_count'
    n = int(exp.group(1))
    if len(set(tags)) != len(tags):
        return False, f'وسم مكرر: {sorted([x for x in tags if tags.count(x) > 1])}'
    if len(set(rows)) != len(rows):
        return False, 'صف مكرر'
    if sorted(set(tags)) != sorted(set(rows)):
        return False, f'وسوم ≠ صفوف: {sorted(set(tags))} vs {sorted(set(rows))}'
    if len(set(rows)) != n:
        return False, f'العدد {len(set(rows))} ≠ expected_count {n}'
    # عدم-الفراغ: كل صف واقعته ومبدأه غير فارغين
    for line in text.splitlines():
        m = re.match(r'^\| (R-\d{2}) \| (.+?) \| (.+?) \|', line)
        if m and (not m.group(2).strip() or not m.group(3).strip()):
            return False, f'صف فارغ: {m.group(1)}'
    return True, f'وسوم={len(set(tags))} · صفوف={len(set(rows))} · متوقع={n} ⇒ PASS'

def main():
    t = DOC.read_text(encoding='utf-8')
    ok, msg = check(t)
    print('الفحص:', msg)
    if not ok:
        sys.exit(1)
    # قتلة القبول (تُطلق يدويًا بـ--kills)
    if '--kills' in sys.argv:
        # قتلة-١: حذف وسم ⇒ يجب أن يفشل
        t1 = t.replace('<!-- rationale: R-07 -->\n', '', 1)
        ok1, _ = check(t1)
        print('قتلة-١ (حذف وسم R-07):', 'فشل الفحص كما يجب ✓' if not ok1 else '⚠️ لم يفشل!')
        if ok1: sys.exit(1)
        # قتلة-٢: حذف صف ⇒ يجب أن يفشل
        t2 = re.sub(r'^\| R-12 \|.*\n', '', t, count=1, flags=re.M)
        ok2, _ = check(t2)
        print('قتلة-٢ (حذف صف R-12):', 'فشل الفحص كما يجب ✓' if not ok2 else '⚠️ لم يفشل!')
        if ok2: sys.exit(1)
        # قتلة-٣: تكرار وسم ⇒ يجب أن يفشل
        t3 = t.replace('<!-- rationale: R-01 -->\n', '<!-- rationale: R-01 -->\n<!-- rationale: R-01 -->\n', 1)
        ok3, _ = check(t3)
        print('قتلة-٣ (تكرار وسم):', 'فشل الفحص كما يجب ✓' if not ok3 else '⚠️ لم يفشل!')
        if ok3: sys.exit(1)

if __name__ == '__main__':
    main()
