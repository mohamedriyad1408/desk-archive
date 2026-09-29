#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مسبر ب٣–ب٦ (نقطة منتصف ن-082) — قتلات المخططات بأرقامها. استدعاء: python3 مسبر-ب3-ب6.py"""
import json, subprocess, sys, os, shutil, copy, tempfile
D = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(D, "مرجع-مخططات-النواة.py")
SB = os.path.join(os.environ.get("PROBE_SB", tempfile.gettempdir()), "مسبر-مخططات")
shutil.rmtree(SB, ignore_errors=True); os.makedirs(SB)

P = F = 0
def run(band, data, name):
    p = os.path.join(SB, f"{band}-{name}.json")
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([sys.executable, REF, band, p], capture_output=True, text=True)
    return r.returncode, r.stdout
def ok(m): global P; P += 1; print(f"  ✅ {m}")
def no(m): global F; F += 1; print(f"  ❌ {m}")

# ═══ ب٣ ═══
print("◆ ب٣ — المصائر والصناديق (رموز SZ3)")
G3 = {"requirements": [
 {"id": "R1", "disposition": "in_plan", "routing": "plan"},
 {"id": "R2", "disposition": "owner_package", "routing": "owner"},
 {"id": "R3", "disposition": "deferred_with_reason", "routing": "knowledge_gap"}]}
rc, out = run("b3", G3, "green")
if rc == 0 and "classified=3; orphans=0" in out: ok("السليم أخضر + سطر التقرير: classified=3; orphans=0")
else: no(f"السليم رُفض: rc={rc} {out.strip()[:120]}")
for nm, mut, sym in [
 ("E1-disp", lambda d: d["requirements"][0].__setitem__("disposition", "pending"), "SZ3-E1"),
 ("E1-rout", lambda d: d["requirements"][1].__setitem__("routing", "bin9"), "SZ3-E1"),
 ("E2-list", lambda d: d["requirements"][2].__setitem__("disposition", ["in_plan", "owner_package"]), "SZ3-E2"),
 ("O1-orph", lambda d: d["requirements"][0].pop("routing"), "SZ3-O1")]:
    d = copy.deepcopy(G3); mut(d); rc, out = run("b3", d, nm)
    if rc == 1 and sym in out: ok(f"{sym} أطلق ({nm})")
    else: no(f"{sym} لم يطلق: rc={rc} {out.strip()[:120]}")

# ═══ ب٤ ═══
print("◆ ب٤ — متجه الادعاء [S,X,N,R,A] (رموز SZ4)")
G4 = {"claims": [
 {"id": "C1", "profile": "architecture", "vector": {"S": 2, "X": 1, "N": 1, "R": 1, "A": 1}},
 {"id": "C2", "profile": "legal", "vector": {"S": 1, "X": 2, "N": "N/A", "R": 2, "A": 1}, "na": {"N": "غير منطبق: لا واجهة أمنية"}}]}
rc, out = run("b4", G4, "green")
if rc == 0: ok("السليم أخضر (متجهان بملفَّي ادعاء)")
else: no(f"السليم رُفض: {out.strip()[:120]}")
for nm, mut, sym in [
 ("V1-scalar", lambda d: d["claims"][0].__setitem__("level", 3), "SZ4-V1"),
 ("V2-missing", lambda d: d["claims"][0]["vector"].pop("A"), "SZ4-V2"),
 ("V3-na", lambda d: d["claims"][1].__setitem__("na", {}), "SZ4-V3"),
 ("V4-zero", lambda d: d["claims"][0]["vector"].__setitem__("S", 0), "SZ4-V4")]:
    d = copy.deepcopy(G4); mut(d); rc, out = run("b4", d, nm)
    if rc == 1 and sym in out: ok(f"{sym} أطلق ({nm})")
    else: no(f"{sym} لم يطلق: rc={rc} {out.strip()[:120]}")
