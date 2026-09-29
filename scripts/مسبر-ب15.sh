#!/usr/bin/env bash
# مسبار ب١٥ — لينتر النصوص: ١١ قبولًا (R2 الحقيقية + عينة نظيفة + ٧ ضوابط سلبية) — قابل للنقل (ن-083).
# الجذر من موضع السكربت أو --repo/$REPO · صفر مسار بيئة ثابت · بيئة الفحص من PROBE_SB/TMPDIR.
# عطل البنية التحتية = رمز خروج 70، ولا يُحتسب ضمن قتلات LX ولا ضمن نجاحها (fail-closed مسبب).
set -uo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${REPO:-$(cd "$D/.." && pwd)}"
R2NAME="${R2_NAME:-الدستور-٣٫٠-مسودة-R2-بعد-المراجعات-2026-09-29.md}"
R2FULL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) ROOT="$(cd "$2" 2>/dev/null && pwd || printf '%s' "$2")"; shift 2;;
    --r2) R2FULL="$2"; shift 2;;
    *) shift;;
  esac
done
L="$D/مرجع-لينتر-النصوص.py"
R2="${R2FULL:-$ROOT/القناة/العمل/$R2NAME}"
SB="${PROBE_SB:-${TMPDIR:-/tmp}}/مسبر-ب15"; rm -rf "$SB"; mkdir -p "$SB"
PASS=0; FAIL=0; INFRA_OK=1
ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }; no(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }
infra(){ echo "  ⛔ [عطل بنيوي — رمز ٧٠] $1" >&2; echo "     (لا يُحتسب ضمن قتلات LX ولا ضمن نجاحها — fail-closed مسبب)" >&2; exit 70; }
[ -f "$L" ] || infra "المرجع غير موجود بجوار السكربت: $L"
[ -d "$ROOT" ] || infra "جذر المستودع غير موجود: $ROOT"
[ -f "$R2" ] || infra "ملف R2 غير موجود: $R2 — مرّر --repo أو R2_NAME"
[ -d "$ROOT/القناة/بريد-القائد" ] || infra "بريد القائد غير موجود تحت $ROOT/القناة"

lint(){ # يفصل عطل البنية عن حكم اللينتر: أي Traceback = عطل بنيوي لا حكم
  local err="$SB/err.$$"; : > "$err"
  python3 "$L" "$@" 2>"$err"; local rc=$?
  if grep -q 'Traceback' "$err" 2>/dev/null; then sed 's/^/    /' "$err" >&2; infra "استثناء غير ملتقط في المرجع — عطل بنيوي لا حكم"; fi
  return $rc
}
echo "════ مسبار ب١٥ — اللينتر ════"
echo "    الجذر المقروء ذاتيًا: $ROOT"
echo "◆ ١) R2 الحقيقية — فشل متوقع (قبل تنظيف ق)"
out=$(lint "$R2" --repo "$ROOT"); rc=$?
echo "$out" | sed 's/^/    /'
l1=$(echo "$out" | grep -E '\[LX1\]' | grep -oE '[0-9]+ موضعًا' | head -1 | grep -oE '^[0-9]+')
l6=$(echo "$out" | grep -E '\[LX6\]' | grep -oE '[0-9]+ موضعًا' | head -1 | grep -oE '^[0-9]+')
[ "${l1:-0}" -gt 0 ] && ok "LX1 أطلق على R2 (وسم متداخل) — العدد المقيس: ${l1}" || no "LX1 لم يطلق"
[ "${l6:-0}" -gt 0 ] && ok "LX6 أطلق على R2 (تاريخ في النواة) — العدد المقيس: ${l6}" || no "LX6 لم يطلق"
[ $rc -eq 1 ] && ok "اللينتر رفض R2 (rc=1) — فشل متوقع حتى نص ق النظيف" || no "اللينتر قبل R2 (rc=$rc)!"
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
out=$(lint "$SB/repo/نظيف.md" --repo "$SB/repo"); rc=$?
echo "$out" | sed 's/^/    /'
[ $rc -eq 0 ] && ok "العينة النظيفة مرّت (rc=0)" || no "العينة النظيفة رُفضت!"
echo "◆ ٣) الضوابط السلبية السبعة (لكل قتلة صورة تُطلقها ورمزها المعلن)"
mk(){ python3 - "$1" "$2" "$SB" <<'PYX'
import sys, pathlib
name, body, sb = sys.argv[1], sys.argv[2], sys.argv[3]
pathlib.Path(f"{sb}/{name}.md").write_text(body, encoding="utf-8")
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
  f="$SB/$(printf '%s' "$c" | tr 'A-Z' 'a-z').md"
  out=$(lint "$f" --repo "$SB/repo" --only "$c"); rc=$?
  [ $rc -eq 1 ] && echo "$out" | grep -q "\[$c\]" && ok "$c أطلق على ضابطه السلبي" || no "$c لم يطلق (rc=$rc)"
done
echo; echo "════ الحصيلة: نجح $PASS · فشل $FAIL ════"
echo "◆ عطل بنيوي (منفصل — لا يُحتسب ضمن الـ١١): جذر غائب يجب أن يُفشل مغلقًا برمز ٧٠"
IERR="${SB}.infra.err"
bash "$0" --repo "$SB/لا-يوجد-هذا-الجذر" >/dev/null 2>"$IERR"; irc=$?
if [ $irc -eq 70 ] && grep -q 'عطل بنيوي' "$IERR"; then echo "  ✅ فشل مغلق برمز ٧٠ مع رسالة مسببة"; else echo "  ❌ العطل البنيوي لم يُرمز ٧٠ (rc=$irc)"; INFRA_OK=0; fi
[ $FAIL -eq 0 ] && [ $INFRA_OK -eq 1 ] || exit 1
