#!/usr/bin/env bash
# يجلب أحدث أحجام البعيد ثم يفك أحدثها إلى مجلد العمل المحلي (القناة).
# المفتاح لا يُكتب في ملف. يعلن: الزائد المحلي، والغائب محليًا (يُسترد)،
# ويحذّر من عودة ملف حُذف توثيقيًا.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${MIFTAH:-}" ]; then
  read -rsp 'مفتاح الفك: ' MIFTAH
  echo
  export MIFTAH
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# ق-٠٠٥: شفاء ذاتي بعد إعادة تجهيز المساحة (origin/الهوية/بت التنفيذ قد تزول).
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
# إعادة التجهيز تُنزل بت التنفيذ عن السكربتات (فارق صفر سطر في git diff).
chmod +x scripts/*.sh 2>/dev/null || true
# تتمة ق-٠٠٥ الثانية: ضجيج تغيير الأذونات (100755→100644) يلوّث status بفارق صفر سطر.
git config core.fileMode false 2>/dev/null || true

git fetch -q origin "$BRANCH" || {
  echo 'تعذر جلب البعيد (شبكة/remote)؛ لا فتح أعمى. صحّح ثم أعد.' >&2
  exit 1
}
if ! git merge --ff-only -q FETCH_HEAD 2>/dev/null; then
  echo 'تحذير: تعذر تحديث النسخة المحلية سريعًا (تعديل محلي على ملفات متتبعة؟).' >&2
  echo 'صحّح وضع جيت المحلي، ثم أعد فتح.sh. لا تختِم على نسخة قديمة.' >&2
  exit 1
fi

# ق-٠٠٧/ب: الرقم ليس زمنًا — الأحدث التزامًا هو الحكم، والأعلى رقمًا يُفتح فقط عند التساوي.
# تعادل الطوابع يحسم للأعلى رقمًا (ختمان في الثانية نفسها واردان).
latest_by_time() { # علاج v-255 (اقتراح م٢ · تنفيذ م١): الكشف من كائنات git لا من ملفات العمل —
  # ملفات العمل قد تكون متخلفة بعد استعادة لقطة فيُفتح/يُبنى على حجم قديم ويجتاز الحراس (واقعة v-255).
  # المرجع HEAD في لحظة النداء: في فتح.sh بعد الدمج = البعيد؛ وفي ختم.sh قبل الدمج = آخر حالتي وبعده = البعيد.
  local f ct best=0 best_f=""
  while IFS= read -r f; do
    ct="$(git log -1 --format=%ct HEAD -- "$f" 2>/dev/null || echo 0)"
    if [ "${ct:-0}" -ge "$best" ] && [ "${ct:-0}" -gt 0 ]; then best="$ct"; best_f="$f"; fi
  done < <(git -c core.quotepath=false ls-tree --name-only HEAD -- vault/ 2>/dev/null | sort)
  echo "$best_f"
}

# تجسيد الأحجام على القرص قبل الفك (علاج v-255): الكشف من كائنات git والملف قد يكون غائبًا من مجلد العمل.
git checkout HEAD -- vault/ 2>/dev/null || true

latest="$(latest_by_time)"
if [ -z "$latest" ]; then
  echo 'لا توجد أحجام مشفّرة بعد؛ شغّل ختم.sh بعد تهيئة مجلد القناة.' >&2
  exit 1
fi
highest="$(ls -1 vault/v-*.enc 2>/dev/null | sort | tail -n 1)"
if [ "$latest" != "$highest" ]; then
  echo "تنبيه ق-٠٠٧: الأعلى رقمًا ($highest) ليس الأحدث زمنًا؛ فتحتُ الأحدث التزامًا: $latest" >&2
fi

tmp="$(mktemp -d)"
work="$(mktemp -d)"
trap 'rm -rf "$tmp" "$work"' EXIT
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -in "$latest" | tar -xz -C "$tmp"

norm() { sed -E 's#^\./##' | sed '/^$/d' | sort; }
( cd "$tmp" && find . -type f | norm ) > "$work/snap.list"
if [ -d القناة ]; then
  had_channel=1
  ( cd القناة && find . -type f | norm ) > "$work/local.list"
else
  had_channel=0
  : > "$work/local.list"
fi

if [ "$had_channel" = 1 ]; then
  missing_local="$(comm -13 "$work/local.list" "$work/snap.list" || true)"
  extras="$(comm -23 "$work/local.list" "$work/snap.list" || true)"
else
  missing_local=""
  extras=""
fi

# خ-٧ (اعتماد م١ ٢٠٢٦-٠٩-١٨): لا يمحو تحرير القناة — تحرير محلي غير مدفوع يوقف الاستخراج
# (نسخة احتياطية تُؤخذ دائمًا عند وجوده؛ والتجاوز المتعمد بـ OPEN_FORCE=1 بعد الدفع).
# القناة/ غير متعقَّبة في جيت (المحتوى يُختم في vault/ مشفَّرًا) — فيُقاس التحرير بمقارنة المحتوى
# مع اللقطة المنزوعة من آخر حجم: ملفات مشتركة تختلف ⇒ تحرير لم يُختم بعد.
dirty="$(diff -rq "$tmp" القناة 2>/dev/null | grep -aE '^Files .* differ$' || true)"
if [ -n "$dirty" ]; then
  backup_dir="${TMPDIR:-/tmp}/desk-archive-local-backups"; mkdir -p "$backup_dir"
  backup="$backup_dir/القناة-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
  tar czf "$backup" القناة 2>/dev/null || true
  echo "تحذير (خ-٧): في القناة/ تحرير محلي غير مدفوع ($(printf '%s\n' "$dirty" | grep -c .) سطرًا) — نسخة احتياطية: $backup"
  if [ "${OPEN_FORCE:-0}" != 1 ]; then
    echo 'الاستخراج لن يمحو تحريرك: ادفعه (ختم.sh) ثم أعد، أو شغّله بـ OPEN_FORCE=1 بعد أخذ النسخة الاحتياطية.' >&2
    exit 7
  fi
fi
mkdir -p القناة
cp -a "$tmp"/. القناة/

[ -n "$missing_local" ] && {
  echo "ملفات غائبة عن نسختك المحلية واستُردّت من $latest ($(printf '%s\n' "$missing_local" | grep -c .)):"
  printf '%s\n' "$missing_local" | sed 's/^/  مُسترد: /'
}
[ -n "$extras" ] && {
  echo 'ملفات محلية زائدة عن آخر حجم (غالبًا مخرجك الجديد — إن لم تتعرف عليها احذفها قبل الختم):'
  printf '%s\n' "$extras" | sed 's/^/  زائد: /'
}

manifest="أداة/محذوف-موثق.md"
if [ -f "$tmp/$manifest" ]; then
  awk -F'\t' '!/^#/ && NF>=2 {print $2}' "$tmp/$manifest" | sort -u > "$work/tombstone.list"
  if [ -s "$work/tombstone.list" ]; then
    resurrected="$(comm -12 "$work/tombstone.list" <(cd القناة && find . -type f | norm) || true)"
    [ -n "$resurrected" ] && {
      echo 'تحذير: ملفات حُذفت توثيقيًا عادت إلى نسختك المحلية؛ الختم سيرفضها إلا بإذن إعادة صريح (ALLOW_RESTORE=1):'
      printf '%s\n' "$resurrected" | sed 's/^/  عائد محذوف: /'
    }
  fi
fi
echo "فُتح آخر حجم بعد جلب البعيد: $latest"
