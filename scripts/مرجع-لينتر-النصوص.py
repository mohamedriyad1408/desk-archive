#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مرجع مبدئي للينتر الدستوري (ب15) — مسودة مسبار ن، غير مفعّل حتى بوابة ب16.
قتلات برموز معلنة: LX1 وسم متداخل · LX2 إحالة ميتة · LX3 معرّف مكرر · LX4 إحالة إلى منسوخ
· LX5 مزود/منصة في النواة · LX6 تاريخ في النواة · LX7 مصطلح بمرادفين.
الاستخدام: مرجع-لينتر-النصوص.py <file> [--core-end '# ملحق'] [--repo DIR] [--only LX1]"""
import re, sys, os
from collections import Counter

CODES = {"LX1": "وسم متداخل", "LX2": "إحالة ميتة", "LX3": "معرّف مكرر",
         "LX4": "إحالة إلى منسوخ", "LX5": "مزود/منصة في النواة", "LX6": "تاريخ في النواة",
         "LX7": "مصطلح بمرادفين"}
SYNONYMS = [("مكلَّف", "مكلف"), ("واردات", "وارِدات"), ("ملحق", "ذيل")]

def main():
    path = sys.argv[1]; a = sys.argv[2:]
    repo = os.path.dirname(os.path.abspath(path)); core_marker = "# ملحق"; only = None
    for i, x in enumerate(a):
        if x == "--repo": repo = a[i+1]
        if x == "--core-end": core_marker = a[i+1]
        if x == "--only": only = a[i+1]
    text = open(path, encoding="utf-8").read(); lines = text.splitlines()
    ci = next((i for i, l in enumerate(lines) if l.startswith(core_marker)), len(lines))
    core = "\n".join(lines[:ci])
    findings = {c: [] for c in CODES}
    depth = 0
    for i, l in enumerate(lines, 1):
        for m in re.finditer(r"</?u>", l):
            if m.group(0) == "<u>":
                depth += 1
                if depth > 1: findings["LX1"].append((i, l[:60]))
            else: depth = max(0, depth - 1)
    def adigits(x): return int("".join(str(int(c)) if c.isdigit() else str("٠١٢٣٤٥٦٧٨٩".index(c)) for c in x))
    maildirs = [d for d in (os.path.join(repo, "بريد-القائد"), os.path.join(repo, "القناة", "بريد-القائد")) if os.path.isdir(d)]
    have_nums = set()
    for d in maildirs:
        for f in os.listdir(d):
            m = re.match(r"ق-([٠-٩\d]+)", f)
            if m: have_nums.add(adigits(m.group(1)))
    for i, l in enumerate(lines, 1):
        for r in set(re.findall(r"ق-[٠-٩]+", l)):
            try: num = adigits(r.split("-")[1])
            except Exception: continue
            if num not in have_nums: findings["LX2"].append((i, r))
        for r in set(re.findall(r"v-[٠-٩\d]+", l)):
            if not os.path.exists(os.path.join(repo, "vault", r + ".enc")): findings["LX2"].append((i, r))
    defs = re.findall(r"^#+\s*(م[٠-٩]+)\b", text, re.M)
    dups = [k for k, v in Counter(defs).items() if v > 1]
    for d in dups: findings["LX3"].append((0, d))
    repealed = set(re.findall(r"^\s*(?:REPEALED|منسوخ)[:\s]+([\w\-٠-٩/]+)", text, re.M))
    for i, l in enumerate(lines, 1):
        for ref in re.findall(r"[٠-٩]+/[٠-٩]+", l):
            if ref in repealed: findings["LX4"].append((i, ref))
    for i, l in enumerate(lines[:ci], 1):
        for m in re.finditer(r"أرينا|Arena|GitHub|Supabase|Vercel|psql|openssl|Actions", l):
            findings["LX5"].append((i, m.group(0)))
        if re.search(r"٢٠٢٦|2026", l): findings["LX6"].append((i, l[:50]))
    for a1, b1 in SYNONYMS:
        if a1 in core and b1 in core: findings["LX7"].append((0, f"{a1}/{b1}"))
    rc = 0
    for c, name in CODES.items():
        if only and c != only: continue
        hit = findings[c]
        if hit:
            rc = 1; print(f"[{c}] {name}: {len(hit)} موضعًا — {hit[:3]}")
        else: print(f"[{c}] {name}: نظيف")
    sys.exit(rc)

if __name__ == "__main__": main()
