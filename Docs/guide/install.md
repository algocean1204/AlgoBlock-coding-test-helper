# AlgoBlock 설치와 실행

이 문서는 설치 파일을 내려받아 여는 법, 채점에 쓰는 언어 도구, 기록이 남는 곳을 설명한다.

## 내려받기

| 운영체제 | 파일 |
|---|---|
| macOS (Apple Silicon) | [AlgoBlock-macos-arm64.dmg](https://github.com/algocean1204/AlgoBlock-coding-test-helper/releases/latest/download/AlgoBlock-macos-arm64.dmg) |

dmg를 열면 `AlgoBlock.app`과 `Applications` 바로가기가 있다. `AlgoBlock.app`을 `Applications`로 끌어다 놓는다.

## 처음 여는 법

설치 파일은 서명하지 않았다. 처음 열 때 "열 수 없다"는 경고가 뜬다. 경고를 닫고 시스템 설정 → 개인정보 보호 및 보안 → '그래도 열기'를 누른다(macOS 14까지는 앱을 우클릭 → '열기'로도 된다). 한 번 열면 다음부터는 그냥 열린다.

## 업데이트

자동 확인이 켜져 있으면 GitHub 릴리스에서 새 버전이 나왔는지 하루에 한 번 본다. 앱을 켤 때 마지막 확인에서 24시간이 지났으면 보고, 그 뒤 24시간마다 본다. 확인하지 못하면(인터넷이 끊기는 등) 1시간 뒤에 다시 보고, 계속 안 되면 2시간, 4시간, 6시간 간격으로 다시 본다. 새 버전이 있으면 위쪽 막대에 '새 버전 x.y.z · 업데이트'가 뜬다. 확인하는 주소와 받은 파일을 검사하는 법은 [보안 구조](../architecture/security.md#업데이트)에 있다.

macOS 앱과 Windows 앱은 다음 순서로 바꾼다.

1. 막대의 '새 버전 x.y.z · 업데이트'를 누르고 '내려받기'를 누른다. 내려받는 진행률이 보인다.
2. 받은 파일이 릴리스에 적힌 값과 맞으면 '내려받고 파일이 맞는지 확인했어요'가 뜬다. 맞지 않으면 파일을 지우고 설치하지 않는다.
3. '다시 시작해 업데이트'를 누른다. 쓰던 코드를 저장하고 채점을 멈춘 뒤 앱을 끝내고, 새 버전으로 바꿔 다시 연다. 새 버전이 열리지 않으면 옛 버전으로 되돌려 연다. 되돌렸으면 다음에 업데이트 창에서 알려 준다.

- 앱이 있는 폴더에 쓸 수 없으면(관리자만 쓸 수 있는 곳. Windows의 Program Files 등) 바꾸지 않는다. 대신 받은 파일의 위치를 보여 주고, '파일 위치 열기'로 Finder나 탐색기에서 연다. macOS는 그 dmg를 열어, Windows는 앱을 끝낸 뒤 받은 exe로 지금 exe를 바꿔 직접 바꾼다.
- Windows에서 바꾸는 도중 컴퓨터가 꺼지는 등으로 멈춰 앱 exe가 없어지고 옆에 `.<앱 이름>.old`(옛 버전)나 `.<앱 이름>.new`(새 버전)만 남았다면, 그 파일의 이름을 앱 이름(예: `AlgoBlock.exe`)으로 바꾸면 된다.
- '이 버전 건너뛰기'를 누르면 그 버전은 막대에 뜨지 않는다. '연결' → '더 정하기' → '업데이트'의 '지금 확인'으로 다시 볼 수 있다.
- '지금 확인'은 하루 한 번의 일정과 상관없이 바로 본다.
- 자동 확인을 끄려면 '연결' → '더 정하기' → '업데이트'에서 '새 버전을 자동으로 확인하기'를 끈다. 끄면 켤 때도 하루마다도 묻지 않는다. '지금 확인'은 그대로 된다.
- 소스로 실행하면 새 버전을 확인만 하고 받지 않는다. 저장소에서 `git pull`로 받는다.

## 소스로 실행하기

저장소를 받아 `uv`로 실행할 수 있다. 명령과 환경 변수는 [개발 환경 만들기](../contributing/dev-setup.md)에 있다.

## 언어 도구

채점은 이 기기에 설치된 도구로 한다. 도구는 PATH에서 찾는다. 앱에는 채점용 도구가 들어 있지 않다. 채점용 Python도 마찬가지다.

| 언어 | 필요한 도구 |
|---|---|
| Python | Python 3. macOS·Linux는 `python3` → `python`, Windows는 `python` → `py` → `python3` 순서로 찾는다 |
| Java | JDK (`javac`, `java`) |
| Kotlin | Kotlin 컴파일러 `kotlinc`와 `java` |
| C++ | `g++` 또는 `clang++` 가운데 하나 (`-std=c++17 -O2`) |
| JavaScript | Node.js (`node`) |
| Go | Go (`go build`) |
| Rust | Rust (`rustc --edition 2021 -O`) |

도구는 있는지만 본다. 버전은 확인하지 않는다.

도구가 없으면 다음과 같이 된다.

- 채점하지 않는다. 언어 고르기 목록에 " · 도구 없음"이 붙지만 고를 수는 있다.
- '예시 실행', '제출', '이 값으로 실행' 단추가 잠긴다.
- 도구가 없어 채점하지 못한 제출은 제출 기록에 남지 않는다.
- '연결' → '더 정하기' → '언어 도구'에서 언어마다 "있음" 또는 "없음"을 볼 수 있다. '다시 확인'을 누르면 다시 센다.

묶은 macOS 앱은 기존 PATH 뒤에 다음 경로를 더해서 찾는다. Windows와 Linux에서는 PATH를 바꾸지 않는다.

- `/opt/homebrew/bin`, `/usr/local/bin`, `~/.pyenv/shims`, `~/.local/bin`, `~/.cargo/bin`, `/usr/local/go/bin`, `~/go/bin`
- Homebrew JDK `/opt/homebrew/opt/openjdk*/bin`과 nvm Node `~/.nvm/versions/node/*/bin`은 각각 이름 순으로 마지막 하나

## 기록이 남는 곳

설치한 macOS 앱의 기록과 키는 `~/Library/Application Support/AlgoBlock`에 남는다. 다른 실행 방식의 위치와 폴더 안의 파일은 [데이터 폴더](../architecture/data.md)에서 본다.

## 알려진 한계

- 내려받기 파일은 macOS Apple Silicon용 하나뿐이다.
- Windows는 실제 Windows PC에서 확인하지 않아 설치 파일을 내려받기 표에 두지 않았다.
- Linux용 설치 파일은 없다.
- 설치 파일은 서명과 공증을 하지 않았다. 처음 한 번은 위 '처음 여는 법'대로 연다.
- 창을 닫으면 진행 중인 채점을 멈추는 정리가 돈다. 메뉴의 '끝내기'로 끝내면 그 정리가 안 돌 수 있다.
