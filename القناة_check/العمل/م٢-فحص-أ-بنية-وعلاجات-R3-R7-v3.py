# -*- coding: utf-8 -*-
# فحوص م٢ المستقلة على R3-R4 — الجزء أ: البنية · أدوات ق/ن على الأثر · التسريب · العلاجات R-01…R-11
import re, pathlib, hashlib, subprocess, sys, json, collections, os
import os, tempfile
ROOT = pathlib.Path(os.environ.get("REPO") or os.getcwd()); CH = ROOT / "القناة"; W = CH / "العمل"; S = ROOT / "scripts"
OUT = pathlib.Path(os.environ.get("M2_OUT") or (tempfile.gettempdir() + "/m2-out")); OUT.mkdir(parents=True, exist_ok=True)
R3p = W / "الدستور-٣٫٠-مسودة-R3-المدمجة-2026-09-29.md"
R4p = W / "الدستور-٣٫٠-النهائية-R3-R7-v3-2026-10-01.md"
R3 = R3p.read_text(encoding="utf-8").split("\n"); R4 = R4p.read_text(encoding="utf-8").split("\n")
def arnum(s): return int("".join(str("٠١٢٣٤٥٦٧٨٩".index(c)) if c in "٠١٢٣٤٥٦٧٨٩" else c for c in s))
def idx(L, prefix): return next(i for i, l in enumerate(L) if l.startswith(prefix))
c0 = idx(R4, "# الطبقة الأولى"); c1 = idx(R4, "# الطبقة الثانية"); c2 = idx(R4, "# الطبقة الثالثة"); c3 = idx(R4, "# بروفايل-واو"); c4 = idx(R4, "# الطبقة الخامسة")
core = R4[c0:c1]
while core and core[-1].strip() in ("", "---"): core.pop()
body = R4[:c4]
(OUT / "core4.md").write_text("\n".join(core) + "\n", encoding="utf-8")
(OUT / "body4.md").write_text("\n".join(body) + "\n", encoding="utf-8")
li = next(i for i, l in enumerate(R4) if l.startswith("| # | الواقعة"))
led = []
for l in R4[li:]:
    if not l.strip(): break
    led.append(l)
(OUT / "ledger4.md").write_text("\n".join(led) + "\n", encoding="utf-8")
print(f"R4: {len(R4)} سطرًا (split) | Core = L{c0+1}..L{c0+len(core)} ({len(core)}) | الطبقات: ٢=L{c1+1} ٣=L{c2+1} ٤=L{c3+1} ٥=L{c4+1} | المتن المعياري = L1..L{c4}")
print("sha256(R4) =", hashlib.sha256(R4p.read_bytes()).hexdigest())
def run(*a):
    r = subprocess.run(list(a), capture_output=True, text=True, cwd=str(ROOT)); return r.returncode, (r.stdout + r.stderr).strip()
ok = lambda b: "✓" if b else "✗"

