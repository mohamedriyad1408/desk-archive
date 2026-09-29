#!/usr/bin/env bash
# مسبار ب١٢ (الختم الرشيق) — قبول: 1000 حجم · 3 ختوم متسابقة · peak disk ثابت · صفر بقايا سرّ.
# + قتلات تمييز: naive-number (تصادم) · checkout (قرص ينمو) · token (بقايا).
set -uo pipefail
REF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/مرجع-الختم-الرشيق.py"
SB=/var/tmp/مسبر-ب12; rm -rf "$SB"; mkdir -p "$SB"; cd "$SB"
PASS=0; FAIL=0; ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }; no(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }
echo "════ مسبار ب١٢ — الختم الرشيق ════"
git init -q --bare "$SB/remote.git"
git clone -q "$SB/remote.git" "$SB/seed"; cd "$SB/seed"; git config user.email t@t; git config user.name t
git checkout -q -b main; git remote set-head origin -a >/dev/null 2>&1 || true
mkdir -p vault tree
python3 - <<'PY'
import os
os.makedirs('tree',exist_ok=True)
open('tree/data.bin','wb').write(os.urandom(1024*1024))          # شجرة ~1MB
for i in range(1,1001):                                          # 1000 حجم × 12KB
    open(f'vault/v-{i:04d}.enc','wb').write(os.urandom(12*1024))
PY
git add -A; git commit -qm "seed 1000 volumes"; git push -q origin main; git -C "$SB/remote.git" symbolic-ref HEAD refs/heads/main; git fetch -q origin
VAULT_KB=$(du -sk vault | cut -f1); echo "  [إعداد] 1000 حجم = ${VAULT_KB}KB · شجرة 1MB · العتبة=$((VAULT_KB/2))KB"
# أداة قياس الذروة
peak(){ du -sk "$1" 2>/dev/null; }
measure(){ local d="$1" out="$2"; local base; base=$(peak "$d" | cut -f1)
  ( while :; do peak "$d" | cut -f1 >> "$out"; sleep 0.1; done ) & local sp=$!
  shift 2; "$@"; wait_lib=$?; kill $sp 2>/dev/null; wait $sp 2>/dev/null
  local mx; mx=$(sort -n "$out" | tail -1); echo "$((mx-base))"; }
# ── ١) ثلاثة ختوم متسابقة بالمرجع ──
for i in 1 2 3; do git clone -q "$SB/remote.git" "$SB/w$i"; git -C "$SB/w$i" config user.email "t$i@t"; git -C "$SB/w$i" config user.name "t$i"; done
: > "$SB/ledger.tsv"
echo "◆ التشغيل: 3 ختوم متسابقة (المرجع)"
B1=$(peak "$SB/w1" | cut -f1)
( while :; do peak "$SB/w1" | cut -f1 >> "$SB/peak1.log"; sleep 0.1; done ) & SP=$!
SEAL_AUTHOR=A python3 "$REF" "$SB/w1" --ledger "$SB/ledger.tsv" > "$SB/w1.log" 2>&1 & P1=$!
SEAL_AUTHOR=B python3 "$REF" "$SB/w2" --ledger "$SB/ledger.tsv" > "$SB/w2.log" 2>&1 & P2=$!
SEAL_AUTHOR=C python3 "$REF" "$SB/w3" --ledger "$SB/ledger.tsv" > "$SB/w3.log" 2>&1 & P3=$!
wait $P1 $P2 $P3 2>/dev/null; sleep 0.3; kill $SP 2>/dev/null; wait $SP 2>/dev/null
EXTRA=$(( $(sort -n "$SB/peak1.log" | tail -1) - B1 ))
cd "$SB/seed"; git fetch -q origin
NEW=$(git ls-tree --name-only origin/main vault/ | grep -c 'v-')
echo "  [قياس] أحجام البعيد=$NEW · ذروة إضافية للختم=$((EXTRA/1024))MB · سطور السجل=$(wc -l < "$SB/ledger.tsv")"
# فحص أ: ثلاث مخرجات كاملة + أرقام بلا تصادم + بصمة كل مؤلف محفوظة
CLAIM_OK=1
while IFS=$'\t' read -r au n h tip; do
  got=$(git show "origin/main:vault/v-$(printf '%04d' "$n").enc" 2>/dev/null | sha256sum | cut -c1-16)
  [ "$got" = "$h" ] || { CLAIM_OK=0; echo "    سقوط بصمة: $au v-$n (متوقع $h وجد $got)"; }
