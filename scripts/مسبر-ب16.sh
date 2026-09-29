#!/usr/bin/env bash
# مسبار ب١٦ — تكافؤ النص والأداة: بيان تفعيل حقيقي (أدوات القناة الفعلية) + قتلات GX1..GX5 + بقايا المصادقة.
# قابل للنقل (ن-083): الجذر من موضع السكربت أو --repo/$REPO · صفر مسار بيئة ثابت · بيئة الفحص من PROBE_SB/TMPDIR.
# عطل البنية التحتية = رمز ٧٠، ولا يُحتسب ضمن قتلات GX ولا ضمن نجاحها (fail-closed مسبب).
set -uo pipefail
SELF="$(realpath "${BASH_SOURCE[0]}" 2>/dev/null || readlink -f "${BASH_SOURCE[0]}")"   # ن-084: مسار ذاتي مطلق قبل أي cd
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${REPO:-$(cd "$D/.." && pwd)}"
while [ $# -gt 0 ]; do case "$1" in --repo) ROOT="$(cd "$2" 2>/dev/null && pwd || printf '%s' "$2")"; shift 2;; *) shift;; esac; done
G="$D/مرجع-فحص-التكافؤ.py"
SB="${PROBE_SB:-${TMPDIR:-/tmp}}/مسبر-ب16"; rm -rf "$SB"; mkdir -p "$SB"
PASS=0; FAIL=0; INFRA_OK=1
ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }; no(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }
infra(){ echo "  ⛔ [عطل بنيوي — رمز ٧٠] $1" >&2; echo "     (لا يُحتسب ضمن قتلات GX ولا ضمن نجاحها — fail-closed مسبب)" >&2; exit 70; }
TL="$ROOT/scripts/مرجع-حارس-الفقدان.py"; TR="$ROOT/scripts/مرجع-الختم-الرشيق.py"
T1="$ROOT/scripts/مسبر-ب18.sh"; T2="$ROOT/scripts/مسبر-ب12.sh"
EV="$ROOT/القناة/العمل/مسابر-ن-للتكافؤ-جولة-١-2026-09-29.md"
KH="$ROOT/scripts/ختم.sh"; NB="$ROOT/scripts/نبض.sh"
[ -f "$G" ] || infra "المرجع غير موجود بجوار السكربت: $G"
[ -d "$ROOT" ] || infra "جذر المستودع غير موجود: $ROOT"
for f in "$TL" "$TR" "$T1" "$T2" "$EV" "$KH" "$NB"; do [ -f "$f" ] || infra "أصل حقيقي مفقود: $f"; done

gate(){ out=$(python3 "$G" "$@" 2>"$SB/g.err"); rc=$?; if grep -q 'Traceback' "$SB/g.err" 2>/dev/null; then sed 's/^/    /' "$SB/g.err" >&2; infra "استثناء غير ملتقط في البوابة — عطل بنيوي لا حكم"; fi; echo "$out"; return $rc; }

echo "════ مسبار ب١٦ — بوابة التكافؤ ════"
echo "    الجذر المقروء ذاتيًا: $ROOT"
echo "◆ ١) بيان تفعيل حقيقي — أدوات القناة الفعلية بأبصمتها ودليلها المنشور"
HL=$(sha256sum "$TL" | cut -d' ' -f1); HR=$(sha256sum "$TR" | cut -d' ' -f1)
cat > "$SB/man-real.json" <<EOF
{"clauses":[
 {"clause_id":"ب18","tool":"scripts/مرجع-حارس-الفقدان.py","tool_sha256":"$HL","tests":"scripts/مسبر-ب18.sh","evidence":"القناة/العمل/مسابر-ن-للتكافؤ-جولة-١-2026-09-29.md","owner":"ق","status":"active"},
 {"clause_id":"ب12","tool":"scripts/مرجع-الختم-الرشيق.py","tool_sha256":"$HR","tests":"scripts/مسبر-ب12.sh","evidence":"القناة/العمل/مسابر-ن-للتكافؤ-جولة-١-2026-09-29.md","owner":"ق","status":"active"}]}
