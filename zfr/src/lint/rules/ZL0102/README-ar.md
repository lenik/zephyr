# CI لـ RPM يطابق Build-Depends من Debian؛ رقع RPM فقط عبر %patch

عند تحويل Build-Depends من debian/control إلى rpmbuild، طبّق تعيينات تجريبية: bash-builtins → bash (يوفّر bash.pc). تعديلات المصدر الخاصة بـ RPM فقط تعيش في packaging/rpm/*.patch وتُطبَّق بـ PatchN + %autosetup/%patch (build-rpm ينسخها إلى SOURCES)؛ لا تُغيّر ملفات .pc النظام في الحاوية.

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
