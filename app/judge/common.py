import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


TIMEOUT_SECONDS = 10  # 실행 한 번(케이스 하나)의 제한
COMPILE_TIMEOUT_SECONDS = 60  # 컴파일 한 번의 제한. kotlinc 첫 실행은 10초를 넘는다
OUTPUT_LIMIT = 4_000_000  # 표준 출력·표준 오류 저마다의 상한(바이트). 넘으면 끝낸다(무한 출력이 메모리를 채우지 않게). 기본 문제의 가장 큰 답은 1MB 안쪽으로 만든다
MEMORY_LIMIT_MB = 2048  # 실행 중 메모리 상한. 넘으면 끝낸다(기기가 멈추지 않게)
SECRET_WORDS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")  # 이름에 이것이 든 환경 변수는 제출 코드에 넘기지 않는다
SECRET_PREFIXES = ("ALGOBLOCK_", "ANTHROPIC_", "OPENAI_", "XAI_", "OPENROUTER_", "AWS_", "GOOGLE_", "AZURE_", "GITHUB_", "GH_")  # 이것으로 시작하는 것도


def missing(*tools):
    for tool in tools:
        if not shutil.which(tool):
            return {
                "status": "toolchain_missing",
                "stdout": "",
                "stderr": f"{tool} 없음",
                "time_ms": 0,
            }
    return None


RUNNING = set()  # 지금 run_command가 돌리는 프로세스. 앱이 끝날 때 kill_running()이 모두 끝낸다
RUNNING_LOCK = threading.Lock()


def kill_running():
    """돌고 있는 채점 프로세스(그룹)를 모두 끝낸다. 서버가 끝날 때 부른다(부모가 죽으면 시간 제한을 지켜 줄 것이 없다)."""
    with RUNNING_LOCK:
        running = list(RUNNING)
    for process in running:
        _kill_tree(process)


def cpu_limit(timeout):
    """자식의 CPU 시간 상한(초). 벽시계 제한보다 넉넉히: JVM처럼 여러 스레드가 CPU 시간을 함께 쓰는 실행기가 정상 실행에서 걸리지 않게."""
    return math.ceil(timeout * 4) + 5


def _cpu_capped(seconds):
    """자식이 exec 전에 부를 함수: CPU 시간 상한을 건다. 부모가 죽어 아무도 끝내 주지 않아도 자식이 스스로 끝난다."""
    import resource

    hard = resource.getrlimit(resource.RLIMIT_CPU)[1]
    seconds = seconds if hard == resource.RLIM_INFINITY else min(seconds, hard)
    return lambda: resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))


