# 소스의 하드코딩 FHS 설치 경로 (@DATADIR@ / configure_file 사용)

### 하드코딩된 /usr는 접두사를 깨뜨립니다

절대 FHS 경로(/usr/share, /usr/bin, …)는 DESTDIR, 비표준 접두사, Meson configure_file 스테이징에서 실패합니다.


### 권장 형태

스크립트는 @PREFIX@ / @DATADIR@ / @LOCALEDIR@(또는 동등물)을 쓰고 Meson을 통해 *.in에서 설치됩니다.


### Solve가 하는 일

Ize는 영향받는 스크립트를 *.in으로 이름 바꾸고 configure_file을 연결합니다. shebang과 실제 경로를 가정한 테스트를 다시 확인하세요.
