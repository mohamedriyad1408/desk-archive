#!/usr/bin/env bash
# العين الحية للقناة — تُشغَّل داخل الدور النشط، غالبًا عبر «نبض.sh سلّح/تابع».
#
# ترصد طبقتين:
#   ١) vault/ الأحجام المشفّرة: أي حجم جديد (لا شيء يمر بلا قراءة الثلاثة) ⇐ كود ٠.
#   ٢) نبض/ المسار العلني: قلوب الزملاء الدوّارة والنداءات والغياب.
#      - نبضة روتينية (استلمت/جاري/منتصف/عودة) تُبتلَع وتُدوَّن في لوحة محلية وتصفّر سقف الصمت.
#      - نبضة عائق ⇐ كود ١٣ · نداء موجَّه إليك ⇐ كود ١٣.
#      - غياب مكلَّف دورتين + سماح بلا نبضة (PULSE_MISS_CYCLES×PULSE_INTERVAL+PULSE_GRACE) ⇐ كود ١٢.
#      - اختفاء نبض زميل (تسليم/إيقاف) يُدوَّن فقط؛ اليقظة تأتي مع الحجم المختوم أو النداء.
#
# الجلسة WATCH_SESSION (١٨٠٠ث) ⇐ كود ١٠ أعد التسليح. ثلاث جلسات بلا أي حدث (لا حجم ولا نبض) ⇐ كود ١١.
#
# الأكوا: ٠ حجم جديد اقرأ الكل · ١٠ أعد التسليح (نبض.sh تابع) · ١١ سقف الصمت ·
#         ١٢ غياب مكلَّف (م١ يُصدر نداءً ويصعّد للمالك خلال ١٠د) · ١٣ عائق/نداء.
#
# حدود السلاح (ق-٠٠٤/ق-٠٠٥): التسليح يعيش ما عاش الدور جالسًا؛ عملية خلف دور منتهٍ
# رصد آلي بلا حكم لا تُحتسب حياة. أول فعل بعد يقظة: قِس سلاحك بناتج أمر وطابع زمني
# (kill -0 + ps -o etime)؛ ملف سلاح يتيم دليل موت. المدد من طوابع git لا من ساعة الجلسات.
set -euo pipefail
cd "$(dirname "$0")/.."

ROLE="${1:-دور}"
INTERVAL="${WATCH_INTERVAL:-30}"
SESSION="${WATCH_SESSION:-1800}"
MAX_ARMS="${WATCH_MAX_ARMS:-3}"
PULSE_INTERVAL="${PULSE_INTERVAL:-180}"
PULSE_GRACE="${PULSE_GRACE:-30}"
PULSE_MISS_CYCLES="${PULSE_MISS_CYCLES:-2}"
PULSE_ESCALATE="${PULSE_ESCALATE:-600}"
PD="نبض"
BOARD_FILE="$PD/البطائق-المفتوحة.md"
STATE=".watch-state-$ROLE"
PIDFILE=".watch-pid-$ROLE"
PSTATE=".watch-pulse-$ROLE"
BOARD_LOCAL=".watch-board-$ROLE"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
ROLES_ALL=(ن م١ م٢)

echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

newest_vol() {
  git ls-tree --name-only FETCH_HEAD vault/ 2>/dev/null \
    | sed -E 's#vault/v-([0-9]+)\.enc#\1#' | sort -n | tail -1
}
role_pfx() { case "$1" in ن) echo ن;; م١) echo م١;; م٢) echo م٢;; *) echo "";; esac; }
ls_pulse() { git -c core.quotepath=false ls-tree --name-only FETCH_HEAD "$PD/" 2>/dev/null; }

pulse_latest_file() { # $1=بادئة
  ls_pulse \
    | sed -nE "s#.*($PD/$1-[0-9]{3}\.md)#\1#p" | sort | tail -1
}
pulse_latest_ct() { # $1=مسار ملف
  [ -n "$1" ] && git log -1 --format=%ct FETCH_HEAD -- "$1" 2>/dev/null || echo 0
}

git fetch -q origin "$BRANCH" || true
base="$(newest_vol)"; base="${base:-0}"

