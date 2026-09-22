# سياسة arch لمصفوفة CI (debian armhf/v7؛ raspi armhf/v6؛ uos/kylin loong64)

Debian armhf يستخدم linux/arm/v7؛ raspi_* يستخدم linux/arm/v6. loong64 فقط لـ uos_*/kylin_*. قد يضيف Ubuntu i386/amd64v3؛ وأيضًا أقسام مصفوفة mingw/cygwin لبناءات Windows الأصلية.

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
