#!/usr/bin/env bash
# مسبار ب15 — لينتر القتلات السبعة: فشل متوقع على عينة R2 ثم نجاح بعد التنظيف + ٧ ضوابط سلبية.
set -uo pipefail
L="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/مرجع-لينتر-النصوص.py"
R2=/var/tmp/desk-archive/القناة/العمل/الدستور-٣٫٠-مسودة-R2-بعد-المراجعات-2026-09-29.md
REPO=/var/tmp/desk-archive
SB=/var/tmp/مسبر-ب15; rm -rf "$SB"; mkdir -p "$SB"; PASS=0; FAIL=0
ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }; no(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }
echo "════ مسبار ب١٥ — اللينتر ════"
echo "◆ ١) R2 الحقيقية — فشل متوقع (قبل التنظيف)"
out=$(python3 "$L" "$R2" --repo "$REPO"); rc=$?
echo "$out" | sed 's/^/    /'
echo "$out" | grep -q 'LX1' && echo "$out" | grep -qE 'LX1.*[1-9]' && ok "LX1 أطلق على R2 (وسم متداخل)" || no "LX1 لم يطلق"
echo "$out" | grep -qE 'LX6.*[1-9]' && ok "LX6 أطلق على R2 (تاريخ في النواة)" || no "LX6 لم يطلق"
[ $rc -eq 1 ] && ok "اللينتر رفض R2 (rc=1) — فشل متوقع قبل تنظيف ق" || no "اللينتر قبل R2 (rc=$rc)!"
echo "◆ ٢) عينة نظيفة — نجاح متوقع"
cat > "$SB/نظيف.md" <<'EOF'
# وثيقة نظيفة
<u>*١. حكم عام.</u>
٢. لا تاريخ هنا ولا شيفرة.
# ملحق أ
٣. الدليل: إحالة ق-٠٠٩.
EOF
mkdir -p "$SB/repo/بريد-القائد" "$SB/repo/vault"; touch "$SB/repo/بريد-القائد/ق-٠٠٩-موجود.md"
cp "$SB/نظيف.md" "$SB/repo/نظيف.md"
out=$(python3 "$L" "$SB/repo/نظيف.md" --repo "$SB/repo"); rc=$?
echo "$out" | sed 's/^/    /'
[ $rc -eq 0 ] && ok "العينة النظيفة مرّت (rc=0)" || no "العينة النظيفة رُفضت!"
echo "◆ ٣) الضوابط السلبية السبعة (لكل قتلة صورة تُطلقها ورمزها المعلن)"
mk(){ python3 - "$1" "$2" <<'PYX'
import sys, pathlib
name, body = sys.argv[1], sys.argv[2]
pathlib.Path(f"/var/tmp/مسبر-ب15/{name}.md").write_text(body, encoding="utf-8")
PYX
}
mk lx1 $'# ع\n<u>*١. مفتوح\n<u>*٢. متداخل</u>\n</u>\n# ملحق أ'
mk lx2 $'# ع\n٣. إحالة إلى ق-٠٧٧ غير موجود.\n# ملحق أ'
mk lx3 $'# ع\n## م٣\n## م٣\n# ملحق أ'
mk lx4 $'# ع\nREPEALED: ٢/١٤\n\nراجع ٢/١٤ في النص.\n# ملحق أ'
mk lx5 $'# ع\n١. يعمل على GitHub.\n# ملحق أ'
mk lx6 $'# ع\n٢. قرار المالك ٢٠٢٦-٠٩-٢٩.\n# ملحق أ'
mk lx7 $'# ع\n٤. على المكلَّف أن يقرأ، وعلى مكلف أن ينفذ.\n# ملحق أ'
for c in LX1 LX2 LX3 LX4 LX5 LX6 LX7; do
  f="$SB/$(echo $c | tr 'A-Z' 'a-z').md"
  out=$(python3 "$L" "$f" --repo "$SB/repo" --only "$c"); rc=$?
  [ $rc -eq 1 ] && echo "$out" | grep -q "\[$c\]" && ok "$c أطلق على ضابطه السلبي" || no "$c لم يطلق (rc=$rc)"
done
echo; echo "════ الحصيلة: نجح $PASS · فشل $FAIL ════"
[ $FAIL -eq 0 ] || exit 1