d = copy.deepcopy(G4); d["claims"] = [d["claims"][0]]; d["claims"][0]["profile"] = "defense"
rc, out = run("b4", d, "V2b-profile")
if rc == 1 and "SZ4-V2" in out: ok("SZ4-V2 أطلق (ملف ادعاء غير معلن)")
else: no(f"SZ4-V2 لم يطلق على ملف غير معلن: {out.strip()[:120]}")

# ═══ ب٥ ═══
print("◆ ب٥ — بروفايلات risk/intake/evidence/advocacy بعقد ب١٧ (رموز SZ5)")
FULL = {"profile_id": "risk-standard", "kind": "risk", "scope": "كل طلب منتج", "assumptions": ["لا أسرار في الشجرة"],
 "parameters": {"min_evidence": 2}, "tests": ["مسبر-ب3"], "owner": "م٢", "version": "1.0", "hash": "abc123"}
G5 = {"profiles": [dict(FULL), dict(FULL, profile_id="intake-standard", kind="intake"), dict(FULL, profile_id="evidence-standard", kind="evidence"), dict(FULL, profile_id="advocacy-standard", kind="advocacy")]}
rc, out = run("b5", G5, "green")
if rc == 0: ok("الأربعة أخضر بعقد ب١٧ الكامل (id/scope/assumptions/parameters/tests/owner/version/hash)")
else: no(f"السليم رُفض: {out.strip()[:120]}")
FIELDS = ["profile_id", "scope", "assumptions", "parameters", "tests", "owner", "version", "hash"]
for i, fld in enumerate(FIELDS, 1):
    d = copy.deepcopy(G5); d["profiles"][0].pop(fld); rc, out = run("b5", d, f"F{i}-{fld}")
    if rc == 1 and f"SZ5-F{i}" in out: ok(f"SZ5-F{i} أطلق (نقص {fld})")
    else: no(f"SZ5-F{i} لم يطلق على نقص {fld}: {out.strip()[:120]}")
d = copy.deepcopy(G5); d["profiles"][2].update({"strength": "minimal", "required_min": "external-critical"})
rc, out = run("b5", d, "M1-weak")
if rc == 1 and "SZ5-M1" in out: ok("SZ5-M1 أطلق (evidence minimal تحت حد external-critical)")
else: no(f"SZ5-M1 لم يطلق: {out.strip()[:120]}")

# ═══ ب٦ ═══
print("◆ ب٦ — مادة الاستيفاء وبوابة صفر حاجب (رموز SZ6)")
G6 = {"requirements": [{"id": "R1", "unknowns": [
 {"id": "U1", "class": "reversible-default", "rollback": "إرجاع القيمة السابقة", "expiry": "2026-10-15"},
 {"id": "U2", "class": "irrelevant-to-scope"},
 {"id": "U3", "class": "blocking-owner", "question": "من يملك القرار؟", "voi": True, "status": "closed"}]}]}
rc, out = run("b6", G6, "green")
if rc == 0 and "dimensions=1; unclassified=0; blocking_open=0" in out: ok("السليم أخضر + سطر البوابة dimensions=1; unclassified=0; blocking_open=0")
else: no(f"السليم رُفض: rc={rc} {out.strip()[:140]}")
for nm, mut, sym in [
 ("U1-class", lambda d: d["requirements"][0]["unknowns"][0].__setitem__("class", "unknown-later"), "SZ6-U1"),
 ("R1-norollback", lambda d: d["requirements"][0]["unknowns"][0].pop("rollback"), "SZ6-R1"),
 ("V1-novou", lambda d: d["requirements"][0]["unknowns"][2].__setitem__("voi", False), "SZ6-V1"),
 ("B1-open", lambda d: d["requirements"][0]["unknowns"][2].__setitem__("status", "open"), "SZ6-B1")]:
    d = copy.deepcopy(G6); mut(d); rc, out = run("b6", d, nm)
    if rc == 1 and sym in out: ok(f"{sym} أطلق ({nm})")
    else: no(f"{sym} لم يطلق: rc={rc} {out.strip()[:140]}")

print(f"\n════ حصيلة المخططات: نجح {P} · فشل {F} ════")
sys.exit(1 if F else 0)
