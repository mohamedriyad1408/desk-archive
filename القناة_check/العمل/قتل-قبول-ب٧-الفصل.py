# -*- coding: utf-8 -*-
# قاتلة قبول ب٧/الفصل (بطاقة التكامل ① + الباب ٢ من ن-086):
#   ① تصدير المضمَر لصف جزئي يجب أن يفشل معلنًا، وتصدير المؤكد وحده يمر.
#   ② S-16/S-21: التوليد يجري في OUT_DIR (مجلد مؤقت) — وفحص diff للشجرة قبل/بعد = صفر فرق،
#      و«Ω»: رفض بلا MIFTAH لا يترك ب٧ مُعاد الكتابة (البوابة في رأس المولد قبل أول كتابة).
# التشغيل (من جذر القناة):  MIFTAH=<key> PYTHONDONTWRITEBYTECODE=1 python3 -B قناة-العمليات/القاتل.py
import hashlib, importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent          # .../القناة/العمل
CH = BASE.parent                                 # .../القناة
GEN = BASE / "مولد-ملحقي-ب٧-ب١١-جولة-٤.py"
B7_REL = "العمل/ملحق-ب٧-سجل-التعاليم-v2.jsonl"

def tree_map(root: Path):
    """خريطة (مسار نسبي ⇒ sha256) لكل ملفات القناة عدا ما لا يُعوَّل عليه (.git ثقيل — يُستثنى)."""
    m = {}
    for dp, dn, fs in os.walk(root):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fs:
            if f.endswith(".pyc") or f.endswith(".enc"):
                continue
            p = Path(dp) / f
            try:
                m[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:
                pass
    return m

def diff_maps(a, b):
    return ([k for k in b if k not in a], [k for k in a if k not in b],
            [k for k in a if k in b and a[k] != b[k]])

results = []
before = tree_map(CH)

# ── ① التوليد في OUT_DIR (S-16): لا لمس للشجرة ──
out = tempfile.mkdtemp(prefix="killer-out-")
os.environ["OUT_DIR"] = out
spec = importlib.util.spec_from_file_location("m", str(GEN))
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)   # البوابة في الرأس + كل الكتابات إلى OUT_DIR
    results.append(f"OUT_DIR: التوليد اكتمل وكتاباته في المجلد المؤقت ✓ ({out})")
except SystemExit as e:
    results.append(f"OUT_DIR: التوليد أنهى نفسه (rc={e.code}) ✗ — لا قتل صالح")
del os.environ["OUT_DIR"]

after = tree_map(CH)
added, removed, changed = diff_maps(before, after)
if not (added or removed or changed):
    results.append("diff الشجرة قبل/بعد التوليد = صفر فرق ✓ (لا لمس لشجرة التشغيل — S-16)")
else:
    results.append(f"الشجرة تغيّرت أثناء التوليد ✗ — +{added} −{removed} ~{changed}")

# ── ② قتلتا التصدير (المضمَر/المؤكد) على صفوف المخرج المؤقت ──
b7_out = Path(out) / B7_REL
if not b7_out.exists():
    results.append("ب٧ لم يُكتب في OUT_DIR ✗ — القاتل بلا صفوف")
    rows = []
else:
    rows = [json.loads(l) for l in b7_out.read_text(encoding="utf-8").splitlines()[1:]]
    results.append(f"ب٧ في OUT_DIR: {len(rows)} صفًا مقروءة ✓")
# بتّ ٣٠/٠٩: ت-٠٠٢ وت-٠٢٨ صارا نشطين بلسان البتّ — الحارس يُقتل بصف تركيبي لا من الملف
assert all(r["status"].startswith(("نشط", "مشروع-فقط")) for r in rows), "بتّ ٣٠/٠٩: غير نشطة!"
fixture = [dict(rows[0], teaching_id="ت-قتل-تركيبي", status="partially-active", quote_kind="literal-partial", confirmed_rule="س", pending_inference="م")]
b2 = next((r for r in rows if r["teaching_id"] == "ت-٠٠٢"), {})
b28 = next((r for r in rows if r["teaching_id"] == "ت-٠٢٨"), {})
if b2.get("status", "").startswith("نشط") and b28.get("status", "").startswith("نشط"):
    try:
        m.export_active_rules(fixture, field="normalized_rule")
        results.append("قتلة-١ (تصدير المضمَر): فشل القتل — مُرَّ! ✗")
    except PermissionError as e:
        results.append(f"قتلة-١ (تصدير المضمَر): فُشل معلن ✓ — {e}")
    try:
        out_rules = m.export_active_rules(fixture, field="confirmed_rule")
        assert all("بنك أسئلة" not in x for x in out_rules), "تسرب المضمر!"
        results.append(f"قتلة-٢ (تصدير المؤكد): مرور ✓ — {len(out_rules)} قاعدة مؤكدة بلا أي مضمر")
    except Exception as e:
        results.append(f"قتلة-٢: فشل غير مقصود ✗ — {e}")
else:
    results.append("صفّا البتّ (ت-٠٠٢/ت-٠٢٨) لم يجدا نشطين ✗")

# ── ③ «Ω»: رفض بلا مفتاح لا يترك ب٧ مُعاد الكتابة (S-21) ──
env = {k: v for k, v in os.environ.items() if k != "MIFTAH"}
env["PYTHONDONTWRITEBYTECODE"] = "1"
before_o = tree_map(CH)
r = subprocess.run([sys.executable, "-B", str(GEN)], cwd=str(CH), env=env, capture_output=True, text=True)
after_o = tree_map(CH)
ao, ro, co = diff_maps(before_o, after_o)
msg = ("MIFTAH غير مضبوط" in (r.stdout + r.stderr))
if r.returncode == 1 and msg and not (ao or ro or co):
    results.append("Ω (بلا مفتاح): rc=1 معلنًا + الشجرة صفر تغيّر ✓ — ب٧ لم يُعد كتابة (S-21 مُغلق)")
else:
    results.append(f"Ω فشل ✗ — rc={r.returncode} · رسالة={msg} · +{ao} −{ro} ~{co}")

# ── ④ سلامة الختام: الشجرة النهائية = الشجرة الابتدائية ──
final = tree_map(CH)
fa, fr, fc = diff_maps(before, final)
if not (fa or fr or fc):
    results.append("سلامة الختام: الشجرة النهائية مطابقة للابتدائية بايتًا ✓")
else:
    results.append(f"سلامة الختام: فرق ✗ +{fa} −{fr} ~{fc}")

print("\n".join(results))
ok = all("✓" in r and "✗" not in r for r in results)
print("PROBE-RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
