#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مسبر ب٩ — معيد إنتاج الدلتا (ن-082). استدعاء: python3 مسبر-ب9.py"""
import json, subprocess, sys, os, shutil, hashlib, tempfile
D = os.path.dirname(os.path.abspath(__file__)); REF = os.path.join(D, "مرجع-مُعِيد-الدلتا.py")
SB = os.path.join(os.environ.get("PROBE_SB", tempfile.gettempdir()), "مسبر-الدلتا")
shutil.rmtree(SB, ignore_errors=True); os.makedirs(SB)
P = F = 0
def ok(m): global P; P += 1; print(f"  ✅ {m}")
def no(m): global F; F += 1; print(f"  ❌ {m}")
def py(*args):
    r = subprocess.run([sys.executable, REF] + list(args), capture_output=True, text=True); return r.returncode, r.stdout + r.stderr
def w(p, s, b=0):
    p = os.path.join(SB, p); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(s)

# ── مشهد أساسي: v1 → v2 (إضافة وتغيير) → v3 (حذف)
w("v1/docs/a.md", "أ" * 100); w("v1/docs/b.md", "ب" * 100); w("v1/core/00.md", "ن" * 4096)
w("v2/docs/a.md", "أ" * 120); w("v2/docs/b.md", "ب" * 100); w("v2/core/00.md", "ن" * 4096); w("v2/docs/c.md", "ج" * 90)
w("v3/docs/a.md", "أ" * 120); w("v3/core/00.md", "ن" * 4096); w("v3/docs/c.md", "ج" * 90)
T = {"tombstones": {"docs/b.md": {"authority": "م٢", "reason": "دمج في a.md بقرار موثق"}}}
w("tombs.json", json.dumps(T, ensure_ascii=False)); w("tombs-empty.json", json.dumps({"tombstones": {}}, ensure_ascii=False))

print("◆ ١) مسار سليم: v1→v2 (إضافة+تغيير) بأثر حقيقي")
for v in ("v1", "v2", "v3"):
    py("snapshot", os.path.join(SB, v), "--out", os.path.join(SB, f"snap-{v}.json"))
rc, out = py("delta", f"{SB}/snap-v1.json", f"{SB}/snap-v2.json", "--tombs", f"{SB}/tombs.json", "--audience", "ن", "--summary", "إصدار تجريبي", "--out", f"{SB}/man12.json")
if rc == 0 and "+1" in out and "~1" in out and "-0" in out: ok(f"delta v1→v2 أخضر: {out.strip().splitlines()[-1].strip()}")
else: no(f"delta v1→v2: rc={rc} {out[:140]}")
rc, out = py("reproduce", f"{SB}/man12.json", f"{SB}/snap-v1.json", f"{SB}/snap-v2.json")
if rc == 0: ok("إعادة إنتاج v1→v2 من الأثر: مطابقة")
else: no(f"reproduce: {out[:140]}")

print("◆ ٢) قتلة DL2: حذف بلا tombstone ⇒ فشل · ثم بدفن مصرّح ⇒ نجاح")
rc, out = py("delta", f"{SB}/snap-v2.json", f"{SB}/snap-v3.json", "--tombs", f"{SB}/tombs-empty.json", "--audience", "ن", "--summary", "إصدار ٣", "--out", f"{SB}/man23-bad.json")
if rc == 1 and "DL2" in out: ok("DL2 أطلق (docs/b.md حُذف بلا سلطة/سبب)")
else: no(f"DL2 لم يطلق: rc={rc} {out[:140]}")
rc, out = py("delta", f"{SB}/snap-v2.json", f"{SB}/snap-v3.json", "--tombs", f"{SB}/tombs.json", "--audience", "ن", "--summary", "إصدار ٣", "--out", f"{SB}/man23.json", "--parent", f"{SB}/man12.json")
if rc == 0 and "†1" in out: ok(f"بدفن مصرّح أخضر + حمل صحيح على man12: {out.strip().splitlines()[-1].strip()}")
else: no(f"الدفن المصرح: rc={rc} {out[:140]}")
rc, out = py("reproduce", f"{SB}/man23.json", f"{SB}/snap-v2.json", f"{SB}/snap-v3.json")
if rc == 0: ok("إعادة إنتاج v2→v3 (بحذف ودفن): مطابقة")
else: no(f"reproduce v2→v3: {out[:140]}")

print("◆ ٣) قتلة DL1: حذف بين حجمين والكاتب يدّعي عدمه — إعادة الإنتاج تقبض")
man = json.load(open(f"{SB}/man23.json", encoding="utf-8")); man["deleted"] = []; man["summary"] = "لا حذف"
w("man23-liar.json", json.dumps(man, ensure_ascii=False))
rc, out = py("reproduce", f"{SB}/man23-liar.json", f"{SB}/snap-v2.json", f"{SB}/snap-v3.json")
if rc == 1 and "DL1" in out: ok("DL1 أطلق (بيان ذاكرة لا يطابق الأثر: الحذف الضائع)")
else: no(f"DL1 لم يطلق: rc={rc} {out[:140]}")

