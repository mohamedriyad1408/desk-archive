#!/usr/bin/env bash
# فحص يقظة سريع (ن-086/ب٨): حجم الرأس < 250KB + حارس إلحاقية الأرشيف أخضر + عدّ فعّال للنقوش.
# لا يكتب شيئًا. يُستدعى من جذر القناة:  bash scripts/فحص-الأرشيف.sh
set -euo pipefail
cd "$(dirname "$0")/.."
HEAD="القناة/العمل/الحالة.md"
ARCH="القناة/العمل/أرشيف-النقوش-٢٠٢٦.md"
MAN="القناة/العمل/فهرس-أرشيف-النقوش-٢٠٢٦.tsv"
sz=$(wc -c < "$HEAD" | tr -d ' ')
nh=$(grep -c '^## نقش' "$HEAD" || true)
if [ -f "$ARCH" ]; then
  na=$(grep -c '^## نقش' "$ARCH" || true)
  python3 -B scripts/فصل-الحالة.py --guard --archive "$ARCH" --manifest "$MAN"
else
  na=0
fi
echo "الرأس: ${sz} B (${nh} نقشًا) · الأرشيف: ${na} نقشًا · الفعّال: $((nh + na))"
if [ "$sz" -ge 250000 ]; then
  echo "تحذير: الرأس بلغ ${sz} B — نافذة إلحاق: مرّر أقدم النقوش إلى الأرشيف بالأداة (فصل-الحالة.py) وقيّد الهجرة." >&2
  exit 4
fi
echo "الفحص أخضر ✓ (الرأس دون 250KB)"
