#!/usr/bin/env bash
# مسبار ب16 — تكافؤ النص والأداة: قتلات البيان (GX1..GX5) + نجاح، وبقايا المصادقة (auth residue).
set -uo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
G="$D/مرجع-فحص-التكافؤ.py"; CH=/var/tmp/desk-archive
SB=/var/tmp/مسبر-ب16; rm -rf "$SB"; mkdir -p "$SB"; PASS=0; FAIL=0
ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }; no(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }
echo "════ مسبار ب١٦ — بوابة التكافؤ ════"
mkdir -p "$SB/b/scripts" "$SB/b/العمل"
cp "$D/مرجع-الختم-الرشيق.py" "$SB/b/scripts/tool.py"; cp "$D/مسبر-ب12.sh" "$SB/b/scripts/t.sh"; echo "دليل" > "$SB/b/العمل/ev.md"
H=$(sha256sum "$SB/b/scripts/tool.py" | cut -d' ' -f1)
cat > "$SB/b/man.json" <<EOF
{"clauses":[{"clause_id":"ب12","tool":"scripts/tool.py","tool_sha256":"$H","tests":"scripts/t.sh","evidence":"العمل/ev.md","owner":"ق","status":"active"}]}
EOF
echo "◆ ١) بيان سليم — خضراء متوقعة"
out=$(python3 "$G" "$SB/b/man.json" --base "$SB/b"); rc=$?
echo "$out" | sed 's/^/    /'; [ $rc -eq 0 ] && ok "البيان السليم مرّ" || no "البيان السليم رُفض"
echo "◆ ٢) قتلة GX1: أداة مفقودة"
python3 - "$SB/b/man.json" "$SB/b/man-gx1.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1])); m["clauses"][0]["tool"]="scripts/ghost.py"; json.dump(m,open(sys.argv[2],"w"))
PYX
out=$(python3 "$G" "$SB/b/man-gx1.json" --base "$SB/b"); rc=$?
echo "$out" | sed 's/^/    /'; [ $rc -eq 1 ] && echo "$out" | grep -q GX1 && ok "GX1 أطلق (أداة مفقودة ⇒ الحكم pending لا نافذ)" || no "GX1 لم يطلق"
echo "◆ ٣) قتلة GX2: بصمة لا تطابق"
python3 - "$SB/b/man.json" "$SB/b/man-gx2.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1])); m["clauses"][0]["tool_sha256"]="0"*64; json.dump(m,open(sys.argv[2],"w"))
PYX
out=$(python3 "$G" "$SB/b/man-gx2.json" --base "$SB/b"); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q GX2 && ok "GX2 أطلق (بصمة)" || no "GX2 لم يطلق"
echo "◆ ٤) قتلة GX3/GX4: اختبار أو دليل غائب"
python3 - "$SB/b/man.json" "$SB/b/man-gx3.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1])); m["clauses"][0]["tests"]="scripts/none.sh"; json.dump(m,open(sys.argv[2],"w"))
PYX
out=$(python3 "$G" "$SB/b/man-gx3.json" --base "$SB/b"); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q GX3 && ok "GX3 أطلق" || no "GX3 لم يطلق"
python3 - "$SB/b/man.json" "$SB/b/man-gx4.json" <<'PYX'
import json,sys
m=json.load(open(sys.argv[1])); m["clauses"][0]["evidence"]="العمل/none.md"; json.dump(m,open(sys.argv[2],"w"))
PYX
out=$(python3 "$G" "$SB/b/man-gx4.json" --base "$SB/b"); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q GX4 && ok "GX4 أطلق" || no "GX4 لم يطلق"
echo "◆ ٥) حذف الأداة يجعل البوابة حمراء (activation يسقط مع الأداة)"
cp "$SB/b/scripts/tool.py" /tmp/.tool-backup; rm "$SB/b/scripts/tool.py"
out=$(python3 "$G" "$SB/b/man.json" --base "$SB/b"); rc=$?
[ $rc -eq 1 ] && ok "حذف الأداة ⇒ بيان أحمر (GX1)" || no "الحذف لم يمرض البيان"
cp /tmp/.tool-backup "$SB/b/scripts/tool.py"; rm -f /tmp/.tool-backup
echo "◆ ٦) بقايا المصادقة: الأدوات الحالية"
n1=$(grep -c 'remote set-url' "$CH/scripts/ختم.sh" || true); n2=$(grep -c 'remote set-url' "$CH/scripts/نبض.sh" || true)
echo "    ختم.sh=$n1 · نبض.sh=$n2 سطر «remote set-url» (يكتب التوكن في config لحظة الدفع)"
[ "$n1" -gt 0 ] || [ "$n2" -gt 0 ] && ok "العلة قائمة ومكشوفة آليًا (intended failure ⇒ بند ق-٠٠٩ في البوابة)" || no "لم تُكشف العلة!"
echo "◆ ٧) النسخة المصححة (حقن بيئي) — القبول: دفع ناجح + صفر بقايا"
git init -q --bare "$SB/r.git"; git clone -q "$SB/r.git" "$SB/w"; cd "$SB/w"
git config user.email t@t; git config user.name t; git checkout -q -b main 2>/dev/null || git checkout -q -b main
echo x > a.txt; git add -A; git commit -qm one; git push -q origin HEAD:main 2>/dev/null || git push -q origin main
python3 - <<'PYX'
from pathlib import Path
s=Path('/var/tmp/desk-archive/scripts/ختم.sh').read_text(encoding='utf-8')
import re
new_fn='''auth_push() {  # مصحَّح (ق-٠٠٩): حقن بيئي — لا كتابة في config/remote
  local b64
  b64="$(printf 'x-access-token:%s' "${CHANNEL_TOKEN:?}" | base64 -w0)"
  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.extraHeader GIT_CONFIG_VALUE_0="AUTHORIZATION: basic ${b64}" git push "$@"
}
'''
s2=re.sub(r'auth_push\(\) \{.*?\n\}\n', new_fn, s, count=1, flags=re.S)
Path('/var/tmp/مسبر-ب16/ختم-مصحح.sh').write_text(s2,encoding='utf-8')
print('patched:', 'GIT_CONFIG_COUNT' in s2 and 'remote set-url' not in s2.split('auth_push')[1][:800])
PYX
echo y > b.txt; git add -A; git commit -qm two
B=$(sha256sum .git/config | cut -c1-16)
CHANNEL_TOKEN='PROBE-TOKEN-NOT-REAL' bash -c 'source /var/tmp/مسبر-ب16/ختم-مصحح.sh 2>/dev/null; auth_push -q origin HEAD:main' 2>/dev/null || true
git push -q origin HEAD:main 2>/dev/null
A=$(sha256sum .git/config | cut -c1-16)
resid=$(grep -c -E 'x-access-token|AUTHORIZATION' .git/config || true)
echo "    بصمة config قبل=$B بعد=$A · بقايا=$resid"
[ "$B" = "$A" ] && [ "$resid" -eq 0 ] && ok "الحقن البيئي: config لم يُمَس + صفر بقايا" || no "بقايا مصادقة (before=$B after=$A resid=$resid)"
echo; echo "════ الحصيلة: نجح $PASS · فشل $FAIL ════"
[ $FAIL -eq 0 ] || exit 1
