#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مرجع مخططات النواة (ب٣–ب٦) — مسودة مسبار ن (ن-082)، غير مفعّل حتى بيان ب١٦.
الاستدعاء: python3 مرجع-مخططات-النواة.py {b3|b4|b5|b6} <fixture.json>
الرموز المعلنة: SZ3-E1 قيمة خارج enum · SZ3-E2 أكثر من قيمة · SZ3-O1 غير مصنف
 SZ4-V1 سلم خطي · SZ4-V2 أبعاد ناقصة/ملف غير معلن · SZ4-V3 N/A بلا سبب · SZ4-V4 بعد حرج صفر
 SZ5-F1..F8 حقل عقد مفقود · SZ5-M1 أضعف من الحد الأدنى
 SZ6-U1 تصنيف مجهول ناقص · SZ6-R1 افتراض عكسي بلا rollback/expiry · SZ6-V1 سؤال بلا VOI · SZ6-B1 بوابة حمراء
مخرجات تقرير مقررة: ب٣ «classified=N; orphans=0» · ب٦ «dimensions=N; unclassified=0; blocking_open=0».
"""
import json, sys

D3 = ["in_plan", "owner_package", "representation_blocker", "deferred_with_reason", "out_of_scope_with_reason"]
R4 = ["plan", "owner", "representation", "knowledge_gap"]
DIMS = ["S", "X", "N", "R", "A"]
PROFILES = {"architecture": {"min": {"S": 2, "X": 1}}, "security": {"min": {"S": 3, "N": 2}}, "legal": {"min": {"R": 2, "X": 2}}}
CONTRACT8 = ["profile_id", "scope", "assumptions", "parameters", "tests", "owner", "version", "hash"]
UNK = ["blocking-owner", "blocking-research", "reversible-default", "irrelevant-to-scope"]
ORDER = {"minimal": 0, "standard": 1, "external-critical": 2}

def b3(d):
    bad, cls = [], 0
    reqs = d.get("requirements", []); total = len(reqs)
    for r in reqs:
        rid = r.get("id", "?"); disp, rout = r.get("disposition"), r.get("routing")
        if isinstance(disp, list) or isinstance(rout, list):
            bad.append(("SZ3-E2", rid, "أكثر من قيمة للمطلب الواحد")); continue
        if disp is not None and disp not in D3:
            bad.append(("SZ3-E1", rid, "disposition خارج القيم الخمس")); continue
        if rout is not None and rout not in R4:
            bad.append(("SZ3-E1", rid, "routing خارج القيم الأربع")); continue
        if disp is None or rout is None:
            bad.append(("SZ3-O1", rid, "مطلب بلا تصنيف (orphan)")); continue
        cls += 1
    print(f"  ب٣: classified={cls}; orphans={total - cls}")
    return bad, (cls == total)

def b4(d):
    bad = []
    for c in d.get("claims", []):
        cid = c.get("id", "?")
        if any(k in c for k in ("level", "rank", "scalar")):
            bad.append(("SZ4-V1", cid, "سلم خطي/scalar ممنوع — الدليل متجه")); continue
        v = c.get("vector", {})
        miss = [x for x in DIMS if x not in v]
        if miss:
            bad.append(("SZ4-V2", cid, f"أبعاد ناقصة: {miss}")); continue
        na = c.get("na", {})
        for k, val in v.items():
            if val == "N/A" and not (isinstance(na, dict) and na.get(k)):
                bad.append(("SZ4-V3", cid, f"N/A بلا سبب معلن في {k}"))
        prof = c.get("profile")
        if prof not in PROFILES:
            bad.append(("SZ4-V2", cid, f"ملف ادعاء غير معلن: {prof}")); continue
        for dim, mn in PROFILES[prof]["min"].items():
            if v.get(dim) == 0:
                bad.append(("SZ4-V4", cid, f"بعد حرج {dim}=0 ⇒ يفشل ولو بقية الأبعاد عالية")); break
    return bad, (not bad)

def b5(d):
    bad = []
    for p in d.get("profiles", []):
        pid = p.get("profile_id", "?")
        for i, f in enumerate(CONTRACT8, 1):
            if f not in p or p.get(f) in (None, "", [], {}):
                bad.append((f"SZ5-F{i}", pid, f"حقل العقد مفقود: {f}"))
        if "required_min" in p and "strength" in p:
            if ORDER.get(p["strength"], 0) < ORDER.get(p["required_min"], 0):
                bad.append(("SZ5-M1", pid, f"profile أضعف من الحد الأدنى ({p['strength']} < {p['required_min']})"))
    return bad, (not bad)

def b6(d):
    bad, tot, uncl, blk = [], len(d.get("requirements", [])), 0, 0
    for r in d.get("requirements", []):
        rid = r.get("id", "?")
        for u in r.get("unknowns", []):
            k = u.get("class")
            if k not in UNK:
                bad.append(("SZ6-U1", rid, f"مجهول بلا تصنيف من الأربعة: {u.get('id')}")); uncl += 1; continue
            if k == "reversible-default" and (not u.get("rollback") or not u.get("expiry")):
                bad.append(("SZ6-R1", rid, f"افتراض قابل للعكس بلا rollback/expiry: {u.get('id')}"))
            if k.startswith("blocking") and u.get("status") != "closed":
                blk += 1  # المقيس: الحواجب المفتوحة لا المغلقة
            if u.get("question") and not u.get("voi"):
                bad.append(("SZ6-V1", rid, f"سؤال بلا VOI (لا يغيّر قرارًا/قبولًا/خطرًا فوق العتبة): {u.get('id')}"))
    print(f"  ب٦: dimensions={tot}; unclassified={uncl}; blocking_open={blk}")
    if blk or uncl:
        bad.append(("SZ6-B1", "البوابة", "blocking_open أو unclassified > 0 ⇒ لا يبدأ بند تنفيذ"))
    return bad, (not bad)

def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("b3", "b4", "b5", "b6"):
        print("الاستدعاء: مرجع-مخططات-النواة.py {b3|b4|b5|b6} <fixture.json>", file=sys.stderr); sys.exit(2)
    d = json.load(open(sys.argv[2], encoding="utf-8"))
    bad, ok = {"b3": b3, "b4": b4, "b5": b5, "b6": b6}[sys.argv[1]](d)
    for sym, rid, msg in bad:
        print(f"  [{sym}] {rid}: {msg}")
    print("حكم المخطط: أخضر (العقد مستوفى)." if ok else "حكم المخطط: أحمر (قتلة مطلقة).")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
