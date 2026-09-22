# posync run_target is externalized as scripts/posync.sh

### posync المضمّن غير قابل للصيانة

heredoc من bash -euc داخل meson.build يتكرر ويصعب تنقيحه. العقد: `zfr translate --sync` من run_target('posync').


### الفائدة

أمر واحد يزامن xgettext/msgmerge؛ يبقى ninja posync قصيرًا؛ يمكن لـ CI استدعاء `zfr translate --sync` أو الاستيراد.


### Solve

يعيد ize ربط posync بـ translate --sync. تحقق من POTFILES بعدها.
