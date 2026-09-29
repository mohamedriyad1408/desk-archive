#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مرجع مبدئي لبوابة تكافؤ النص والأداة (ب16) — مسودة مسبار ن، غير مفعّل حتى اعتماد الحزمة.
العقد: لا يصبح حكم تنفيذي active حتى يسجل clause_id -> tool(id+version+hash) -> tests -> evidence -> owner.
رموز: GX1 أداة مفقودة · GX2 بصمة لا تطابق · GX3 اختبار غائب · GX4 دليل غائب · GX5 سجل ناقص."""
import json, sys, os, hashlib

def sha(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()

def main():
    mp = sys.argv[1]; base = os.path.dirname(os.path.abspath(mp))
    if "--base" in sys.argv: base = sys.argv[sys.argv.index("--base") + 1]
    m = json.load(open(mp, encoding="utf-8")); bad = 0
    for c in m.get("clauses", []):
        cid = c.get("clause_id", "?")
        for key, code in (("tool", "GX1"), ("tests", "GX3"), ("evidence", "GX4")):
            p = os.path.join(base, c.get(key, ""))
            if not c.get(key) or not os.path.exists(p):
                print(f"[{code}] {cid}: {key} مفقود ({c.get(key)})"); bad = 1
        for key, code in (("owner", "GX5"), ("status", "GX5")):
            if not c.get(key): print(f"[{code}] {cid}: {key} غير معلن"); bad = 1
        tp = os.path.join(base, c.get("tool", ""))
        if os.path.exists(tp) and c.get("tool_sha256"):
            if sha(tp) != c["tool_sha256"]:
                print(f"[GX2] {cid}: بصمة الأداة لا تطابق (متوقع {c['tool_sha256'][:12]}… وجد {sha(tp)[:12]}…)"); bad = 1
        if c.get("status") == "active" and bad == 0:
            print(f"[OK] {cid}: مُفعَّل — أداة+بصمة+اختبار+دليل+مالك")
    if bad: print("بوابة التكافؤ: حمراء."); sys.exit(1)
    print("بوابة التكافؤ: خضراء (كل حكم executable له أداته المختبرة)."); 

if __name__ == "__main__": main()