print("\n════ ١) أدوات ق/ن على الأثر النهائي (من استنساخي) ════")
rc, o = run(sys.executable, str(S / "لينتر-العموم.py"), "gate", str(OUT / "core4.md")); print("بوابة GP01–GP16 على Core(R4) rc=%d |" % rc, o.splitlines()[-1])
print("   مجاميع:", [x.strip() for x in o.splitlines() if "(core)=" in x])
rc, o = run(sys.executable, str(S / "مرجع-لينتر-النصوص.py"), str(R4p), "--repo", str(ROOT), "--core-end", "# الطبقة الثانية"); print("لينتر LX بحد Core الصحيح rc=%d" % rc); print("\n".join("   " + x for x in o.splitlines()))
rc, o = run(sys.executable, str(S / "لينتر-العموم.py"), "pair", str(OUT / "core4.md"), str(OUT / "ledger4.md")); print("pair على Core وحده rc=%d |" % rc, " ".join(o.splitlines()[-3:]))
rc, o = run(sys.executable, str(S / "لينتر-العموم.py"), "pair", str(OUT / "body4.md"), str(OUT / "ledger4.md")); print("pair على المتن المعياري كله rc=%d |" % rc, " ".join(o.splitlines()[-3:]))
rc, o = run(sys.executable, str(W / "فحص-التعليل-R3-R7-v3.py"), "--kills"); print("فحص-التعليل (ق) --kills rc=%d:" % rc); print("\n".join("   " + x for x in o.splitlines()))
# مواضع الوسوم
tags = [(i + 1, re.search(r"R-\d{2}", l).group(0)) for i, l in enumerate(R4) if "<!-- rationale:" in l]
inC = [t for n, t in tags if c0 < n <= c0 + len(core)]; outC = [t for n, t in tags if not (c0 < n <= c0 + len(core))]
print(f"وسوم rationale: {len(tags)} (فريدة {len(set(t for _, t in tags))}) | داخل Core: {len(inC)} {inC} | خارج Core: {len(outC)} {outC}")
ex = [(i + 1, l) for i, l in enumerate(R4) if "expected_count" in l]; print("expected_count:", ex[:2])
h = hashlib.sha256((S / "لينتر-العموم.py").read_bytes()).hexdigest(); print("لينتر-العموم.py غير ممسوس (بصمة ٨d83a596…):", ok(h.startswith("8d83a596")), h[:16])
rc, o = run("git", "diff", "--stat", "8d89d1c", "HEAD", "--", "scripts/"); print("تغيير scripts/ بين v-538 والآن:", o or "لا شيء ✓")

print("\n════ ٢) اختبار التسريب: معلّق ت-NNN داخل Core(R4) (تطابق كلمات) ════")
rows = [json.loads(l) for l in (W / "ملحق-ب٧-سجل-التعاليم-v2.jsonl").read_text(encoding="utf-8").splitlines()[1:]]
STOP = set("التي الذي التي على إلى عن من في مع أو لا ما هذا هذه ذلك بعد قبل كل أي إذا إن ثم حتى عند لكن كما قد هو هي".split())
def words(s):
    s = re.sub(r"[\u064B-\u0652]", "", s); return {w for w in re.findall(r"[\u0621-\u064A]{4,}", s) if w not in STOP}
def score(P, l):
    Sx = words(P); return (len(Sx & words(l)) / len(Sx) if len(Sx) >= 3 else 0)
res = []
for x in rows:
    if x["status"] == "partially-active": P = x.get("pending_inference", "")
    elif x["status"] == "pending-authority-ack": P = x["normalized_rule"]
    else: continue
    b = max(((score(P, l), c0 + i + 1) for i, l in enumerate(core)), key=lambda t: t[0]); res.append((b[0], x["teaching_id"], b[1], P[:60]))
res.sort(reverse=True)
for sc, tid, ln, P in res[:6]: print(f"   {sc:4.0%} {tid} ↔ Core L{ln}: {P}")
hit100 = [r for r in res if r[0] >= 0.99]; print("تطابق ≥٩٩٪ (تسريب نصي):", hit100 or "لا شيء ✓")

print("\n════ ٣) العلاجات R-01…R-11 بالأثر ════")
full = "\n".join(R4)
def has(s): return s in full
# R-01
i0 = next(i for i, l in enumerate(R4) if "جدول المواضع المنسوخة الكامل" in l)
rep_rows = [l for l in R4[i0:i0 + 14] if l.startswith("| ") and not l.startswith("| الموضع") and not l.startswith("|---")]
print("R-01 صفوف REPEALED:", len(rep_rows), "(المطلوب ٧)", ok(len(rep_rows) == 7))
print("R-01 م٦/٣١ منسوب لـR2:", ok(has("م٦/٣١ (من مسودة R2 لا من نص ٢٫٩)")), "| البند ٢١ مستثنى:", ok(has("عدا البند ٢١ الحي")), "| مؤشر قسم صفر/٨:", ok(has("Core قسم صفر/٨")))
print("R-01 «(CAS)» بجانب البند ٢١ (عيب دلالة):", "موجود ✗" if "صار أصلًا في Core م٦/١٠ (CAS)" in full else "غائب ✓")
# مؤشرات خريطة التتبع
def parse_arts(L, rx):
    arts = {}; cur = None
    for l in L:
        m = re.match(rx, l)
        if m: cur = arnum(m.group(1)); arts[cur] = set(); continue
        if l.startswith("# ") and not l.startswith("## "): cur = None
        if cur:
            m2 = re.match(r"^\s*([٠-٩]+)\.\s", l)
            if m2: arts[cur].add(arnum(m2.group(1)))
    return arts
