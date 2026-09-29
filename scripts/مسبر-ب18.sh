#!/usr/bin/env bash
# مسبار ب١٨ (لا-فقدان) — قتلات القبول الخمس + حالتا نجاح + تدقيق التاريخ + تمييز ضد النسخة الساذجة.
# التشغيل: bash scripts/مسبر-ب18.sh   (يعمل في /var/tmp/مسبر-ب18، لا يمس القناة)
set -uo pipefail
GUARD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/مرجع-حارس-الفقدان.py"
G(){ python3 "$GUARD" "$1" --repo "$2" "${@:3}"; }
SB=/var/tmp/مسبر-ب18; rm -rf "$SB"; mkdir -p "$SB"; cd "$SB"
PASS=0; FAIL=0
ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }
no(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }
mkvol(){ # يصنع حجمًا (tar للحالة الحية) ويثبّته
  tar czf "vault/v-$(printf '%03d' "$1").enc" --exclude=./.git --exclude=./vault --exclude=./meta . 2>/dev/null
  G snapshot . >/dev/null; git add -A >/dev/null; git commit -qm "volume-$1" >/dev/null; git push -q origin main >/dev/null 2>&1; }
setup(){ local d="$1"; git init -q --bare "$SB/$d-remote.git"
  git clone -q "$SB/$d-remote.git" "$SB/$d" 2>/dev/null; cd "$SB/$d"
  git config user.email t@t; git config user.name t; git checkout -q -b main 2>/dev/null || true
  git symbolic-ref HEAD refs/heads/main; git push -q origin main 2>/dev/null || true
  mkdir -p meta vault; echo "أ" > f1.md; echo "ب" > f2.md; echo "ج" > f3.md; echo "د" > f4.md; echo "هـ" > f5.md; mkvol 1; mkvol 2; mkvol 3; }

