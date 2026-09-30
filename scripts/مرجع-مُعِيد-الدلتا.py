#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مرجع معيد إنتاج الدلتا (ب٩) — مسودة مسبار ن (ن-082)، غير مفعّل حتى بيان ب١٦.
عقد: كل إصدار يولّد change manifest منذ آخر revision قرأه الدور: added/changed/deleted/tombstoned + summary + audience.
يُعاد توليد البيان من الأثر (بصمات الملفات) لا من ذاكرة الكاتب. حذف بلا tombstone يفشل.
الرموز: DL1 بيان لا يطابق إعادة الإنتاج · DL2 حذف بلا tombstone · DL3 سلسلة مقطوعة · DL4 جمهور/ملخص ناقص.
الاستدعاء:
  snapshot <dir> --out snap.json
  delta <snapA> <snapB> --tombs t.json --audience ن --summary "..." --out man.json [--parent man-prev.json]
    (S-3: --parent مسار ملفٍ للحمل فقط؛ المخزَّن في البيان هو manifest_sha للبيان الأب — لا مسار)
  reproduce <man.json> <snapA> <snapB>
  wake <man.json> --dir <tree> --audience ن
  chain <man.json> --parent <man-prev.json>
"""
import json, sys, os, hashlib

def sh(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.load(open(p, encoding="utf-8"))
def msha(m):  # بصمة البيان من محتواه (بلا حقل البصمة)
    return sh(json.dumps({k: v for k, v in m.items() if k != "manifest_sha"},
                         sort_keys=True, ensure_ascii=False).encode())
def save(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

def snapshot(d):
    out = {}
    for dp, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, d)] = sh(open(p, "rb").read())
    return {"files": out}

def delta(a, b, tombs, audience, summary, parent=None):
    fa, fb = a["files"], b["files"]
    added = sorted(k for k in fb if k not in fa)
    changed = sorted(k for k in fb if k in fa and fa[k] != fb[k])
    deleted = sorted(k for k in fa if k not in fb)
    bad = []
    if not summary or not audience: bad.append(("DL4", "-", "بيان بلا summary/audience"))
    tomb_ok, tomb_bad = [], []
    for k in deleted:
        (tomb_ok if k in tombs else tomb_bad).append(k)
    if tomb_bad: bad.append(("DL2", ",".join(tomb_bad), "حذف بلا tombstone (سلطة+سبب)"))
    man = {"parent": parent, "summary": summary, "audience": audience,
           "added": added, "changed": changed, "deleted": deleted, "tombstoned": tomb_ok}
    man["manifest_sha"] = msha(man)   # وحيد عبر دالة موحدة (S-3)
    return man, bad

def reproduce(man, a, b):
    fresh, bad = delta(a, b, {k: True for k in man.get("tombstoned", [])}, man.get("audience"), man.get("summary"), man.get("parent"))
    for f in ("added", "changed", "deleted", "tombstoned"):
        if sorted(fresh[f]) != sorted(man.get(f, [])):
            bad.append(("DL1", f, f"بيان الكاتب لا يطابق إعادة الإنتاج: كاتب={man.get(f)} أثر={fresh[f]}"))
    return bad

def wake(manpath, tree, audience):
    man = load(manpath)
    read = [manpath]
    total = os.path.getsize(manpath)
    targeted = [k for k in man["added"] + man["changed"] if audience in man.get("aud", {}).get(k, man["audience"])]
    for k in targeted:
        p = os.path.join(tree, k)
        if os.path.exists(p): total += os.path.getsize(p); read.append(p)
    return total, read, targeted

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    c = sys.argv[1]; av = sys.argv[2:]
    def opt(name, default=None):
        return av[av.index(name) + 1] if name in av else default
    if c == "snapshot":
        save(snapshot(av[0]), opt("--out", "snap.json")); print("لقطة:", opt("--out", "snap.json")); return
    if c == "delta":
        par_ref = None
        if opt("--parent"):
            pr = load(opt("--parent"))
            if pr.get("manifest_sha") != msha(pr):
                print("  [DL3] -: البيان الأب معدَّل بعد توليده (بصمته لا تطابق محتواه)"); sys.exit(1)
            par_ref = pr["manifest_sha"]           # S-3: يُخزَّن manifest_sha لا المسار
        man, bad = delta(load(av[0]), load(av[1]), load(opt("--tombs"))["tombstones"] if opt("--tombs") else {}, opt("--audience", "الكل"), opt("--summary", ""), par_ref)
        p = opt("--out", "man.json")
        save(man, p)
        for s, r, m in bad: print(f"  [{s}] {r}: {m}")
        print(f"  delta: +{len(man['added'])} ~{len(man['changed'])} -{len(man['deleted'])} †{len(man['tombstoned'])}")
        sys.exit(1 if bad else 0)
    if c == "reproduce":
        bad = reproduce(load(av[0]), load(av[1]), load(av[2]))
        for s, r, m in bad: print(f"  [{s}] {r}: {m}")
        print("إعادة الإنتاج: مطابقة." if not bad else "إعادة الإنتاج: غير مطابقة.")
        sys.exit(1 if bad else 0)
    if c == "wake":
        t, read, tgt = wake(av[0], opt("--dir"), opt("--audience", "ن"))
        print(f"  كلفة اليقظة: {t} بايت (بيان + {len(tgt)} ملفًا موجّهًا) · القراءات: {len(read)}")
        sys.exit(0)
    if c == "chain":
        man, pr = load(av[0]), load(opt("--parent"))
        if pr.get("manifest_sha") != msha(pr):
            print("  [DL3] -: البيان الأب معدَّل بعد توليده (بصمته لا تطابق محتواه)"); sys.exit(1)
        if man.get("parent") != pr.get("manifest_sha"):
            print("  [DL3] -: سلسلة استئناف مقطوعة (parent ≠ بصمة السابق)"); sys.exit(1)
        if man.get("manifest_sha") != msha(man):
            print("  [DL3] -: البيان الابن معدَّل بعد توليده"); sys.exit(1)
        print("  السلسلة متصلة (رابط صحيح)."); sys.exit(0)
    print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
