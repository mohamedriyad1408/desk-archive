#!/usr/bin/env bash
# المراقب الحي للقناة — يُشغَّل داخل الدور النشط بعد كل ختم، لا يُشغَّل من المالك.
#
# السلوك:
#   - يفحص البريد كل WATCH_INTERVAL ثانية (الافتراضي ٣٠) بجلب عام بلا توكن.
#   - عند ظهور أي حجم جديد (لأن لا شيء يمر على القناة بلا قراءة الثلاثة) ينتهي بكود ٠:
#     افتح القناة، اقرأ كل جديد، تصرّف حسب بطاقتك، أو تحدَّ ما لَمحتَه من خطأ، أو أعد التسليح.
#   - الجلسة الواحدة WATCH_SESSION ثانية (الافتراضي ١٨٠٠ = ٣٠ دقيقة) ثم كود ١٠:
#     أَعِد تشغيل المراقب فورًا بلا خاتمة ولا تقرير.
#   - بعد WATCH_MAX_ARMS جلسات متتالية بلا حدث (الافتراضي ٣ = ٩٠ دقيقة) كود ١١:
#     إجراء السقف في الدستور (نقطة مراقبة مختومة، استفسار/حالة ضعف/سلسلة جديدة حسب المنتظَر).
#
# الأكوا: ٠ حدث جديد استيقظ · ١٠ أعد التسليح · ١١ السقف · غيره خطأ.
set -euo pipefail
cd "$(dirname "$0")/.."

ROLE="${1:-دور}"
INTERVAL="${WATCH_INTERVAL:-30}"
SESSION="${WATCH_SESSION:-1800}"
MAX_ARMS="${WATCH_MAX_ARMS:-3}"
STATE=".watch-state-$ROLE"
PIDFILE=".watch-pid-$ROLE"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

newest() {
  git ls-tree --name-only FETCH_HEAD vault/ 2>/dev/null \
    | sed -E 's#vault/v-([0-9]+)\.enc#\1#' | sort -n | tail -1
}

git fetch -q origin "$BRANCH" || true
base="$(newest)"; base="${base:-0}"

arm=1
[ -f "$STATE" ] && arm="$(cat "$STATE")"
if [ "$arm" -gt "$MAX_ARMS" ]; then
  rm -f "$STATE"
  echo "سقف المراقبة: $((arm-1)) جلسات متتالية بلا حدث — كود ١١: نفّذ إجراء السقف الدستوري." >&2
  exit 11
fi
echo "$arm" > "$STATE"
echo "تسليح $arm/$MAX_ARMS — $ROLE — أرصد الأحجام من $base كل ${INTERVAL}ث لمدة ${SESSION}ث (البطاقة الموجّهة توقظ، والكل يُقرأ)."

end=$((SECONDS+SESSION))
while [ "$SECONDS" -lt "$end" ]; do
  sleep "$INTERVAL"
  git fetch -q origin "$BRANCH" || true
  cur="$(newest)"; cur="${cur:-0}"
  if [ "$cur" -gt "$base" ]; then
    rm -f "$STATE" "$PIDFILE"
    trap - EXIT
    echo "حدث جديد: حجم $cur — كود ٠: شغّل فتح.sh واقرأ كل الجديد وتصرّف."
    exit 0
  fi
done
next=$((arm+1))
echo "$next" > "$STATE"
if [ "$next" -gt "$MAX_ARMS" ]; then
  echo "اكتملت $MAX_ARMS جلسات بلا حدث — إعادة التشغيل التالية تعطي كود ١١ فورًا: جهّز إجراء السقف." >&2
fi
echo "انتهت جلسة المراقب $arm — كود ١٠: أعد تشغيل المراقب فورًا بلا خاتمة." >&2
exit 10