echo "════ مسبار ب١٨ — قتلات القبول ════"
setup A
# قتلة ١: فقد صامت حديث (المطلوب: رفض 4 + استعادة تلقائية ثم نظافة)
echo "◆ ق١: فقد صامت لحديث (f3)"
rm f3.md
out=$(G check . 2>&1); rc=$?
echo "$out" | sed 's/^/    /'
[ $rc -eq 4 ] && echo "$out" | grep -q 'استُعيد' && ok "ق١ رُفضت برمز ٤ مع استعادة تلقائية" || no "ق١: rc=$rc"
[ -f f3.md ] && ok "ق١: الملف استُعيد فعليًا" || no "ق١: لم يُستعد"
rc2=$(G check . >/dev/null 2>&1; echo $?); [ "$(echo "$rc2" | tail -1)" -eq 0 ] && ok "ق١: بعد الاستعادة — نظيف (٠)" || no "ق١: ما زال مرفوضًا"
# قتلة ٢: قاعدة قديمة (CAS) — المطلوب 5
echo "◆ ق٢: شجرة على قاعدة قديمة"
git checkout -q -b stale-test HEAD~1
out=$(G check . 2>&1); rc=$?
echo "$out" | sed 's/^/    /'
[ $rc -eq 5 ] && ok "ق٢ رُفضت برمز ٥ (CAS)" || no "ق٢: rc=$rc"
git checkout -q main
# قتلة ٣: ثلاثة سباقات، كل منها يسقط ملفًا مختلفًا — الثلاثة تُرفض
echo "◆ ق٣: ثلاثة سباقات متزامنة (كلٌّ يسقط ملفًا مختلفًا)"
for i in 1 2 3; do rm -rf "$SB/A-c$i"; cp -r "$SB/A" "$SB/A-c$i"; done
( cd "$SB/A-c1" && rm f1.md && G check . >/dev/null 2>&1; echo $? > "$SB/rc1" ) &
( cd "$SB/A-c2" && rm f2.md && G check . >/dev/null 2>&1; echo $? > "$SB/rc2" ) &
( cd "$SB/A-c3" && rm f5.md && G check . >/dev/null 2>&1; echo $? > "$SB/rc3" ) &
wait
r1=$(cat "$SB/rc1" 2>/dev/null); r2=$(cat "$SB/rc2" 2>/dev/null); r3=$(cat "$SB/rc3" 2>/dev/null)
[ "$r1" = 4 ] && [ "$r2" = 4 ] && [ "$r3" = 4 ] && ok "ق٣: الثلاثة رُفضت (4/4/4)" || no "ق٣: رموز ($r1/$r2/$r3)"
# قتلة ٤+نجاح: دفن مصرّح ينجح، وإحياء غير مصرّح يُرفض
echo "◆ ق٤+ن١: دفن مصرّح ثم إحياء غير مصرّح"
G tombstone . f4.md "مالك-المهمة" "سبب-موثق" >/dev/null; git add meta; git commit -qm "tombstone-f4"; git push -q origin main; rm f4.md
out=$(G check . 2>&1); rc=$?
[ $rc -eq 0 ] && ok "ن١: الحذف المصرّح مرّ (٠)" || { no "ن١: rc=$rc"; echo "$out" | sed 's/^/    /'; }
echo "مُحيا" > f4.md
out=$(G check . 2>&1); rc=$?
[ $rc -eq 4 ] && echo "$out" | grep -q 'إحياء غير مصرح' && ok "ق٤: الإحياء غير المصرّح رُفض (٤)" || { no "ق٤: rc=$rc"; echo "$out" | sed 's/^/    /'; }
rm f4.md
# قتلة ٥: فقد قديم تجاوز نافذة K — المطلوب: يبقى مكتشفًا (Manifest تراكمي)، والساذج يُفلت
echo "◆ ق٥: فقد قديم تجاوز النافذة (سقط عند v5، الكشف عند v9)"
rm f5.md; G snapshot . >/dev/null; git add -A; git commit -qm "v4-drop-f5-silently"; git push -q origin main
mkvol 5; mkvol 6; mkvol 7          # مرّت النافذة (K=2)
out=$(G check . 2>&1); rc=$?
echo "$out" | sed 's/^/    /'
[ $rc -eq 4 ] && echo "$out" | grep -q 'f5.md' && ok "ق٥: الفقد القديم كُشف (٤)" || no "ق٥: rc=$rc"
echo "◆ ق٥-س: النسخة الساذجة (لقطة غير تراكمية = آخر حجم) — تُفلت (إثبات تمييز المسبار)"
rm -rf "$SB/N"; git init -q --bare "$SB/N-remote.git"; git clone -q "$SB/N-remote.git" "$SB/N"; cd "$SB/N"
git config user.email t@t; git config user.name t; git checkout -q -b main
git remote set-head origin -a >/dev/null 2>&1 || true; mkdir -p meta vault
echo "seed" > .seed; git add -A; git commit -qm seed; git push -q origin main; git fetch -q origin; git remote set-head origin -a >/dev/null 2>&1 || true; rm .seed; git rm -q --cached .seed; rm -f .seed
echo "x" > g1.md; echo "y" > g2.md; echo "z" > g5.md
naive_snap(){ find . -type f ! -path './.git/*' ! -path './meta/*' ! -path './vault/*' -printf '%P\n' | sort > meta/live-set.tsv; }  # غير تراكمية
tar czf vault/v-001.enc g1.md g2.md g5.md; naive_snap; git add -A; git commit -qm v1; git push -q origin main
rm g5.md; tar czf vault/v-002.enc g1.md g2.md; naive_snap; git add -A; git commit -qm v2; git push -q origin main
echo "w" > g3.md; tar czf vault/v-003.enc g1.md g2.md g3.md; naive_snap; git add -A; git commit -qm v3; git push -q origin main
rm g5.md 2>/dev/null; nout=$(G check . 2>&1); nrc=$?
if [ $nrc -eq 0 ]; then ok "ق٥-س: الساذج أفلت كما هو متوقع (exit 0) ⇒ القتلة تميّز"; else echo "    (الساذج رُفض بالرمز $nrc — ملاحظة)"; fi
cd "$SB/A"
# تدقيق التاريخ
echo "◆ تدقيق التاريخ (union−tombstones == live)"
out=$(G audit . 2>&1); rc=$?
echo "$out" | sed 's/^/    /'
[ $rc -eq 0 ] && ok "التدقيق مطابق" || no "التدقيق فشل (rc=$rc)"
echo; echo "════ الحصيلة: نجح $PASS · فشل $FAIL ════"
[ $FAIL -eq 0 ] || exit 1
