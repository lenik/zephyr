# posync run_target이 scripts/posync.sh로 외부화됨

po/가 있으면 meson.run_target('posync')는 인라인 bash -euc heredoc이 아니라 scripts/posync.sh를 호출해야 합니다. 추출하려면 `zfr ize`를 실행하세요.

### 인라인 posync는 유지 불가합니다

meson.build 안의 bash -euc heredoc은 템플릿마다 중복되고 디버그가 고통스럽습니다. 계약은 run_target('posync')에서 연결된 `zfr translate --sync`(Python)이며, 인라인 heredoc이 아닙니다.


### 이득

한 명령으로 xgettext/msgmerge를 로컬 동기화; ninja posync는 짧게 유지; CI는 `zfr translate --sync`를 호출하거나 `translate.sync`를 import할 수 있습니다.


### Solve

Ize는 run_target('posync')를 프로젝트 Python 진입점을 통해 translate --sync를 호출하도록 다시 씁니다(zfr 안에서는 import 우선). 이후 POTFILES와 언어 플래그를 확인하세요.