# baseline النبض عند التسليح (قديم لا يوقظ).
: > "$PSTATE"
for r in "${ROLES_ALL[@]}"; do
  pfx="$(role_pfx "$r")"; f="$(pulse_latest_file "$pfx")"; ct="$(pulse_latest_ct "$f")"
  echo "$pfx|$f|$ct" >> "$PSTATE"
done
ls_pulse | grep -F '/نداء-' | sort >> "$PSTATE" || true

# نداء معلق موجه إليّ لحظة التسليح (دور أُعيد إيقاظه بعد نداء) يُعامل كحدث فوري.
while IFS= read -r pre_call; do
  [ -z "$pre_call" ] && continue
  if git show "FETCH_HEAD:$pre_call" 2>/dev/null | grep -q "إلى: $ROLE"; then
    rm -f "$STATE" "$PSTATE" "$PIDFILE"; trap - EXIT
    echo "نداء معلق موجّه إليك منذ قبل تسليحك: $pre_call — كود ١٣: نفّذ نبض.sh تابع $ROLE فيُطهَّر بأول نبضة."
    exit 13
  fi
done < <(ls_pulse | grep -F '/نداء-' || true)

arm=1
[ -f "$STATE" ] && arm="$(cat "$STATE")"
if [ "$arm" -gt "$MAX_ARMS" ]; then
  rm -f "$STATE"
  echo "سقف المراقبة: $((arm-1)) جلسات متتالية بلا حدث — كود ١١: نفّذ إجراء السقف الدستوري." >&2
  exit 11
fi
echo "$arm" > "$STATE"
echo "تسليح $arm/$MAX_ARMS — $ROLE — أحجام من $base · عين على النبض كل ${INTERVAL}ث (دورة القلب ${PULSE_INTERVAL}ث، حد الغياب $((PULSE_MISS_CYCLES*PULSE_INTERVAL+PULSE_GRACE))ث)."

seen_get() { # $1=pfx ⇒ سطر baseline
  grep -m1 "^$1|" "$PSTATE" 2>/dev/null || echo "$1||0"
}
seen_set() { # $1=pfx $2=file $3=ct
  grep -v "^$1|" "$PSTATE" > "$PSTATE.tmp" || true; echo "$1|$2|$3" >> "$PSTATE.tmp"; mv "$PSTATE.tmp" "$PSTATE"
}

exit_event() { # $1=كود $2=رسالة
  rm -f "$STATE" "$PSTATE" "$PIDFILE"; trap - EXIT
  echo "$2"
  exit "$1"
}

