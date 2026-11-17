"""화면을 브라우저 없이 네이티브 창으로 연다(macOS는 WKWebView, Windows는 WebView2). pywebview가 있어야 한다.

실행: cd app && uv run --no-project --python 3.12 --with langgraph --with pywebview python ui/window.py
서버(server.py)를 같은 프로세스에서 같이 띄운다. 이미 켜져 있으면(데이터 폴더 잠금) 알리고 끝난다.
"""

import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import webview  # noqa: E402

import server  # noqa: E402


def notify(text: str) -> None:
    """설치 앱은 콘솔이 없어 표준 오류가 보이지 않는다: 작은 알림 창으로 알린다. 못 띄우면 표준 오류에만."""
    print(text, file=sys.stderr, flush=True)
    try:
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e", f'display dialog "{text.replace(chr(34), chr(39))}" with title "AlgoBlock" buttons {{"확인"}} default button 1 giving up after 20'], capture_output=True, timeout=30)
        elif sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, text, "AlgoBlock", 0x40)
    except Exception:  # noqa: BLE001 - 알림이 안 떠도 앱은 어차피 끝난다
        pass


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
    httpd = server.start()  # 잠금과 포트 판단이 끝난 뒤에만 창을 연다(먼저 켜진 앱의 응답을 보고 창을 열지 않게)
    if isinstance(httpd, str):
        return notify(httpd)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    threading.Thread(target=server.serve, args=(httpd,), daemon=True).start()
    webview.create_window("AlgoBlock", url, width=1440, height=900, min_size=(1024, 680), background_color=background())
    webview.start()  # 창을 닫으면 돌아온다(메뉴의 '끝내기'는 돌아오지 않고 끝나 채점기의 CPU 시간 상한만 남는다)
    server.stop_grading()


if __name__ == "__main__":
    main()
