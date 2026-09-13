#!/usr/bin/env bash
# القلب النابض للقناة — مسار علني منفصل عن مسار العمل المشفّر.
# دستور ٢٫٤ / توجيه ٠٠٧: نبضات آنية صغيرة (حال وأرقام ومواعيد، بلا أي مضمون)،
# ملف دوّار لكل دور يُمحى عند كل نبضة، وكشف غياب ميكانيكي بعد دورتين صامتتين.
#
# الأوامر:
#   نبض.sh بطاقة <دور> <رقم-البطاقة> <مدة-دقيقة>   لم١: يفتح بطاقة في المناوبة العلنية
#   نبض.sh سلّح  <دور> <رقم-البطاقة> <مدة-دقيقة>   نبضة استلام + قلب خلفي + يجلس مكان العين
#   نبض.sh تابع  <دور>                              إعادة تسليح العين (والقلب إن مات)
#   نبض.sh جاري  <دور>                              نبضة فورية: جاري العمل (تزيل علم العائق)
#   نبض.sh عائق <دور>                              نبضة عائق فورية (التفاصيل في الحجم المختوم)
#   نبض.sh سلمت <دور>                              إيقاف القلب + تطهير الملف + شطب البطاقة
#   نبض.sh أوقف <دور>                              لم١: تطهير للتبديل/الإلغاء (يعمل وإن كان القلب ميتًا)
#   نبض.sh نداء <إلى-دور> <رقم-البطاقة>            لم١: نداء استفسار علني يُطهَّر بأول نبضة استجابة
#   نبض.sh قلب  <دور> <رقم-البطاقة> <مدة-دقيقة>    وضع داخلي تطلقه سلّح (لا يُستدعى يدويًا)
#
# متغيرات البيئة: PULSE_INTERVAL (١٨٠ث) · PULSE_GRACE (٣٠ث) · PULSE_MISS_CYCLES (٢)
#                CHANNEL_ROLE · CHANNEL_TOKEN (توكن الدفع إن لم يكن في عنوان origin)
set -euo pipefail
cd "$(dirname "$0")/.."

PD="نبض"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
INTERVAL_S="${PULSE_INTERVAL:-180}"
GRACE_S="${PULSE_GRACE:-30}"
MISS_CYCLES="${PULSE_MISS_CYCLES:-2}"
JITTER_S="${PULSE_JITTER:-20}"   # اهتزاز ابتدائي فقط يمنع تزامن قلوب انطلقت معًا؛ الدورة ثابتة بعدها.
BOARD="$PD/البطائق-المفتوحة.md"
LOCK=".pulse-lock"
PUBLIC_URL="${CHANNEL_REPO_URL:-https://github.com/mohamedriyad1408/desk-archive.git}"

# حالات النبض المعدودة وحدها — لا نص حر علنيًا (منع تسريب المضمون في المسار العلني).
S_RECV="تم الاستلام"
S_WORK="جاري العمل"
S_BLOCK="عائق — التفاصيل في القناة"
S_MID="المنتصف"
S_BACK="عدت بعد انقطاع — جاري العمل"
S_LATE="متأخر عن الموعد"

role_prefix() { case "$1" in ن) echo "ن";; م١) echo "م١";; م٢) echo "م٢";; *) echo "خطأ: دور غير معروف: $1 (ن|م١|م٢)" >&2; exit 2;; esac; }
ls_pulse() { git -c core.quotepath=false ls-tree --name-only FETCH_HEAD "$PD/" 2>/dev/null; }

heal() { # شفاء ق-٠٠٥ مختصر: origin والهوية والأذونات.
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "$PUBLIC_URL"
  git config user.email >/dev/null 2>&1 || {
    if [ -n "${CHANNEL_ROLE:-}" ]; then git config user.name "قناة-${CHANNEL_ROLE}"; git config user.email "${CHANNEL_ROLE}@channel.local";
    else git config user.name "desk-archive channel"; git config user.email "channel@desk-archive.local"; fi
  }
  git config core.fileMode false 2>/dev/null || true
}

