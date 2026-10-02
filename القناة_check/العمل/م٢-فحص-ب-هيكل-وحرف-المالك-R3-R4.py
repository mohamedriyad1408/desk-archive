# -*- coding: utf-8 -*-
# فحوص م٢ — الجزء ب: الهيكل · المسرد · الرزمة · حرف المالك · الأخطاء الإملائية الجديدة
import re, pathlib, glob, collections, json, hashlib
import os, tempfile
ROOT = pathlib.Path(os.environ.get("REPO") or os.getcwd()); CH = ROOT / "القناة"; W = CH / "العمل"
R4 = (W / "الدستور-٣٫٠-مسودة-R3-R4-2026-09-29.md").read_text(encoding="utf-8").split("\n")
ok = lambda b: "✓" if b else "✗"
def arnum(s): return int("".join(str("٠١٢٣٤٥٦٧٨٩".index(c)) if c in "٠١٢٣٤٥٦٧٨٩" else c for c in s))
def idx(L, p): return next(i for i, l in enumerate(L) if l.startswith(p))
c0 = idx(R4, "# الطبقة الأولى"); c1 = idx(R4, "# الطبقة الثانية")
core = R4[c0:c1]
print("════ الهيكل (هيكل-المقابلة) ════")
sk = (W / "هيكل-المقابلة-٣٫٠-2026-09-29.md").read_text(encoding="utf-8").split("\n")
print("\n".join("  " + l[:200] for l in sk[:8]))
hdr_i = next(i for i, l in enumerate(sk) if l.startswith("| معرف"))
print("  رأس الجدول:", sk[hdr_i][:230])
rows = [[x.strip() for x in l.strip().strip("|").split("|")] for l in sk[hdr_i + 2:] if l.startswith("| ")]
print(f"  صفوف = {len(rows)} | أعمدة = {len(rows[0])}")
ids = [r[0] for r in rows]
print("  معرفات فريدة:", ok(len(set(ids)) == len(ids)), "| الصفوف:", ids[:5], "…", ids[-6:])
# عناوين Core الفعلية
heads = {}
for i, l in enumerate(core):
    if l.startswith("## "):
        t = l[3:].strip(); m = re.match(r"المادة ([٠-٩]+)", t)
        k = "C-" + str(arnum(m.group(1))) if m else ("C-0" if t.startswith("قسم صفر") else "ANNEX1" if t.startswith("الملحق المعياري ١") else None)
        if k: heads[k] = (c0 + i + 1, t)
print("  عناوين Core (بالملحق):", len(heads), "| مواد بلا صف:", [k for k in heads if k not in ids])
bad = []
for r in rows:
    if r[0] in heads and heads[r[0]][1] != r[1]: bad.append((r[0], heads[r[0]][0], heads[r[0]][1][:60], r[1][:60]))
print("  عناوين عربية لا تطابق R4 حرفًا:", len(bad)); [print("    ", b) for b in bad[:8]]
# عدّ البنود المرقمة لكل مادة في R4 مقابل عمود AR/EN إن وُجد
cnt = {}; cur = None
for l in core:
    m = re.match(r"^## (?:المادة ([٠-٩]+) —|قسم صفر)", l)
    if m: cur = "C-" + str(arnum(m.group(1))) if m.group(1) else "C-0"; cnt[cur] = 0; continue
    if l.startswith("## "): cur = None
    if cur and re.match(r"^\s*[٠-٩]+\.\s", l): cnt[cur] += 1
print("  بنود Core المرقمة:", sum(cnt.values()), "(ق: ١٢٨)")
cols = sk[hdr_i].split("|")
print("  هل للهيكل عمود عدد بنود؟", [c.strip() for c in cols if "بند" in c or "clause" in c.lower() or "AR" in c and "EN" in c])
mism = []
for r in rows:
    if r[0] in cnt:
        nums = [int(x) for x in re.findall(r"\d+", " ".join(r[6:]))] if len(r) > 6 else []
        if nums and cnt[r[0]] not in nums: mism.append((r[0], cnt[r[0]], r[6:]))
print("  صفوف عدد البنود فيها لا يطابق عدّي:", mism[:6] or "لا شيء ✓")
print("  بصمات: أعمدة AR/EN فارغة:", sum(1 for r in rows if len(r) > 5 and not r[4] and not r[5]), "من", len(rows))

