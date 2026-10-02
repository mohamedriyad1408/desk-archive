#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فاحص مطابقة الترجمة EN-v4 — بطاقة جلسة-١٦ (بأمر المالك ٢٠٢٦-١٠-٠١)
═══════════════════════════════════════════════════════════════════
(أ) البنود المرقمة عربي × إنجليزي: متساوية عدديًا وبالتسلسل ذاته، بعد تطبيع ٠-٩→0-9
    + بنية العناوين (مستويات #) وترقيم أقسام الملاحق.
(ب) كل السلاسل الحرفية التقنية الموجودة في العربية (مسارات/رموز/بصمات/ANNEX-ids/
    الإحالات المضغوطة/المعرفات الهندية) موجودة بنصها في الإنجليزية ±صفر —
    وفي الاتجاه العكسي: لا سلسلة تقنية في متن الإنجليزية غير موجودة في العربية.
(ج) العينة التامة تمرّ قبل أي تسليم: النتيجة النهائية PASS/FAIL (رقم خروج ٠/١).

تشغيل:  python3 -B العمل/فحص-مطابقة-ترجمة-EN-v4.py
المصدران (نسبًا إلى مجلد هذا الفاحص):
  العربي:  الدستور-٣٫٠-النهائية-R3-R7-v4-2026-10-01.md   (الحاكم — محبر)
  الإنجليزي: الدستور-٣٫٠-EN-R3-R7-v4-2026-10-01.md        (النص المقابل)
  جسم الترجمة = ما قبل علامة <!-- TRANSLATOR-APPARATUS (الذيل جهاز ترجمة مصرح به من البطاقة).
"""
import re
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AR = ROOT / 'الدستور-٣٫٠-النهائية-R3-R7-v4-2026-10-01.md'
EN = ROOT / 'الدستور-٣٫٠-EN-R3-R7-v4-2026-10-01.md'

AR_T = AR.read_text(encoding='utf-8')
EN_T = EN.read_text(encoding='utf-8')
EN_BODY = EN_T.split('<!-- TRANSLATOR-APPARATUS')[0]

AD = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')  # تطبيع الأرقام قبل مقارنة البنود

results = []
def check(name, ok, detail=''):
    results.append(ok)
    tag = '✔ PASS' if ok else '✘ FAIL'
    line = f'{tag}  {name}'
    if detail:
        line += f'  —  {detail}'
    print(line)

print('═' * 72)
print('فاحص مطابقة الترجمة EN-v4 — بطاقة جلسة-١٦')
print(f'العربية : {AR.name}  ({len(AR_T):,} بايت)')
print(f'الإنجليزية: {EN.name}  ({len(EN_T):,} بايت · الجسم {len(EN_BODY):,})')
print('═' * 72)

# ═══════════════ (أ) البنود المرقمة ═══════════════
CL = re.compile(r'^\s*([٠-٩0-9]+)\.(?!\d)', re.M)   # (?!\d) يستبعد أرقام الإصدارات 2.0
A = [m.group(1).translate(AD) for m in CL.finditer(AR_T)]
B = [m.group(1).translate(AD) for m in CL.finditer(EN_BODY)]
check('(أ-١) عدد البنود المرقمة', len(A) == len(B), f'AR={len(A)} · EN={len(B)}')
if A == B:
    check('(أ-٢) تسلسل البنود ١:١ (بعد تطبيع ٠-٩→0-9)', True,
          f'{len(A)} بندًا بنفس الترتيب')
else:
    i = next((k for k in range(min(len(A), len(B))) if A[k] != B[k]),
             min(len(A), len(B)))
    check('(أ-٢) تسلسل البنود ١:١', False,
          f'أول اختلاف عند الفهرس {i}: AR={A[i] if i < len(A) else "—"} · '
          f'EN={B[i] if i < len(B) else "—"}')

HA = [len(m.group(1)) for m in re.finditer(r'^(#{1,6}) ', AR_T, re.M)]
HB = [len(m.group(1)) for m in re.finditer(r'^(#{1,6}) ', EN_BODY, re.M)]
check('(أ-٣) بنية العناوين (مستويات # بالتسلسل)', HA == HB,
      f'AR={len(HA)} · EN={len(HB)}')

NA = [m.translate(AD) for m in re.findall(r'^#{1,4} ([٠-٩0-9]+)\)', AR_T, re.M)]
NB = [m.translate(AD) for m in re.findall(r'^#{1,4} ([٠-٩0-9]+)\)', EN_BODY, re.M)]
check('(أ-٤) ترقيم أقسام الملاحق والبيئة', NA == NB,
      f'AR={len(NA)} قسمًا · EN={len(NB)}')

# ═══════════════ (ب) السلاسل الحرفية ═══════════════
CLASSES = {
    'backtick (نص مضغوط بين علامتي `)': r'`([^`]+)`',
    'بصمة hex (40–64)': r'\b[0-9a-f]{40,64}\b',
    'ANNEX-ids': r'ANNEX-[A-Za-z0-9./]+',
    'رموز الفحص IG-L': r'IG-L\d+',
    'صفوف التعليل R-NN': r'(?<![A-Za-z0-9])R-\d{2}\b',
    'N-NN': r'(?<![A-Za-z0-9])N-\d{2}\b',
    'S-N': r'(?<![A-Za-z0-9])S-\d+\b',
    'ADR-NNN': r'ADR-\d{3}',
    'P1NN': r'(?<![A-Za-z0-9])P1\d{2}\b',
    'تعاليم ت-NNN': r'ت-\d{3}',
    'إسناد ر-NN': r'ر-\d{2}',
    'بحث-N': r'بحث-[٠-٩0-9]+',
    'م۷-صفر': r'م[٠-٩]+-صفر',
    'مراحل خ-N': r'خ-[٠-٩0-9]+',
    'قواعد ث-N': r'ث-[٠-٩0-9]+',
    'عدسات عN': r'ع[٠-٩]+',
    'ملاحق بN': r'ب[٠-٩]+',
    'جلسات جN': r'ج[٠-٩]+',
    'قياسات ق-NNN': r'ق-[٠-٩0-9]+',
    'إحالة مضغوطة مN/M': r'م[٠-٩0-9]+/[٠-٩0-9]+',
    'قوس مرجعي (N/M) هندي': r'\([٠-٩]+/[٠-٩]+\)',
    'معرف مرحلة N-M هندي': r'(?<![٠-٩0-9])[٠-٩]-[٠-٩](?![٠-٩0-9])',
    'أحكام ص-…': r'ص-[ء-ي]+[٠-٩]*',
    'إصدارات R3-R7…': r'(?<![A-Za-z0-9])R\d(?:-R\d)*(?:-v\d)?(?![A-Za-z0-9])',
    'v-NNN': r'v-[A-Za-z0-9]{3,}',
    'مسارات ذات امتداد': r'[^\s`|]+\.(?:md|py|sh|json|enc|txt)\b',
    'رموز لاتينية كبيرة': r'(?<![A-Za-z])[A-Z]{2,}(?![a-z])',
}

miss_fwd = []
for name, pat in CLASSES.items():
    toks = sorted(set(m if not isinstance(m, tuple) else m[0]
                      for m in re.findall(pat, AR_T)))
    bad = [s for s in toks if s not in EN_T]
    for s in bad:
        miss_fwd.append((name, s))
    check(f'(ب) {name}', not bad,
          f'{len(toks) - len(bad)}/{len(toks)}' + (f' · ناقص: {bad}' if bad else ''))

# م-أ (إحالة حرفية)
need_ma = 'م-أ' in AR_T
check('(ب) إحالة م-أ الحرفية', (not need_ma) or ('م-أ' in EN_T),
      'م-أ' if need_ma else '—')

# أكوا: عدد occurrences في جسم EN ≥ عدد العربية
aq_ar, q_en = AR_T.count('أكوا'), EN_BODY.count('أكوا')
check('(ب) أكوا (بعدد ورودها)', q_en >= aq_ar, f'AR={aq_ar} · EN(body)={q_en}')

# الإحالات الطويلة: المادة N/M → Article N/M أو Art. N/M
pairs = sorted(set((a.translate(AD), b.translate(AD)) for a, b in
                   re.findall(r'المادة\s*([٠-٩0-9]+)\s*/\s*([٠-٩0-9]+)', AR_T)))
long_missing = [f'Article {a}/{b}' for a, b in pairs
                if f'Article {a}/{b}' not in EN_T and f'Art. {a}/{b}' not in EN_T]
check('(ب) إحالات طويلة «المادة N/M» → Article/Art. N/M', not long_missing,
      f'{len(pairs) - len(long_missing)}/{len(pairs)}'
      + (f' · ناقص: {long_missing}' if long_missing else ''))

singles = sorted(set(a.translate(AD) for a in
                     re.findall(r'المادة\s*([٠-٩0-9]+)(?![\s/]*[٠-٩/])', AR_T)))
sing_missing = [f'Article {n}' for n in singles
                if f'Article {n} ' not in EN_T and f'Article {n},' not in EN_T
                and f'Art. {n}' not in EN_T and f'Article {n}(' not in EN_T]
check('(ب) إحالات طويلة «المادة N» → Article/Art. N', not sing_missing,
      f'{len(singles) - len(sing_missing)}/{len(singles)}'
      + (f' · ناقص: {sing_missing}' if sing_missing else ''))

# ═══ الاتجاه العكسي: لا سلاسل مخترعة في جسم الإنجليزية ═══
miss_rev = []
for name, pat in CLASSES.items():
    toks = sorted(set(m if not isinstance(m, tuple) else m[0]
                      for m in re.findall(pat, EN_BODY)))
    bad = [s for s in toks if s not in AR_T]
    for s in bad:
        miss_rev.append((name, s))
check('(ب-عكسي) لا سلسلة تقنية في جسم EN غائبة عن العربية', not miss_rev,
      ('متفق عليها جميعًا' if not miss_rev else f'مخترعة: {miss_rev}'))

# ═══════════════ (ج) الحصيلة والعينة التامة ═══════════════
npass = sum(1 for r in results if r)
nfail = len(results) - npass
info_terms = EN_BODY.count('[term?]')
info_rows = len(re.findall(r'^\| [^|]+ \| [^|]+ \| [^|]+ \|$',
                           EN_T.split('### ب)')[1].split('##')[0], re.M)) \
    if '### ب)' in EN_T else -1

print('─' * 72)
print(f'معلوماتي: علامات [term?] في الجسم = {info_terms} · صفوف مقترحات المصطلح = {info_rows}')
print('─' * 72)
verdict = 'PASS' if nfail == 0 else 'FAIL'
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
print(f'النتيجة النهائية: {verdict} — {npass}/{len(results)} فحصًا ناجحًا'
      + ('' if nfail == 0 else f' ({nfail} فاشلًا)'))
print(f'سطر القياس: python3 -B العمل/فحص-مطابقة-ترجمة-EN-v4.py → {verdict} '
      f'(فحوص={len(results)} ناجحة={npass}) · UTC {stamp}')
sys.exit(0 if nfail == 0 else 1)