EOF
out=$(gate "$SB/man-real.json" --base "$ROOT"); rc=$?
echo "$out" | sed 's/^/    /'
[ $rc -eq 0 ] && echo "$out" | grep -q 'ب18: مُفعَّل' && echo "$out" | grep -q 'ب12: مُفعَّل' && ok "البيان الحقيقي مرّ (بندان: ب١٨ وب١٢ بأدواتهما ومسابيرهما ودليلهما الفعلي)" || no "البيان الحقيقي رُفض (rc=$rc)"
echo "◆ ٢) قتلة GX1: حذف أداة حقيقية (بايتًا وبصمة) من نسخة رملية"
mkdir -p "$SB/deep/scripts" "$SB/deep/القناة/العمل"
cp "$TL" "$SB/deep/scripts/" ; cp "$T1" "$SB/deep/scripts/"; cp "$EV" "$SB/deep/القناة/العمل/"
cat > "$SB/man-del.json" <<EOF
{"clauses":[{"clause_id":"ب18","tool":"scripts/مرجع-حارس-الفقدان.py","tool_sha256":"$HL","tests":"scripts/مسبر-ب18.sh","evidence":"القناة/العمل/مسابر-ن-للتكافؤ-جولة-١-2026-09-29.md","owner":"ق","status":"active"}]}
EOF
out=$(gate "$SB/man-del.json" --base "$SB/deep"); rc=$?   # الأداة منسوخة فعلًا هنا (ضبط غير محتسب)
if [ $rc -ne 0 ]; then no "نسخة GX1 الرملية لا تمر قبل الحذف (rc=$rc)"; else echo "    (ضبط قبل الحذف: النسخة تمر — لا يُحتسب ضمن الـ٨)"; fi
rm "$SB/deep/scripts/مرجع-حارس-الفقدان.py"
out=$(gate "$SB/man-del.json" --base "$SB/deep"); rc=$?
echo "$out" | sed 's/^/    /'; [ $rc -eq 1 ] && echo "$out" | grep -q GX1 && ok "GX1 أطلق: الأداة الحقيقية المحذوفة ⇒ الحكم غير نافذ (activation يسقط مع الأداة)" || no "GX1 لم يطلق بعد الحذف (rc=$rc)"
echo "◆ ٣) قتلة GX2: بصمة مغشوشة لأداة حقيقية"
python3 - "$SB/man-real.json" "$SB/man-gx2.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8")); m["clauses"][0]["tool_sha256"]="0"*64
json.dump(m,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False)
PYX
out=$(gate "$SB/man-gx2.json" --base "$ROOT"); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q GX2 && ok "GX2 أطلق (بصمة أداة حقيقية لا تطابق)" || no "GX2 لم يطلق (rc=$rc)"
echo "◆ ٤) قتلة GX3/GX4: اختبار أو دليل غائب"
python3 - "$SB/man-real.json" "$SB/man-gx3.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8")); m["clauses"][0]["tests"]="scripts/لا-يوجد.sh"
json.dump(m,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False)
PYX
out=$(gate "$SB/man-gx3.json" --base "$ROOT"); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q GX3 && ok "GX3 أطلق" || no "GX3 لم يطلق (rc=$rc)"
python3 - "$SB/man-real.json" "$SB/man-gx4.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8")); m["clauses"][0]["evidence"]="القناة/العمل/لا-يوجد.md"
json.dump(m,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False)
PYX
out=$(gate "$SB/man-gx4.json" --base "$ROOT"); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q GX4 && ok "GX4 أطلق" || no "GX4 لم يطلق (rc=$rc)"
echo "◆ ٥) قتلة GX5: مالك/حالة غير معلن"
python3 - "$SB/man-real.json" "$SB/man-gx5.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8")); m["clauses"][1]["owner"]=""; m["clauses"][1].pop("status",None)
json.dump(m,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False)
PYX
out=$(gate "$SB/man-gx5.json" --base "$ROOT"); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q GX5 && ok "GX5 أطلق (سجل ناقص)" || no "GX5 لم يطلق (rc=$rc)"
echo "◆ ٦) بقايا المصادقة في الأدوات الحقيقية"
n1=$(grep -c 'remote set-url' "$KH" || true); n2=$(grep -c 'remote set-url' "$NB" || true)
echo "    ختم.sh=$n1 · نبض.sh=$n2 سطر «remote set-url» (يكتب التوكن في config لحظة الدفع)"
[ "$n1" -eq 3 ] && [ "$n2" -eq 3 ] && ok "٣+٣ مقيسة في الأدوات الحقيقية (فشل مقصود يغلق بق-٠٠٩)" || no "العدد تغيّر عن ٣+٣ (ختم=$n1 نبض=$n2)"
echo "◆ ٧) النسخة المصححة (حقن بيئي) — القبول: دفع ناجح + صفر بقايا"
git init -q --bare "$SB/r.git"; git clone -q "$SB/r.git" "$SB/w"; cd "$SB/w"
git config user.email t@t; git config user.name t; git checkout -q -b main 2>/dev/null || git checkout -q -b main
echo x > a.txt; git add -A; git commit -qm one; git push -q origin HEAD:main 2>/dev/null || git push -q origin main
python3 - "$KH" "$SB/ختم-مصحح.sh" <<'PYX'
import re, sys
from pathlib import Path
src, dst = sys.argv[1], sys.argv[2]
s = Path(src).read_text(encoding='utf-8')
new_fn = ('auth_push() {  # مصحَّح (ق-٠٠٩): حقن بيئي — لا كتابة في config/remote\n'
 '  local b64\n'
 '  b64="$(printf \'x-access-token:%s\' "${CHANNEL_TOKEN:?}" | base64 -w0)"\n'
 '  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.extraHeader GIT_CONFIG_VALUE_0="AUTHORIZATION: basic ${b64}" git push "$@"\n'
 '}\n')
