# -*- coding: utf-8 -*-
# تدقيق لا-فقدان القانون: وحدات ٢٫٩ التي لا أثر لمعناها في R3-R4 (تحضير للفحص اليدوي)
import re, pathlib, collections
import os, tempfile
ROOT = pathlib.Path(os.environ.get("REPO") or os.getcwd()); CH = ROOT / "القناة"; W = CH / "العمل"
OUT = pathlib.Path(os.environ.get("M2_OUT") or (tempfile.gettempdir() + "/m2-out")); OUT.mkdir(parents=True, exist_ok=True)
L29 = (CH / "الدستور.md").read_text(encoding="utf-8").split("\n")
R4 = (W / "الدستور-٣٫٠-مسودة-R3-R4-2026-09-29.md").read_text(encoding="utf-8").split("\n")
R3 = (W / "الدستور-٣٫٠-مسودة-R3-المدمجة-2026-09-29.md").read_text(encoding="utf-8").split("\n")
SUB = [("المستشار الأول", "مدير التشغيل"), ("المستشار الثاني", "المحقق المستقل"), ("قائد المنظومة", "حارس الوثيقة"), ("بيت القناة", "بيت القناة"),
       ("الريبو", "المستودع"), ("ريبو", "مستودع"), ("المالك", "سلطة القرار"), ("القائد", "حارس الوثيقة"), ("المنفذ", "المنفذ")]
STOP = set("التي الذي التي على إلى عن من في مع أو لا ما هذا هذه ذلك بعد قبل كل أي إذا إن ثم حتى عند لكن كما قد هو هي هذا تكون يكون يجب فقط أيضا لأن حيث بين عليه عليها منه منها له لها".split())
def norm(s):
    s = re.sub(r"[\u064B-\u0652\u0640]", "", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    return s
def stem(w):
    for p in ("وبال", "وال", "بال", "لل", "ال", "و", "ب", "ل", "ف"):
        if w.startswith(p) and len(w) - len(p) >= 3: return w[len(p):]
    return w
def WS(s, sub=False):
    if sub:
        for a, b in SUB: s = s.replace(a, b)
    s = norm(s); ws = [stem(w) for w in re.findall(r"[\u0621-\u064A]{3,}", s)]
    return {w for w in ws if w not in STOP}
# وحدات ٢٫٩: كل سطر غير فارغ/غير عنوان/غير فاصل، حتى قبل «سجل التعديل:»
end = next(i for i, l in enumerate(L29) if l.startswith("**سجل التعديل:**"))
units = []; art = "صدر"; infence = False
for i, l in enumerate(L29[:end], 1):
    if l.strip().startswith("```"): infence = not infence; continue
    if infence: continue
    m = re.match(r"^## (.*)", l)
    if m: art = m.group(1)[:38]; continue
    m = re.match(r"^# (.*)", l)
    if m: art = m.group(1)[:38]; continue
    t = l.strip()
    if not t or t.startswith("|---") or t == "---" or t.startswith(">"): continue
    wl = WS(t, True)
    if len(wl) >= 6: units.append((i, art, t, wl))
r4lines = [(i + 1, l, WS(l)) for i, l in enumerate(R4) if l.strip()]
print("وحدات ٢٫٩:", len(units), "| أسطر R4:", len(r4lines))
res = []
for i, art, t, wl in units:
    best = max(((len(wl & w2) / len(wl), n) for n, l, w2 in r4lines), key=lambda x: x[0])
    res.append((best[0], i, art, t, best[1]))
res.sort()
import json
json.dump([{"cov": c, "l29": i, "art": a, "text": t, "r4": n} for c, i, a, t, n in res], open(str(OUT / "loss.json"), "w"), ensure_ascii=False)
low = [r for r in res if r[0] < 0.40]
print("وحدات تغطيتها < 40% بأفضل سطر R4:", len(low), "من", len(res))
by = collections.Counter(a for c, i, a, t, n in low); print("توزيعها بالمادة/الملحق:"); [print("  ", k, v) for k, v in by.most_common(40)]

# ── تصفية وحدات ٢٫٩ «القانونية» (خارج الكتل المعلن نسخها/نقلها لطبقة البيئة) وطباعة المرشحين للفحص اليدوي ──
def _n(s): return int("".join(str("٠١٢٣٤٥٦٧٨٩".index(c)) for c in s))
def declared(x):
    a, t = x["art"], x["text"]
    if a.startswith("المادة ٦"):
        m = re.match(r"^([٠-٩]+)\.", t)
        if m: return _n(m.group(1)) >= 10
    if a.startswith("قسم صفر"):
        m = re.match(r"^([٠-٩]+)\.", t)
        if m: return _n(m.group(1)) >= 8
    if a.startswith(("الملحق ب", "ملحق د", "ملحق هـ", "الملحق ج")): return True
    if a.startswith("بطاقة") and "واقع مشترك" in t: return True
    return False
cand = [{"cov": c, "l29": i, "art": a, "text": t, "r4": n} for c, i, a, t, n in res if c < 0.65]
cand = [x for x in cand if not declared(x)]
print("وحدات قانونية تغطيتها <65% وغير معلن نسخها:", len(cand)); cur = None
for x in sorted(cand, key=lambda x: x["l29"]):
    if x["art"] != cur: cur = x["art"]; print("\n■", cur)
    print(f"  L{x['l29']:<3} {x['cov']:.0%} ←R4 L{x['r4']:<3} | {x['text'][:150]}")
print("\n── فحص وجود العبارات المفتاحية في ٢٫٩ / R2 / R3 / R4 (بلا ملحق واو) ──")
_T = {"٢٫٩": L29 and "\n".join(L29), "R2": (W / "الدستور-٣٫٠-مسودة-R2-بعد-المراجعات-2026-09-29.md").read_text(encoding="utf-8"), "R3": "\n".join(R3), "R4": "\n".join(R4)}
_r4 = _T["R4"]; _i = _r4.find("# ٢) معايير القبول الموقعة"); _j = _r4.find("# الطبقة الخامسة"); _T["R4"] = _r4[:_i] + _r4[_j:]
_keys = ["درجات الخطر أربع", "اتصال بخدمة لا يعني", "«شغال»", "ثوابت الأمان", "خطة تعويض", "لا تعطيل حارس", "إتلاف بيانات", "سقف الخطر المُصرَّح", "خطة استرداد", "حزمة القرار: واحدة", "صفحة واحدة", "توقيع صلاحية البحث", "فحص ثوابت وآثار جانبية", "اكتمال دورك", "حد أمان"]
print("%-34s" % "العبارة" + "".join("%8s" % k for k in _T))
for k in _keys: print("%-34s" % k + "".join("%8d" % _T[n].count(k) for n in _T))
