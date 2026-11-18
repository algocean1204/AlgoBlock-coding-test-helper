# PyInstaller 설정. 화면(app/ui) + 튜터(app/tutor) + 모델 연결(app/llm) + 채점기(app/judge)를 하나로 묶는다.
# macOS: dist/AlgoBlock.app (build_mac.sh가 .dmg로 싼다). Windows: dist/AlgoBlock.exe 하나(onefile).
import os
import re
import sys
import tempfile
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

APP = Path(SPECPATH).parent
ROOT = APP.parent  # 저장소 루트. 모델 연결 코드를 app.llm이라는 이름으로 부른다
UI = APP / "ui"
FLAVOR = os.environ.get("ALGOBLOCK_FLAVOR", "")  # dev면 개발용 앱(이름·번들 id·자료 폴더·포트가 배포용과 다르고 업데이트하지 않는다). 릴리스에는 올리지 않는다
assert FLAVOR in ("", "dev"), f"ALGOBLOCK_FLAVOR는 비우거나 dev다(지금 {FLAVOR!r})"
NAME = "AlgoBlock Dev" if FLAVOR == "dev" else "AlgoBlock"
VERSION = re.search(r'^VERSION = "([^"]+)"', (UI / "updater.py").read_text(encoding="utf-8"), re.M)[1]  # 앱의 버전은 updater.py 한 곳(업데이트가 이 값과 견준다)


def keep(name: str) -> bool:
    """시험과 측정 도구는 묶지 않는다(화면이 쓰는 eval 모듈 셋만 남긴다)."""
    if ".tests" in name:
        return False
    if name.startswith("tutor.eval."):
        return name in ("tutor.eval.cli_client", "tutor.eval.drive", "tutor.eval.scenarios")
    return True


hidden = ["server", "window", "casegen"] + collect_submodules("tutor", filter=keep) + collect_submodules("app.llm")
hidden += collect_submodules("langgraph") + collect_submodules("qdrant_client.local") + ["onnxruntime", "tokenizers"]
datas = [(str(UI / name), "ui") for name in ("index.html", "app.css", "app.js", "highlight.js", "builtin.json", "PretendardVariable.woff2", "PretendardVariable-LICENSE.txt", "icon.svg", "favicon.svg", "tour-demos.js", "tour-demos.css")]
datas += [(str(APP / "tutor" / "plan" / "guide.md"), "tutor/plan")]
# 배포물에 라이선스 글을 같이 넣는다(이 앱의 MIT, 함께 묶는 것들의 고지)
datas += [(str(APP.parent / "LICENSE"), "licenses"), (str(APP.parent / "Docs" / "THIRD_PARTY_NOTICES.md"), "licenses"), (str(UI / "stageshow" / "LICENSE-stageshow.txt"), "licenses")]
datas += [(str(path), str(Path("judge") / path.relative_to(APP / "judge").parent))
          for path in (APP / "judge").rglob("*")
          if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".md"]
datas += collect_data_files("langgraph")
# 임베딩 모델 파일 둘. 빌드 스크립트가 app/packaging/models에 받아 둔다(없으면 여기서 멈춘다: 모델 없는 설치 파일을 만들지 않는다)
MODELS = Path(SPECPATH) / "models"
assert all((MODELS / name).is_file() for name in ("model.onnx", "tokenizer.json")), "app/packaging/models가 비었습니다. 빌드 스크립트로 빌드하세요."
datas += [(str(MODELS / name), "models") for name in ("model.onnx", "tokenizer.json")]
if FLAVOR:  # 실행기가 묶음 안의 이 파일로 빌드 종류를 안다(환경 변수는 Finder로 연 앱에 전해지지 않는다)
    marker = Path(tempfile.mkdtemp()) / "flavor"
    marker.write_text(FLAVOR, encoding="utf-8")
    datas += [(str(marker), ".")]

a = Analysis(
    [str(Path(SPECPATH) / "launcher.py")],
    pathex=[str(APP), str(UI), str(ROOT)],
    datas=datas,
    hiddenimports=hidden,
    excludes=["tkinter", "pytest", "IPython", "matplotlib", "tutor.tests", "fastembed"],
    noarchive=False,
)
pyz = PYZ(a.pure)
# 파이썬 UTF-8 모드. Windows의 기본 글자 인코딩(cp949, cp1252)으로 한글 출력·파일 읽기가 깨지지 않게 한다
UTF8 = [("X utf8", None, "OPTION")]

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, UTF8, exclude_binaries=True, name=NAME, console=False, target_arch=None)
    coll = COLLECT(exe, a.binaries, a.datas, name=NAME)
    app = BUNDLE(
        coll, name=f"{NAME}.app", bundle_identifier="io.github.algocean1204.algoblock" + (".dev" if FLAVOR == "dev" else ""), icon=str(Path(SPECPATH) / "icon" / "icon.icns"),
        info_plist={"CFBundleDisplayName": NAME, "CFBundleName": NAME, "CFBundleShortVersionString": VERSION,
                    "NSHighResolutionCapable": True, "LSMinimumSystemVersion": "12.0"},
    )
else:
    from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct,
                                                     VSVersionInfo)

    numbers = (*map(int, VERSION.split(".")), 0)  # 0.2.1 → (0, 2, 1, 0). 파일 속성의 제품 이름·버전(코드 서명은 이 둘이 정해진 값이기를 요구한다)
    strings = {"CompanyName": "algocean", "FileDescription": NAME, "FileVersion": VERSION, "InternalName": NAME, "LegalCopyright": "Copyright (c) 2026 algocean. MIT License.",
               "OriginalFilename": f"{NAME}.exe", "ProductName": NAME, "ProductVersion": VERSION}
    version = VSVersionInfo(ffi=FixedFileInfo(filevers=numbers, prodvers=numbers),
                            kids=[StringFileInfo([StringTable("040904B0", [StringStruct(k, v) for k, v in strings.items()])]), VarFileInfo([VarStruct("Translation", [1033, 1200])])])
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, UTF8, name=NAME, console=False, upx=False, icon=str(Path(SPECPATH) / "icon" / "icon.ico"), version=version)
