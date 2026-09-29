#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مسبار ب10 (نشر الحالة والنبض) — مسودة مسبار ن، غير مفعّل حتى بوابة ب16.
القبول: ① التزامات idle=0 (لا نبضة بلا انتقال مادي) ② أربع انتقالات ⇒ أربع حالات
③ لا يُصدَر «غياب» بساعة الجدار خارج دورة الحياة المعلنة.
الأوضاع: --real <repo> <rev-range> | --fixture | --lifecycle"""
import subprocess, sys, tempfile, os

TRANSITIONS = ("استلم", "منتصف", "سلمت", "عائق", "بطاقة")  # فتح/شطب بطاقة = تغيّر سجل الإسناد

def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout

def classify(msg):
    m = msg.strip()
    if not m.lower().startswith(("pulse", "نبض", "بطاقة")):
        return "work"
    return "transition" if any(t in m for t in TRANSITIONS) else "idle-pulse"

def run_real(repo, rng):
    out = git(repo, "log", "--format=%H|%s", rng)
    counts = {"work": 0, "transition": 0, "idle-pulse": 0}
    idle = []
    for line in out.splitlines():
        if "|" not in line: continue
        h, m = line.split("|", 1); k = classify(m); counts[k] += 1
        if k == "idle-pulse": idle.append((h[:8], m[:60]))
    print(f"[حقيقي {rng}] work={counts['work']} transition={counts['transition']} idle-pulse={counts['idle-pulse']}")
    for h, m in idle[:6]: print(f"    idle: {h} {m}")
    if counts["idle-pulse"] == 0:
        print("✅ idle=0 — مطابق للسياسة الانتقالية"); return 0
    print("❌ idle>0 — السياسة الحالية ما زالت دورية (فشل مقصود قبل نفاذ ب10)"); return 1

def run_fixture():
    d = tempfile.mkdtemp(prefix="b10-")
    git(d, "init", "-q"); git(d, "config", "user.email", "t@t"); git(d, "config", "user.name", "t")
    seq = ["pulse: role استلم card", "pulse: role منتصف card", "work: deliverable",
           "pulse: role عائق card", "pulse: role سلمت card"]
    for i, m in enumerate(seq):
        open(os.path.join(d, f"f{i}"), "w").write("x"); git(d, "add", "-A"); git(d, "commit", "-qm", m)
    rc = 0; out = git(d, "log", "--format=%s")
    idle = [m for m in out.splitlines() if classify(m) == "idle-pulse"]
    trans = [m for m in out.splitlines() if classify(m) == "transition"]
    print(f"[صورة انتقالية] transition={len(trans)} idle={len(idle)}")
    if len(trans) == 4 and not idle:
        print("✅ أربع انتقالات ⇒ أربع حالات، idle=0"); rc = 0
    else:
        print("❌ خلل في الصورة الانتقالية"); rc = 1
    return rc

def run_lifecycle():
    """لا غياب بساعة الجدار خارج دورة الحياة: الغياب يُشتق من دورة الحياة المعلنة لا من الزمن وحده."""
    def detector(card_open, gap_s, lifecycle_alive):
        if not card_open: return None                      # بطاقة مغلقة ⇒ لا حكم غياب إطلاقًا
        if not lifecycle_alive: return "no-verdict-outside-lifecycle"
        return "absence" if gap_s > 390 else None
    cases = [  # (وصف, بطاقة, فجوة, حياة, المتوقع)
        ("بطاقة مغلقة + فجوة 4000ث", False, 4000, False, None),
        ("حياة مفتوحة + فجوة 300ث",  True,  300,  True,  None),
        ("حياة مفتوحة + فجوة 400ث",  True,  400,  True,  "absence"),
        ("خارج دورة الحياة + فجوة 4000ث", True, 4000, False, "no-verdict-outside-lifecycle"),
    ]
    rc = 0
    for d, co, gap, al, exp in cases:
        got = detector(co, gap, al)
        good = got == exp
        print(f"  {'✅' if good else '❌'} {d}: got={got} expected={exp}")
        rc |= 0 if good else 1
    print("✅ قتل دورة الحياة: لا غياب بزمن الجدار خارج الحياة المعلنة" if rc == 0 else "❌ فشل القتل")
    return rc

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    if a[0] == "--real": sys.exit(run_real(a[1], a[2]))
    if a[0] == "--fixture": sys.exit(run_fixture())
    if a[0] == "--lifecycle": sys.exit(run_lifecycle())
