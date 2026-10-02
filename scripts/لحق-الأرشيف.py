#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""لحق «الحالة.md» بالأرشيف — الأداة اللاحقة لفصل-الحالة.py (ب٨/R-06 · بطاقة ن-086 الباب ٤).

السياق: فصل-الحالة.py يفصل مرة واحدة (وحارس الإلحاقية يرفض الفصل الثاني) — وهذه الأداة
تُكمل ما بُني عليه: تنقل أقدم نقوش الرأس إلى **ذيل الأرشيف** (إلحاق-فقط) وتمدّد الفهرس
ببصمة كل مقطع، فتعود نسبة الرأس إلى حدّ الحارس (‏< 250KB).

المبادئ (كالأصل — لا تُخفَّف):
- نفس التقسيم والتسمية: مقاطع عند `## `؛ المنقول نقوش فقط؛ غير النقش يبقى في الرأس بموضعه.
- الأرشيف إلحاق-فقط: لا تحرير ولا حذف ولا إعادة ترتيب؛ الجديد يُضاف في الذيل وحده.
- حفظ بايتي مبرهن: الرأس الجديد = القديم − المنقول + سجل النقل · الأرشيف الجديد = القديم + المنقول.
- الفهرس يمتدّ بالترقيم المتصل (460…)، وكل صف ببصمة المقطع وطوله وعنوانه.
- شروط قبل الكتابة: الأرشيف القائم أخضر عند حارس الإلحاقية؛ الأرشيف الجديد أخضر محسوبًا؛
  الرأس الناتج < 250KB؛ العدّ الكلي محفوظ. أي شرط فاشل ⇒ رفض بلا كتابة.
- بصمات قبل/بعد تُطبع (sha256) للرأس والأرشيف والفهرس.

الاستعمال:
  python3 -B scripts/لحق-الأرشيف.py --dry [--keep 30]     # خطة وقياسات بلا كتابة
  python3 -B scripts/لحق-الأرشيف.py --apply [--keep 30]   # النقل (افتراضيًا: إبقاء آخر ٣٠ نقشًا)
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

H = lambda b: hashlib.sha256(b).hexdigest()
DATE_DEFAULT = "2026-10-02"
MAX_HEAD = 250_000


def parse_blocks(t: str):
    """يعيد (preamble, [(start, end, header)]) بتقسيم عند كل سطر `## ` — منطق فصل-الحالة.py نفسه."""
    ms = [m.start() for m in re.finditer(r"(?m)^## ", t)]
    if not ms:
        return t, []
    pre = t[:ms[0]]
    blocks = []
    for i, s in enumerate(ms):
        e = ms[i + 1] if i + 1 < len(ms) else len(t)
        blocks.append((s, e, t[s:t.find("\n", s)] if t.find("\n", s) != -1 else t[s:]))
    return pre, blocks


def is_naqsh(hdr: str) -> bool:
    return hdr.startswith("## نقش")


def guard_ok(arch_text: str, man_rows: list) -> tuple:
    """منطق حارس الإلحاقية (كالأصل): كل صف مفهرس يقابل مقطع نقش ببصمته؛ الزيادة في الذيل فقط."""
    _, blocks = parse_blocks(arch_text)
    naq_blk = [arch_text[s:e].encode() for (s, e, h) in blocks if is_naqsh(h)]
    if len(naq_blk) < len(man_rows):
        return False, f"مقاطع الأرشيف {len(naq_blk)} < المفهرسة {len(man_rows)}"
    bad = [r[0] for r in man_rows if H(naq_blk[int(r[0]) - 1]) != r[1]]
    if bad:
        return False, f"بصمات مغايرة للمفهرس (أرقام {bad[:8]})"
    return True, f"كل المقاطع المفهرسة ({len(man_rows)}) ببصماتها · زيادة {len(naq_blk) - len(man_rows)} في الذيل"


def load_manifest(man: Path):
    rows, header = [], []
    for line in man.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            header.append(line)
        elif line.strip():
            parts = line.split("\t")
            if len(parts) >= 4:
                rows.append(parts[:4])
    return header, rows


