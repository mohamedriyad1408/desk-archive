#!/usr/bin/env bash
# يلتقط مجلد القناة كاملًا في حجم مشفّر جديد، يفحص، ثم يلتزم ويدفع.
# قبل الختم يفحص تحرك البعيد؛ إن سبقه غيره يرفض ويطبع خطوات الاستدراك بلا دهس.
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
git fetch -q origin "$BRANCH" || true
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
out="$(printf 'vault/v-%03d.enc' "$n")"

tar -czf - -C القناة . | openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:MIFTAH -out "$out"

bash scripts/فحص.sh

git add vault
git commit -q -m "snapshot $(printf '%03d' "$n")"

if ! git push origin HEAD 2>&1 | sed 's#//[^@]*@#//***@#g'; then
  echo 'ممنوع: فشل الدفع (سباق في اللحظة الأخيرة على الأرجح). يُتراجَع هذا الحجم المحلي.' >&2
  git reset -q --mixed HEAD~1
  rm -f "$out"
  echo 'استدرك: bash scripts/فتح.sh ثم bash scripts/ختم.sh.' >&2
  exit 3
fi
echo "خُتم ودُفع الحجم: $out"
