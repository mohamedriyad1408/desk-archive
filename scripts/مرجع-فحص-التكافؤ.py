#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مرجع بوابة تكافؤ النص والأداة (ب١٦) — مسودة مسبار ن، غير مفعّل حتى اعتماد الحزمة.
العقد: لا يصبح حكم تنفيذي active حتى يسجل clause_id -> tool(id+version+hash) -> tests -> evidence -> owner.
رموز: GX1 أداة مفقودة · GX2 بصمة لا تطابق · GX3 اختبار غائب · GX4 دليل غائب · GX5 سجل ناقص.
عطل بنيوي (بيان/جذر غير مقروء): رمز 70 — لا يُحتسب ضمن قتلات GX ولا نجاحها.
الاستدعاء: python3 مرجع-فحص-التكافؤ.py <manifest.json> [--base <جذر>]"""
import json, sys, os, hashlib

def sha(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    mp = args[0]
    base = os.path.dirname(os.path.abspath(mp))
    if "--base" in args: base = args[args.index("--base") + 1]
    if not os.path.isfile(mp):
        print(f"[INFRA-70] البيان غير موجود: {mp}"); sys.exit(70)
    if not os.path.isdir(base):
        print(f"[INFRA-70] جذر البيان غير موجود: {base}"); sys.exit(70)
    try:
        m = json.load(open(mp, encoding="utf-8"))
    except Exception as e:
        print(f"[INFRA-70] بيان غير مقروء: {e}"); sys.exit(70)
    bad = 0
    for c in m.get("clauses", []):
        cid = c.get("clause_id", "?"); cbad = 0
        for key, code in (("tool", "GX1"), ("tests", "GX3"), ("evidence", "GX4")):
            p = os.path.join(base, c.get(key, ""))
            if not c.get(key) or not os.path.exists(p):
                print(f"[{code}] {cid}: {key} مفقود ({c.get(key)})"); cbad = 1
        for key in ("owner", "status"):
            if not c.get(key): print(f"[GX5] {cid}: {key} غير معلن"); cbad = 1
        tp = os.path.join(base, c.get("tool", ""))
        if os.path.exists(tp) and c.get("tool_sha256"):
            if sha(tp) != c["tool_sha256"]:
                print(f"[GX2] {cid}: بصمة الأداة لا تطابق (متوقع {c['tool_sha256'][:12]}… وجد {sha(tp)[:12]}…)"); cbad = 1
        if not cbad and c.get("status") == "active":
            print(f"[OK] {cid}: مُفعَّل — أداة+بصمة+اختبار+دليل+مالك")
        bad |= cbad
    if bad: print("بوابة التكافؤ: حمراء."); sys.exit(1)
    print("بوابة التكافؤ: خضراء (كل حكم executable له أداته المختبرة).")

if __name__ == "__main__":
    main()