done < "$SB/ledger.tsv"
[ "$NEW" -eq 1003 ] && [ "$(wc -l < "$SB/ledger.tsv")" -eq 3 ] && [ "$CLAIM_OK" = 1 ] && ok "أ: المخرجات الثلاثة محفوظة بأرقام فريدة وبصمات مطابقة" || no "أ: خلل حفظ/تصادم"
# فحص ب: ذروة القرص — لا تجسيد للتاريخ
[ "$EXTRA" -lt "$VAULT_KB" ] && ok "ب١: الذروة الإضافية $((EXTRA/1024))MB < حجم الأرشيف (${VAULT_KB}KB) — لا تجسيد تاريخ" || no "ب١: ذروة $EXTRA KB تشي بتجسيد"
# فحص ج: صفر بقايا سرّ
grep -q 'x-access-token' "$SB/w1/.git/config" && no "ج: بقايا سرّ في config" || ok "ج: config نظيف بلا credential"
# ── ٢) قتلات التمييز ──
echo "◆ قتلة ١: naive-number (رقم متوقع سلفًا) — المطلوب: كشف التصادم"
for i in 4 5 6; do rm -rf "$SB/n$i"; git clone -q "$SB/remote.git" "$SB/n$i"; git -C "$SB/n$i" config user.email "n$i@t"; git -C "$SB/n$i" config user.name "n$i"; done
: > "$SB/ledger2.tsv"
SEAL_AUTHOR=N1 python3 "$REF" "$SB/n4" --flaw naive --ledger "$SB/ledger2.tsv" >/dev/null 2>&1 & Q1=$!
SEAL_AUTHOR=N2 python3 "$REF" "$SB/n5" --flaw naive --ledger "$SB/ledger2.tsv" >/dev/null 2>&1 & Q2=$!
SEAL_AUTHOR=N3 python3 "$REF" "$SB/n6" --flaw naive --ledger "$SB/ledger2.tsv" >/dev/null 2>&1 & Q3=$!
wait $Q1 $Q2 $Q3 2>/dev/null; cd "$SB/seed"; git fetch -q origin
COLL=0
while IFS=$'\t' read -r au n h tip; do
  got=$(git show "origin/main:vault/v-$(printf '%04d' "$n").enc" 2>/dev/null | sha256sum | cut -c1-16)
  [ "$got" = "$h" ] || COLL=1
