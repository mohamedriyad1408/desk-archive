#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فصل «الحالة.md»: رأس نشط (آخر N نقشًا) + أرشيف إلحاق-فقط — بطاقة ن-086 الباب ٤ (ب٨/R-06).

المبادئ:
- تقسيم عند كل سطر عنوان `## ` (تسلسل مقاطع لا يتداخل). النقوش = المقاطع التي يبدأ عنوانها بـ«## نقش».
- يُنقل من الرأس إلى الأرشيف: مقاطع النقوش الأدنى خارج آخر N نقشًا **فقط**. أي مقطع غير نقش
  (وصايا/سجلات/خطوات…) يبقى في الرأس في موضعه — لا تحريك ولا حذف.
- حفظ بايتي تام: with-preamble + Σ مقاطع = الملف الأصلي بايتًا (بلا فواصل مضافة).
- لكل مقطع منقول بصمة sha256 في فهرس مستقل؛ والأرشيف إلحاق-فقط يُتحقق منه بحارس.
- الهجرة تُقيَّد في الرأس (سجل هجرة: بصمتا قبل/بعد · العدّ قبل=بعد) وفي ترويسة الأرشيف.

الاستعمال:
  python3 -B scripts/فصل-الحالة.py --dry                      # خطة + قياسات بلا كتابة
  python3 -B scripts/فصل-الحالة.py --apply                    # الهجرة (افتراضيًا: رأس آخر ٣٠ نقشًا)
  python3 -B scripts/فصل-الحالة.py --apply --keep 30
  python3 -B scripts/فصل-الحالة.py --guard                    # حارس الإلحاقية (الأرشيف مقابل الفهرس)
"""
import argparse, hashlib, re, sys
from pathlib import Path

H = lambda b: hashlib.sha256(b).hexdigest()

def parse_blocks(t: str):
    """يعيد (preamble, [(start, end, header)]) بتقسيم عند كل سطر `## `."""
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

def plan(t: str, keep: int):
    pre, blocks = parse_blocks(t)
    naq = [i for i, (_, _, h) in enumerate(blocks) if is_naqsh(h)]
    if len(naq) <= keep:
        return pre, blocks, naq, set()
    move_idx = set(naq[:-keep]) if keep else set(naq)
    return pre, blocks, naq, move_idx

def split_bytes(t: str, move_idx, blocks, pre):
    b_t = t.encode()
    moved = "".join(t[blocks[i][0]:blocks[i][1]] for i in sorted(move_idx))
    keep_parts = [pre] + [t[s:e] for i, (s, e, _) in enumerate(blocks) if i not in move_idx]
    kept = "".join(keep_parts)
    assert len(kept.encode()) + len(moved.encode()) == len(b_t), "انتهاك حفظ البايت"
    return kept, moved

ARCH_HDR = """# أرشيف النقوش — ٢٠٢٦ (إلحاق-فقط) — {date}
# بُني بموجب بطاقة ن-086 (الباب ٤ · ب٨/R-06): فصل «العمل/الحالة.md» — الأداة: scripts/فصل-الحالة.py
# القاعدة: لا تحرير ولا حذف ولا إعادة ترتيب لمقطع أُرشف. كل نقل جديد يمر بالأداة ويُقيَّد في فهرس-أرشيف-النقوش-٢٠٢٦.tsv.
# بصمة أصل الحالة.md قبل الفصل: {pre_sha} · المقاطع المفصولة: {n_moved} نقشًا · الحجم المنقول: {moved_b} B

