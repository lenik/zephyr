# VERSION يطابق debian/changelog

### مصدر حقيقة واحد

يجب أن يطابق `VERSION` أحدث إدخال في `debian/changelog`. يعيد `.githooks/pre-commit` القياسي (مع `core.hooksPath=.githooks`) كتابة `VERSION` عند الالتزام.


### عند ضبط خطاف مزامنة

إن وُجد خطاف pre-commit ذلك ويُزامن VERSION من سجل التغييرات، فعدم التطابق المؤقت حتى الالتزام التالي متوقع — يُبلّغ lint بـ **ok** بدل التحذير.


### عند عدم ضبط خطاف

عدم التطابق **warn**: وافق VERSION يدويًا أو ثبّت الخطاف القياسي عبر `zfr ize`، ثم `git config core.hooksPath .githooks`.
