#!/usr/bin/env bash
# يلتقط مجلد القناة كاملًا في حجم مشفّر جديد، يفحص، ثم يلتزم ويدفع.
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

last="$(ls -1 vault/v-*.enc 2>/dev/null | sed -E 's#.*/v-([0-9]+)\.enc#\1#' | sort -n | tail -n 1 || true)"
n=$((10#${last:-0} + 1))
out="$(printf 'vault/v-%03d.enc' "$n")"

tar -czf - -C القناة . | openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -out "$out"

bash scripts/فحص.sh

git add vault
git commit -m "snapshot $(printf '%03d' "$n")" >/dev/null
git push origin HEAD 2>&1 | sed 's#//[^@]*@#//***@#g'
echo "خُتم ودُفع الحجم: $out"
