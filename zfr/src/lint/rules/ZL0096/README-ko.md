# 빌드/배포/유지보수 스크립트가 scripts/ 아래에 있음

루트 수준 *.sh 헬퍼와 look / install-symlinks / uninstall-symlinks / posync / deploy용 meson run_target 본문은 scripts/에 있어야 합니다. 옮기고 다시 연결하려면 `zfr ize`를 실행하세요.

### 유지보수 스크립트는 scripts/ 아래

저장소 루트의 install-symlinks / deploy 헬퍼는 패키징 표면을 어지럽힙니다. Zephyr는 그것들을 scripts/에 둡니다. 카탈로그 동기화와 DESTDIR 미리보기는 가능하면 맞춤 posync.sh/look.sh 대신 `zfr translate --sync`와 `zfr build --look`입니다.


### 탐지

루트 *.sh 유지보수 이름과 외부화하거나 zfr 하위 명령으로 바꿔야 할 인라인 run_target 본문에 표시합니다.


### 이동 후

문서와 옛 경로를 호출하던 CI를 갱신하세요. Solve는 Meson run_target을 scripts/… 또는 zfr translate/build로 다시 씁니다.
