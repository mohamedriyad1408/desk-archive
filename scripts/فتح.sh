#!/usr/bin/env bash
# يفك آخر حجم مشفّر إلى مجلد العمل المحلي (القناة). المفتاح لا يُكتب في ملف.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${MIFTAH:-}" ]; then
  read -rsp 'مفتاح الفك: ' MIFTAH
  echo
  export MIFTAH
fi

latest="$(ls -1 vault/v-*.enc 2>/dev/null | sort | tail -n 1 || true)"
if [ -z "$latest" ]; then
  echo 'لا توجد أحجام مشفّرة بعد؛ شغّل ختم.sh بعد تهيئة مجلد القناة.' >&2
  exit 1
fi

mkdir -p القناة
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -in "$latest" | tar -xz -C القناة
echo "فُتح آخر حجم: $latest"