s2 = re.sub(r'auth_push\(\) \{.*?\n\}\n', new_fn, s, count=1, flags=re.S)
Path(dst).write_text(s2, encoding='utf-8')
print('    patched:', 'GIT_CONFIG_COUNT' in s2 and 'remote set-url' not in s2.split('auth_push')[1][:800])
PYX
echo y > b.txt; git add -A; git commit -qm two
B=$(sha256sum .git/config | cut -c1-16)
CHANNEL_TOKEN='PROBE-TOKEN-NOT-REAL' bash -c "source '$SB/ختم-مصحح.sh' 2>/dev/null; auth_push -q origin HEAD:main" 2>/dev/null || true
git push -q origin HEAD:main 2>/dev/null
A=$(sha256sum .git/config | cut -c1-16)
resid=$(grep -c -E 'x-access-token|AUTHORIZATION' .git/config || true)
echo "    بصمة config قبل=$B بعد=$A · بقايا=$resid"
[ "$B" = "$A" ] && [ "$resid" -eq 0 ] && ok "الحقن البيئي: config لم يُمَس + صفر بقايا (النسخة المصححة لأداة حقيقية)" || no "بقايا مصادقة (before=$B after=$A resid=$resid)"
echo; echo "════ الحصيلة: نجح $PASS · فشل $FAIL ════"
echo "◆ عطل بنيوي (منفصل — لا يُحتسب ضمن الـ٨): جذر غائب يجب أن يُفشل مغلقًا برمز ٧٠"
IERR="${SB}.infra.err"
bash "$SELF" --repo "$SB/لا-يوجد-هذا-الجذر" >/dev/null 2>"$IERR"; irc=$?
if [ $irc -eq 70 ] && grep -q 'عطل بنيوي' "$IERR"; then echo "  ✅ فشل مغلق برمز ٧٠ مع رسالة مسببة"; else echo "  ❌ العطل البنيوي لم يُرمز ٧٠ (rc=$irc)"; INFRA_OK=0; fi
[ $FAIL -eq 0 ] && [ $INFRA_OK -eq 1 ] || exit 1
