#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مسبر ب١٧ — بوابة العموم والحرفية (ن-082). استدعاء: python3 مسبر-ب17.py"""
import subprocess, sys, os, shutil, re, tempfile
D = os.path.dirname(os.path.abspath(__file__)); REF = os.path.join(D, "لينتر-العموم.py")
ROOT = os.environ.get("REPO") or os.path.dirname(D)          # جذر المستودع من موضع السكربت — صفر مسار ثابت
if "--repo" in sys.argv: ROOT = sys.argv[sys.argv.index("--repo") + 1]
SB = os.path.join(os.environ.get("PROBE_SB", tempfile.gettempdir()), "مسبر-العموم")
shutil.rmtree(SB, ignore_errors=True); os.makedirs(SB)
P = F = 0
def ok(m): global P; P += 1; print(f"  ✅ {m}")
def no(m): global F; F += 1; print(f"  ❌ {m}")
def py(*a):
    r = subprocess.run([sys.executable, REF] + list(a), capture_output=True, text=True); return r.returncode, r.stdout + r.stderr
def w(p, s):
    p = os.path.join(SB, p); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(s)

CLEAN = """# نواة كونية — مثال نظيف
## مادة ١ — الحياة
لا تُفترض استمرارية عملية بعد حد حياة بيئتها. تُنشر الحالة عند انتقال مادي فقط، ويعلن Environment Profile نموذج الحياة.
## مادة ٢ — الحكم
لا يحكم إلا نص داخل الحزمة المعيارية بمعرّف وإصدارة وبصمة؛ وتفشل البوابة صاخبة عند تعذرها.
<!-- rationale: R-001 -->
## مادة ٣ — الفصل
تُفصل قدرات التأليف والتنفيذ والحكم بقدر الخطر؛ وعند الجمع يُعلن التعارض ويضاف تحقق مستقل.
<!-- scope: profile -->
مثال بيئة: يعمل على GitLab داخل /home/agent، وثلاثة أدوار في الفريق.
<!-- scope: core -->
## مادة ٤ — الحد المسبب
ثلاثة أدوار كحد فصل سلطة <!-- مسبب: فصل السلطة بالخطر يفرض حدًا أدنى --> عند المهام الحرجة.
<!-- rationale: R-002 -->
"""
w("core-clean.md", CLEAN)
rc, out = py("gate", f"{SB}/core-clean.md")
if rc == 0 and "خضراء" in out: ok("النواة النظيفة عبرت البوابة (صفر حظر) + نطاق profile سمح بالاسم والمسار والرتبة داخله")
else: no(f"النواة النظيفة رُفضت: rc={rc} {out.strip()[:200]}")

KILLS = [
 ("GP01", "تُنجز المهمة مش٩٤ بلا كتالوج."),
 ("GP02", "صدر القرار بتاريخ 2026-09-29 بعد مراجعة."),
 ("GP03", "التفصيل كما في ق-٠٠٩ المعتمد."),
 ("GP04", "ثبت بالتجربة ست ساعات أن الحل صالح."),
 ("GP05", "الواقعة v-٥١٨ أثبتت الاستمرارية."),
 ("GP06", "يرفع الأثر إلى GitHub كل انتقال."),
 ("GP07", "القلب النابض يمسك المناوبة."),
 ("GP08", "اليوم يبدأ الفريق التنفيذ."),
 ("GP09", "كان كذا حتى هذا القرار ثم تغير."),
 ("GP10", "المفتاح ghp_K9x مخزّن عند المشغل."),
 ("GP11", "ثلاثة أدوار للفريق بلا استثناء."),
 ("GP12", "يعيش المستودع في /var/tmp/desk."),
 ("GP13", "يجري remote set-url origin قبل الدفع."),
 ("GP14", "م٢ يوقع الإقفال بعد التحقق."),
 ("GP15", "يمنع checkout لأي تاريخ سابق."),
 ("GP16", "سعة القرص 20GB لكل بيئة."),
]
print("◆ قتلات الأنماط الستة عشر (لكل نمط صورة تُطلقه ورمز معلن)")
for sym, line in KILLS:
    w(f"kill-{sym}.md", CLEAN + "\n" + line + "\n")
    rc, out = py("gate", f"{SB}/kill-{sym}.md")
    if rc == 1 and sym in out: ok(f"{sym} أطلق على صورته")
    else: no(f"{sym} لم يطلق: rc={rc} {out.strip()[:140]}")

