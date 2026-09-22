# Build/deploy/maintenance scripts live under scripts/

### 유지보수 스크립트는 scripts/

루트의 install-symlinks/deploy는 패키징 표면을 어지럽힙니다. 동기화·DESTDIR 미리보기는 `zfr translate --sync` / `zfr build --look`.


### 탐지

루트 *.sh와 외부화할 inline run_target을 표시.


### 이동 후

문서와 CI 갱신. Solve가 Meson을 scripts/… 또는 zfr로 재작성.