print("◆ ٤) السلسلة (S-3): المسار الموجب أولًا ثم القتلات")
rc, out = py("chain", f"{SB}/man23.json", "--parent", f"{SB}/man12.json")
if rc == 0 and "متصلة" in out: ok("الرابط الصحيح #١ (man23 ← man12) مرّ — مسار موجب لا يطلق DL3")
else: no(f"الرابط الصحيح رُفض زورًا: rc={rc} {out[:140]}")
# إصدار رابع ورابط صحيح ثانٍ
import shutil as _sh
_sh.copytree(f"{SB}/v3", f"{SB}/v4")
w("v4/docs/a.md", "أ" * 140)
py("snapshot", f"{SB}/v4", "--out", f"{SB}/snap-v4.json")
rc, out = py("delta", f"{SB}/snap-v3.json", f"{SB}/snap-v4.json", "--tombs", f"{SB}/tombs.json", "--audience", "ن", "--summary", "إصدار ٤", "--out", f"{SB}/man34.json", "--parent", f"{SB}/man23.json")
rc2, out2 = py("chain", f"{SB}/man34.json", "--parent", f"{SB}/man23.json")
if rc == 0 and rc2 == 0: ok("الرابط الصحيح #٢ (man34 ← man23) مرّ")
else: no(f"الرابط الثاني: delta rc={rc} chain rc={rc2} {out2[:120]}")
rc, out = py("chain", f"{SB}/man34.json", "--parent", f"{SB}/man12.json")
if rc == 1 and "DL3" in out: ok("DL3 أطلق: رابط مفصول (القفز فوق man23) رُفض معلنًا")
else: no(f"المفصول لم يُرفض: rc={rc} {out[:140]}")
man = json.load(open(f"{SB}/man23.json", encoding="utf-8")); man["summary"] = "بعد التوليد"
w("man23-tampered.json", json.dumps(man, ensure_ascii=False))
rc, out = py("chain", f"{SB}/man23-tampered.json", "--parent", f"{SB}/man12.json")
if rc == 1 and "DL3" in out: ok("DL3 أطلق: بيان عُدّل بعد توليده (سلامة البصمة الذاتية)")
else: no(f"التعديل اللاحق لم يُقبض: rc={rc} {out[:140]}")
rc, out = py("delta", f"{SB}/snap-v1.json", f"{SB}/snap-v2.json", "--tombs", f"{SB}/tombs.json", "--summary", "", "--out", f"{SB}/man-nosum.json")
if rc == 1 and "DL4" in out: ok("DL4 أطلق (ملخص/جمهور ناقص)")
else: no(f"DL4 لم يطلق: rc={rc} {out[:120]}")

print("◆ ٥) اختبار ١٠٠ إصدار: كلفة اليقظة لا تنمو بحجم الأرشيف")
W = os.path.join(SB, "work"); os.makedirs(W)
open(os.path.join(W, "core.md"), "w").write("ن" * (512 * 1024))  # أساس 512KB
arch = 512 * 1024; costs = []
for k in range(1, 101):
    body = f"إصدار {k} ".encode() + bytes(4096)
    open(os.path.join(W, f"rev-{k:03d}.md"), "wb").write(body); arch += len(body)
    py("snapshot", W, "--out", f"{SB}/snap-{k}.json")
    if k == 1:
        py("delta", f"{SB}/snap-1.json", f"{SB}/snap-1.json", "--tombs", f"{SB}/tombs.json", "--audience", "ن", "--summary", "بداية", "--out", f"{SB}/man-001.json")
    else:
        pr = f"{SB}/man-{k-1:03d}.json"
        py("delta", f"{SB}/snap-{k-1}.json", f"{SB}/snap-{k}.json", "--tombs", f"{SB}/tombs.json", "--audience", "ن", "--summary", f"إصدار {k}", "--out", f"{SB}/man-{k:03d}.json", "--parent", pr)
    if k in (10, 50, 100):
        rc, out = py("wake", f"{SB}/man-{k:03d}.json", "--dir", W, "--audience", "ن")
        b = int(out.split("كلفة اليقظة:")[1].split("بايت")[0].strip()); costs.append((k, b, arch))
        print(f"    إصدار {k:3d}: يقظة={b:6d}B · أرشيف تراكمي={arch:8d}B")
big = [c for c in costs if c[0] == 100][0]
if big[1] <= 65536 and big[1] * 10 <= big[2]: ok(f"كلفة اليقظة عند ١٠٠ إصدار ثابتة ({big[1]}B ≤ 64KB و ≤ عُشر الأرشيف {big[2]}B)")
else: no(f"كلفة اليقظة تنمو: {big}")
if max(c[1] for c in costs) - min(c[1] for c in costs) <= 512: ok("الفارق بين إصدار ١٠ و٥٠ و١٠٠ ≤ ٥١٢ بايت (لا نمو)")
else: no(f"الكلفة نمت بين النقاط: {costs}")
print(f"\n════ حصيلة الدلتا: نجح {P} · فشل {F} ════")
sys.exit(1 if F else 0)
