#!/usr/bin/env bash
# يفشل إن وُجد في التتبع أي ملف مكشوف خارج القائمة البيضاء، أو حجم لا يبدأ بتوقيع التشفير.
set -euo pipefail
cd "$(dirname "$0")/.."

pattern='^(README\.md|حقوق\.md|\.optout|\.ai_exclude|\.gitignore|scripts/[^/]+|\.github/workflows/[^/]+|vault/v-[0-9]+\.enc)$'
bad=0

while IFS= read -r f; do
  if ! [[ "$f" =~ $pattern ]]; then
    echo "ممنوع: ملف مكشوف خارج القائمة البيضاء: $f" >&2
    bad=1
  fi
done < <(git -c core.quotepath=false ls-files)

shopt -s nullglob
for f in vault/v-*.enc; do
  if [ "$(head -c 8 "$f")" != 'Salted__' ]; then
    echo "ممنوع: حجم لا يحمل توقيع التشفير: $f" >&2
    bad=1
  fi
done

if [ "$bad" -ne 0 ]; then
  echo 'الفحص فشل.' >&2
  exit 1
fi
echo 'الفحص نظيف: لا مكشوف خارج القائمة البيضاء.'
