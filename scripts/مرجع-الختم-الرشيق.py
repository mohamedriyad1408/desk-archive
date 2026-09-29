#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مرجع مبدئي للختم الرشيق (ب12) — مسودة مسبار ن (ق may replace). غير مفعّل حتى بوابة ب16.
العقد: يقرأ رأس البعيد من object database · يختار الرقم تحت CAS · لا يجسّد تاريخ blobs ·
peak disk تابع للشجرة الحية لا عدد الأحجام · لا يكتب credential في remote/config.
الاستخدام: مرجع-الختم-الرشيق.py <repo> [--flaw naive|checkout|token] [--ledger FILE] [--author ID]"""
import subprocess, sys, os, hashlib, tarfile, io, time

def git(repo, *a, check=True):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    if check and r.returncode != 0:
        print("git", a, r.stderr, file=sys.stderr); sys.exit(130)
    return r.stdout

def tree_files(repo):
    out=[]
    for dp,dns,fns in os.walk(repo):
        rel=os.path.relpath(dp,repo)
        if rel.split(os.sep)[0] in ('.git','vault'): dns[:]=[]; continue
        for f in fns: out.append(os.path.join(dp,f))
    return sorted(out)

def next_number(repo):
    out = git(repo, "ls-tree", "--name-only", "origin/main", "vault/", check=False)
    ns = [int(l.split("v-")[1].split(".")[0]) for l in out.splitlines() if "v-" in l]
    return (max(ns)+1) if ns else 1

def build_volume(repo, path, note=""):
    files = tree_files(repo)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for f in files: t.add(f, arcname=os.path.relpath(f, repo))
        if note:                                   # غيرية المحتوى بين المؤلفين (واقعية السباق)
            info = tarfile.TarInfo("seal-meta.txt"); b = note.encode(); info.size = len(b)
            t.addfile(info, io.BytesIO(b))
    data = buf.getvalue()
    open(path, "wb").write(data)
    return hashlib.sha256(data).hexdigest()[:16]

def main():
    repo, flaw, ledger, author = sys.argv[1], None, None, os.environ.get("SEAL_AUTHOR", "anon")
    a = sys.argv[2:]
    for i, x in enumerate(a):
        if x == "--flaw": flaw = a[i+1]
        if x == "--ledger": ledger = a[i+1]
        if x == "--author": author = a[i+1]
    if flaw == "checkout":                      # علة مقصودة: تجسيد التاريخ كاملًا (peak ينمو مع N)
        tmp = os.path.join(repo, ".checkout-peak"); os.makedirs(tmp, exist_ok=True)
        subprocess.run(["bash","-c",f"git -C {repo} archive origin/main vault | tar -x -C {tmp}"], check=True)
    for attempt in range(1, 7):
        git(repo, "fetch", "-q", "origin")
        git(repo, "reset", "-q", "--hard", "origin/main")   # أساس نظيف كل محاولة (وإلا أُبقيت بقايا المحاولة فطمست رقم غيرنا)
        if flaw == "token":                     # علة مقصودة: credential في config
            cfg = os.path.join(repo, ".git", "config"); txt = open(cfg).read()
            if "x-access-token:PROBE" not in txt:
                open(cfg, "w").write(txt + '\n[probe]\n\turl = https://x-access-token:PROBE@example.invalid/repo.git\n')
        if flaw == "naive":
            if "_n_fixed" not in globals():
                globals()["_n_fixed"] = len([f for f in os.listdir(os.path.join(repo, "vault")) if f.startswith("v-")]) + 1
            n = globals()["_n_fixed"]
        else:
            n = next_number(repo)
        vpath = os.path.join(repo, "vault", f"v-{n:04d}.enc")
        h = build_volume(repo, vpath, note=f"{author}:{n}")
        git(repo, "add", f"vault/v-{n:04d}.enc")
        git(repo, "commit", "-qm", f"seal {n} by {author}")
        r = subprocess.run(["git", "-C", repo, "push", "-q", "origin", "HEAD:main"], capture_output=True, text=True)
        if r.returncode == 0:
            if ledger:
                open(ledger, "a").write(f"{author}\t{n}\t{h}\t{git(repo,'rev-parse','HEAD').strip()[:8]}\n")
            print(f"ختم {author}: v-{n:04d} sha {h} (محاولة {attempt})"); return 0
        time.sleep(0.05)
    print("فشل الختم بعد 6 محاولات", file=sys.stderr); sys.exit(1)

if __name__ == "__main__": main()
