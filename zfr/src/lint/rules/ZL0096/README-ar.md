# نصوص البناء/النشر/الصيانة تقع تحت scripts/

مساعدات *.sh على الجذر وأجسام meson run_target لـ look / install-symlinks / uninstall-symlinks / posync / deploy تنتمي إلى scripts/. شغّل `zfr ize` للنقل وإعادة التوصيل.

### سكربتات الصيانة تحت scripts/

مساعدات install-symlinks / deploy على جذر المستودع تشوّش سطح التعبئة. يبقيها Zephyr تحت scripts/. مزامنة الكتالوج ومعاينة DESTDIR هما `zfr translate --sync` و `zfr build --look` بدل posync.sh/look.sh المخصّصة عند الإمكان.


### الاكتشاف

يعلّم أسماء *.sh للصيانة على الجذر وأجسام run_target المضمّنة التي يجب إخراجها أو استبدالها بأوامر zfr الفرعية.


### بعد النقل

حدّث الوثائق وأي CI استدعى المسارات القديمة. Solve يعيد كتابة أهداف Meson run_target إلى scripts/… أو zfr translate/build.
