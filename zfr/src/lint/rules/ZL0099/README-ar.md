# سير عمل GitHub Actions لـ release-packages (مصفوفة Docker بلا تبعيات متداخلة)

توقّع .github/workflows/release-packages.yml يُطلق عند release published، مع مساعدات scripts/ci. تبعيات النظراء تستخدم scripts/ci/deps.conf وجلب تثبيت فقط (لا بناء متداخل أبدًا). مكوّن Apt هو main.

### {title}

القاعدة {id} (`{code}`) جزء من عقد تخطيط
packaging/ في zephyr. تلميح الشدة الافتراضي: {sev}.

### ماذا يفعل lint

{detail}
مُنفَّذ تحت `{code}` في `zfr lint`. تحمل النتائج
عند الإمكان نص إصلاح ملموس. أعد تعيين الشدة بـ
`-w` / `-e` / `--strict`.

### عند تغيير الشجرة

قد تمس الإصلاحات packaging أو meson.build أو المصادر أو نسخ
السقالات. قارن Maintainer و Depends و %files وسكربتات *.in قبل الرفع.
