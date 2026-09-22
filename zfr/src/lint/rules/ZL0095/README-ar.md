# run_target الخاص بـ posync مُخرَج كـ scripts/posync.sh

عند وجود po/ يجب أن يستدعي meson.run_target('posync') ملف scripts/posync.sh بدل heredoc لـ bash -euc مضمّن. شغّل `zfr ize` للاستخراج.

### posync المضمّن غير قابل للصيانة

heredoc لـ bash -euc داخل meson.build يتكرر عبر القوالب ويصعب تصحيحه. العقد هو `zfr translate --sync` (Python) موصول من run_target('posync')، لا heredoc مضمّن.


### العائد

أمر واحد يزامن xgettext/msgmerge محليًا؛ يبقى ninja posync قصيرًا؛ يمكن لـ CI استدعاء `zfr translate --sync` أو استيراد `translate.sync`.


### Solve

Ize يعيد كتابة run_target('posync') لاستدعاء translate --sync عبر مدخل Python للمشروع (استيراد أولًا داخل zfr). تحقق بعد ذلك من POTFILES وأعلام اللغة.
