## ZL0001

### 긴 파일은 소유를 방해합니다

매우 긴 소스는 검토·테스트·소유가 어렵습니다. Zephyr는 패키지 하위 응집 모듈과 얇은 진입점을 선호합니다.


### 개선 이점

더 작은 리뷰 diff, 명확한 경계, 쉬운 단위 테스트, 적은 머지 충돌.


### 임계값

비어 있지 않은 줄을 셉니다(build/debian/po/… 제외). ~600 note, ~1000 warn. 템플릿 예는 건너뜀.


### 수정은 수동

파일을 나누고 meson/install/import를 갱신. `zfr ize`는 자동 분할하지 않음.


## ZL0095
### 인라인 posync는 유지보수 불가

meson.build의 bash -euc heredoc은 템플릿마다 중복되고 디버그가 어렵습니다. 계약은 run_target('posync')의 `zfr translate --sync`.


### 이점

한 명령으로 xgettext/msgmerge. ninja posync는 짧게, CI는 `zfr translate --sync` 또는 import.


### Solve

ize가 posync를 translate --sync로 연결. 이후 POTFILES 확인.


## ZL0096
### 유지보수 스크립트는 scripts/

루트의 install-symlinks/deploy는 패키징 표면을 어지럽힙니다. 동기화·DESTDIR 미리보기는 `zfr translate --sync` / `zfr build --look`.


### 탐지

루트 *.sh와 외부화할 inline run_target을 표시.


### 이동 후

문서와 CI 갱신. Solve가 Meson을 scripts/… 또는 zfr로 재작성.