end=$((SECONDS+SESSION))
while [ "$SECONDS" -lt "$end" ]; do
  sleep "$INTERVAL"
  git fetch -q origin "$BRANCH" || true

  # (١) الأحجام أولوية.
  cur="$(newest_vol)"; cur="${cur:-0}"
  if [ "$cur" -gt "$base" ]; then
    exit_event 0 "حدث جديد: حجم $cur — كود ٠: شغّل فتح.sh واقرأ كل الجديد وتصرّف."
  fi

  now="$(date -u +%s)"
  board_now="$(git show "FETCH_HEAD:$BOARD_FILE" 2>/dev/null || true)"
  board_lines=()
  while IFS=$'\t' read -r card r2 issued mins; do
    [ "${card:0:1}" = "#" ] && continue
    [ -z "${card:-}" ] && continue
    board_lines+=("$card"$'\t'"$r2"$'\t'"$issued"$'\t'"$mins")
  done <<< "$board_now"

  # (٢) نبض الأدوار.
  for r2 in "${ROLES_ALL[@]}"; do
    pfx="$(role_pfx "$r2")"
    f_new="$(pulse_latest_file "$pfx")"; ct_new="$(pulse_latest_ct "$f_new")"
    old="$(seen_get "$pfx")"; f_old="${old#*|}"; f_old="${f_old%|*}"; ct_old="${old##*|}"
    [ -z "$ct_new" ] && ct_new=0

    if [ "$ct_new" != "$ct_old" ] && [ "$ct_new" -gt 0 ]; then
      seen_set "$pfx" "$f_new" "$ct_new"
      echo 1 > "$STATE"  # أي نبضة = القناة حية، تُصفّر سقف الصمت.
      if [ "$r2" != "$ROLE" ]; then
        body="$(git show "FETCH_HEAD:$f_new" 2>/dev/null || true)"
        if grep -q "الحالة: عائق" <<< "$body"; then
          exit_event 13 "نبضة عائق من $r2 ($f_new) — كود ١٣: افتح واقرأ عائقه في القناة (النبضة العلنية بلا تفاصيل)."
        fi
      fi
    fi
  done

  # (٣) نداء موجَّه إليّ.
  while IFS= read -r call; do
    [ -z "$call" ] && continue
    grep -qxF "$call" "$PSTATE" && continue
    if git show "FETCH_HEAD:$call" 2>/dev/null | grep -q "إلى: $ROLE"; then
      echo "$call" >> "$PSTATE"
      exit_event 13 "نداء استفسار موجّه إليك: $call — كود ١٣: إن كنت حيًّا نفّذ: نبض.sh تابع $ROLE (أو سلّح)، فيُطهَّر النداء بأول نبضة."
    fi
  done < <(ls_pulse | grep -F '/نداء-' || true)

  # (٤) كشف الغياب من المناوبة.
  for line in "${board_lines[@]:-}"; do
    [ -z "$line" ] && continue
    IFS=$'\t' read -r card r2 issued mins <<< "$line"
    [ "$r2" = "$ROLE" ] && continue
    pfx2="$(role_pfx "$r2")"; f2="$(pulse_latest_file "$pfx2")"; ct2="$(pulse_latest_ct "$f2")"
    last="$issued"; [ "${ct2:-0}" -gt 0 ] && last="$ct2"
    age=$(( now - last ))
    limit=$(( PULSE_MISS_CYCLES*PULSE_INTERVAL + PULSE_GRACE ))
    if [ "$age" -gt "$limit" ]; then
      esc=".watch-12-$r2-$card"
      fire=1
      if [ -f "$esc" ]; then [ $(( now - $(cat "$esc") )) -lt "$PULSE_ESCALATE" ] && fire=0; fi
      if [ "$fire" = 1 ]; then
        echo "$now" > "$esc"
        if [ "$ROLE" = "م١" ]; then
          exit_event 12 "غياب: $r2 على بطاقة $card — آخر إشارة قبل ${age}ث (حد ${limit}ث) — كود ١٢: نفّذ «نبض.sh نداء $r2 $card»، وإن لم يعد في دورة واحدة أوقفه وأعد التسليح لبديل وردّ على المالك خلال ١٠ دقائق بصيغة التصعيد."
        else
          exit_event 12 "غياب مرصود: $r2 على بطاقة $card منذ ${age}ث — كود ١٢ (النداء والتصعيد من م١ وحده): سجّل مشاهدتك في أول مخرَج لك وأعد تسليح عينك."
        fi
      fi
    fi
  done

  # (٥) لوحة محلية للاطمئنان (لا توقظ).
  {
    echo "لوحة النبض — $ROLE — $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    for line in "${board_lines[@]:-}"; do
      [ -z "$line" ] && continue
      IFS=$'\t' read -r card r2 issued mins <<< "$line"
      pfx2="$(role_pfx "$r2")"; f2="$(pulse_latest_file "$pfx2")"; ct2="$(pulse_latest_ct "$f2")"
      last="$issued"; [ "${ct2:-0}" -gt 0 ] && last="$ct2"
      age=$(( now - last ))
      st="—"; [ -n "$f2" ] && st="$(git show "FETCH_HEAD:$f2" 2>/dev/null | sed -n 's/^- الحالة: //p')"
      rem="—"; [ -n "${mins:-}" ] && rem=$(( issued + mins*60 - now ))
      echo "$r2 · $card · آخر نبضة قبل ${age}ث · $st · متبقٍ ${rem}ث"
    done
    [ ${#board_lines[@]} -eq 0 ] && echo "لا بطائق مفتوحة."
  } > "$BOARD_LOCAL"
done

next=$((arm+1))
echo "$next" > "$STATE"
if [ "$next" -gt "$MAX_ARMS" ]; then
  echo "اكتملت $MAX_ARMS جلسات بلا حدث — التشغيلة التالية كود ١١ فورًا: جهّز إجراء السقف." >&2
fi
echo "انتهت جلسة العين $arm — كود ١٠: أعد التسليح فورًا (نبض.sh تابع $ROLE إن كان لك قلب، أو انتظر.sh $ROLE)." >&2
exit 10
