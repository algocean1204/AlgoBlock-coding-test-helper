# packaging: 설치 파일 만들기

화면(`app/ui`), 튜터(`app/tutor`), 모델 연결(`app/llm`), 채점기(`app/judge`)를 PyInstaller로 한 묶음으로 만든다. 기기 안 임베딩 모델(multilingual-e5-small)도 같이 넣는다.

받은 사람이 앱을 여는 법은 [Docs/guide/install.md](../../Docs/guide/install.md)에 있다. 이 문서는 빌드하는 사람을 위한 것이다.

설치 파일과 모델 파일은 저장소에 넣지 않는다(이 폴더의 `.gitignore`).

## 파일

| 파일 | 하는 일 |
| --- | --- |
| `launcher.py` | 시작점. 묶였을 때(`sys.frozen`) 데이터 폴더, 화면 폴더, 채점기 폴더, 임베딩 모델 폴더를 환경 변수로 넘긴다. 기본은 창을 열고 `--server`를 주면 서버만 띄운다. `--check-embed`는 묶은 모델을 한 번 돌려 본다 |
| `algoblock.spec` | PyInstaller 설정. macOS는 `.app`, Windows는 `onefile` `.exe`를 만든다. `models/`의 `model.onnx`와 `tokenizer.json`이 없으면 여기서 멈춘다 |
| `build_mac.sh` | macOS 빌드. 모델을 받고, `.app`을 `.dmg`로 싸고, 릴리스용 사본의 해시 파일(`SHA256SUMS-macos-<아키텍처>`)을 만든다 |
| `build_win.ps1` | Windows PC에서 하는 빌드(정식 길). 모델을 받고, 릴리스용 사본의 해시 파일(`SHA256SUMS-windows-x64`)을 만든다 |
| `build_win_docker.sh` | macOS·Linux에서 Docker로 하는 Windows 빌드(Wine + Windows 파이썬 3.12). 모델은 밖에서 받아 둔다 |
| `icon/` | 앱 아이콘(`icon.icns`, `icon.ico`)과 그것을 만드는 `make_icon.py` |
| `models/` | 빌드 때 받는 임베딩 모델 폴더. 저장소에 넣지 않는다 |
| `.gitignore` | `build/`, `dist/`, `.build-venv/`, `dist-win/`, `models/`를 막는다 |

## 빌드

### 모델 받기 (모든 빌드 공통)

빌드 스크립트가 빌드 전에 `embed.py fetch`로 `app/packaging/models`에 모델을 받는다. 이미 있으면 받지 않는다.

- 받는 것: `model.onnx`(반정밀 fp16)와 `tokenizer.json`. 합계 약 250MB다.
- 받을 때 크기와 SHA-256을 확인한다. 다르면 지우고 멈춘다.
- 직접 받을 때: `cd app && python3 tutor/knowledge/embed.py fetch packaging/models`

### macOS

```bash
sh app/packaging/build_mac.sh
```

