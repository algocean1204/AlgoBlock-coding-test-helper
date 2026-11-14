# Windows 실행 파일(.exe 하나)을 만든다. Windows에서만 돈다(PyInstaller는 다른 OS용을 만들지 못한다).
# 쓰는 법(PowerShell, uv 설치돼 있어야 함): powershell -ExecutionPolicy Bypass -File app\packaging\build_win.ps1
# 결과: app\packaging\dist\AlgoBlock.exe와 릴리스에 올리는 고정 이름의 사본 AlgoBlock-windows-x64.exe
# 그 사본의 SHA-256을 dist\SHA256SUMS에 적는다(macOS와 같은 꼴. 앱의 업데이트가 받은 파일을 이 값과 견준다. 릴리스에 함께 올린다)
# 화면은 WebView2(Windows 11 기본, Windows 10은 대부분 설치돼 있다)를 쓴다.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
# 바깥 명령(uv, python, pyinstaller)은 실패해도 PowerShell이 멈추지 않는다: 종료 코드를 보고 멈춘다
uv venv -q --allow-existing --python 3.12 .build-venv
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv pip install -q --python .build-venv\Scripts\python.exe pyinstaller langgraph pywebview qdrant-client pypdf onnxruntime tokenizers
if ($LASTEXITCODE) { exit $LASTEXITCODE }
.build-venv\Scripts\python.exe ..\tutor\knowledge\embed.py fetch models  # 임베딩 모델(약 250MB). 이미 있으면 받지 않는다
if ($LASTEXITCODE) { exit $LASTEXITCODE }
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
.build-venv\Scripts\pyinstaller.exe --noconfirm --clean --log-level WARN algoblock.spec
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$Release = "AlgoBlock-windows-x64.exe"
Copy-Item dist\AlgoBlock.exe "dist\$Release"  # 릴리스에 올리는 고정 이름의 사본
$Hash = (Get-FileHash "dist\$Release" -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText((Join-Path $PSScriptRoot "dist\SHA256SUMS"), "$Hash  $Release`n")  # '<해시>  <파일 이름>' 한 줄, UTF-8(BOM 없음), LF
Get-Item dist\AlgoBlock.exe, "dist\$Release" | Select-Object Name, Length
Get-Content dist\SHA256SUMS