def _kill_tree(process):
    """제출 코드가 띄운 자식 프로세스까지 끝낸다."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=10)
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        process.kill()
    except OSError:
        pass


def _memory_mb(process):
    """프로세스가 지금 쓰는 메모리(MB). 알 수 없으면 0."""
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            read = ctypes.windll.kernel32.K32GetProcessMemoryInfo
            read.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
            return counters.WorkingSetSize // 2**20 if read(int(process._handle), ctypes.byref(counters), counters.cb) else 0
        found = subprocess.run(["ps", "-o", "rss=", "-p", str(process.pid)], capture_output=True, text=True, timeout=5).stdout.strip()
        return int(found) // 1024 if found else 0
    except Exception:  # noqa: BLE001 - 재지 못하면 상한을 걸지 않을 뿐이다
        return 0


def run_command(command, cwd, stdin="", timeout=TIMEOUT_SECONDS, memory_mb=MEMORY_LIMIT_MB, cpu_seconds=None):
    """실행하고 {status, stdout, stderr, time_ms}. 시간(timeout), 출력 크기(OUTPUT_LIMIT), 메모리(memory_mb, None이면 안 봄)를 넘으면 자식까지 끝낸다.
    CPU 시간은 cpu_seconds(없으면 cpu_limit(timeout))를 넘으면 자식이 스스로 끝난다(POSIX).

    한계: 파일·네트워크 접근은 막지 않는다(사용자 기기에서 사용자 권한으로 도는 자기 코드다). 격리가 필요해지면 컨테이너나 OS 샌드박스로 감싼다.
    """
    started = time.perf_counter()
    options = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
               else {"start_new_session": True, "preexec_fn": _cpu_capped(cpu_seconds or cpu_limit(timeout))})
    # 한계: Windows는 CPU 시간 상한을 걸지 않는다(앱이 끝날 때 kill_running만 믿는다). 걸려면 Job Object가 필요하다
    env = {name: value for name, value in os.environ.items()
           if not any(word in name.upper() for word in SECRET_WORDS) and not name.upper().startswith(SECRET_PREFIXES)}  # API 키 같은 비밀 값은 넘기지 않는다
    process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={**env, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}, **options)
    with RUNNING_LOCK:
        RUNNING.add(process)
    try:
        return _collect(process, stdin, timeout, memory_mb, started)
    finally:
        with RUNNING_LOCK:
            RUNNING.discard(process)


def _collect(process, stdin, timeout, memory_mb, started):
    """run_command의 나머지: 입력을 넣고 출력을 읽으며 제한을 지킨다."""
    chunks = {"stdout": [], "stderr": []}
    stopped = []  # 우리가 끝낸 까닭(output_limit, memory_limit, timeout). 첫 것만 쓴다
    done = threading.Event()

    def stop(why):
        stopped.append(why)
        _kill_tree(process)

    def read(name, pipe):
        size = 0
        for chunk in iter(lambda: pipe.read(65536), b""):
            size += len(chunk)
            if size > OUTPUT_LIMIT:
                stop("output_limit")
                break
            chunks[name].append(chunk)
        pipe.close()

    def feed():
        try:
            process.stdin.write(stdin.encode("utf-8"))
            process.stdin.close()
        except OSError:  # 입력을 읽지 않고 끝난 프로그램
            pass

    def watch():
        while not done.wait(0.25):
            if _memory_mb(process) > memory_mb:
                stop("memory_limit")
                return

    threads = [threading.Thread(target=read, args=(name, pipe), daemon=True) for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr))]
    threads.append(threading.Thread(target=feed, daemon=True))
    if memory_mb:
        threads.append(threading.Thread(target=watch, daemon=True))
    for thread in threads:
        thread.start()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop("timeout")
        process.wait()
    if os.name != "nt":
        _kill_tree(process)  # 정상 종료여도 남은 자식(같은 프로세스 그룹)을 끝낸다. 출력 관을 물던 자식이 죽어 읽기가 곧 끝난다
    # 한계: Windows는 끝난 주 프로세스의 자식을 taskkill /T로 찾지 못해(끝난 PID는 다시 쓰일 수도 있어 부르지 않는다) 남긴다. 잡으려면 Job Object가 필요하다
    # 한계: setsid로 새 세션을 만든 자식은 그룹 밖이라 못 잡는다(격리가 필요). 그 자식이 관을 물어도 아래 1초 기다림 뒤 결과를 낸다
    done.set()
    for thread in threads:
        thread.join(timeout=1)  # 주 프로세스가 끝났으니 남은 출력은 곧 다 읽힌다. 관을 문 자식을 기다리지 않는다
    out = {name: b"".join(parts).decode("utf-8", "replace").replace("\r\n", "\n") for name, parts in chunks.items()}
    if stopped:
        return {"status": stopped[0], **out, "time_ms": int(timeout * 1000) if stopped[0] == "timeout" else int((time.perf_counter() - started) * 1000)}
    return {"status": "passed" if process.returncode == 0 else "runtime_error", **out,
            "time_ms": int((time.perf_counter() - started) * 1000), "returncode": process.returncode}


def compile_command(command, cwd, timeout=COMPILE_TIMEOUT_SECONDS):
    """성공이면 None, 실패면 compile_error 또는 timeout 결과."""
    result = run_command(command, cwd, timeout=timeout, memory_mb=None)  # 컴파일러의 메모리는 보지 않는다
    if result["status"] == "passed":
        return None
    result["status"] = "timeout" if result["status"] == "timeout" else "compile_error"
    return result


HEAD_LINES = {}  # 언어 → runner가 사용자 코드 파일 앞에 붙이는 줄 수. 지금 runner는 모두 사용자 코드를 제 파일 첫 줄부터 놓는다(main 이름만 같은 줄에서 바꾼다)
LINE_PATTERNS = {"python": r'File "(?:[^"]*[/\\])?{file}", line (\d+)'}  # 그 밖의 언어: Java·Kotlin 스택 (Main.java:3), 컴파일러 main.cpp:2:5, Go 스택 /…/main.go:3, Rust panicked at main.rs:3:5, Node main.js:3
LINE_LAST = {"python"}  # 가장 안쪽 프레임이 라이브러리(heapq 등)일 수 있어 사용자 파일의 마지막 프레임을 쓴다


def error_line(language, file, source, text):
    """오류 글(표준 오류)에서 사용자 코드 파일 file의 줄 번호(1부터). 모르거나 사용자 코드 밖(runner 쪽 줄)이면 None."""
    pattern = re.compile(LINE_PATTERNS.get(language, r"(?<![\w.]){file}:(\d+)").replace("{file}", re.escape(file)))
    found, warned = [], False
    for row in (text or "").splitlines():
        head = re.match(r"\s*(warning|error)\b", row)
        if head:
            warned = head.group(1) == "warning"  # rustc는 머리 줄 다음의 ' --> main.rs:2:5' 줄에 자리를 적는다
        match = pattern.search(row)
        if match and not warned and not re.search(r":\s*warning\b", row):  # 컴파일러 경고(main.cpp:2:5: warning:)는 오류가 아니다
            found.append(int(match.group(1)))
    if not found:
        return None
    line = (found[-1] if language in LINE_LAST else found[0]) - HEAD_LINES.get(language, 0)
    return line if 1 <= line <= source.count("\n") + 1 else None


def print_result(language, mode, case_id, result):
    print(f"[{language}/{mode}] case {case_id}: {result['status']}")
    if result.get("stdout"):
        print(result["stdout"].rstrip())
    if result.get("stderr"):
        print(result["stderr"].rstrip(), file=sys.stderr)


def load_cases(mode_dir):
    return json.loads((Path(mode_dir) / "cases.json").read_text(encoding="utf-8"))


def work_directory():
    return tempfile.TemporaryDirectory(prefix="algoblock-check-")


def same_value(actual, expected):
    """JSON 값 비교. 기대값이 정수면 정확히, 실수면 1e-6 오차를 허용한다. 참/거짓은 수와 섞지 않는다."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
    if isinstance(actual, int) and isinstance(expected, int):
        return actual == expected  # 정수는 정확히. 큰 수의 하나 차이도 틀린 답이다
    if isinstance(actual, float) and isinstance(expected, int):  # 실수로 낸 정수 답(3.0)은 정확히 그 정수일 때만 맞다
        return actual.is_integer() and abs(actual) <= 2**53 and int(actual) == expected
    if isinstance(actual, (int, float)) and isinstance(expected, float):
        return math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6)
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(same_value(a, e) for a, e in zip(actual, expected))
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(same_value(actual[k], expected[k]) for k in actual)
    return actual == expected