- 결과: `app/packaging/dist/AlgoBlock-<버전>-<아키텍처>.dmg`와 그 사본 `app/packaging/dist/AlgoBlock-macos-<아키텍처>.dmg`. 아키텍처는 `uname -m`의 값(`arm64` 또는 `x86_64`)이다.
- 릴리스에 올리는 파일은 고정 이름의 사본(`AlgoBlock-macos-arm64.dmg`, `AlgoBlock-macos-x86_64.dmg`)이다.
- `app/packaging/dist/SHA256SUMS-macos-<아키텍처>`에 그 사본의 SHA-256이 한 줄(`<해시>  <파일 이름>`) 적힌다. 릴리스에 올리는 법은 아래 [릴리스의 SHA256SUMS](#릴리스의-sha256sums)에 있다.
- 안의 앱: `app/packaging/dist/AlgoBlock.app`
- 빌드하는 맥의 아키텍처로만 만든다. Intel 맥용은 Intel 맥에서 빌드한다.
- 서명과 공증은 없다.

### Windows, Windows PC에서

PowerShell에서 uv가 설치된 상태로 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File app\packaging\build_win.ps1
```

- 결과: `app\packaging\dist\AlgoBlock.exe`와 그 사본 `app\packaging\dist\AlgoBlock-windows-x64.exe`. 릴리스에 올리는 파일은 사본이다.
- `app\packaging\dist\SHA256SUMS-windows-x64`에 사본의 SHA-256이 macOS와 같은 꼴로 한 줄(`<해시>  AlgoBlock-windows-x64.exe`) 적힌다.
- `uv`, `python`, `pyinstaller`가 실패하면 그 종료 코드로 멈춘다. 이 명령들이 표준 오류에 쓰는 경고로는 멈추지 않는다.
- 화면은 WebView2를 쓴다.

### Windows, 맥·리눅스에서 Docker로

Docker가 필요하다. 이미지 `tobix/pywine:3.12`를 linux/amd64로 실행하므로 Apple Silicon에서는 에뮬레이션된다.

```bash
sh app/packaging/build_win_docker.sh
```

- 결과: `app/packaging/dist-win/AlgoBlock.exe`(x86-64, 파일 하나)와 그 사본 `app/packaging/dist-win/AlgoBlock-windows-x64.exe`, 사본의 해시 파일 `app/packaging/dist-win/SHA256SUMS-windows-x64`(`build_win.ps1`과 같은 꼴).
- 컨테이너는 소스를 읽기 전용으로 보므로 모델은 밖에서 받아 `app/packaging/models`에 둔다.
- Wine 빌드에서만 `numpy<2`를 깐다. numpy 2는 Wine에 없는 함수를 불러 빌드 중 import가 죽는다.
- Wine에서 만든 파일이다. 정식 빌드는 `build_win.ps1`이다.

### 릴리스의 SHA256SUMS

앱의 업데이트(`app/ui/updater.py`)는 릴리스에서 `SHA256SUMS`라는 이름의 파일 하나를 읽는다. 받은 파일을 그 안의 줄과, GitHub이 주는 파일의 `digest`가 있으면 그 값과도 견준다. 다르거나 견줄 값이 없으면 설치하지 않는다.

빌드는 플랫폼마다 다른 이름(`SHA256SUMS-<플랫폼>`)으로 줄 하나를 쓴다. 그래서 여러 빌드의 결과를 한곳에 모아도 서로 덮어쓰지 않는다. 릴리스에 올리기 전에 이번 릴리스의 빌드가 낸 파일을 모두 모아 하나로 합치고, 합친 `SHA256SUMS`를 설치 파일과 함께 올린다.

```bash
cat SHA256SUMS-* > SHA256SUMS
```

- 올린 설치 파일마다 줄이 하나씩 있어야 한다. 줄이 없는 플랫폼의 업데이트는 '`SHA256SUMS`에 이 파일이 없어' 받지 않는다.
- `SHA256SUMS-<플랫폼>` 파일은 릴리스에 올리지 않아도 된다.

## 묶는 것과 빼는 것

묶는 것:

- 앱 자체의 파이썬 런타임(PyInstaller가 싣는다)
- 화면 파일(`ui` 폴더): `index.html`, `app.css`, `app.js`, 글꼴 `PretendardVariable.woff2`와 그 라이선스, 앱 아이콘 `icon.svg`, 탭 아이콘 `favicon.svg`, 처음 안내 데모 `tour-demos.js`·`tour-demos.css`
- 기본 문제 파일 `builtin.json`(화면 파일과 같은 `ui` 폴더에 든다)
- 서버 모듈 `server`, `window`와 서버가 불러오는 `casegen`, `casemake`, `problemkit`, `stubs`, `updater`. `server`·`window`·`casegen`은 `hiddenimports`에 있고, 나머지는 PyInstaller가 `server`의 import를 따라 싣는다
- 앱 아이콘: macOS는 `icon/icon.icns`, Windows는 `icon/icon.ico`
- `tutor` 패키지. 시험(`.tests`)과 eval 대부분을 뺀다. 남기는 것은 `tutor.eval.cli_client`, `tutor.eval.drive`, `tutor.eval.scenarios`다.
- `tutor/plan/guide.md`
- `app.llm`(모델 연결 `app/llm`. 저장소 루트를 경로에 넣어 이 이름으로 부른다)
- 채점기 `app/judge` 전체(묶음 안 `judge` 폴더. `.md` 파일과 `__pycache__`는 뺀다)
- langgraph와 `qdrant_client.local`
- 임베딩 모델 파일 둘(`models/model.onnx`, `models/tokenizer.json`)과 `onnxruntime`, `tokenizers`

빼는 것: tkinter, pytest, IPython, matplotlib, fastembed, `tutor.tests`.

- 임베딩은 onnxruntime과 tokenizers로 직접 돌린다(`tutor/knowledge/embed.py`).
- 채점에 쓰는 파이썬은 싣지 않는다. 채점기는 사용자 기기의 `python3`(Windows는 `python`, `py`, `python3` 순)을 부른다(`judge/python/runner.py`). 다른 언어의 컴파일러와 실행기도 사용자 기기의 것을 쓴다.
- 파이썬 UTF-8 모드 옵션(`X utf8`)을 켠다. Windows의 기본 인코딩에서 한글 입출력이 깨지지 않게 한다.

## 런처가 넘기는 환경 변수

| 변수 | 값 | 쓰는 곳 |
| --- | --- | --- |
| `ALGOBLOCK_UI_DATA` | 사용자 데이터 폴더 | `app/ui/server.py` |
| `ALGOBLOCK_UI_STATIC` | 묶음 안 `ui` 폴더 | `app/ui/server.py` |
| `ALGOBLOCK_JUDGE_DIR` | 묶음 안 `judge` 폴더 | `app/tutor/eval/drive.py`(`JUDGE_PATH`) |
| `ALGOBLOCK_EMBED_DIR` | 묶음 안 `models` 폴더 | `app/ui/server.py`의 `index()` → `tutor/knowledge/index.py`의 `open_index` |

이미 있는 값은 덮지 않는다(`setdefault`).

macOS에서는 `PATH` 뒤에 다음을 더한다. Finder에서 연 앱은 PATH가 짧아 채점용 파이썬과 컴파일러를 못 찾을 수 있기 때문이다. Windows는 이 보정을 하지 않는다.

- `/opt/homebrew/bin`, `/usr/local/bin`
- `~/.pyenv/shims`, `~/.local/bin`
- `~/.cargo/bin`(Rust), `/usr/local/go/bin`, `~/go/bin`(Go)
- `/opt/homebrew/opt/openjdk*/bin`(Homebrew JDK. 있으면 이름순 마지막 것 하나)
- `~/.nvm/versions/node/*/bin`(nvm Node. 있으면 이름순 마지막 것 하나)

데이터 폴더 위치는 `launcher.py`의 `data_dir`이 정한다. macOS는 `~/Library/Application Support/AlgoBlock`, Windows는 `%APPDATA%\AlgoBlock`, 그 밖은 `$XDG_DATA_HOME/AlgoBlock`(없으면 `~/.local/share/AlgoBlock`)이다. 들어 있는 파일은 [Docs/architecture/data.md](../../Docs/architecture/data.md)에 있다.

## 확인할 때: `--server`와 `--check-embed`

창 없이 서버만 띄워 화면을 브라우저로 본다.

```bash
# macOS
app/packaging/dist/AlgoBlock.app/Contents/MacOS/AlgoBlock --server
# Windows
app\packaging\dist\AlgoBlock.exe --server
```

띄운 뒤 `http://127.0.0.1:8791`을 연다. 포트는 `ALGOBLOCK_UI_PORT`로 바꾼다.

임베딩 모델이 묶였는지는 `--check-embed`로 본다. 묶은 모델을 한 번 돌려 이름, 차원, 벡터 길이의 제곱합을 찍는다.

```bash
# macOS
app/packaging/dist/AlgoBlock.app/Contents/MacOS/AlgoBlock --check-embed
# Windows
app\packaging\dist\AlgoBlock.exe --check-embed
```

정상이면 `intfloat/multilingual-e5-small@614241f/fp16 384 1.0`이 나온다.

## 알려진 한계

- 코드 서명과 공증이 없다.
- 창을 닫으면 `window.py`가 `server.stop_grading()`으로 돌던 채점 실행기를 끝낸다. 메뉴의 '끝내기'로 끝내면 `webview.start()`가 돌아오지 않아 이 정리가 돌지 않을 수 있다. 그때 남은 채점 실행기는 채점기의 CPU 시간 상한에서 멈춘다(POSIX). Windows에서는 앱 프로세스가 끝나며 채점기의 작업 객체 핸들이 닫혀 바로 끝난다.
- 창 모드는 포트(`ALGOBLOCK_UI_PORT`, 기본 8791)를 이미 다른 프로그램이 쓰고 있으면 서버를 새로 띄우지 않고 그 주소를 그대로 연다(`window.py`의 `serve`).

## 버전 바꾸기

- 버전은 `app/ui/updater.py`의 `VERSION` 한 곳(지금 `0.1.0`)에서 고친다. `algoblock.spec`은 이 값을 `CFBundleShortVersionString`에, `build_mac.sh`는 버전이 붙은 `.dmg` 파일 이름에 쓴다. 고정 이름의 사본에는 버전이 없다.
- 앱의 업데이트는 이 값과 릴리스 태그(`v<버전>`)를 숫자로 견준다. 태그와 이 값이 다르면 새 버전을 설치한 뒤에도 또 새 버전이 있다고 알린다. 그래서 바꿔 끼우기 전에 dmg 안 앱의 `CFBundleShortVersionString`이 태그와 같은지 본다.
- Windows: 파일 이름에 버전이 없다(`AlgoBlock.exe`, `AlgoBlock-windows-x64.exe`). 실행 파일에 버전 정보를 넣지 않는다.
