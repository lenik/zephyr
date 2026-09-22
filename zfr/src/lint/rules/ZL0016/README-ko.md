# VERSION이 debian/changelog과 일치

### 단일 진실 공급원

`VERSION`은 최신 `debian/changelog` 항목과 일치해야 합니다. 표준 `.githooks/pre-commit`(`core.hooksPath=.githooks`와 함께)이 커밋 시 `VERSION`을 다시 씁니다.


### 동기화 훅이 설정된 경우

해당 pre-commit 훅이 있고 changelog에서 VERSION을 동기화하면, 다음 커밋까지의 일시적 불일치는 예상됩니다 — lint는 경고 대신 **ok**를 보고합니다.


### 훅이 없는 경우

불일치는 **warn**: VERSION을 손으로 맞추거나 `zfr ize`로 표준 훅을 설치한 뒤 `git config core.hooksPath .githooks`.
