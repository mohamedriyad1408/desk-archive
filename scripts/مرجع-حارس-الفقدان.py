#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مرجع مبدئي لحارس «لا-فقدان» (ب18) — مسودة مسبار ن، غير مفعّلة حتى بوابة ب16.
مصدر الحقيقة: meta/live-set.tsv تراكميًا + meta/tombstones.tsv (لا نافذة K، لا «آخر حجم»).
الاستخدام: مرجع-حارس-الفقدان.py {check|snapshot|tombstone <p> <auth> <reason>|audit|refresh} [--repo DIR]"""
import os, subprocess, sys, tempfile, hashlib, shutil

def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f"git {' '.join(args)}: {r.stderr.strip()}", file=sys.stderr); sys.exit(130)
    return r.stdout.strip()

def parse_args():
    args = sys.argv[1:]
    repo = os.getcwd()
    if "--repo" in args:
        i = args.index("--repo"); repo = args[i + 1]; del args[i:i + 2]
    return repo, args

def tree_files(repo):
    out = {}
    for dp, dns, fns in os.walk(repo):
        rel = os.path.relpath(dp, repo)
        if rel == ".": rel = ""
        if rel.split(os.sep)[0] in (".git", "meta", "vault"): dns[:] = []; continue
        for f in fns:
            p = os.path.join(dp, f); r = os.path.relpath(p, repo)
            out[r] = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    return out

def read_file(repo, path):
    p = os.path.join(repo, path)
    if not os.path.exists(p): return None
    return dict(l.split("\t", 1) for l in open(p, encoding="utf-8").read().splitlines() if "\t" in l)

def show(repo, rev, path):
    r = subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None

def head_rev(repo):
    for ref in ("refs/remotes/origin/main", "refs/remotes/origin/HEAD", "HEAD"):
        r = subprocess.run(["git", "-C", repo, "rev-parse", ref], capture_output=True, text=True)
        if r.returncode == 0: return r.stdout.strip()
    return ""

def cmd_snapshot(repo):
    prev = read_file(repo, "meta/live-set.tsv") or {}
    prev.update(tree_files(repo))                      # تراكمي: الجديد يحدّث، ولا يُسقط إلا بدفن
    os.makedirs(f"{repo}/meta", exist_ok=True)
    with open(f"{repo}/meta/live-set.tsv", "w", encoding="utf-8") as fh:
        for k in sorted(prev): fh.write(f"{k}\t{prev[k]}\n")
    rev = git(repo, "rev-parse", "HEAD", check=False)
    if rev: open(f"{repo}/meta/base.rev", "w").write(rev + "\n")
    print(f"لقطة live-set تراكمية: {len(prev)} مسارًا.")

def cmd_tombstone(repo, pos):
    p, auth, reason = pos[0], pos[1], pos[2]
    os.makedirs(f"{repo}/meta", exist_ok=True)
    with open(f"{repo}/meta/tombstones.tsv", "a", encoding="utf-8") as fh:
        fh.write(f"{p}\t{auth}\t{reason}\n")
    print(f"دُفن: {p} (سلطة: {auth})")

def cmd_check(repo):
    subprocess.run(["git", "-C", repo, "fetch", "-q", "origin"], capture_output=True)
    base = head_rev(repo)
    # CAS بالنسب: رأس البعيد يجب أن يكون أصلًا لـHEAD (لا شجرة متخلفة/منفصلة تدفع)
    default = subprocess.run(["git", "-C", repo, "symbolic-ref", "-q", "--short",
                              "refs/remotes/origin/HEAD"], capture_output=True, text=True).stdout.strip()
    ref = default.split("/", 1)[-1] if default else "main"
    if base:
        anc = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor",
                              base, "HEAD"], capture_output=True)
        if anc.returncode != 0:
            print(f"شجرة غير مؤسسة على الرأس البعيد ({ref}@{base[:8]}): صالح ثم أعد (CAS).", file=sys.stderr)
            sys.exit(5)
    remote_set = {}
    raw = show(repo, base, "meta/live-set.tsv")
    if raw:
        remote_set = dict(l.split("\t", 1) for l in raw.decode().splitlines() if "\t" in l)
    tomb_raw = show(repo, base, "meta/tombstones.tsv") or b""
    tombs = {l.split("\t")[0] for l in tomb_raw.decode().splitlines() if l.strip()}
    now = tree_files(repo)
    missing = [p for p in remote_set if p not in now and p not in tombs]
    added = [p for p in now if p not in remote_set]
    changed = [p for p in now if p in remote_set and now[p] != remote_set[p]]
    revived = [p for p in tombs if p in now]
    print(f"تقرير المرشح: added={len(added)} changed={len(changed)} missing={len(missing)} revived={len(revived)} tombstones={len(tombs)}")
    blocked = False
    for p in missing:
        data = show(repo, base, p)
        if data is None:                              # بحث في التاريخ عن آخر نسخة تحمله (تجاوز النافذة)
            for c in git(repo, "rev-list", "--all", "--", p, check=False).splitlines():
                data = show(repo, c, p)
                if data is not None: break
        if data is not None:
            dst = os.path.join(repo, p); os.makedirs(os.path.dirname(dst) or repo, exist_ok=True)
            open(dst, "wb").write(data); print(f"استُعيد (غير مدفون): {p}")
        else:
            print(f"مفقود بلا مصدر استعادة: {p}")
        blocked = True
    for p in revived:
        print(f"إحياء غير مصرح لمسار مدفون: {p}"); blocked = True
    if blocked:
        print("لا-فقدان: رُفض — راجع المفقود/المُحيا.", file=sys.stderr); sys.exit(4)
    print("لا-فقدان: نظيف.")

def cmd_audit(repo):
    union = set()
    for c in git(repo, "rev-list", "--all", check=False).splitlines():
        raw = show(repo, c, "meta/live-set.tsv")
        if raw:
            union.update(l.split("\t")[0] for l in raw.decode().splitlines() if "\t" in l)
    tombs = set((read_file(repo, "meta/tombstones.tsv") or {}).keys())
    head = git(repo, "rev-parse", "HEAD", check=False)
    raw = show(repo, head, "meta/tombstones.tsv") or b""
    tombs |= {l.split("\t")[0] for l in raw.decode().splitlines() if l.strip()}
    live = set(tree_files(repo))
    expect = union - tombs
    if expect == live:
        print(f"تدقيق التاريخ: مطابق (union−tombstones == live، {len(live)} مسارًا).")
    else:
        print(f"تدقيق التاريخ: اختلاف! ناقص منها: {sorted(expect-live)[:10]} زائد فيها: {sorted(live-expect)[:10]}", file=sys.stderr)
        sys.exit(6)

if __name__ == "__main__":
    r, pos = parse_args()
    cmd = pos[0] if pos else ""
    try:
        if cmd == "check": cmd_check(r)
        elif cmd == "snapshot": cmd_snapshot(r)
        elif cmd == "tombstone": cmd_tombstone(r, pos[1:])
        elif cmd == "audit": cmd_audit(r)
        else:
            print("الاستخدام: مرجع-حارس-الفقدان.py {check|snapshot|tombstone <path> <authority> <reason>|audit} [--repo DIR]"); sys.exit(2)
    except IndexError:
        print("ناقص وسائط الأمر.", file=sys.stderr); sys.exit(2)
