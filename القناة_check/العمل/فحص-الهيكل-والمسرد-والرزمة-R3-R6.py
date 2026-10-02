#!/usr/bin/env python3
# فحص-الهيكل-والمسرد-والرزمة-R3-R6.py — فاحص المشتقات الثلاثة المصانة يدويًا (S-14 — قرار م١ ٤ في بطاقة جلسة-٨)
# الهيكل والمسرد والرزمة لا مولد مختومًا لها بعد (ختم مولداتها مؤجل لطور الأدوات ب١٦) — فشرط صيانتها اليدوية فاحصٌ هذا.
# قتلة: تغيير عنوان ⇒ فشل · تغيير عدّاد ⇒ فشل · تحريف حرف المالك ⇒ فشل.
import re, sys, pathlib, glob

W = pathlib.Path(__file__).resolve().parent
CH = W.parent
R5 = (W / 'الدستور-٣٫٠-النهائية-R3-R6-2026-09-30.md').read_text(encoding='utf-8')
fails = []

def ok(cond, msg):
    print(('✓ ' if cond else '✗ ') + msg)
    if not cond:
        fails.append(msg)

# ═══ ١) الهيكل ═══
sk = (W / 'هيكل-المقابلة-٣٫٠-2026-09-29.md').read_text(encoding='utf-8').split('\n')
hdr_i = next(i for i, l in enumerate(sk) if l.startswith('| معرف'))
rows = [[x.strip() for x in l.strip().strip('|').split('|')] for l in sk[hdr_i + 2:] if l.startswith('| ')]
ids = [r[0] for r in rows]
ok(len(rows) == 28, f'الهيكل: 28 صفًا (الفعلي {len(rows)})')
ok(len(set(ids)) == len(ids), 'الهيكل: معرفات فريدة')
# العناوين الحرفية من R3-R6
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
EN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
heads = {}
for l in R5.split('\n'):
    if l.startswith('## '):
        t = l[3:].strip()
        m = re.match(r'المادة ([٠-٩]+)', t)
        if m:
            heads['C-' + str(int(m.group(1).translate(EN)))] = t
        elif t.startswith('قسم صفر'):
            heads['C-0'] = t
        elif t.startswith('الملحق المعياري ١'):
            heads['ANNEX1'] = t
bad = [(r[0], r[1], heads[r[0]]) for r in rows if r[0] in heads and heads[r[0]] != r[1]]
ok(not bad, f'الهيكل: العناوين تطابق R3-R5 حرفيًا {bad[:2] if bad else ""}')
ok(all(k in ids for k in heads), f'الهيكل: كل عناوين Core لها صف ({[k for k in heads if k not in ids]})')
# عدّ البنود
cnt = {}
cur = None
for l in R5.split('\n'):
    m = re.match(r'^## (?:المادة ([٠-٩]+) —|قسم صفر)', l)
    if m:
        cur = 'C-' + str(int(m.group(1).translate(EN))) if m.group(1) else 'C-0'
        cnt[cur] = 0
        continue
    if l.startswith('## '):
        cur = None
    if cur and re.match(r'^\s*[٠-٩]+\.\s', l):
        cnt[cur] += 1
core_items = sum(cnt.values())
mism = []
for r in rows:
    if r[0] in cnt:
        try:
            n = int(r[4].translate(EN))
        except ValueError:
            continue
        if n != cnt[r[0]]:
            mism.append((r[0], n, cnt[r[0]]))
ok(not mism, f'الهيكل: عمود عدد البنود مطابق للعدّ الآلي {mism[:4] if mism else ""} (المجموع {core_items})')

# ═══ ٢) المسرد ═══
g = (W / 'بذرة-المسرد-الحاكم-٣٫٠-2026-09-29.md').read_text(encoding='utf-8')
terms = [l.split('|')[1].strip() for l in g.split('\n') if l.startswith('| ') and not l.startswith('| المصطلح') and not l.startswith('|---')]
ok(len(terms) == 25, f'المسرد: 25 صفًا — ٢٤ مفهومًا + المكافئة (الفعلي {len(terms)})')
ok(len(set(terms)) == len(terms), 'المسرد: صفر ازدواج')
missing = [t for t in terms if t not in R5]
ok(not missing, f'المسرد: كل مصطلح يرد بنصه في R3-R5 {missing[:3] if missing else ""}')
ok('representation_blocker ≡ personal_representation_blocker' in g, 'المسرد: سطر المكافئة (S-6)')

