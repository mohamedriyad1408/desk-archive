#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فاحص «إهمال عدسة» — بطاقة ن-089 (أ) — ٢٠٢٦-١٠-٠١

يفحص التقرير الختامي الواحد (قالب R3-R7: القوالب/التقرير-الختامي-الواحد.md — الملحق المعياري ٢/٤)
ويعلن الحالات الحمراء بأسماء أحكامها (IG-L1…IG-L6)، وخروجه rc=0 أخضر / rc=1 أحمر معلن.

الاستعمال:
  python3 -B scripts/فاحص-إهمال-عدسة.py <التقرير.md> [--repo جذر]      # فحص ملف
  python3 -B scripts/فاحص-إهمال-عدسة.py --sample-pass                  # عتبة: عيّنة تامة تخرج خضراء
  python3 -B scripts/فاحص-إهمال-عدسة.py --acceptance                   # ثلاث قتلات القبول (تعمل ذاتيًا)
"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path

AR = "١٢٣٤٥"
LENS_IDS = {"ع١", "ع٢", "ع٣"}
DIGIT = {c: i + 1 for i, c in enumerate(AR)}

def cells_of(line: str):
    if not line.strip().startswith("|"):
        return None
    return [c.strip() for c in line.strip().strip("|").split("|")]

def arabic_reason(txt: str) -> str:
    core = txt.replace("N/A", "").replace("N\\A", "").strip(" :：[]（）()")
    return core if len(re.findall(r"[\u0600-\u06FF]", core)) >= 3 else ""

def ref_traceable(ref: str, repo: Path | None):
    """يعيد (ok, سبب). المرجع يحلّ إن حمل: v-NNN أو بصمة hex≥7 أو أمرًا بين ` ` أو مسارًا/ملفًا موجودًا."""
    r = ref.strip()
    if not r or r in {"-", "—", "؟", "...", "…"}:
        return False, "مرجع فارغ"
    if re.search(r"v-\d{3,}", r) or re.search(r"\b[0-9a-f]{7,}\b", r) or re.search(r"`[^`]+`", r):
        return True, ""
    paths = re.findall(r"[^\s`|()]+(?:/[^\s`|()]+|\.(?:md|py|sh|json|jsonl|tsv|yml|yaml|txt))\b", r)
    if not paths:
        return False, "لا يحمل معرّفًا يحلّ (حجم/بصمة/أمر/مسار)"
    if repo is None:
        return True, ""
    for p in paths:
        p = p.split("#")[0].strip("<>,;")
        cands = [repo / p, repo / "القناة" / p, repo.parent / p]
        if any(c.exists() for c in cands):
            return True, ""
    return False, f"المسار لا يوجد على القرص: {paths[0]}"

