#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""لينتر العموم (ب١٧) — مسودة مسبار ن (ن-082)، غير مفعّل حتى بيان ب١٦.
بوابة ١٦ نمطًا موحدة (إطار م١ ع١–ع١٠ + إضافات مسح م٢ الست) + allowlist هيكلي بالكتل والنطاقات
(core/profile/history) + عدّاد المساواة: صفوف سجل التعليل = الحوادث المنقولة من المتن.
الرموز: GP01..GP16 نمط · GPR1 إحالة لا تحل · GPR2 صف يتيم · GPR3 عدّاد عدم المساواة · GPC1..GPC4 cold-start بيئة.
الاستدعاء: gate <ملف> · pair <متن> <سجل> · coldstart <مجلد يحوي cs1..cs4>
"""
import json, os, re, sys

PATTERNS = [
 ("GP01", "مشروع/معلم مرقّم", r"مش[\s\-]?\d|مش[\s\-]?[٠-٩]+"),
 ("GP02", "تاريخ ميلادي في المتن", r"(?:20\d{2}|٢٠[٠-٩]{2})[-/][01]?\d[-/][0-3]?\d|يوم\s+القرار"),
 ("GP03", "إحالة ملف واقعة", r"(?:ق|توجيه|ج)[-ـ]?[٠-٩0-9]{2,3}\b"),
 ("GP04", "قياس حادثي", r"ثبت\s+بالتجربة|قياس\s+يوم|ست\s+ساعات|واقعة\s+مسجلة|أُثبت\s+بـ"),
 ("GP05", "معرّف واقعة/التزام", r"\bv[-ـ][٠-٩0-9]+\b|\b[0-9a-f]{8,40}\b|run[\s\-]?\d+"),
 ("GP06", "اسم مزود/منصة", r"GitHub|Arena|Supabase|Vercel|Postgres|GitLab|Slack|أرينا"),
 ("GP07", "شعار/استعارة منسوخة", r"القلب\s+النابض|الأكوا|تسليح|السلاح|عين\s+المراقب"),
 ("GP08", "عبارة زمنية حينية", r"\bاليوم\b|هذه\s+الجولة|حاليًا|(?:^|\s)الآن(?:\s|$)|غدًا|وقت\s+الكتابة"),
 ("GP09", "عبارة انتقال تاريخية", r"حتى\s+هذا\s+القرار|كان\s+كذا|سابقًا\s+كان|قبل\s+هذا\s+القرار"),
 ("GP10", "توكن/اعتماد في المتن", r"ghp_|sbp_|vcp_|sk-|miftah-|Bearer\s|AUTHORIZATION"),
 ("GP11", "رتبة ثابتة (cardinality)", r"(ثلاث|ثلاثة|أربع|أربعة|خمسة|ستة|سبعة)\s*(أدوار|وكلاء|مقاعد|أختام|ختم|واردات|دورات|إيقاظات|بيئات)"),
 ("GP12", "مسار محلي", r"/home/|/var/tmp|/tmp/|C:\\\\|\.git/"),
 ("GP13", "اعتماد يُكتب في ملف", r"remote\s+set-url|\.git/config|توكن.{0,12}(?:config|ملف)"),
 ("GP14", "اسم مقعد", r"(?:^|\s)م١(?:\s|$)|(?:^|\s)م٢(?:\s|$)|(?:^|\s)م٣(?:\s|$)|(?:^|\s)م٤(?:\s|$)"),
 ("GP15", "رابط تقني بمزود", r"(?:^|\s)SHA(?:\s|$)|(?:^|\s)git(?:\s|$)|GitHub\s+Actions|vault/|نبض/|checkout|blob"),
 ("GP16", "رقم حصة/سعة", r"\d+\s*(?:MB|GB|KB)|حصة|الحساب\s+المجاني|سعة\s+القرص"),
]
AGG = {"GP02": "incident_token_count", "GP03": "incident_token_count", "GP05": "incident_token_count",
       "GP04": "incident_token_count", "GP01": "incident_token_count", "GP10": "secret_token_count",
       "GP06": "brand_or_tool_binding", "GP15": "brand_or_tool_binding", "GP12": "path_binding",
       "GP13": "credential_binding", "GP14": "seat_binding", "GP11": "fixed_team_cardinality",
       "GP16": "quota_binding", "GP07": "metaphor_binding", "GP08": "deictic_time", "GP09": "historical_transition"}

def scope_lines(text):
    """allowlist هيكلي: كل كتلة لها نطاق (core افتراضيًا)؛ النطاق يُعلن بـ <!-- scope: ... -->"""
    scope, out = "core", []
    for i, line in enumerate(text.splitlines(), 1):
        m = re.search(r"<!--\s*scope:\s*(core|profile|history)", line)
        if m: scope = m.group(1); out.append((i, line, scope, None)); continue
        m = re.search(r"<!--\s*مسبب:\s*(.+?)\s*-->", line)
        out.append((i, line, scope, m.group(1) if m else None))
    return out

def gate(path):
    text = open(path, encoding="utf-8").read()
    hits, counts = [], {p[0]: 0 for p in PATTERNS}
    for i, line, scope, cause in scope_lines(text):
        if scope != "core": continue  # البروفايل والتعليل يحق لهما ما يُحظر على النواة
        for sym, name, rx in PATTERNS:
            if re.search(rx, line):
                if sym == "GP11" and cause:  # الاستثناء الوحيد: حد فصل سلطة مسبب بالخطر
                    continue
                counts[sym] += 1; hits.append((sym, name, i, line.strip()[:70]))
    aggs = {}
    for sym, n in counts.items(): aggs[AGG[sym]] = aggs.get(AGG[sym], 0) + n
    return counts, hits, aggs

def pair(core, ledger):
    bad = []
    ct = open(core, encoding="utf-8").read(); lt = open(ledger, encoding="utf-8").read()
    refs = re.findall(r"<!--\s*rationale:\s*(R-\d+)\s*-->", ct)
    rows = re.findall(r"^\|\s*(R-\d+)\s*\|", lt, re.M)
    dups = {r for r in refs if refs.count(r) > 1}
    for r in sorted(set(refs) - set(rows)): bad.append(("GPR1", r, "إحالة إلى تعليل غير موجود"))
    for r in sorted(set(rows) - set(refs)): bad.append(("GPR2", r, "صف تعليل يتيم (بلا حادثة منقولة تقابله)"))
    if len(refs) != len(rows) or dups: bad.append(("GPR3", "-", f"عدّاد عدم المساواة: إحالات={len(refs)} صفوف={len(rows)} تكرار={sorted(dups)}"))
    return len(refs), len(rows), bad

def coldstart(root):
    """الأربع: وكيل مفرد بلا git · متعدد خارج منصة الجولات · CI منظم · غير برمجي.
    المقيس: كل سؤال قرار يحل إلى حقل معلن في profile بيئته؛ وبلا profile لا يُحل (فشل مغلق)."""
    bad = []
    for k in range(1, 5):
        d = os.path.join(root, f"cs{k}")
        core, prof, qf = (os.path.join(d, f) for f in ("core.md", "profile.env.md", "questions.tsv"))
        if not os.path.isdir(d) or not os.path.exists(qf):
            bad.append((f"GPC{k}", d, "بيئة ناقصة")); continue
        g = gate(core)
        if any(g[0].values()): bad.append((f"GPC{k}", "core", "نواة البيئة لا تعبر بوابة العموم"))
        if not os.path.exists(prof):
            n = len([l for l in open(qf, encoding="utf-8") if l.strip()])
            bad.append((f"GPC{k}", "profile", f"بلا profile: {n} سؤال قرار غير قابل للحل (فشل مغلق)")); continue
        fields = set(re.findall(r"^\s*([a-z_]+)\s*:", open(prof, encoding="utf-8").read(), re.M))
        for j, line in enumerate(open(qf, encoding="utf-8"), 1):
            line = line.strip()
            if not line or line.startswith("#"): continue
            qid, need = (line.split("\t") + [""])[:2]
            if need and need not in fields:
                bad.append((f"GPC{k}", qid, f"حقل غير معلن في profile البيئة: {need}"))
    return bad

def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(2)
    c = sys.argv[1]
    if c == "gate":
        counts, hits, aggs = gate(sys.argv[2])
        for sym, name, i, txt in hits[:24]: print(f"  [{sym}] س{i} {name}: {txt}")
        for k in sorted(aggs): print(f"  {k}(core)={aggs[k]}")
        print("بوابة العموم: خضراء (صفر حظر في النواة)." if not hits else f"بوابة العموم: حمراء ({len(hits)} موضعًا).")
        sys.exit(0 if not hits else 1)
    if c == "pair":
        refs, rows, bad = pair(sys.argv[2], sys.argv[3])
        for s, r, m in bad: print(f"  [{s}] {r}: {m}")
        print(f"عدّاد المساواة: إحالات منقولة={refs} · صفوف تعليل={rows}")
        sys.exit(0 if not bad else 1)
    if c == "coldstart":
        bad = coldstart(sys.argv[2])
        for s, r, m in bad: print(f"  [{s}] {r}: {m}")
        print("cold-start الأربع: خضراء." if not bad else f"cold-start: حمراء ({len(bad)}).")
        sys.exit(0 if not bad else 1)
    print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
