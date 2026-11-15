"""화면을 브라우저 없이 네이티브 창으로 연다(macOS는 WKWebView, Windows는 WebView2). pywebview가 있어야 한다.

실행: cd app && uv run --no-project --python 3.12 --with langgraph --with pywebview python ui/window.py
서버(server.py)를 같은 프로세스에서 같이 띄운다. 이미 떠 있으면 그 서버의 화면을 연다.
"""

import os
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import webview  # noqa: E402

import server  # noqa: E402


def serve() -> None:
    try:
        server.main()
    except OSError as exc:  # 포트를 이미 쓰고 있다: 떠 있는 서버를 그대로 쓴다
        print(f"서버를 새로 띄우지 않았습니다: {exc}", file=sys.stderr)


def os_dark() -> bool:
    """운영체제가 어두운 화면인가. 읽지 못하면 밝은 화면으로 본다."""
    try:
        if sys.platform == "darwin":
            return subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True, text=True, timeout=3).stdout.strip() == "Dark"
        if sys.platform == "win32":
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
    except Exception:  # noqa: BLE001 - 창 바탕색만 틀어질 뿐이라 읽지 못하면 밝게
        pass
    return False


def background() -> str:
    """창이 켜질 때 흰 면이 먼저 비치지 않게 고른 화면 색의 바탕(--bg)을 준다."""
    scheme = server.scheme_pref()
    return "#111113" if scheme == "dark" or (scheme == "system" and os_dark()) else "#F5F5F7"


def main() -> None:
    url = f"http://127.0.0.1:{os.environ.get('ALGOBLOCK_UI_PORT', '8791')}/"
    threading.Thread(target=serve, daemon=True).start()
    for _ in range(50):  # 서버가 받을 때까지 최대 10초
        try:
            urllib.request.urlopen(url, timeout=1).close()
            break
        except OSError:
            time.sleep(0.2)
    webview.create_window("AlgoBlock", url, width=1440, height=900, min_size=(1024, 680), background_color=background())
    webview.start()  # 창을 닫으면 돌아온다(메뉴의 '끝내기'는 돌아오지 않고 끝나 채점기의 CPU 시간 상한만 남는다)
    server.stop_grading()


if __name__ == "__main__":
    main()
