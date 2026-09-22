# posync run_target is externalized as scripts/posync.sh

### 인라인 posync는 유지보수 불가

meson.build의 bash -euc heredoc은 템플릿마다 중복되고 디버그가 어렵습니다. 계약은 run_target('posync')의 `zfr translate --sync`.


### 이점

한 명령으로 xgettext/msgmerge. ninja posync는 짧게, CI는 `zfr translate --sync` 또는 import.


### Solve

ize가 posync를 translate --sync로 연결. 이후 POTFILES 확인.
