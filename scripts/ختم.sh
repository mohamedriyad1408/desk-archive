#!/usr/bin/env bash
# يلتقط مجلد القناة كاملًا في حجم مشفّر جديد، يفحص، ثم يلتزم ويدفع.
# الحراس قبل الإنشاء:
#   - تحرك البعيد: استدراك داخلي (مزامنة ثلاثية بملف-ملف) ثم يكمل الختم (ق-٠٠٧/ب٢).
#   - نقص الملفات عن أحدث حجم: رفض برمز 4؛ الحذف الموثق فقط بـ ALLOW_DELETE=1.
#   - عودة ملف حُذف توثيقيًا: رفض برمز 5؛ إعادته عمدًا فقط بـ ALLOW_RESTORE=1.
#   - دفن محتوى قائم (عناوين أقسام في أحدث حجم تختفي محليًا): رفض برمز 6؛
#     الدفن الموثق فقط بـ ALLOW_BURY=1 ويُسجَّل في أداة/مدفون-موثق.md (ق-٠٠٧/ج).
#   - رقم الحجم يُقفل على البعيد: يُحسب من الشجرتين معًا، ويُعاد ترقيمه إن احتُجز
#     أثناء السباق، وفحص ازدواج الرقم بمحتوى مغاير داخل فحص.sh قبل كل دفع (ق-٠٠٧/أ).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${MIFTAH:-}" ]; then
  read -rsp 'مفتاح الفك: ' MIFTAH
  echo
  export MIFTAH
fi

if [ ! -d القناة ]; then
  echo 'مجلد القناة غير موجود؛ شغّل فتح.sh أولًا.' >&2
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# ق-٠٠٥: شفاء ذاتي بعد إعادة التجهيز (مطابق لفتح.sh).
CHANNEL_REPO_URL="${CHANNEL_REPO_URL:-https://github.com/mohamedriyad1408/desk-archive.git}"
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$CHANNEL_REPO_URL"
  echo "شفاء: أُعيد ضبط remote origin محليًا ($CHANNEL_REPO_URL)."
fi
if ! git config user.email >/dev/null 2>&1; then
  if [ -n "${CHANNEL_ROLE:-}" ]; then
    git config user.name "قناة-${CHANNEL_ROLE}"; git config user.email "${CHANNEL_ROLE}@channel.local"
  else
    git config user.name "desk-archive channel"; git config user.email "channel@desk-archive.local"
  fi
  echo "شفاء: ضُبطت هوية الالتزام المحلية (عيّن CHANNEL_ROLE=ن|م٢|م١ لتمييز دورك)."
