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
git fetch -q origin "$BRANCH"
if ! git merge --ff-only -q FETCH_HEAD 2>/dev/null; then
  echo 'تحذير: تعذر تحديث النسخة المحلية سريعًا (تعديل محلي على ملفات متتبعة؟).' >&2
  echo 'صحّح وضع جيت المحلي، ثم أعد فتح.sh. لا تختِم على نسخة قديمة.' >&2
  exit 1
fi

latest="$(ls -1 vault/v-*.enc 2>/dev/null | sort | tail -n 1 || true)"
if [ -z "$latest" ]; then
  echo 'لا توجد أحجام مشفّرة بعد؛ شغّل ختم.sh بعد تهيئة مجلد القناة.' >&2
  exit 1
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