a29 = parse_arts((CH / "الدستور.md").read_text(encoding="utf-8").split("\n"), r"^## المادة ([٠-٩]+) —")
r4a = parse_arts(R4[c0:c1], r"^## المادة ([٠-٩]+) —")
ti = next(i for i, l in enumerate(R4) if l.startswith("| مادة ٢٫٩ | مصيرها في R3"))
bad = []; n = 0
for l in R4[ti + 2:ti + 40]:
    if not l.startswith("| "): break
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(c) < 2: continue
    n += 1
    for m in re.finditer(r"^م([٠-٩]+)(?:/([٠-٩]+)(?:[–-]([٠-٩]+))?)?", c[0]):
        a = arnum(m.group(1))
        if a not in a29: bad.append((c[0], "مادة 2.9 غير موجودة"))
        elif m.group(2):
            lo = arnum(m.group(2)); hi = arnum(m.group(3)) if m.group(3) else lo
            miss = [k for k in range(lo, hi + 1) if k not in a29[a]]
            if miss and "من مسودة R2" not in c[0]: bad.append((c[0], f"بنود 2.9 ناقصة {miss[:4]}"))
    for m in re.finditer(r"Core م([٠-٩]+)(?:/([٠-٩]+)(?:[–-]([٠-٩]+))?)?", c[1]):
        a = arnum(m.group(1))
        if a not in r4a: bad.append((c[1], "مادة R4 غير موجودة"))
        elif m.group(2):
            lo = arnum(m.group(2)); hi = arnum(m.group(3)) if m.group(3) else lo
            miss = [k for k in range(lo, hi + 1) if k not in r4a[a]]
            if miss: bad.append((c[1], f"بنود R4 ناقصة {miss}"))
print(f"R-01 مؤشرات خريطة التتبع: {n} صفًا · مؤشرات لا تحل: {bad or 'لا شيء ✓'}")
# R-02
print("R-02/ص-ج٢ تعريف الحزمة (م١٣):", ok(has("الحزمة الحاكمة") and has("المثبتة في رزمتها بالمعرّف والبصمة") and has("واو-بواو")))
# R-03
ri = next(i for i, l in enumerate(R4) if l.startswith("| درجة الخطر | intake_profile"))
tbl = R4[ri:ri + 5]; print("R-03 جدول risk→profiles:", ok(len([t for t in tbl if t.startswith("| `")]) == 3), "(٣ درجات)", "| عينتان:", ok(has("**عينتان:**")), "| عقد الثمانية في م٩/٤:", ok(has("**عقد البروفايل (الحقول الثمانية):**")))
v11 = (W / "تفسير-م٢-لمعايير-واو-v1.1-2026-09-29.md").read_text(encoding="utf-8")
for ph in ("زاويتان مستقلتان", "بروفايل التخصص", "الأمن/القانون/المال/الجديد/المتنازع/غير العكوس", "منخفض الخطر المعروف"):
    print(f"   عبارة v1.1 §٢ «{ph}» في جدول R4:", ok(ph in "\n".join(tbl) or ph in full.split("جدول risk→profiles")[1][:2500]))