def check(text: str, repo: Path | None):
    red, notes = [], []
    # ① جدول المخرجات الخمسة عشر
    out_rows = []
    for line in text.splitlines():
        c = cells_of(line)
        if c and len(c) >= 4 and c[0] in LENS_IDS:
            m = re.match(r"([١٢٣٤٥])", c[1])
            idx = DIGIT.get(m.group(1)) if m else None
            out_rows.append((c[0], idx, c[2], c[3]))
    seen = [(l, i) for l, i, _, _ in out_rows]
    dup = sorted({p for p in seen if seen.count(p) > 1})
    expected = {(l, i) for l in LENS_IDS for i in range(1, 6)}
    missing = sorted(expected - set(seen))
    if len(out_rows) != 15 or missing or dup:
        red.append(f"IG-L1 نقص صف من الخمسة عشر: صفوف={len(out_rows)} · ناقص={[f'{l}-{i}' for l, i in missing]} · مكرر={dup}")
    # ② الحالة والدليل
    for lens, idx, status, ref in out_rows:
        tag = f"{lens}-{idx}"
        if "N/A" in status:
            if not arabic_reason(status):
                red.append(f"IG-L2 {tag}: N/A بلا سبب معلن ({status!r})")
        elif "تم" in status:
            ok, why = ref_traceable(ref, repo)
            if not ok:
                red.append(f"IG-L3 {tag}: «تمّ» بلا مرجع دليل يحلّ — {why} ({ref!r})")
        else:
            red.append(f"IG-L2 {tag}: حالة غير معروفة ({status!r}) — المطلوب «تمّ» أو N/A بسبب معلن")
    # ③ سجل المراحل خ-١…خ-٥
    stages = {}
    for line in text.splitlines():
        c = cells_of(line)
        if c and len(c) >= 2:
            m = re.match(r"^خ-([١٢٣٤٥])(?:\s|$)", c[0])
            if m:
                stages[DIGIT[m.group(1)]] = (c[1], c[2] if len(c) > 2 else "")
    if len(stages) != 5:
        red.append(f"IG-L6 سجل المراحل ناقص: وجد {len(stages)}/٥")
    order = []
    for i in range(1, 6):
        st = stages.get(i, ("", ""))[0]
        if st == "" or "…" in st or ".." in st:
            red.append(f"IG-L7 خ-{i}: خانة غير معبأة")
            state = "OPEN"
        elif "نعم" in st:
            state = "CLOSED"
        elif "N/A" in st and arabic_reason(st):
            state = "NA"
        else:
            red.append(f"IG-L7 خ-{i}: حالة غير مقبولة ({st!r})")
            state = "OPEN"
        order.append(state)
    for i in range(1, 5):
        if order[i] == "CLOSED" and any(order[j] not in ("CLOSED", "NA") for j in range(i)):
            red.append(f"IG-L5 بدأ خ-{i+1} قبل إقفال خ-{i}: {order}")
            break
    # ④ الأقسام الإلزامية
    for name, pat in [("فئة المخاطرة (أ/ب)", r"فئة المخاطرة"), ("المؤجلات بأرقام سجل قراراتها", r"المؤجلات"),
                      ("«لم يُقَس»", r"لم يُقَس"), ("«ما تبقى مفتوحًا»", r"ما تبقى مفتوحًا")]:
        if not re.search(pat, text):
            red.append(f"IG-L6 قسم إلزامي غائب: {name}")
    notes.append(f"صفوف المخرجات: {len(out_rows)}/١٥ · سجل المراحل: {len(stages)}/٥ · الحالات: {order}")
    return red, notes

SAMPLE = """# قالب — عيّنة تامة (اختبار عتبة)
**المهمة:** عيّنة · **الحجم:** v-567
## ١)
| العدسة | المخرج | الحالة [تمّ / N/A بسبب معلن] | مرجع الدليل |
|---|---|---|---|
| ع١ | ١. الأثر بالأرقام | تمّ | `python3 -B probe.py` ← v-567 · 4aa7213e |
| ع١ | ٢. الجذر الاستراتيجي | تمّ | القناة/العمل/الحالة.md |
| ع١ | ٣. مسارات بديلة | N/A: لا مسار بديل داخل النطاق | — |
| ع١ | ٤. قرار موثّق | تمّ | v-567 |
| ع١ | ٥. معيار نجاح | تمّ | 82612b41 |
| ع٢ | ١. مسح المسارات | تمّ | القناة/العمل/الحالة.md |
| ع٢ | ٢. الجذر وتصنيفه | تمّ | v-566 |
| ع٢ | ٣. المخاطرة الهندسية | N/A: لا خطر مالي في النطاق | — |
| ع٢ | ٤. تخطيط أحادي المحور | تمّ | 5ab70ed |
| ع٢ | ٥. زاويتا التحقق | تمّ | v-567 |
| ع٣ | ١. لقطة مسبقة | تمّ | القناة/العمل/الحالة.md |
| ع٣ | ٢. تطبيق الجذر | تمّ | v-567 |
| ع٣ | ٣. قفل الهوية | تمّ | config=0 ← v-567 |
| ع٣ | ٤. إثبات حي | تمّ | `bash scripts/فحص-الأرشيف.sh` ← 82612b41 |
| ع٣ | ٥. تحقق متقاطع | تمّ | v-567 |
## ٢) سجل المراحل
| المرحلة | أُقفلت بمخرجها؟ | المرجع |
|---|---|---|
| خ-١ القياس | نعم | v-566 |
| خ-٢ الجذر | نعم | v-566 |
| خ-٣ التخطيط | نعم | v-567 |
| خ-٤ التنفيذ | نعم | v-567 |
| خ-٥ الإثبات الحي | نعم | 82612b41 |
## ٣) فئة المخاطرة (أ/ب)
**الفئة:** أ — التصنيف: حد أمان.
## ٤) المؤجلات بأرقام سجل قراراتها
| المؤجَّل | رقم القرار | الموضع |
|---|---|---|
| صفر | — | — |
## ٥) قسم «لم يُقَس»
- لم يُقَس في هذه العيّنة ما خرج عن النطاق.
## ٦) قسم «ما تبقى مفتوحًا»
- لا شيء.
"""

