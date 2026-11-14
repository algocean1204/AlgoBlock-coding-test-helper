"""설치 파일의 시작점. 화면(웹)과 서버(튜터·채점기)를 한 프로세스로 띄운다.

묶였을 때(PyInstaller): 화면 파일과 채점기는 묶음 안에서, 사용자 데이터(DB·키·등록 문항)는 사용자 폴더에서 찾게 환경 변수를 넘긴다.
--server 를 주면 창 없이 서버만 띄운다(확인용). --check-embed 는 묶인 임베딩 모델을 한 번 돌려 이름과 차원을 찍는다.
"""

import os
import re
import sys
from pathlib import Path

APP = "AlgoBlock"


def data_dir() -> Path:
    """사용자 데이터 폴더. macOS ~/Library/Application Support, Windows %APPDATA%, 그 밖은 ~/.local/share."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / APP


def prepare() -> None:
    bundle = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    data = data_dir()
    os.environ.setdefault("ALGOBLOCK_UI_DATA", str(data))
    os.environ.setdefault("ALGOBLOCK_UI_STATIC", str(bundle / "ui"))
    os.environ.setdefault("ALGOBLOCK_JUDGE_DIR", str(bundle / "judge"))
    os.environ.setdefault("ALGOBLOCK_EMBED_DIR", str(bundle / "models"))  # 같이 묶은 임베딩 모델(기기 안에서 돈다. 내려받지 않는다)
    if sys.platform == "darwin":
        # Finder에서 연 앱은 PATH가 짧다. 사용자가 설치한 파이썬·컴파일러(채점에 쓴다)를 찾게 흔한 자리를 더한다
        home = Path.home()
        extra = ["/opt/homebrew/bin", "/usr/local/bin", str(home / ".pyenv" / "shims"), str(home / ".local" / "bin"),
                 str(home / ".cargo" / "bin"), "/usr/local/go/bin", str(home / "go" / "bin")]  # Rust(rustup), Go
        # Homebrew의 JDK는 /opt/homebrew/bin에 이어지지 않고, nvm의 Node는 버전 폴더 안에 있다(가장 높은 버전을 쓴다)
        newest = lambda path: [int(n) for n in re.findall(r"\d+", path.parent.name)]  # v9.11.2 < v22.1.0(글자 순서로는 v9가 뒤다)
        for found in (sorted(Path("/opt/homebrew/opt").glob("openjdk*/bin")), sorted((home / ".nvm" / "versions" / "node").glob("*/bin"), key=newest)):
            extra += [str(found[-1])] if found else []
        os.environ["PATH"] = os.pathsep.join([os.environ.get("PATH", ""), *extra])


def main() -> None:
    if getattr(sys, "frozen", False):
        prepare()
    if "--check-embed" in sys.argv:  # 빌드 확인용: 묶인 임베딩 모델이 실제로 도는지 본다
        from tutor.knowledge import embed

        vector = embed.e5_embedder(os.environ["ALGOBLOCK_EMBED_DIR"])(["확인"])[0]
        print(embed.NAME, len(vector), round(sum(x * x for x in vector), 4), flush=True)
    elif "--server" in sys.argv:
        import server

        server.main()
    else:
        import window

        window.main()


if __name__ == "__main__":
    main()