lay = [(n_, R4[i + 1:i + 6]) for n_, i in (("٢", c1), ("٣", c2), ("٤", c3))]
for n_, blk in lay:
    t = "\n".join(blk); vals = re.findall(r"(profile_id|owner|version|tests)\s*[:=]\s*\S+", t)
    print(f"R-03 رأس الطبقة {n_}: كتلة CONTRACT8 =", ok("CONTRACT8" in t), "| قيم الحقول (profile_id/owner/version/tests) مكتوبة:", vals or "لا — أسماء بلا قيم ✗")
print("R-03 أسماء الطبقات في عناوين # :", [R4[i][:40] for i in (c1, c2, c3)], "← الاسم الوصفي انتقل إلى ذيل اقتباس العقد")
# R-04
a4 = [l for l in core if l.startswith("٤. كل مطلب يُستوفى")]; print("R-04 م١١/٤ = القاعدة المؤكدة حرفًا:", ok(bool(a4) and a4[0].strip() == "٤. كل مطلب يُستوفى فراغُه من المشروع والأسئلة قبل التنفيذ."))
print("R-04 قوس ت-٠٣٩ محذوف من م٢٠/٤:", ok("(النسبة العليا" not in full), "| م٢١/٤ معدّلة:", ok("٤. سلسلة supersedes بلا دوران (آليًا)." in full))
# R-05
i21 = next(i for i, l in enumerate(core) if l.startswith("٢. **حالات الصف"))
cl = core[i21]; print("R-05 م٢١/٢ مكررة القائمة:", "نعم ✗" if cl.count("`partially-active`") >= 2 else "لا ✓", "| يبقى «`literal` نشط بنصه»:", "نعم ✗" if "`literal` نشط بنصه" in cl else "لا ✓")
sh = [(r["teaching_id"]) for r in rows if r["source_hash"][:16] != r.get("source_hash_short", "")]; print("R-05 source_hash_short ≠ بادئة:", sh or "لا شيء ✓ (٤٧/٤٧)")
# R-06
print("R-06 سطر إحالة م٦/٢ إلى ANNEX-B8/v2:", ok("`ANNEX-B8/v2`" in full))
# R-07
a44 = next(l for l in core if l.startswith("٤. **قراءة كل جديد"))
need = ["change manifest منذ آخر revision قرأه الدور", "added/changed/deleted/tombstoned", "summary + audience", "يقرأ الدور البيان كاملًا والملفات الموجهة إليه وكل مادة يقرر فيها", "لا يلزم قراءة الأرشيف كله"]
print("R-07 م٤/٤ تحمل نص ب٩ المختوم (5 مقاطع):", [ok(x in a44) for x in need])
# R-09
print("R-09 م١٢/٦ «لا تُترجم ولا تُعاد تسميتها»:", ok("وأنماط المطابقة لا تُترجم ولا تُعاد تسميتها." in full))
lp = "\n".join(R4[R4.index(next(l for l in R4 if l.startswith("## الملحق المعياري ١"))):c1])
print("R-09 الملحق المعياري ١: الحقول الستة:", [ok(f in lp) for f in ("authority_language", "normative_language", "operational_artifact_language", "identifier_policy", "clause_mapping", "conflict_rule")])
print("R-09 «(زاي)» إحالة غير محلولة داخل الملحق:", "موجودة ✗" if "(زاي)" in lp else "غائبة ✓")
# R-10
print("R-10 Core: «النبض» / «القائد» / «(SHA)»:", ["موجود ✗" if w in "\n".join(core) else "غائب ✓" for w in ("والنبض", "أمر القائد", "(SHA)")])
# R-11
print("R-11 الأخطاء الأربعة:", [("باقٍ ✗" if w in full else "مصحّح ✓") for w in ("التعلام", "التُّقاءُ", "فكلي", "تعدسة")])
print("عيوب جديدة: «موثف»:", "موجودة ✗" if "موثف" in full else "لا ✓")
