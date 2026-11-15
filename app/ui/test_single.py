"""앱을 두 번 켰을 때의 판단(single.py와 server.main). 둘째 프로세스는 실제로 띄운다.

실행: cd app && python3 -B ui/test_single.py     (test_server.py도 이것을 부른다)
"""

import contextlib
import io
import os
import signal
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import single  # noqa: E402


def holder(folder: Path, port: int) -> subprocess.Popen:
    proc = subprocess.Popen([sys.executable, "-B", str(HERE / "single.py"), str(folder), str(port)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    assert proc.stdout.readline().strip() == "held"
    return proc


def run() -> None:
    import server

    with tempfile.TemporaryDirectory() as raw:
        folder = Path(raw)
        first = holder(folder, 8791)
        assert single.guard(folder, 9999) == 8791  # 켜져 있으면 그 포트를 알려 준다
        first.kill()  # 비정상 종료: 잠금 파일은 남지만 잠금은 풀린다
        first.wait()
        assert (folder / "app.lock").exists()
        assert single.guard(folder, 9999) is None, "죽은 프로세스의 잠금이 남아 막혔다"
        assert "8791" in single.running_message(8791) and "이미 켜져" in single.running_message(0)

        # server.main: 이미 켜져 있으면 키 읽기·업데이트 확인을 시작하지 않고 False
        other = Path(raw) / "second"
        other.mkdir()
        second = holder(other, 8123)
        err = io.StringIO()
        with patch.object(server, "DATA", other), patch.object(server.updater, "start") as start, patch.object(server, "load_keys") as keys, contextlib.redirect_stderr(err):
            assert server.main() is False
        assert not start.called and not keys.called and "이미 켜져" in err.getvalue(), err.getvalue()
        second.kill()
        second.wait()

        # 잠금은 비었는데 포트를 다른 프로그램이 쓰고 있다: 그 서버를 쓰지 않고 알린 뒤 False
        free = Path(raw) / "third"
        free.mkdir()
        with socket.socket() as busy:
            busy.bind(("127.0.0.1", 0))
            busy.listen()
            err = io.StringIO()
            with patch.dict(os.environ, {"ALGOBLOCK_UI_PORT": str(busy.getsockname()[1])}), patch.object(server, "DATA", free), patch.object(server.updater, "start") as start, contextlib.redirect_stderr(err):
                assert server.main() is False
            assert not start.called and "다른 프로그램" in err.getvalue(), err.getvalue()
    print("ok")


if __name__ == "__main__":
    os.environ.setdefault("ALGOBLOCK_UI_DATA", tempfile.mkdtemp(prefix="algoblock-ui-test-"))
    run()