print("◆ العدّاد الآلي: صفوف سجل التعليل = الحوادث المنقولة")
CORE2 = "## حكم\nقاعدة مجردة مع مرجع تعليل <!-- rationale: R-001 --> ثم قاعدة أخرى <!-- rationale: R-002 -->\n"
w("pair/core.md", CORE2)
w("pair/ledger.md", "| R-001 | حادثة: قياس يوم القرار 285MB والقناة 273MB |\n| R-002 | حادثة: سقوط 271 صفًا عند الحجم 508 |\n")
rc, out = py("pair", f"{SB}/pair/core.md", f"{SB}/pair/ledger.md")
if rc == 0 and "إحالات منقولة=2 · صفوف تعليل=2" in out: ok("التساوي ٢=٢ أخضر")
else: no(f"التساوي: rc={rc} {out.strip()[:160]}")
w("pair/ledger-missing.md", "| R-001 | حادثة واحدة فقط |\n")
rc, out = py("pair", f"{SB}/pair/core.md", f"{SB}/pair/ledger-missing.md")
if rc == 1 and "GPR1" in out and "GPR3" in out: ok("GPR1+GPR3 أطلقا (صف مفقود ⇒ إحالة لا تحل وعدّاد غير متساوٍ)")
else: no(f"GPR1/3: rc={rc} {out.strip()[:160]}")
w("pair/ledger-orphan.md", "| R-001 | ح |\n| R-002 | ح |\n| R-009 | صف يتيم بلا حادثة |\n")
rc, out = py("pair", f"{SB}/pair/core.md", f"{SB}/pair/ledger-orphan.md")
if rc == 1 and "GPR2" in out: ok("GPR2 أطلق (صف يتيم)")
else: no(f"GPR2: rc={rc} {out.strip()[:160]}")
w("pair/core-dup.md", "## حكم\nقاعدة <!-- rationale: R-001 --> وأخرى <!-- rationale: R-001 -->\n")
rc, out = py("pair", f"{SB}/pair/core-dup.md", f"{SB}/pair/ledger-missing.md")
if rc == 1 and "GPR3" in out: ok("GPR3 أطلق (إحالة مكررة)")
else: no(f"GPR3: rc={rc} {out.strip()[:160]}")

print("◆ cold-start الأربع (وكيل مفرد بلا git · متعدد خارج المنصة · CI منظم · غير برمجي)")
ENVS = {
 "cs1": ("solo-no-vcs", {"mode": "solo-no-vcs", "state_path": "local-ledger.md", "evidence_form": "manual-hash", "handoff": "none"}),
 "cs2": ("multi-nonarena", {"mode": "multi-nonarena", "state_path": "shared-file", "evidence_form": "signed-note", "handoff": "declared-handoff"}),
 "cs3": ("regulated-ci", {"mode": "regulated-ci", "state_path": "pipeline-store", "evidence_form": "ci-artifact", "handoff": "pipeline-handoff"}),
 "cs4": ("non-software", {"mode": "non-software", "state_path": "case-file", "evidence_form": "documented-quote", "handoff": "review-handoff"}),
}
for k, (name, fields) in ENVS.items():
    w(f"{k}/core.md", CLEAN.replace("<!-- rationale: R-001 -->", "").replace("<!-- rationale: R-002 -->", ""))
    prof = "\n".join(f"{a}: {b}" for a, b in fields.items())
    w(f"{k}/profile.env.md", f"# بروفايل بيئة: {name}\n{prof}\n")
    qs = ["q_state\tstate_path", "q_evidence\tevidence_form", "q_handoff\thandoff"]
    w(f"{k}/questions.tsv", "\n".join(qs) + "\n")
rc, out = py("coldstart", SB)
if rc == 0: ok("الأربع خضراء: كل سؤال قرار يحل إلى حقل معلن في بروفايل بيئته")
else: no(f"coldstart: rc={rc} {out.strip()[:200]}")
for k in ENVS:
    shutil.move(f"{SB}/{k}/profile.env.md", f"{SB}/{k}/profile.env.hidden")
rc, out = py("coldstart", SB)
if rc == 1 and all(f"GPC{i}" in out for i in range(1, 5)) and "فشل مغلق" in out: ok("GPC1..GPC4 أطلقت جميعًا (بلا بروفايل: أسئلة القرار غير قابلة للحل ⇒ فشل مغلق)")
else: no(f"cold-start kills: rc={rc} {out.strip()[:200]}")

print("◆ قياس حقيقي على R2 (الفشل مقصود ومعلن — التنظيف عند ق)")
R2 = os.path.join(ROOT, "القناة/العمل/الدستور-٣٫٠-مسودة-R2-بعد-المراجعات-2026-09-29.md")
if not os.path.isfile(R2):
    print(f"  ⛔ [عطل بنيوي — رمز ٧٠] R2 غير موجود: {R2} (لا يُحتسب ضمن القتلات ولا النجاح — fail-closed)", file=sys.stderr)
    sys.exit(70)
if os.path.exists(R2):
    rc, out = py("gate", R2)
    aggs = dict(re.findall(r"^\s{2}([a-z_]+)\(core\)=(\d+)", out, re.M))
    top = ", ".join(f"{k}={v}" for k, v in sorted(aggs.items(), key=lambda x: -int(x[1]))[:5] if int(v))
    n = sum(int(v) for v in aggs.values())
    print(f"    R2: حمراء بـ{n} موضعًا — الأبرز: {top}")
    if rc == 1 and n > 0: ok("R2 رسبت في البوابة بأرقامها (فشل مقصود حتى نص ق النظيف)")
    else: no(f"قياس R2 غير متوقع: rc={rc}")
else: no("ملف R2 غير موجود")
print(f"\n════ حصيلة العموم: نجح {P} · فشل {F} ════")
sys.exit(1 if F else 0)
