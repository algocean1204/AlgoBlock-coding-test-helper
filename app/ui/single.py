"""한 데이터 폴더는 한 프로세스만 쓴다: 폴더 안의 잠금 파일에 운영체제 잠금을 건다.
프로세스가 어떻게 끝나든 운영체제가 잠금을 풀므로, 비정상 종료 뒤에도 막히지 않는다(파일이 남아도 잠금은 없다)."""

import os
import sys
from pathlib import Path

HELD = []  # 잡은 파일을 프로세스가 끝날 때까지 쥐고 있어야 잠금이 유지된다
OFFSET = 16  # 윈도의 바이트 잠금은 잠근 칸을 다른 프로세스가 읽지 못하게 하므로 포트는 잠근 칸 밖에 적는다


def _lock(fd) -> bool:
    try:
        if sys.platform == "win32":
            import msvcrt

            fd.seek(0)
            msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def guard(data: Path, port: int) -> int | None:
    """잠금을 잡으면 None(내 포트를 적어 둔다). 이미 다른 프로세스가 쥐고 있으면 그 프로세스의 포트(모르면 0)."""
    path = data / "app.lock"
    fd = open(path, "a+b")
    if not _lock(fd):
        try:
            with open(path, "rb") as other:
                other.seek(OFFSET)
                return int(other.read(8).strip(b"\0 ") or 0)
        except (OSError, ValueError):
            return 0
        finally:
            fd.close()
    fd.seek(OFFSET)
    fd.truncate(OFFSET)
    fd.write(str(port).encode().ljust(8))
    fd.flush()
    HELD.append(fd)
    return None


def running_message(port: int) -> str:
    where = f" http://127.0.0.1:{port}/ 에서" if port else ""
    return f"AlgoBlock이 이미 켜져 있어요.{where} 열려 있는 창을 쓰세요. 새로 띄우지 않았습니다."


if __name__ == "__main__":
    # 두 번째 프로세스의 판단을 시험이 부르는 용도: python single.py <폴더> <포트>
    other = guard(Path(sys.argv[1]), int(sys.argv[2]))
    print("held" if other is None else f"busy {other}", flush=True)
    if other is None:
        sys.stdin.readline()
