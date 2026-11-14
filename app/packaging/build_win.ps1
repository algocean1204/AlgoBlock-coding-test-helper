# Windows 실행 파일(.exe 하나)을 만든다. Windows에서만 돈다(PyInstaller는 다른 OS용을 만들지 못한다).
# 쓰는 법(PowerShell, uv 설치돼 있어야 함): powershell -ExecutionPolicy Bypass -File app\packaging\build_win.ps1
# 결과: app\packaging\dist\AlgoBlock.exe   화면은 WebView2(Windows 11 기본, Windows 10은 대부분 설치돼 있다)를 쓴다.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
uv venv -q --allow-existing --python 3.12 .build-venv
uv pip install -q --python .build-venv\Scripts\python.exe pyinstaller langgraph pywebview qdrant-client pypdf onnxruntime tokenizers
.build-venv\Scripts\python.exe ..\tutor\knowledge\embed.py fetch models  # 임베딩 모델(약 250MB). 이미 있으면 받지 않는다
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
.build-venv\Scripts\pyinstaller.exe --noconfirm --clean --log-level WARN algoblock.spec
Copy-Item dist\AlgoBlock.exe dist\AlgoBlock-windows-x64.exe  # 릴리스에 올리는 고정 이름의 사본
Get-Item dist\AlgoBlock.exe, dist\AlgoBlock-windows-x64.exe | Select-Object Name, Length