def run(state: Path, arch: Path, man: Path, keep: int, date: str, apply: bool) -> int:
    t = state.read_text(encoding="utf-8")
    b0 = t.encode()
    sha0 = H(b0)
    arch_old = arch.read_text(encoding="utf-8")
    arch_old_b = arch_old.encode()
    man_header, man_rows = load_manifest(man)

    # شرط ٠: الأرشيف القائم أخضر
    ok, why = guard_ok(arch_old, man_rows)
    if not ok:
        print(f"مرفوض: الأرشيف القائم ليس أخضر عند حارس الإلحاقية ({why}) — لا نقل فوق مشكوك.", file=sys.stderr)
        return 4

    pre, blocks = parse_blocks(t)
    naq = [i for i, (_, _, h) in enumerate(blocks) if is_naqsh(h)]
    if len(naq) <= keep:
        print(f"لا نقل: النقوش في الرأس {len(naq)} ≤ المحتفظ {keep} — لا تغيير.")
        return 0
    move_idx = set(naq[:-keep])

    moved = "".join(t[blocks[i][0]:blocks[i][1]] for i in sorted(move_idx))
    kept = "".join([pre] + [t[s:e] for i, (s, e, _) in enumerate(blocks) if i not in move_idx])
    moved_b = moved.encode()

    # امتداد الفهرس
    start_n = (int(man_rows[-1][0]) + 1) if man_rows else 1
    new_rows = []
    for j, i in enumerate(sorted(move_idx)):
        s, e, hdr = blocks[i]
        seg = t[s:e].encode()
        new_rows.append([str(start_n + j), H(seg), str(len(seg)), hdr.strip()[:120]])
    man_new_txt = "\n".join(man_header + ["\t".join(r) for r in man_rows + new_rows]) + "\n"

    # الأرشيف الجديد: ذيل فقط
    sep = "" if arch_old.endswith("\n") or arch_old == "" else "\n"
    arch_new_txt = arch_old + sep + moved
    arch_new_b = arch_new_txt.encode()

    # شرط ١: حفظ بايتي الرأس
    if len(kept.encode()) + len(moved_b) != len(b0):
        print("مرفوض: انتهاك حفظ بايت الرأس — لا كتابة.", file=sys.stderr)
        return 5
    # شرط ٢: الأرشيف الجديد أخضر
    ok2, why2 = guard_ok(arch_new_txt, man_rows + new_rows)
    if not ok2:
        print(f"مرفوض: الأرشيف الجديد يسقط الحارس ({why2}) — لا كتابة.", file=sys.stderr)
        return 5
    # شرط ٣: العدّ الكلي محفوظ
    tot_before = len(naq) + len(man_rows)
    tot_after = (len(naq) - len(move_idx)) + len(man_rows + new_rows)
    if tot_before != tot_after:
        print(f"مرفوض: العدّ غير محفوظ ({tot_before} ≠ {tot_after}).", file=sys.stderr)
        return 5

    ledger = (
        f"\n## سجل نقل النقوش — {date} (لحاق الحالة/الأرشيف — الأداة اللاحقة ب٨/R-06)\n\n"
        f"- قبل: {len(b0)} B · النقوش {len(naq)} · بعد: مقاطع محفوظة {len(kept.encode())} B ({len(naq) - len(move_idx)} نقشًا) "
        f"+ سجل النقل هذا · الأرشيف {len(arch_new_b)} B ({len(man_rows + new_rows)} نقشًا مفصولًا في المجموع، منها {len(move_idx)} في هذا النقل)\n"
        f"- حفظ بايتي: الأرشيف {len(arch_old_b)} + المنقول {len(moved_b)} = {len(arch_new_b)} ✓ · "
        f"والأصل كاملًا: محفوظ {len(kept.encode())} + منقول {len(moved_b)} = {len(b0)} ✓ · "
        f"والعدّ: {len(man_rows + new_rows)} + {len(naq) - len(move_idx)} = {tot_after} ✓\n"
        f"- بصمات: أصل الحالة {sha0} · الرأس قبل إلحاق هذا السجل {H(kept.encode())} · الأرشيف الجديد {H(arch_new_b)} · الفهرس الجديد {H(man_new_txt.encode())}\n"
        f"- الأداة: `scripts/لحق-الأرشيف.py` (نفس قواعد ب٨: إلحاق-فقط · فهرس ببصمة كل مقطع · حفظ بايتي · وشرطها قبل الكتابة: حارس الإلحاقية أخضر على القائم وعلى الجديد)."
    )
    head_new = kept + ledger
    head_new_b = head_new.encode()

    # شرط ٤: الرأس الناتج دون العتبة
    if len(head_new_b) >= MAX_HEAD:
        print(f"مرفوض: الرأس الناتج {len(head_new_b)} B ≥ {MAX_HEAD} — زد المنقول (قلّل --keep).", file=sys.stderr)
        return 3

    print(f"الخطة: نقل {len(move_idx)} نقشًا · إبقاء {len(naq) - len(move_idx)} · "
          f"الرأس {len(b0)} → {len(head_new_b)} B · الأرشيف {len(arch_old_b)} → {len(arch_new_b)} B · "
          f"الفهرس {len(man_rows)} → {len(man_rows + new_rows)} صفًا")
    print(f"  أول منقول: {blocks[min(move_idx)][2][:80]}")
    print(f"  آخر منقول: {blocks[max(move_idx)][2][:80]}")
    print(f"  حارس الإلحاقية (محسوبًا على الجديد): أخضر ✓ — {why2}")

    if not apply:
        print("dry: لا كتابة.")
        return 0

    state.write_text(head_new, encoding="utf-8")
    arch.write_text(arch_new_txt, encoding="utf-8")
    man.write_text(man_new_txt, encoding="utf-8")
    print(f"تم النقل: رأس {H(head_new_b)} · أرشيف {H(arch_new_b)} · فهرس {H(man_new_txt.encode())}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="القناة/العمل/الحالة.md")
    ap.add_argument("--archive", default="القناة/العمل/أرشيف-النقوش-٢٠٢٦.md")
    ap.add_argument("--manifest", default="القناة/العمل/فهرس-أرشيف-النقوش-٢٠٢٦.tsv")
    ap.add_argument("--keep", type=int, default=30)
    ap.add_argument("--date", default=DATE_DEFAULT)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    return run(Path(args.state), Path(args.archive), Path(args.manifest), args.keep, args.date, args.apply)


if __name__ == "__main__":
    sys.exit(main())
