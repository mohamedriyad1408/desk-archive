#!/usr/bin/env bash
# يلتقط مجلد القناة كاملًا في حجم مشفّر جديد، يفحص، ثم يلتزم ويدفع.
# حارسان قبل الإنشاء:
#   - تحرك البعيد: رفض برمز 2 مع خطوات الاستدراك.
#   - نقص الملفات عن أحدث حجم: رفض برمز 4؛ الحذف الموثق فقط بـ ALLOW_DELETE=1.
#   - عودة ملف حُذف توثيقيًا: رفض برمز 5؛ إعادته عمدًا فقط بـ ALLOW_RESTORE=1.
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

if ! git fetch -q origin "$BRANCH"; then
  echo 'تعذر جلب البعيد؛ لا ختم بلا معرفة تحركه (امنع الختم الأعمى).' >&2
  exit 2
fi
behind="$(git rev-list --count HEAD..FETCH_HEAD 2>/dev/null || echo 0)"
if [ "$behind" -gt 0 ]; then
  echo "ممنوع الختم: البعيد أحدث من نسختك بـ$behind التزامًا (وكيل سبقك بالدفع)." >&2
  echo 'استدرك بالتسلسل (مخرجاتك الجديدة ذات الأسماء الفريدة لن تُمس):' >&2
  echo '  ١) git merge --ff-only FETCH_HEAD' >&2
  echo '  ٢) bash scripts/فتح.sh' >&2
  echo '  ٣) راجع «الملفات الزائدة» المعلنة وتأكد أن مخرجك بينها' >&2
  echo '  ٤) bash scripts/ختم.sh' >&2
  exit 2
fi

last="$(ls -1 vault/v-*.enc 2>/dev/null | sed -E 's#.*/v-([0-9]+)\.enc#\1#' | sort -n | tail -n 1 || true)"
n=$((10#${last:-0} + 1))
nn="$(printf '%03d' "$n")"
out="vault/v-$nn.enc"

norm() { sed -E 's#^\./##' | sed '/^$/d' | sort; }
tmp="$(mktemp -d)"
work="$(mktemp -d)"
trap '
  rm -rf "$tmp" "$work"
  if [ "${SEAL_OK:-0}" != 1 ] && [ -n "${out:-}" ] && [ -f "$out" ]; then
    rm -f "$out"
    echo "نظّف حجما يتيما بعد فشل الختم: $out (أعد الختم بعد الاستدراك)." >&2
  fi
' EXIT

if [ -n "$last" ]; then
  latestv="$(printf 'vault/v-%03d.enc' "$((10#$last))")"
  openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -in "$latestv" | tar -xz -C "$tmp"
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
      printf '%s\t%s\n' "$nn" "$f" >> "$manifest"
    done <<< "$missing"
  else
    echo 'استدرك بـ bash scripts/فتح.sh لاستردادها. الحذف المقصود فقط: ALLOW_DELETE=1 bash scripts/ختم.sh.' >&2
    exit 4
  fi
fi

tar -czf - -C القناة . | openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -out "$out"

bash scripts/فحص.sh

# كل ما في مجلد القناة (ومنه سجل الحذف الموثق) داخل الحجم المشفّر؛ لا يُضاف منه نص مكشوف.
# ق-٠٠٥: الحجم الجديد وحده يُضاف — فلا يُكنَس حجم يتيم سابق فيُدفَن تحت رقم تالٍ.
git add "$out"
git commit -q -m "snapshot $nn" || {
  echo 'فشل الالتزام (تحقق من هوية جيت/الحالة المحلية)؛ حُجِم أي يتيم بالتنظيف التلقائي.' >&2
  exit 1
}

if ! git push origin HEAD 2>&1 | sed 's#//[^@]*@#//***@#g'; then
  echo 'ممنوع: فشل الدفع (سباق في اللحظة الأخيرة على الأرجح). يُتراجَع هذا الحجم المحلي.' >&2
  SEAL_OK=0
  git reset -q --mixed HEAD~1
  rm -f "$out"
  echo 'استدرك: bash scripts/فتح.sh ثم bash scripts/ختم.sh.' >&2
  exit 3
fi
SEAL_OK=1
echo "خُتم ودُفع الحجم: $out"