# دفع باصطحاب التوكن من متغير البيئة عند الحاجة، ثم إعادة العنوان العام (التوكن لا يُكتب في ملف).
auth_push() {
  local url; url="$(git remote get-url origin)"
  if [[ "$url" == *"@"* ]]; then git push "$@"; return; fi
  if [ -n "${CHANNEL_TOKEN:-}" ]; then
    git remote set-url origin "https://x-access-token:${CHANNEL_TOKEN}@github.com/mohamedriyad1408/desk-archive.git"
    if git push "$@"; then git remote set-url origin "$url"; return 0; fi
    git remote set-url origin "$url"; return 1
  fi
  git push "$@"
}

sync_pulse_tree() { # نبض/ = قمة البعيد تمامًا (يمس نبض وحدها؛ vault والقناة لا يتأثران).
  git fetch -q origin "$BRANCH" || return 1
  git reset -q --mixed FETCH_HEAD
  mkdir -p "$PD"
  git checkout -q FETCH_HEAD -- "$PD" 2>/dev/null || true
  git clean -fdq "$PD"
}

with_lock() { # قفل محلي بين القلب والأوامر اليدوية في نفس النسخة. استدعه دائمًا داخل ( … ) ليُفتح.
  command -v flock >/dev/null 2>&1 || { echo "flock مطلوب لتشغيل النبض." >&2; exit 2; }
  exec 200>"$LOCK"
  if ! flock -w 30 200; then echo "تعذر قفل النبض خلال ٣٠ث (قلب عالق؟)؛ أعد المحاولة." >&2; exit 1; fi
}

pulse_commit() { # $1=رسالة الالتزام. التعديلات في نبض/ منجزة قبل النداء. إعادة بـrebase بلا مساس.
  local msg="$1" i
  # دفاع: مجلد نبض بروتوكولي حصرًا — لا يُلتزم غير ملفات .md المعروفة البنية.
  find "$PD" -type f ! -name '*.md' -print -exec rm -f {} \; >/dev/null 2>&1 || true
  git add -A -- "$PD"
  if git diff --cached --quiet; then return 0; fi
  git commit -q -m "$msg"
  for i in 1 2 3 4 5 6; do
    if auth_push -q origin HEAD; then return 0; fi
    echo "دفعة النبض تعارضت؛ إعادة قاعدة ومحاولة $i." >&2
    git fetch -q origin "$BRANCH" || true
    if git rebase -q FETCH_HEAD 2>/dev/null; then
      auth_push -q origin HEAD && return 0
    fi
    git rebase --abort 2>/dev/null || true
    sleep 1
  done
  echo "تعذر دفع نبضة بعد ٤ محاولات (إعادة العملية idempotent)." >&2
  return 1
}

ensure_dir() { mkdir -p "$PD"; [ -f "$BOARD" ] || cat > "$BOARD" <<'EOF'
# المناوبة — بطائق النبض المفتوحة
# علني بلا مضمون: أرقام وحالات ومواعيد فقط. التفاصيل في القناة المشفّرة.
# الصيغة (حقول بتبويب): رقم-البطاقة <TAB> الدور <TAB> لحظة-الإصدار(epoch UTC) <TAB> المدة(دقيقة)
# يفتحها م١: نبض.sh بطاقة <دور> <رقم> <مدة> · وتُشطب تلقائيًا بـ: نبض.sh سلمت/أوقف <دور>
EOF
}