fi
chmod +x scripts/*.sh 2>/dev/null || true
git config core.fileMode false 2>/dev/null || true

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

if ! git fetch -q origin "$BRANCH"; then
  echo 'تعذر جلب البعيد؛ لا ختم بلا معرفة تحركه (امنع الختم الأعمى).' >&2
  exit 2
fi

norm() { sed -E 's#^\./##' | sed '/^$/d' | sort; }
extract_volume() { tar -xz -C "$1" 2>/dev/null; }

latest_by_time() { # أحدث حجم بالزمن (ق-٠٠٧/ب: الرقم ليس زمنًا)؛ التعادل للأعلى رقمًا
  local f ct best=0 best_f=""
  while IFS= read -r f; do
    ct="$(git log -1 --format=%ct -- "$f" 2>/dev/null || echo 0)"
    if [ "${ct:-0}" -ge "$best" ] && [ "${ct:-0}" -gt 0 ]; then best="$ct"; best_f="$f"; fi
  done < <(ls -1 vault/v-*.enc 2>/dev/null | sort)
  echo "$best_f"
}
tree_max_number() { # أعلى رقم حجم على شجرة معطاة
  git -c core.quotepath=false ls-tree --name-only "${1:-FETCH_HEAD}" -- vault/ 2>/dev/null \
    | sed -nE 's#^vault/v-([0-9]+)\.enc$#\1#p' | sort -n | tail -1
}
local_max_number() {
  ls -1 vault/v-*.enc 2>/dev/null | sed -nE 's#.*v-([0-9]+)\.enc$#\1#p' | sort -n | tail -1
}
next_free_number() { # أعلى المحلي والبعيد معًا + ١ (ق-٠٠٧/أ)
  local lm rm_ lv rv
  lm="$(local_max_number)"; rm_="$(tree_max_number FETCH_HEAD)"
  lv=$((10#${lm:-0})); rv=$((10#${rm_:-0}))
  [ "$lv" -ge "$rv" ] && echo $((lv+1)) || echo $((rv+1))
}

# ─── الاستدراك الداخلي عند تحرك البعيد (ق-٠٠٧/ب٢: لا يُترك للوكيل) ───
# مزامنة ثلاثية بملف-ملف: أساس = آخر حجم قبل التحرك · منا = مجلد القناة · عنهم = أحدث حجم بعده.
# ما لم أمسه يأخذ نسخة الأقران · ما لم يمسوه يبقى لي · ما المسناه معًا: نسختي (وحارس
# الدفن أدناه يرفض إن كانت نسختي تُسقط عناوين أقسامهم).
if [ "$(git rev-list --count HEAD..FETCH_HEAD 2>/dev/null || echo 0)" -gt 0 ]; then
  echo 'البعيد تحرك؛ أستدرك داخليًا (مزامنة ثلاثية بملف-ملف) …' >&2
  base_vol="$(latest_by_time)"
  base_dir="$(mktemp -d)"
  if [ -n "$base_vol" ]; then
    openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -in "$base_vol" | extract_volume "$base_dir" || {
      echo 'تعذر فك حجم الأساس للاستدراك؛ لا ختم أعمى.' >&2; rm -rf "$base_dir"; exit 2; }
  fi
  if ! git merge --ff-only -q FETCH_HEAD 2>/dev/null; then
    echo 'تعذر التحديث السريع (تعديل محلي على ملفات متتبعة؟)؛ صحّح يدويًا ثم أعد الختم.' >&2
    rm -rf "$base_dir"; exit 2
  fi
  theirs_vol="$(latest_by_time)"
  theirs_dir="$(mktemp -d)"
  openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -in "$theirs_vol" | extract_volume "$theirs_dir" || {
    echo 'تعذر فك أحدث حجم بعد المزامنة؛ لا ختم أعمى.' >&2; rm -rf "$base_dir" "$theirs_dir"; exit 2; }
  while IFS= read -r rel; do
    if [ -f "$theirs_dir/$rel" ] && [ ! -f "القناة/$rel" ]; then
      # ملف الأقران غير موجود محليًا (جديد منهم أو حذفٌ محلي غير موثق): تُؤخذ نسختهم،
      # وحارسا النقص والعائد المحذوف أدناه يفصلان في الحذف الموثق.
      cp "$theirs_dir/$rel" "القناة/$rel"
      continue
    fi
    [ -f "القناة/$rel" ] || continue
    mine_h="$(sha256sum "القناة/$rel" | cut -d' ' -f1)"
    base_h=""; [ -f "$base_dir/$rel" ] && base_h="$(sha256sum "$base_dir/$rel" | cut -d' ' -f1)"
    theirs_h=""; [ -f "$theirs_dir/$rel" ] && theirs_h="$(sha256sum "$theirs_dir/$rel" | cut -d' ' -f1)"
    if [ "$mine_h" = "$base_h" ] || [ -z "$base_h" ]; then
      [ -n "$theirs_h" ] && cp "$theirs_dir/$rel" "القناة/$rel"
    elif [ "$theirs_h" = "$base_h" ] || [ -z "$theirs_h" ]; then
      :
    else
      # معدَّل من الطرفين: دمج اتحادي (قناة الإلحاق) — أساس + إلحاقا الطرفين معًا،
      # وحارس الدفن أدناه يظل يرفض ما يُسقط عناوين أقسام الأقران.
      m_tmp="$(mktemp)"; b_tmp="$(mktemp)"; t_tmp="$(mktemp)"
      cp "القناة/$rel" "$m_tmp"; cp "$base_dir/$rel" "$b_tmp"; cp "$theirs_dir/$rel" "$t_tmp"
      if git merge-file --union -L منا -L أساس -L عنهم "$m_tmp" "$b_tmp" "$t_tmp" 2>/dev/null && [ -s "$m_tmp" ]; then
        cp "$m_tmp" "القناة/$rel"
        echo "دمج اتحادي: $rel (أُبقي إلحاقا الطرفين)." >&2
      else
        echo "تحذير: $rel معدَّل من الطرفين وبلا دمج — أبقيتُ نسختك؛ حارس الدفن يفصل أدناه." >&2
      fi
      rm -f "$m_tmp" "$b_tmp" "$t_tmp"
    fi
  done < <( { (cd القناة && find . -type f | norm); (cd "$theirs_dir" && find . -type f | norm); } | sort -u )
  rm -rf "$base_dir" "$theirs_dir"
  echo 'اكتمل الاستدراك الداخلي.' >&2
fi

n="$(next_free_number)"

tmp="$(mktemp -d)"
work="$(mktemp -d)"
trap '
  rm -rf "$tmp" "$work"
  if [ "${SEAL_OK:-0}" != 1 ] && [ -n "${out:-}" ] && [ -f "$out" ]; then
    rm -f "$out"
    echo "نظّف حجما يتيما بعد فشل الختم: $out (أعد الختم بعد الاستدراك)." >&2
  fi
' EXIT

latest_ref_vol="$(latest_by_time)"
if [ -n "$latest_ref_vol" ]; then
  openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -in "$latest_ref_vol" | extract_volume "$tmp"
  ( cd "$tmp" && find . -type f | norm ) > "$work/prev.list"
else
  : > "$work/prev.list"
fi
( cd القناة && find . -type f | norm ) > "$work/cur.list"

missing="$(comm -23 "$work/prev.list" "$work/cur.list" || true)"

manifest_rel="أداة/محذوف-موثق.md"
manifest="القناة/$manifest_rel"
: > "$work/resurrected"
if [ -f "$manifest" ]; then
  awk -F'\t' '!/^#/ && NF>=2 {print $2}' "$manifest" | sort -u > "$work/tomb.list"
  comm -12 "$work/tomb.list" "$work/cur.list" > "$work/resurrected" || true
fi

if [ -s "$work/resurrected" ]; then
  echo 'ممنوع الختم: ملفات حُذفت توثيقيًا عادت محليًا:' >&2
  sed 's/^/  عائد محذوف: /' "$work/resurrected" >&2
  if [ "${ALLOW_RESTORE:-0}" = 1 ]; then
    echo 'إذن إعادة صريح (ALLOW_RESTORE=1): تُشطب من سجل الحذف الموثق ويُستأنف الختم.' >&2
    awk -F'\t' 'BEGIN{while((getline l < "'"$work/resurrected"'")>0) r[l]=1} /^#/ {print; next} NF>=2 && ($2 in r) {next} {print}' "$manifest" > "$manifest.new"
    mv "$manifest.new" "$manifest"
  else
    echo 'إن كانت العودة مقصودة: ALLOW_RESTORE=1 bash scripts/ختم.sh، وإلا احذفها ثم أعد الختم.' >&2
    exit 5
  fi
fi

if [ -n "$missing" ]; then
  echo 'ممنوع الختم: ملفات كانت في أحدث حجم وغابت عن نسختك (حذف عرضي أو فك ناقص أو مساحة قديمة):' >&2
  printf '%s\n' "$missing" | sed 's/^/  غائب: /' >&2
  if [ "${ALLOW_DELETE:-0}" = 1 ]; then
    echo 'إذن حذف صريح (ALLOW_DELETE=1): يُسجَّل الحذف توثيقيًا ويُستأنف الختم.' >&2
    mkdir -p "$(dirname "$manifest")"
    [ -f "$manifest" ] || printf '# حذف موثق — يملؤه سكربت الختم بإذن ALLOW_DELETE=1\n# الصيغة: رقم الحجم <TAB> المسار\n' > "$manifest"
    while IFS= read -r f; do
      printf '%s\t%s\n' "$n" "$f" >> "$manifest"
    done <<< "$missing"
  else
    echo 'استدرك بـ bash scripts/فتح.sh لاستردادها. الحذف المقصود فقط: ALLOW_DELETE=1 bash scripts/ختم.sh.' >&2
    exit 4
  fi
fi

# ─── حارس الدفن (ق-٠٠٧/ج): لا يختفي عنوان قسم من ملف قائم بين آخر حجم ونسختي ───
buried_report="$work/buried.list"
: > "$buried_report"
while IFS= read -r rel; do
  [ -f "القناة/$rel" ] || continue
  if ! cmp -s "$tmp/$rel" "القناة/$rel"; then
    gone="$(comm -23 <(grep -E '^#{2,6} ' "$tmp/$rel" | sort -u) <(grep -E '^#{2,6} ' "القناة/$rel" | sort -u) || true)"
    if [ -n "$gone" ]; then
      echo "$rel" >> "$buried_report"
      printf '%s\n' "$gone" | sed "s#^#    عنوان مدفون: #" >&2
    fi
  fi
done < <(comm -12 "$work/prev.list" "$work/cur.list" || true)

if [ -s "$buried_report" ]; then
  echo 'ممنوع الختم: دفن محتوى قائم — عناوين أقسام من أحدث حجم اختفت من نسختك (ق-٠٠٧):' >&2
  sed 's/^/  ملف مدفون: /' "$buried_report" >&2
  if [ "${ALLOW_BURY:-0}" = 1 ]; then
    echo 'إذن دفن صريح (ALLOW_BURY=1): يُسجَّل في أداة/مدفون-موثق.md ويُستأنف الختم.' >&2
    bury_manifest="القناة/أداة/مدفون-موثق.md"
    mkdir -p "$(dirname "$bury_manifest")"
    [ -f "$bury_manifest" ] || printf '# دفن موثق — يملؤه سكربت الختم بإذن ALLOW_BURY=1\n# الصيغة: رقم الحجم <TAB> المسار <TAB> العناوين المدفونة\n' > "$bury_manifest"
    while IFS= read -r rel; do
      gone="$(comm -23 <(grep -E '^#{2,6} ' "$tmp/$rel" | sort -u) <(grep -E '^#{2,6} ' "القناة/$rel" | sort -u) | tr '\n' '؛')"
      printf '%s\t%s\t%s\n' "$n" "$rel" "$gone" >> "$bury_manifest"
    done < "$buried_report"
  else
    echo 'إن كان الدفن مقصودًا: ALLOW_BURY=1 bash scripts/ختم.sh؛ وإلا افتح وادمج نقوش أقرانك ثم اختم.' >&2
    exit 6
  fi
fi

# ─── الإنشاء والفحص والالتزام والدفع — دورة قابلة لإعادة الدخول ───
# كل دورة: إنشاء نظيف ← فحص ← التزام ← جلب ← (إعادة ترقيم | تأسيس فوق البعيد) ← دفع.
# كل مسار فشل يُنظف التزامها وحجمها قبل الدورة التالية فلا يتبقى يتيم ولا رقم مزدوج.
attempt=0
SEAL_OK=0
while :; do
  attempt=$((attempt+1))
  nn="$(printf '%03d' "$n")"
  out="vault/v-$nn.enc"
  if [ -e "$out" ]; then
    echo "ممنوع: الرقم v-$nn مشغول محليًا ($out) — لن يُدفن حجم تحت رقم قائم." >&2
    exit 3
  fi
  mkdir -p vault
  tar -czf - -C القناة . | openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -out "$out"

  bash scripts/فحص.sh

  git add "$out"
  git commit -q -m "snapshot $nn" || {
    echo 'فشل الالتزام (تحقق من هوية جيت/الحالة المحلية)؛ حُجِم أي يتيم بالتنظيف التلقائي.' >&2
    exit 1
  }

  git fetch -q origin "$BRANCH" || true
  if [ "$(git rev-parse -q --verify FETCH_HEAD 2>/dev/null)" != "$(git rev-parse HEAD~1)" ]; then
    remote_latest="$(tree_max_number FETCH_HEAD)"
    if [ "${remote_latest:-0}" -ge "$n" ]; then
      # الرقم صار على البعيد (سباق) — إعادة ترقيم كاملة.
      if [ "$attempt" -ge 4 ]; then
        echo 'تكرر سباق الترقيم؛ تراجع الالتزام وحجزه يُنظف — أعد الختم.' >&2
        git reset -q --mixed HEAD~1; rm -f "$out"; exit 3
      fi
      echo "سباق ترقيم: v-$nn صار على البعيد؛ أُعيد الترقيم (محاولة $attempt)." >&2
      git reset -q --mixed HEAD~1; rm -f "$out"
      n="$(next_free_number)"
      continue
    fi
    if ! git rebase -q FETCH_HEAD 2>/dev/null; then
      git rebase --abort 2>/dev/null || true
      echo 'تعذر التأسيس فوق البعيد (rebase)؛ تراجع الالتزام — أعد الختم بعد الاستدراك.' >&2
      git reset -q --mixed HEAD~1; rm -f "$out"; exit 3
    fi
    if ! bash scripts/فحص.sh; then
      echo 'فحص ما بعد التأسيس رسب (ازدواج رقم؟)؛ تراجع الالتزام — أعد الختم برقم جديد.' >&2
      git reset -q --mixed HEAD~1; rm -f "$out"; exit 3
    fi
  fi

  if auth_push -q origin HEAD 2>/dev/null; then
    SEAL_OK=1
    echo "خُتم ودُفع الحجم: $out"
    break
  fi

  if [ "$attempt" -ge 4 ]; then
    echo 'ممنوع: فشل الدفع مرارًا (سباق متكرر). يُتراجَع هذا الحجم المحلي.' >&2
    git reset -q --mixed HEAD~1; rm -f "$out"
    echo 'استدرك: bash scripts/فتح.sh ثم bash scripts/ختم.sh.' >&2
    exit 3
  fi
  echo 'فشل الدفع (سباق في اللحظة الأخيرة)؛ تأسيس جديد فوق البعيد ودورة جديدة.' >&2
  git reset -q --mixed HEAD~1; rm -f "$out"
done

# إعلان الأيتام المحلية (أحجام غير مدفوعة) — لا تُحذف آليًا؛ قد تكون نفقة استدراك قائمة.
orphans="$(git ls-files --others --exclude-standard -- vault/ 2>/dev/null || true)"
[ -n "$orphans" ] && printf '%s\n' "$orphans" | sed 's/^/تنبيه: حجم محلي غير مدفوع (يتيم): /' >&2
true