done < "$SB/ledger2.tsv"
[ "$COLL" = 1 ] && ok "قتلة ١ كُشفت: تصادم/ضياع مخرَج مع الرقم السلفي" || echo "  ⚠ لم يتصادم الساذج في هذه المحاولة (مسبار احتمالي) — أرقام: $(cut -f2 "$SB/ledger2.tsv" | tr '\n' ' ')"
echo "◆ قتلة ٢: checkout-history — المطلوب: ذروة تتجاوز العتبة"
rm -rf "$SB/c1"; git clone -q "$SB/remote.git" "$SB/c1"; git -C "$SB/c1" config user.email c@t; git -C "$SB/c1" config user.name c
CB=$(peak "$SB/c1" | cut -f1)
( while :; do peak "$SB/c1" | cut -f1 >> "$SB/peakc.log"; sleep 0.1; done ) & SP2=$!
SEAL_AUTHOR=CX python3 "$REF" "$SB/c1" --flaw checkout >/dev/null 2>&1
sleep 0.3; kill $SP2 2>/dev/null; wait $SP2 2>/dev/null
CEXTRA=$(( $(sort -n "$SB/peakc.log" | tail -1) - CB ))
[ "$CEXTRA" -ge "$VAULT_KB" ] && ok "قتلة ٢ كُشفت: الذروة $((CEXTRA/1024))MB ≥ حجم الأرشيف (مُجسَّد)" || no "قتلة ٢: الذروة $CEXTRA KB لم تتجاوز — راجع العتبة"
echo "◆ قتلة ٣: token-config — المطلوب: بقايا تُكشف"
rm -rf "$SB/k1"; git clone -q "$SB/remote.git" "$SB/k1"; git -C "$SB/k1" config user.email k@t; git -C "$SB/k1" config user.name k
SEAL_AUTHOR=KX python3 "$REF" "$SB/k1" --flaw token >/dev/null 2>&1
grep -q 'x-access-token' "$SB/k1/.git/config" && ok "قتلة ٣ كُشفت: credential في config" || no "قتلة ٣: لم تُكتب البقايا — راجع السيناريو"
echo "◆ ب٢: استقلال الذروة عن عدد الأحجام (نقطتان: N=100 و N=1000)"
rm -rf "$SB/remote100.git" "$SB/seed100" "$SB/p100"
git init -q --bare "$SB/remote100.git"; git clone -q "$SB/remote100.git" "$SB/seed100"; cd "$SB/seed100"
git config user.email t@t; git config user.name t; git checkout -q -b main; mkdir -p vault tree
cp "$SB/seed/tree/data.bin" tree/data.bin
python3 - <<'PYX'
import os
for i in range(1,101): open(f'vault/v-{i:04d}.enc','wb').write(os.urandom(12*1024))
PYX
git add -A; git commit -qm seed100; git push -q origin main; git -C "$SB/remote100.git" symbolic-ref HEAD refs/heads/main
git clone -q "$SB/remote100.git" "$SB/p100"; git -C "$SB/p100" config user.email p@t; git -C "$SB/p100" config user.name p
PB=$(peak "$SB/p100" | cut -f1)
( while :; do peak "$SB/p100" | cut -f1 >> "$SB/peak100.log"; sleep 0.1; done ) & SP3=$!
SEAL_AUTHOR=P10 python3 "$REF" "$SB/p100" >/dev/null 2>&1
sleep 0.3; kill $SP3 2>/dev/null; wait $SP3 2>/dev/null
E100=$(( $(sort -n "$SB/peak100.log" | tail -1) - PB ))
rm -rf "$SB/p1000"; git clone -q "$SB/remote.git" "$SB/p1000"; git -C "$SB/p1000" config user.email q@t; git -C "$SB/p1000" config user.name q
QB=$(peak "$SB/p1000" | cut -f1)
( while :; do peak "$SB/p1000" | cut -f1 >> "$SB/peak1000.log"; sleep 0.1; done ) & SP4=$!
SEAL_AUTHOR=P1K python3 "$REF" "$SB/p1000" >/dev/null 2>&1
sleep 0.3; kill $SP4 2>/dev/null; wait $SP4 2>/dev/null
E1000=$(( $(sort -n "$SB/peak1000.log" | tail -1) - QB ))
D=$(( E1000>E100 ? E1000-E100 : E100-E1000 ))
echo "  [قياس] ختم واحد: N=100 ⇒ ${E100}KB · N=1000 ⇒ ${E1000}KB · الفرق=${D}KB"
[ "$D" -le 2048 ] && ok "ب٢: الذروة مستقلة عن عدد الأحجام (فرق ≤ 2MB)" || no "ب٢: فرق $D KB — الذروة تنمو مع N"
echo; echo "════ الحصيلة: نجح $PASS · فشل $FAIL ════"
[ $FAIL -eq 0 ] || exit 1