next_seq() { # $1=بادئة الدور. أعلى رقم مدفوع + ١.
  local pfx="$1" n
  n="$(ls_pulse | sed -nE "s#.*${PD}/${pfx}-([0-9]{3})\.md#\1#p" | sort -n | tail -1)"
  echo $((10#${n:-0} + 1))
}

latest_file() { local pfx="$1"
  ls_pulse | sed -nE "s#.*(${PD}/${pfx}-[0-9]{3}\.md)#\1#p" | sort | tail -1
}

board_has_card() { grep -Pq "^$2\t$1\t" "$BOARD" 2>/dev/null; }

board_add() { # $1=دور $2=بطاقة $3=مدة دقيقة
  ensure_dir
  board_has_card "$1" "$2" && return 0
  printf '%s\t%s\t%s\t%s\n' "$2" "$1" "$(date -u +%s)" "$3" >> "$BOARD"
}

board_remove_role() { # يشطب كل بطائق الدور (التسليم/الإيقاف).
  [ -f "$BOARD" ] || return 0
  grep -vP "\t$1\t[0-9]+\t[0-9]+\$" "$BOARD" > "$BOARD.tmp" || true
  mv "$BOARD.tmp" "$BOARD"
}

card_info() { grep -P "\t$1\t[0-9]+\t[0-9]+\$" "$BOARD" 2>/dev/null | tail -1 | cut -f3,4; }

# يحذف ملف نبض الدور القديم ونداءاته المعلّقة، ويكتب الجديد (التزام واحد).
write_pulse() { # $1=دور $2=الحالة
  local pfx seq nn old call f remaining now issued mins mid late state="$2"
  pfx="$(role_prefix "$1")"
  for old in "$PD/$pfx"-*.md; do [ -e "$old" ] && rm -f "$old"; done
  for call in "$PD"/نداء-*.md; do
    [ -e "$call" ] || continue
    grep -q "إلى: $1" "$call" 2>/dev/null && rm -f "$call"
  done
  seq="$(next_seq "$pfx")"; nn="$(printf '%03d' "$seq")"; f="$PD/$pfx-$nn.md"
  now="$(date -u +%s)"; remaining="—"
  if [ -f "$BOARD" ]; then
    read -r issued mins <<< "$(card_info "$1" || true)"
    if [ -n "${issued:-}" ] && [ -n "${mins:-}" ]; then
      remaining=$(( issued + mins*60 - now ))
      if [ "$remaining" -lt 0 ]; then
        late=$(( (-remaining + 59)/60 ))
        state="$S_LATE ب${late} دقيقة"
      fi
      mid=$(( issued + mins*60/2 ))
      [ "$now" -ge "$mid" ] && [ ! -f ".pulse-mid-$1" ] && { touch ".pulse-mid-$1"; state="$S_MID · $state"; }
    fi
  fi
  {
    echo "# نبضة $1 — $nn"
    echo "- الحالة: $state"
    echo "- الطابع: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "- المتبقي على التسليم: $remaining ث"
    echo "- دورة القلب: ${INTERVAL_S}ث؛ صمت دورتين + ${GRACE_S}ث = غياب"
  } > "$f"
  echo "$f"
}

heart_alive() { local p="$1"; [ -f "$p" ] && kill -0 "$(cat "$p")" 2>/dev/null; }

# إيقاف قاطع للقلب: TERM مع مهلة تأكيد ثم KILL؛ لا تطهير قبل تأكد الموت وإلا عاد فأنشأ نبضة.
stop_heart() {
  local pidf="$1" pid i
  if [ -f "$pidf" ]; then
    pid="$(cat "$pidf" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
      for i in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
      if kill -0 "$pid" 2>/dev/null; then kill -9 "$pid" 2>/dev/null || true; sleep 0.5; fi
    fi
  fi
  rm -f "$pidf"
}

# ---------------- الأوامر ----------------
cmd="${1:-}"; shift || true

heal
case "$cmd" in
  بطاقة)
    role="${1:?}"; card="${2:?}"; mins="${3:?}"
    role_prefix "$role" >/dev/null
    ( with_lock; sync_pulse_tree; ensure_dir
      board_add "$role" "$card" "$mins"
      pulse_commit "pulse: بطاقة $card لـ$role" ) && echo "فُتحت البطاقة $card ($role، $mins دقيقة) في المناوبة." ;;

  سلّح)
    role="${1:?}"; card="${2:?}"; mins="${3:?}"
    role_prefix "$role" >/dev/null
    pidf=".pulse-pid-$role"
    if heart_alive "$pidf"; then echo "قلب $role حيٌّ أصلًا (pid $(cat "$pidf"))؛ استخدم: تابع $role." >&2; exit 1; fi
    ( with_lock; sync_pulse_tree; ensure_dir
      board_add "$role" "$card" "$mins"
      write_pulse "$role" "$S_RECV (بطاقة $card، المدة $mins دقيقة)" >/dev/null
      pulse_commit "pulse: $role استلم $card" )
    rm -f ".pulse-mid-$role" ".pulse-back-$role"
    # الإطلاق خارج مقطع القفل وإغلاق واصفيه حتى لا يرث الابن حيازة قفل (علوق أبدي).
    nohup bash scripts/نبض.sh قلب "$role" "$card" "$mins" 200>&- 9>&- >> ".pulse-heart-$role.log" 2>&1 &
    echo "$!" > "$pidf"; sleep 1
    echo "قلب $role ينبض كل ${INTERVAL_S}ث؛ تجلس العين الآن (الأكوا: ٠ حجم · ١٢ غياب · ١٣ عائق/نداء/تسليم · ١٠ أعدها بـ: نبض.sh تابع $role)."
    exec bash scripts/انتظر.sh "$role" ;;

  قلب)
    role="${1:?}"; card="${2:?}"; mins="${3:?}"
    pidf=".pulse-pid-$role"; echo $$ > "$pidf"
    trap 'rm -f "$pidf"; exit 0' TERM INT
    echo "قلب $role بدأ (pid $$)، دورة ${INTERVAL_S}ث."
    beat=0
    while true; do
      if [ "$beat" = 0 ]; then sleep $((INTERVAL_S + RANDOM % (JITTER_S+1))); beat=1; else sleep "$INTERVAL_S"; fi
      flag="$S_WORK"; [ -f ".pulse-flag-$role" ] && flag="$S_BLOCK"
      # المقطع الحرج كله في subshell ليُفتح القفل بين الدورات فلا تُحجَب الأوامر اليدوية.
      ( with_lock
        sync_pulse_tree
        pfx="$(role_prefix "$role")"; old="$(latest_file "$pfx")"; state="$flag"
        if [ -n "$old" ]; then
          ct="$(git log -1 --format=%ct FETCH_HEAD -- "$old" 2>/dev/null || echo 0)"
          age=$(( $(date -u +%s) - ct ))
          if [ "$age" -gt $(( MISS_CYCLES*INTERVAL_S + GRACE_S )) ] && [ ! -f ".pulse-back-$role" ]; then
            touch ".pulse-back-$role"; state="$S_BACK"
          fi
        fi
        write_pulse "$role" "$state" >/dev/null
        pulse_commit "pulse: $role نبض" || true
      ) || true
    done ;;

  تابع)
    role="${1:?}"; role_prefix "$role" >/dev/null
    pidf=".pulse-pid-$role"
    if ! heart_alive "$pidf"; then
      rm -f "$pidf"
      resume=".pulse-resume-$role"
      ( with_lock; sync_pulse_tree; ensure_dir
        line="$(grep -P "\t$role\t[0-9]+\t[0-9]+\$" "$BOARD" 2>/dev/null | tail -1)"
        [ -n "$line" ] || { echo "لا بطاقة مفتوحة لـ$role على البعيد؛ لا قلب يُستأنف. سلّح ببطاقة جديدة." >&2; exit 1; }
        printf '%s' "$line" > "$resume" )
      line="$(cat "$resume")"; card="$(printf '%s' "$line" | cut -f1)"; mins="$(printf '%s' "$line" | cut -f4)"
      rm -f "$resume" ".pulse-back-$role"
      # الإطلاق بعد إغلاق القفل ومع منع توريث واصفيه (وإلا يرث القلب الحجز فيعلّ الجميع).
      nohup bash scripts/نبض.sh قلب "$role" "$card" "$mins" 200>&- 9>&- >> ".pulse-heart-$role.log" 2>&1 &
      echo "$!" > "$pidf"; sleep 1
      echo "أُعيد إطلاق قلب $role بعد انقطاع (بطاقة $card)."
    fi
    echo "العين تتابع لـ$role …"
    exec bash scripts/انتظر.sh "$role" ;;

  جاري|عائق)
    role="${1:?}"; role_prefix "$role" >/dev/null
    ( with_lock; sync_pulse_tree; ensure_dir
      if [ "$cmd" = عائق ]; then
        touch ".pulse-flag-$role"; write_pulse "$role" "$S_BLOCK" >/dev/null
        pulse_commit "pulse: $role عائق" && echo "نبضة عائق دُفعت؛ انقش العائق تفصيلًا في الحالة واختم (المسار العلني بلا مضمون)."
      else
        rm -f ".pulse-flag-$role"; write_pulse "$role" "$S_WORK" >/dev/null
        pulse_commit "pulse: $role جاري" && echo "نبضة جاري فورية دُفعت."
      fi ) ;;

  سلمت|أوقف)
    role="${1:?}"; role_prefix "$role" >/dev/null
    pfx="$(role_prefix "$role")"; pidf=".pulse-pid-$role"
    stop_heart "$pidf"
    rm -f ".pulse-flag-$role" ".pulse-mid-$role" ".pulse-back-$role" ".pulse-heart-$role.log" ".pulse-resume-$role"
    kind="$([ "$cmd" = سلمت ] && echo سلمت || echo أوقف-للتبديل)"
    ( with_lock; sync_pulse_tree; ensure_dir
      for old in "$PD/$pfx"-*.md; do [ -e "$old" ] && rm -f "$old"; done
      for call in "$PD"/نداء-*.md; do [ -e "$call" ] || continue; grep -q "إلى: $role" "$call" 2>/dev/null && rm -f "$call"; done
      board_remove_role "$role"
      pulse_commit "pulse: $role $kind — تطهير" )
    echo "تطهير $role: القلب أوقف وملف النبض والنداءات والبطاقة شُطبت. أوقف الآن عينك (عملية انتظر.sh، حامل .watch-pid-$role) قبل إقرار الخروج." ;;

  نداء)
    role="${1:?}"; card="${2:?}"; role_prefix "$role" >/dev/null
    ( with_lock; sync_pulse_tree; ensure_dir
      n="$(ls_pulse | sed -nE 's#.*نداء-([0-9]{3})-.*#\1#p' | sort -n | tail -1)"
      nn="$(printf '%03d' $((10#${n:-0} + 1)))"; f="$PD/نداء-$nn-إلى-$role.md"
      {
        echo "# نداء استفسار $nn — إلى: $role"
        echo "- البطاقة: $card"
        echo "- من: المستشار الأول"
        echo "- الطابع: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        echo "- السبب: دورتان بلا نبضة (القلب غائب أو البيئة أُعيد تجهيزها)."
        echo "- إن كنت حيًّا: نبض.sh تابع $role (أو سلّح إن بدأت للتو)؛ أول نبضة تُطهّر هذا النداء."
      } > "$f"
      pulse_commit "pulse: نداء $nn إلى $role" ) && echo "نداء إلى $role دُفع." ;;

  *)
    echo "الاستخدام: نبض.sh {بطاقة|سلّح|تابع|جاري|عائق|سلمت|أوقف|نداء} … (راجع ترويسة السكربت)." >&2; exit 2 ;;
esac
