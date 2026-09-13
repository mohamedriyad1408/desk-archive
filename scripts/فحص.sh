#!/usr/bin/env bash
# يفشل إن وُجد في التتبع أي ملف مكشوف خارج القائمة البيضاء، أو حجم لا يبدأ بتوقيع التشفير،
# أو رقم حجم مزدوج بمحتوى مغاير في تاريخ الفرعة منذ قاعدة الفحص (ق-٠٠٧/أ).
set -euo pipefail
cd "$(dirname "$0")/.."

pattern='^(README\.md|حقوق\.md|\.optout|\.ai_exclude|\.gitignore|scripts/[^/]+|\.github/workflows/[^/]+|vault/v-[0-9]+\.enc|نبض/[^/]+\.md)$'
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

# ق-٠٠٧/أ — ازدواج رقم الحجم بمحتوى مغاير: مسار vault/v-NNN.enc الواحد يجب أن يحمل
# بلوبًا واحدًا عبر التاريخ كله. القاعدة: أقدم التزام يحمل علامة DUPCHECK-BASE في فحص.sh
# (فما قبله ازدواجات تاريخية موثقة في ق-٠٠٧ تُترك لسجلها؛ فما بعده ممنوع منعًا قاطعًا).
dup_base=""
while IFS= read -r c; do
  if git show "$c:scripts/فحص.sh" 2>/dev/null | grep -q 'DUPCHECK-BASE'; then dup_base="$c"; break; fi
done < <(git log --format=%H --reverse -- scripts/فحص.sh 2>/dev/null || true)
if [ -z "$dup_base" ]; then
  dup_base="$(git rev-parse HEAD 2>/dev/null || echo '')"
  [ -n "$dup_base" ] && echo 'تنبيه: نسخة الفحص الحديثة غير ملتزمة بعد؛ فحص الازدواج يبدأ من HEAD.' >&2
fi
if [ -n "$dup_base" ]; then
  declare -A seen_blob
  while IFS= read -r c; do
    while IFS=$' \t' read -r _mode _type blob path; do
      [ -n "$path" ] || continue
      if [ -n "${seen_blob[$path]:-}" ] && [ "${seen_blob[$path]}" != "$blob" ]; then
        echo "ممنوع: رقم حجم مزدوج بمحتوى مغاير في التاريخ: $path (ق-٠٠٧/أ)" >&2
        bad=1
      fi
      seen_blob[$path]="$blob"
    done < <(git -c core.quotepath=false ls-tree "$c" -- vault/ 2>/dev/null | sed 's/\t/ /')
  done < <(git rev-list HEAD --not "$dup_base" 2>/dev/null || true)
fi

if [ "$bad" -ne 0 ]; then
  echo 'الفحص فشل.' >&2
  exit 1
fi
echo 'الفحص نظيف: لا مكشوف خارج القائمة البيضاء ولا ازدواج أرقام.'