# ═══ ٣) الرزمة ═══
pk = (W / 'رزمة-دفوع-الوثيقة-٣٫٠-2026-09-29.md').read_text(encoding='utf-8')
own_f = glob.glob(str(W / 'واردة-المالك-2026-09-29-حسم-م-أ-*.md'))[0]
own_src = pathlib.Path(own_f).read_text(encoding='utf-8')
own = re.search(r"## حرف المالك حرفيًا.*?\n\n> (.*?)\n\n##", own_src, re.S).group(1).strip()
m = re.search(r'> «(لغة الأثر.*?)»\n', pk, re.S)
ok(m and m.group(1).strip() == own, 'الرزمة: اقتباس §٥ == حرف الحامل حرفيًا')
ok('خيالا' in pk and 'خيالًا' not in pk, 'الرزمة: «خيالا» بلا تنوين')
ok('R3-R6' in pk and 'عدّاد الفقد' in pk, 'الرزمة: مآل R3-R6 وعدّاد الفقد معلنان')
ok('٣٦ قيدًا' in pk, 'الرزمة: عدد قيود الليدجر (36) محدث')
ok('ز١' in pk and 'ز٨' in pk and 'قائمة الزلات المعلنة قبل الإصلاح' in pk, 'الرزمة: قائمة الزلات ز١–ز٨ المعلنة قبل الإصلاح موجودة')

# ═══ القتلات ═══
if '--kills' in sys.argv:
    # قتلة-١: تحريف عنوان في الهيكل ⇒ يفشل فحص العناوين
    fake = sk[:]
    for i, l in enumerate(fake):
        if l.startswith('| C-1 '):
            fake[i] = l.replace('الغاية والسيادة', 'الغاية والسيادة والهدف')
            break
    t = '\n'.join(fake)
    bad2 = [(r[0],) for r in [[x.strip() for x in l.strip().strip('|').split('|')] for l in t.split('\n') if l.startswith('| ')] if r and r[0] in heads and heads[r[0]] != r[1]]
    print('قتلة-١ (تحريف عنوان هيكل):', 'فشل الفحص كما يجب ✓' if bad2 else '⚠️ لم يفشل!')
    if not bad2: sys.exit(1)
    # قتلة-٢: عدّاد مزيف ⇒ يفشل
    fake2 = sk[:]
    for i, l in enumerate(fake2):
        if l.startswith('| C-10 '):
            fake2[i] = re.sub(r'\| ٧ \|', '| ٤ |', l)
            break
    rows2 = [[x.strip() for x in l.strip().strip('|').split('|')] for l in '\n'.join(fake2).split('\n') if l.startswith('| ')]
    mism2 = [r[0] for r in rows2 if r and r[0] in cnt and r[4].translate(EN).isdigit() and int(r[4].translate(EN)) != cnt[r[0]]]
    print('قتلة-٢ (عدّاد مزيف):', 'فشل الفحص كما يجب ✓' if mism2 else '⚠️ لم يفشل!')
    if not mism2: sys.exit(1)
    # قتلة-٣: حرف مالك محرف في الرزمة ⇒ يفشل
    pk2 = pk.replace('والمالك الأوفر خيالا', 'والمالك الأوفر خيالًا')
    m2 = re.search(r'> «(لغة الأثر.*?)»\n', pk2, re.S)
    print('قتلة-٣ (تنوين في حرف المالك):', 'فشل الفحص كما يجب ✓' if not (m2 and m2.group(1).strip() == own) else '⚠️ لم يفشل!')
    if m2 and m2.group(1).strip() == own: sys.exit(1)

print('RESULT:', 'PASS' if not fails else f'FAIL ({len(fails)})')
sys.exit(1 if fails else 0)
