#!/usr/bin/env bash
# يجلب أحدث أحجام البعيد ثم يفك أحدثها إلى مجلد العمل المحلي (القناة).
# المفتاح لا يُكتب في ملف. الملفات الزائدة المحلية (كمخرَج جديد لم يُختم بعد) تبقى وتُعلَن.
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

mkdir -p القناة
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -in "$latest" | tar -xz -C "$tmp"
cp -a "$tmp"/. القناة/

if [ -d القناة ]; then
  extras="$(comm -23 \
    <(cd القناة && find . -type f | sort) \
    <(cd "$tmp"   && find . -type f | sort) || true)"
  if [ -n "$extras" ]; then
    echo 'ملفات محلية زائدة عن آخر حجم (غالبًا مخرجك الجديد — إن لم تتعرف عليها احذفها قبل الختم):'
    echo "$extras" | sed 's/^/  زائد: /'
  fi
fi
echo "فُتح آخر حجم بعد جلب البعيد: $latest"