"""

def do_apply(state: Path, arch: Path, man: Path, keep: int, date: str):
    t = state.read_text(encoding="utf-8")
    b0 = t.encode(); sha0 = H(b0)
    pre, blocks, naq, move_idx = plan(t, keep)
    if not move_idx:
        print(f"لا فصل: النقوش {len(naq)} ≤ المحتفظ {keep} — لا تغيير.")
        return 0
    kept, moved = split_bytes(t, move_idx, blocks, pre)
    if arch.exists():
        print(f"مرفوض: الأرشيف موجود مسبقًا ({arch}) — الفصل الأول مرة واحدة. للحاق بأداة أخرى راجع الفهرس.", file=sys.stderr)
        return 2
    # فهرس المقاطع
    rows = ["#\tsha256\tbytes\tعنوان المقطع"]
    for n, i in enumerate(sorted(move_idx), 1):
        s, e, hdr = blocks[i]
        seg = t[s:e].encode()
        rows.append(f"{n}\t{H(seg)}\t{len(seg)}\t{hdr.strip()[:120]}")
    man_txt = "\n".join(rows) + "\n"
    arch_txt = ARCH_HDR.format(date=date, pre_sha=sha0, n_moved=len(move_idx), moved_b=len(moved.encode())) + moved
    # سجل الهجرة في الرأس
    n_keep = len(naq) - len(move_idx)
    ledger = (
        f"\n## سجل هجرة النقوش — {date} (فصل الحالة/الأرشيف · بطاقة ن-086 الباب ٤)\n\n"
        f"- قبل: {len(b0)} B · النقوش {len(naq)} · بعد: الرأس {len(kept.encode())} B ({n_keep} نقشًا) · الأرشيف {len(arch_txt.encode())} B ({len(move_idx)} نقشًا مفصولًا)\n"
        f"- العدّ محفوظ: {len(move_idx)} + {n_keep} = {len(naq)} ✓ (نقشٌ لم يُفقد ولم يُكرَّر — التقسيم بايتيًا: {len(kept.encode())}+{len(moved.encode())}={len(b0)} ✓)\n"
        f"- بصمات: أصل الحالة {sha0} · الرأس قبل إلحاق هذا السجل {H(kept.encode())} · الأرشيف {H(arch_txt.encode())} · فهرس المقاطع {H(man_txt.encode())} — وبصمة ملف الرأس كاملًا بعد الإلحاق تُطبع وحدها وتُقيَّد في وثيقة القياس (المرجعية الدائرية تُرفض لا تُلفَّق)\n"
        f"- الأداة: `scripts/فصل-الحالة.py` · الفهرس: `العمل/فهرس-أرشيف-النقوش-٢٠٢٦.tsv` · القاعدة: الأرشيف إلحاق-فقط؛ الرأس يحمل آخر {keep} نقشًا."
    )
    head_out = kept + ledger
    if len(head_out.encode()) > 250_000:
        print(f"مرفوض: الرأس الناتج {len(head_out.encode())} B > 250KB — راجع عدد المحتفظ به.", file=sys.stderr)
        return 3
    state.write_text(head_out, encoding="utf-8")
    arch.write_text(arch_txt, encoding="utf-8")
    man.write_text(man_txt, encoding="utf-8")
    print(f"تم الفصل: الرأس {len(head_out.encode())} B ({n_keep} نقشًا) · الأرشيف {len(arch_txt.encode())} B ({len(move_idx)} مقطعًا) · الفهرس {len(man_txt.encode())} B")
    print(f"بصمات: أصل {sha0} · رأس {H(head_out.encode())} · أرشيف {H(arch_txt.encode())}")    # فحص ذاتي فوري: إعادة التقسيم
    t2 = state.read_text(encoding="utf-8")
    pre2, b2 = parse_blocks(t2)
    n2 = [i for i, (_, _, h) in enumerate(b2) if is_naqsh(h)]
    tot = len(n2) + len(move_idx)
    print(f"فحص ذاتي: الرأس {len(n2)} نقشًا + الأرشيف {len(move_idx)} = {tot} (الأصل {len(naq)} → {'مطابق ✓' if tot == len(naq) else 'غير مطابق ✗'})")
    return 0

def do_guard(arch: Path, man: Path):
    t = arch.read_text(encoding="utf-8")
    _, blocks = parse_blocks(t)
    naq_blk = [t[s:e].encode() for (s, e, h) in blocks if is_naqsh(h)]
    rows = [l.split("\t") for l in man.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    rows = [r for r in rows if len(r) >= 4]
    if len(naq_blk) < len(rows):
        print(f"انتهاك إلحاقية: مقاطع الأرشيف {len(naq_blk)} < المفهرسة {len(rows)} — أُزيل مقطع ✗", file=sys.stderr)
        return 1
    bad = [r[0] for r in rows if H(naq_blk[int(r[0]) - 1]) != r[1]]
    if bad:
        print(f"انتهاك إلحاقية: بصمات مقاطع مغايرة للمفهرس (أرقام {bad[:8]}) — أُعيد كتابة مقاطع قديمة ✗", file=sys.stderr)
        return 1
    print(f"حارس الإلحاقية: خضراء ✓ — كل المقاطع المفهرسة ({len(rows)}) حاضرة ببصماتها في موضعها، وزيادة ({len(naq_blk) - len(rows)}) إن وُجدت في الذيل فقط.")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="القناة/العمل/الحالة.md")
    ap.add_argument("--archive", default="القناة/العمل/أرشيف-النقوش-٢٠٢٦.md")
    ap.add_argument("--manifest", default="القناة/العمل/فهرس-أرشيف-النقوش-٢٠٢٦.tsv")
    ap.add_argument("--keep", type=int, default=30)
    ap.add_argument("--date", default="2026-09-30")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--guard", action="store_true")
    a = ap.parse_args()
    state, arch, man = Path(a.state), Path(a.archive), Path(a.manifest)
    if a.guard:
        return do_guard(arch, man)
    t = state.read_text(encoding="utf-8")
    if a.dry:
        b0 = t.encode()
        pre, blocks, naq, move_idx = plan(t, a.keep)
        kept, moved = split_bytes(t, move_idx, blocks, pre)
        print(f"الخطة: أصل {len(b0)} B · بصمة {H(b0)} · مقاطع {len(blocks)} · نقوش {len(naq)}")
        print(f"  → يُنقل: {len(move_idx)} نقشًا ({len(moved.encode())} B) · يبقى: {len(naq)-len(move_idx)} نقشًا · الرأس الناتج ≈ {len(kept.encode())+400} B (قبل سجل الهجرة)")
        print(f"  → الأرشيف المرتقب: {len(ARCH_HDR.format(date=a.date, pre_sha=H(b0), n_moved=len(move_idx), moved_b=len(moved.encode())).encode())+len(moved.encode())} B")
        print(f"  → غير نقش يبقى في الرأس: {sum(1 for (_,_,h) in blocks if not is_naqsh(h))} مقطعًا")
        return 0
    return do_apply(state, arch, man, a.keep, a.date)

if __name__ == "__main__":
    sys.exit(main())