def run_one(path: Path, repo):
    text = path.read_text(encoding="utf-8")
    red, notes = check(text, repo)
    for n in notes:
        print("معلومة:", n)
    for r in red:
        print("أحمر:", r)
    print("RESULT:", "DANGER" if red else "GREEN")
    return 1 if red else 0

def acceptance():
    tmp = Path(tempfile.mkdtemp(prefix="ig-kills-"))
    cases = []
    base = SAMPLE
    (tmp / "complete.md").write_text(base, encoding="utf-8")
    # قتلة ١: حذف مخرج (صف ع٣/٥)
    k1 = "\n".join(l for l in base.splitlines() if not l.startswith("| ع٣ | ٥."))
    (tmp / "k1-missing-row.md").write_text(k1, encoding="utf-8")
    # قتلة ٢: إفراغ دليل مع بقاء «تمّ»
    k2 = base.replace("| ع٣ | ٤. إثبات حي | تمّ | `bash scripts/فحص-الأرشيف.sh` ← 82612b41 |",
                      "| ع٣ | ٤. إثبات حي | تمّ |  |")
    (tmp / "k2-empty-ref.md").write_text(k2, encoding="utf-8")
    # قتلة ٣: قلب تسلسل خ (خ-٤ نعم قبل إقفال خ-٢)
    k3 = base.replace("| خ-٢ الجذر | نعم | v-566 |", "| خ-٢ الجذر |  |  |")
    (tmp / "k3-bad-order.md").write_text(k3, encoding="utf-8")
    expect = {"complete.md": ("GREEN", 0), "k1-missing-row.md": ("DANGER", 1),
              "k2-empty-ref.md": ("DANGER", 1), "k3-bad-order.md": ("DANGER", 1)}
    ok = True
    for name, (want, wrc) in expect.items():
        print(f"\n── {name} (المتوقع: {want}) ──")
        text = (tmp / name).read_text(encoding="utf-8")
        red, _ = check(text, None)
        got = "DANGER" if red else "GREEN"
        for r in red:
            print("   أحمر:", r)
        good = (got == want)
        ok &= good
        print(f"   الناتج: {got} {'✓' if good else '✗'}")
    print("\nACCEPTANCE:", "PASS — العيّنة التامة خضراء والثلاث قتلات حمراء معلنة" if ok else "FAIL")
    return 0 if ok else 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report", nargs="?")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--sample-pass", action="store_true")
    ap.add_argument("--acceptance", action="store_true")
    a = ap.parse_args()
    if a.acceptance:
        return acceptance()
    if a.sample_pass:
        tmp = Path(tempfile.mkdtemp(prefix="ig-sample-")) / "sample.md"
        tmp.write_text(SAMPLE, encoding="utf-8")
        print("── عيّنة تامة (عتبة نجاح) ──")
        rc = run_one(tmp, None)
        print("SAMPLE-PASS:", "PASS ✓" if rc == 0 else "FAIL ✗")
        return rc
    if not a.report:
        ap.error("يلزم مسار التقرير أو --sample-pass/--acceptance")
    return run_one(Path(a.report), Path(a.repo).resolve() if a.repo else None)

if __name__ == "__main__":
    sys.exit(main())
