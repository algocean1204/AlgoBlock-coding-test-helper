#!/bin/sh
# macOS·Linux에서 Windows 실행 파일(.exe)을 만든다. Docker 안의 Wine + Windows 파이썬으로 PyInstaller를 돌린다.
# 쓰는 법: sh app/packaging/build_win_docker.sh     결과: app/packaging/dist-win/AlgoBlock.exe (x86-64, 파일 하나)
# Windows PC가 있으면 build_win.ps1이 정식 길이다. 여기서 만든 파일은 창(WebView2)까지는 Wine에서 확인하지 못한다.
set -e
cd "$(dirname "$0")/../.."
mkdir -p app/packaging/dist-win
python3 app/tutor/knowledge/embed.py fetch app/packaging/models  # 임베딩 모델(약 250MB). 컨테이너는 소스를 읽기 전용으로 보므로 밖에서 받아 둔다
# numpy<2: numpy 2는 Wine에 없는 함수(ucrtbase crealf)를 불러 빌드 중 import가 죽는다. 진짜 Windows에서는 1.26도 그대로 돈다.
docker run --rm --platform linux/amd64 -e WINEDEBUG=-all -v "$PWD":/src:ro -v "$PWD/app/packaging/dist-win":/out tobix/pywine:3.12 bash -c '
  wine python -m pip install -q --disable-pip-version-check --no-warn-script-location pyinstaller langgraph pywebview qdrant-client pypdf onnxruntime tokenizers "numpy<2" &&
  cd /src/app/packaging &&
  wine python -m PyInstaller --noconfirm --clean --log-level ERROR --distpath "Z:\\out" --workpath "C:\\algoblockbuild" algoblock.spec'
cp app/packaging/dist-win/AlgoBlock.exe app/packaging/dist-win/AlgoBlock-windows-x64.exe  # 릴리스에 올리는 고정 이름의 사본
# 그 사본의 SHA-256을 build_win.ps1과 같은 이름·꼴로 적는다. 리눅스는 sha256sum, macOS는 shasum
cd app/packaging/dist-win
if command -v sha256sum >/dev/null; then sha256sum AlgoBlock-windows-x64.exe; else shasum -a 256 AlgoBlock-windows-x64.exe; fi > SHA256SUMS-windows-x64
ls -lh AlgoBlock.exe AlgoBlock-windows-x64.exe
cat SHA256SUMS-windows-x64