def same_function_output(stdout, expected):
    """함수 모드: 마지막 줄을 JSON으로 읽어 기대값(JSON 글)과 비교한다. JSON이 아니면 글로 비교한다."""
    lines = stdout.strip().splitlines()
    actual_text = lines[-1].strip() if lines else ""
    try:
        actual = json.loads(actual_text)
    except json.JSONDecodeError:
        return actual_text == str(expected).strip()
    if not isinstance(expected, str):  # cases.json에 기대값을 JSON 값 그대로 쓴 경우
        return same_value(actual, expected)
    try:
        return same_value(actual, json.loads(expected))
    except (json.JSONDecodeError, TypeError):
        # 기대값이 따옴표 없는 글(abc)이면 반환된 문자열과 글로 비교한다
        return isinstance(actual, str) and actual == str(expected).strip()


_DECIMAL = re.compile(r"[-+]?\d+\.\d+(?:[eE][-+]?\d+)?")


def _same_row(got, want, decimal=False):
    """한 줄 비교. 글자가 같으면 같다. decimal(문제가 실수 답을 허용한다)이면 낱말끼리 견주되, 기대 출력에 소수로 적힌 낱말만 1e-6 오차 안에서 같게 본다
    (함수 모드의 실수 비교와 같은 기준). 낱말 사이의 공백은 글자 그대로 같아야 한다.
    기대 출력의 모양(소수점)만 보고 늘 오차를 켜면 자릿수가 정해진 문제의 틀린 형식('3.5'와 '3.50')이 통과했다. 허용 여부는 문제가 정한다."""
    if got == want:
        return True
    if not decimal:
        return False
    a, b = re.split(r"(\s+)", got), re.split(r"(\s+)", want)
    if len(a) != len(b):
        return False
    for mine, theirs in zip(a, b):
        if mine == theirs:
            continue
        if not _DECIMAL.fullmatch(theirs):
            return False
        try:
            if not math.isclose(float(mine), float(theirs), rel_tol=1e-6, abs_tol=1e-6):
                return False
        except ValueError:
            return False
    return True


def same_program_output(stdout, expected, decimal=False):
    """프로그램 모드: 줄마다 끝 공백을 빼고, 끝의 빈 줄을 빼고 비교한다. decimal이면 기대 출력의 소수 낱말은 1e-6 오차 안에서 같게 본다."""

    def lines(text):
        rows = [row.rstrip() for row in str(text).replace("\r\n", "\n").split("\n")]
        while rows and not rows[-1]:
            rows.pop()
        return rows

    got, want = lines(stdout), lines(expected)
    return len(got) == len(want) and all(_same_row(a, b, decimal) for a, b in zip(got, want))