print("\n════ بذرة المسرد ════")
g = (W / "بذرة-المسرد-الحاكم-٣٫٠-2026-09-29.md").read_text(encoding="utf-8").split("\n")
terms = [l.split("|")[1].strip() for l in g if l.startswith("| ") and not l.startswith("| المصطلح") and not l.startswith("|---")]
full = "\n".join(R4)
print(f"  مصطلحات={len(terms)} (ق: ٢٣) · مكررة={[t for t in set(terms) if terms.count(t) > 1] or 'لا ✓'}")
print("  مصطلحات لا ترد بنصها في R4:", [t for t in terms if t not in full] or "لا شيء ✓")
print("  سطر المكافئة:", ok(any("representation_blocker" in t and "personal_representation_blocker" in l for t, l in zip(terms, [x for x in g if x.startswith('| ')][2:]))) , "|", [l[:150] for l in g if "personal_representation_blocker" in l][:1])

print("\n════ حرف المالك (بلا تصحيح إملائي ولا إعراب — ونقطة ولا نسج) ════")
own_f = glob.glob(str(W / "واردة-المالك-2026-09-29-حسم-م-أ-*.md"))[0]
own_src = pathlib.Path(own_f).read_text(encoding="utf-8")
own = re.search(r"## حرف المالك حرفيًا.*?\n\n> (.*?)\n\n##", own_src, re.S).group(1).strip()
tail = own[own.index("فالحق أحق"):]
# R4: اقتباس م-أ في سجل التعليل
q = [m.group(1) for l in R4 for m in [re.search(r"«(فالحق أحق.*?)»", l)] if m]
print("  اقتباس سجل التعليل:", [(x == tail, x[-30:]) for x in q], "← المطابقة الحرفية للحامل ✓/✗")
pk = (W / "رزمة-دفوع-الوثيقة-٣٫٠-2026-09-29.md").read_text(encoding="utf-8")
m = re.search(r"> «(لغة الأثر.*?)»\n", pk, re.S); qp = m.group(1).strip() if m else ""
print("  اقتباس رزمة الدفوع §٥ == حرف المالك:", ok(qp == own), f"({len(qp)} مقابل {len(own)})")
# ت-٠١٨ في المادة ٩/٦
prof = pathlib.Path(CH / "المعرفة/المكتبة/07-OWNER-PROFILE.md").read_text(encoding="utf-8").split("\n")[71]
qq = "بره تخصصي... أنت والمنفذ وتخلصوا كل حاجة"
print("  م٩/٦ الاقتباس حرفي في 07-OWNER-PROFILE L72:", ok(qq in prof), "| وروده في R4:", ok(f"«{qq}»" in full))
import difflib
if q and q[0] != tail:
    sm = difflib.SequenceMatcher(None, tail, q[0], autojunk=False)
    print("  فروق اقتباس التعليل عن الحامل:", [(t, repr(tail[i1:i2]), repr(q[0][j1:j2])) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"])

print("\n════ كلمات جديدة في R4 غير موجودة في أي ملف قناة آخر (كشف أخطاء إملائية في المضاف) ════")
def words(s):
    s = re.sub(r"[\u064B-\u0652\u0640]", "", s); return re.findall(r"[\u0621-\u064A]{3,}", s)
corpus = collections.Counter()
skip = ("الدستور-٣٫٠-مسودة-R3-R4", "هيكل-المقابلة", "رزمة-دفوع", "بذرة-المسرد", "سجل-التعديل-النهائي", "حكم-م٢-المدمج")
for p in glob.glob(str(CH / "**/*.md"), recursive=True):
    if any(s in p for s in skip) or p.endswith("الحالة.md"): continue
    corpus.update(set(words(pathlib.Path(p).read_text(encoding="utf-8", errors="ignore"))))
mine = collections.Counter(words("\n".join(R4)))
new = sorted([(c, w) for w, c in mine.items() if corpus[w] == 0], reverse=True)
print(f"  كلمات R4 الفريدة غير الواردة في بقية القناة: {len(new)}")
print("  ", [w for c, w in new][:60])
