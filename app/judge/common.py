import contextlib
import ctypes
import functools
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
# JVM(Java·Kotlin 실행)의 표준 입출력을 UTF-8로. 관(pipe)으로 이어진 표준 출력은 OS 기본 인코딩을 써서 Windows(cp1252, cp949)에서 한글이 ?로 깨졌다.
# JDK 17은 file.encoding을, 18은 sun.stdout.encoding을, 19부터는 stdout.encoding을 본다.
# macOS·Linux에서는 C/POSIX 로케일이 아니면 바뀌지 않는다(그 로케일에서는 깨지던 한글이 바로 나온다)
JAVA_UTF8 = ("-Dfile.encoding=UTF-8", "-Dsun.stdout.encoding=UTF-8", "-Dsun.stderr.encoding=UTF-8", "-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8")
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


# --- Windows: 작업 객체(Job Object) ---
# 제출 코드를 새 작업 하나에 넣는다. 작업을 끝내면(TerminateJobObject) 그 안의 손자까지 모두 끝나고, 작업 핸들이 닫히면(앱이 죽어도) 모두 끝난다.
# 프로세스를 멈춘 채로 만들고(CREATE_SUSPENDED) 작업에 넣은 뒤 재개한다. 그래서 작업에 들기 전에 자식을 띄워 빠져나갈 틈이 없다.
# subprocess는 주 스레드 핸들을 닫아 버리므로 스레드는 Toolhelp로 찾아 재개한다(멈춘 채 갓 만든 프로세스의 스레드는 하나다).
# 다른 길을 고르지 않은 까닭: _winapi.CreateProcess를 직접 부르면 관(pipe)과 핸들 상속을 다시 짜야 하고, CREATE_BREAKAWAY_FROM_JOB는
# 앱 자신이 든 작업이 빠져나가기를 허락하지 않으면 프로세스 만들기부터 실패한다. 작업 안의 작업(Windows 8부터)은 따로 할 일이 없다.
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000  # 창 없는 앱(설치 파일)에서 채점할 때마다 콘솔 창이 뜨지 않게
JOB_LIMIT_PROCESS_TIME = 0x00000002  # PerProcessUserTimeLimit
JOB_LIMIT_ACTIVE_PROCESS = 0x00000008  # ActiveProcessLimit(작업 안에서 동시에 살아 있는 프로세스 수)
JOB_LIMIT_JOB_MEMORY = 0x00000200  # JobMemoryLimit(작업 전체의 커밋 메모리)
JOB_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400  # 죽은 프로그램이 오류 보고 창을 띄운 채 시간 초과까지 남지 않게
JOB_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_EXTENDED_LIMIT_INFORMATION = 9  # JOBOBJECTINFOCLASS의 JobObjectExtendedLimitInformation
JOB_ASSOCIATE_COMPLETION_PORT_INFORMATION = 7  # JobObjectAssociateCompletionPortInformation
JOB_MSG_ACTIVE_PROCESS_LIMIT = 3  # 완료 포트로 오는 알림: 작업의 동시 프로세스 수가 상한을 넘으려 했다
JOB_MSG_JOB_MEMORY_LIMIT = 10  # 완료 포트로 오는 알림: 작업의 프로세스가 작업 메모리 상한을 넘는 커밋을 하려 했다
JOB_MEMORY_FACTOR = 2  # 작업의 커밋 상한 = memory_mb × 이것. 커밋은 실제로 쓰는 메모리(작업 집합)보다 앞서 잡힌다(JVM의 첫 힙 등).
#                        memory_limit 판정은 POSIX처럼 0.25초마다 재는 작업 집합이 하고, 이 상한은 그 사이의 급한 증가를 막는 바닥이다
# 작업 안의 동시 프로세스 수 상한(제출 코드 한 번의 실행). 끝없이 프로세스를 만드는 코드(포크 폭탄)가 기기를 느리게 하지 않게 한다.
# 값의 근거: 정상 풀이는 주 프로세스 하나다. venv의 python.exe는 실제 인터프리터를 한 번 더 띄워 둘이고, 풀이가 subprocess·multiprocessing으로 몇 개를
# 띄울 수 있다. 보통 기기의 multiprocessing.Pool(논리 CPU 수)도 들어가도록 넉넉히 64로 잡는다(채점에서 이만큼 쓰는 풀이는 없다).
# 논리 CPU가 60개를 넘는 기기의 Pool()은 막힐 수 있다(그런 기기에서 이 한계에 걸리면 stderr에 한 줄이 붙는다).
# 컴파일러(g++, go build가 자식을 많이 띄운다)에는 걸지 않는다(compile_command가 processes=None을 넘긴다)
JOB_PROCESS_LIMIT = 64
# SetErrorMode 플래그. 자식은 부모의 오류 모드를 물려받는다: 오류 창을 띄우는 대신 호출이 실패하고 프로세스가 바로 끝난다
SEM_FAILCRITICALERRORS = 0x0001  # DLL을 찾지 못함(MinGW 런타임 등) 같은 '치명적 오류' 창
SEM_NOGPFAULTERRORBOX = 0x0002  # 일반 보호 오류(죽은 프로그램) 창
SEM_NOOPENFILEERRORBOX = 0x8000  # 파일을 열지 못함 창
ERROR_MODE = SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX
ERROR_MODE_LOCK = threading.Lock()  # 오류 모드는 프로세스 전체의 값이라 이 모듈의 두 실행이 서로의 '되돌릴 값'을 덮지 않게(한계는 _quiet_errors)
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
JOB_LOCK = threading.Lock()  # 작업 핸들을 쓰는 것(끝내기)과 닫는 것이 겹치지 않게
_warned = []


class JobBasicLimit(ctypes.Structure):  # JOBOBJECT_BASIC_LIMIT_INFORMATION (x64: 64바이트)
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", ctypes.c_uint32),
                ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", ctypes.c_uint32), ("SchedulingClass", ctypes.c_uint32)]


class JobIoCounters(ctypes.Structure):  # IO_COUNTERS (48바이트)
    _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                     "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class JobExtendedLimit(ctypes.Structure):  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION (x64: 144바이트)
    _fields_ = [("BasicLimitInformation", JobBasicLimit), ("IoInfo", JobIoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class JobCompletionPort(ctypes.Structure):  # JOBOBJECT_ASSOCIATE_COMPLETION_PORT (x64: 16바이트)
    _fields_ = [("CompletionKey", ctypes.c_void_p), ("CompletionPort", ctypes.c_void_p)]


class ThreadEntry(ctypes.Structure):  # THREADENTRY32 (28바이트)
    _fields_ = [("dwSize", ctypes.c_uint32), ("cntUsage", ctypes.c_uint32), ("th32ThreadID", ctypes.c_uint32), ("th32OwnerProcessID", ctypes.c_uint32),
                ("tpBasePri", ctypes.c_int32), ("tpDeltaPri", ctypes.c_int32), ("dwFlags", ctypes.c_uint32)]


@functools.cache
def _kernel32():
    """kernel32의 함수에 형을 붙인다(핸들은 포인터 크기: 형이 없으면 64비트에서 잘린다). 다른 모듈의 ctypes.windll 설정과 섞이지 않게 따로 연다."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    handle, flag, dword, pointer = ctypes.c_void_p, ctypes.c_int, ctypes.c_uint32, ctypes.c_void_p
    for name, result, args in (("CreateJobObjectW", handle, [pointer, ctypes.c_wchar_p]), ("SetInformationJobObject", flag, [handle, ctypes.c_int, pointer, dword]),
                               ("AssignProcessToJobObject", flag, [handle, handle]), ("TerminateJobObject", flag, [handle, ctypes.c_uint]),
                               ("CloseHandle", flag, [handle]), ("SetErrorMode", dword, [dword]), ("GetErrorMode", dword, []), ("CreateToolhelp32Snapshot", handle, [dword, dword]),
                               ("Thread32First", flag, [handle, pointer]), ("Thread32Next", flag, [handle, pointer]),
                               ("OpenThread", handle, [dword, flag, dword]), ("ResumeThread", dword, [handle]),
                               ("CreateIoCompletionPort", handle, [handle, handle, ctypes.c_size_t, dword]),
                               ("GetQueuedCompletionStatus", flag, [handle, pointer, pointer, pointer, dword])):
        function = getattr(kernel, name)
        function.restype, function.argtypes = result, args
    return kernel


def _win_error(what):
    code = ctypes.get_last_error()
    return OSError(code, f"{what} 실패(Windows 오류 {code})")


@contextlib.contextmanager
def _quiet_errors():
    """프로세스를 만드는 동안만 이 프로세스의 오류 모드에 오류 창 끄기를 더하고, 끝나면 원래 값으로 되돌린다(앱 자신의 동작은 그대로).
    한계: CPython이 확장 모듈을 불러올 때 잠금 없이 오류 모드를 바꾸므로, 그와 겹치면 드물게 되돌린 값이 어긋날 수 있다."""
    kernel = _kernel32()
    with ERROR_MODE_LOCK:
        before = kernel.GetErrorMode()
        kernel.SetErrorMode(before | ERROR_MODE)
        try:
            yield
        finally:
            kernel.SetErrorMode(before)


def _windows_job(process, cpu_seconds, memory_mb, processes=None):
    """멈춘 채 만든 process를 제한을 건 새 작업에 넣고 작업 핸들을 낸다. processes(없으면 상한 없음)는 작업 안의 동시 프로세스 수 상한이다.
    실패하면 OSError(만든 작업은 닫는다. 프로세스는 건드리지 않는다)."""
    kernel = _kernel32()
    job = kernel.CreateJobObjectW(None, None)  # 보안 속성 없음: 핸들이 자식에게 상속되지 않는다
    if not job:
        raise _win_error("CreateJobObject")
    try:
        limit = JobExtendedLimit()
        basic = limit.BasicLimitInformation
        basic.LimitFlags = JOB_LIMIT_KILL_ON_JOB_CLOSE | JOB_LIMIT_DIE_ON_UNHANDLED_EXCEPTION | JOB_LIMIT_PROCESS_TIME
        basic.PerProcessUserTimeLimit = int(cpu_seconds * 10_000_000)  # 100ns 단위. 넘으면 Windows가 그 프로세스를 끝낸다
        if processes:
            basic.LimitFlags |= JOB_LIMIT_ACTIVE_PROCESS
            basic.ActiveProcessLimit = processes
        if memory_mb:
            basic.LimitFlags |= JOB_LIMIT_JOB_MEMORY
            limit.JobMemoryLimit = min(memory_mb * JOB_MEMORY_FACTOR * 2**20, ctypes.c_size_t(-1).value)  # 32비트 파이썬에서 잘려 0이 되지 않게
        if not kernel.SetInformationJobObject(job, JOB_EXTENDED_LIMIT_INFORMATION, ctypes.byref(limit), ctypes.sizeof(limit)):
            raise _win_error("SetInformationJobObject")
        if not kernel.AssignProcessToJobObject(job, int(process._handle)):
            raise _win_error("AssignProcessToJobObject")
    except BaseException:
        kernel.CloseHandle(job)
        raise
    return job


def _memory_port(job):
    """작업에 완료 포트를 붙여 '작업 메모리 상한' 알림을 받게 한다. 커밋 상한은 넘는 할당을 거절할 뿐 프로세스를 끝내지 않아서,
    이 알림으로 실행 오류와 memory_limit를 가린다(POSIX처럼 memory_limit로 판정한다). 붙이지 못하면 None(판정은 실행 오류로 남는다)."""
    kernel = _kernel32()
    port = kernel.CreateIoCompletionPort(ctypes.c_void_p(-1).value, None, 0, 1)  # INVALID_HANDLE_VALUE: 파일 없는 새 포트
    if not port:
        return None
    link = JobCompletionPort(None, port)
    if kernel.SetInformationJobObject(job, JOB_ASSOCIATE_COMPLETION_PORT_INFORMATION, ctypes.byref(link), ctypes.sizeof(link)):
        return port
    kernel.CloseHandle(port)
    return None


def _job_events(process):
    """process의 작업이 완료 포트로 보낸 알림 종류의 집합(커밋 메모리 상한, 프로세스 수 상한). 포트에 쌓인 알림을 기다리지 않고 모두 읽는다(알림 전달은 보장되지 않아 못 받으면 빈 집합)."""
    port = getattr(process, "algoblock_port", None)
    if not port:
        return set()
    kernel, message, key, overlapped = _kernel32(), ctypes.c_uint32(), ctypes.c_size_t(), ctypes.c_void_p()
    events = set()
    while kernel.GetQueuedCompletionStatus(port, ctypes.byref(message), ctypes.byref(key), ctypes.byref(overlapped), 0):
        events.add(message.value)
    return events


def _resume(pid):
    """멈춘 채 만든 프로세스 pid의 스레드를 재개한다. 하나도 재개하지 못하면 OSError."""
    kernel = _kernel32()
    snapshot = kernel.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snapshot in (None, ctypes.c_void_p(-1).value):  # INVALID_HANDLE_VALUE
        raise _win_error("CreateToolhelp32Snapshot")
    resumed = 0
    try:
        entry = ThreadEntry()
        entry.dwSize = ctypes.sizeof(entry)
        more = kernel.Thread32First(snapshot, ctypes.byref(entry))
        while more:
            if entry.th32OwnerProcessID == pid:
                thread = kernel.OpenThread(THREAD_SUSPEND_RESUME, False, entry.th32ThreadID)
                if thread:
                    resumed += kernel.ResumeThread(thread) != 0xFFFFFFFF
                    kernel.CloseHandle(thread)
            more = kernel.Thread32Next(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    if not resumed:
        raise _win_error("멈춘 프로세스의 스레드 재개")  # 글에 PID를 넣지 않는다(같은 경고를 한 번만 적는다)


def _start_windows(process, cpu_seconds, memory_mb, processes=None):
    """멈춘 채 만든 process를 작업에 넣고 재개한다. (종류, 까닭) 또는 (None, None)을 낸다(조용히 넘기지 않는다).
    종류 no_job: 작업을 쓰지 못해 작업 없이 돌렸다. not_started: 재개하지 못해 끝냈다(실행 오류로 남는다)."""
    kind = warning = None
    try:
        process.algoblock_job = _windows_job(process, cpu_seconds, memory_mb, processes)
        process.algoblock_port = _memory_port(process.algoblock_job) if memory_mb else None
    except Exception as error:  # noqa: BLE001 - 작업 없이도 채점은 한다(시간 초과 때 taskkill로 끝내고, 메모리는 작업 집합으로 잰다)
        kind, warning = "no_job", f"Windows 작업 객체를 쓰지 못해 CPU 시간 상한·커밋 메모리 상한·프로세스 수 상한·남은 자식 정리 없이 돌렸습니다: {error}"
    try:
        _resume(process.pid)
    except Exception as error:  # noqa: BLE001 - 멈춘 채 두면 시간 초과까지 기다린다: 끝내고 실행 오류로 남긴다
        _kill_tree(process)
        kind, warning = "not_started", f"제출 코드를 시작하지 못했습니다: {error}"
    if warning and warning not in _warned:  # 서버 기록에 한 번
        _warned.append(warning)
        print(f"채점기: {warning}", file=sys.stderr)
    return kind, warning


def _end_job(process, close=False):
    """process의 작업(Windows)을 끝내 그 안의 모든 프로세스를 끝낸다. close면 작업 핸들도 닫는다. 작업이 없거나 끝내지 못하면 False."""
    with JOB_LOCK:
        job = getattr(process, "algoblock_job", None)
        if not job:
            return False
        ended = bool(_kernel32().TerminateJobObject(job, 1))
        if close:
            _kernel32().CloseHandle(job)
            process.algoblock_job = None
            if getattr(process, "algoblock_port", None):
                _kernel32().CloseHandle(process.algoblock_port)
                process.algoblock_port = None
        return ended


def _windows_program(command, cwd):
    """Windows의 CreateProcess는 상대 경로(./app)를 cwd가 아니라 부모의 현재 폴더에서 찾고, .exe만 붙여 찾아 .bat(kotlinc)을 못 찾는다.
    그래서 첫 낱말을 절대 경로로 바꾼다. ./app은 작업 폴더의 app.exe(g++)나 app(go·rustc가 이름 그대로 만든 것)이다."""
    first = command[0]
    if first.startswith("./"):
        base = Path(cwd) / first[2:]
        found = next((str(path) for path in (base.with_name(base.name + ".exe"), base) if path.is_file()), str(base))
    else:
        found = shutil.which(first) or first
    return [found, *command[1:]]


def _kill_tree(process):
    """제출 코드가 띄운 자식 프로세스까지 끝낸다."""
    try:
        if os.name == "nt":
            if not _end_job(process):  # 작업이 없을 때만: 지금 살아 있는 자식 트리를 찾아 끝낸다
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


def run_command(command, cwd, stdin="", timeout=TIMEOUT_SECONDS, memory_mb=MEMORY_LIMIT_MB, cpu_seconds=None, processes=JOB_PROCESS_LIMIT):
    """실행하고 {status, stdout, stderr, time_ms}. 시간(timeout), 출력 크기(OUTPUT_LIMIT), 메모리(memory_mb, None이면 안 봄)를 넘으면 자식까지 끝낸다.
    CPU 시간은 cpu_seconds(없으면 cpu_limit(timeout))를 넘으면 자식이 스스로 끝난다(POSIX는 RLIMIT_CPU, Windows는 작업 객체의 사용자 모드 시간).
    Windows는 작업 안의 동시 프로세스 수도 processes(None이면 안 건다)로 막고, 프로세스를 만드는 동안 오류 창을 끈다(SetErrorMode).
    Windows에서 작업 객체를 쓰지 못하면 작업 없이 돌리고 결과에 warning(까닭)과 warning_kind(no_job, 시작하지 못했으면 not_started)를 붙인다.

    한계: 파일·네트워크 접근은 막지 않는다(사용자 기기에서 사용자 권한으로 도는 자기 코드다). 격리가 필요해지면 컨테이너나 OS 샌드박스로 감싼다.
    """
    started = time.perf_counter()
    cpu = cpu_seconds or cpu_limit(timeout)
    windows = os.name == "nt"
    if windows:
        command = _windows_program(command, cwd)
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW | CREATE_SUSPENDED}  # 작업에 넣은 뒤 _start_windows가 재개한다
    else:
        options = {"start_new_session": True, "preexec_fn": _cpu_capped(cpu)}
    env = {name: value for name, value in os.environ.items()
           if not any(word in name.upper() for word in SECRET_WORDS) and not name.upper().startswith(SECRET_PREFIXES)}  # API 키 같은 비밀 값은 넘기지 않는다
    with _quiet_errors() if windows else contextlib.nullcontext():  # 자식이 이 오류 모드를 물려받는다
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env={**env, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}, **options)
    with RUNNING_LOCK:
        RUNNING.add(process)
    try:
        kind = warning = None
        if windows:
            kind, warning = _start_windows(process, cpu, memory_mb, processes)
            started = time.perf_counter()  # 작업 준비(작업 만들기, 스레드 찾기)는 실행 시간에 넣지 않는다. 프로세스는 재개한 뒤에야 돈다
        result = _collect(process, stdin, timeout, memory_mb, started)
        events = _job_events(process) if windows else ()
        if result["status"] == "runtime_error" and JOB_MSG_JOB_MEMORY_LIMIT in events:
            result = {**result, "status": "memory_limit"}  # 커밋 상한이 할당을 거절해 죽었다(POSIX의 메모리 측정과 같은 판정)
        if JOB_MSG_ACTIVE_PROCESS_LIMIT in events and result["status"] != "passed":  # 알림이 오면 끝난 이유를 알 수 있게 한 줄 덧붙인다(전달은 보장되지 않는다)
            stderr = result["stderr"]
            result = {**result, "stderr": (stderr if not stderr or stderr.endswith("\n") else stderr + "\n") + f"프로세스 수 상한({processes})에 걸렸어요\n"}
        return {**result, "warning": warning, "warning_kind": kind} if warning else result
    finally:
        with RUNNING_LOCK:
            RUNNING.discard(process)
        if windows:
            _end_job(process, close=True)


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
    if os.name != "nt" or getattr(process, "algoblock_job", None):
        _kill_tree(process)  # 정상 종료여도 남은 자식(같은 프로세스 그룹, Windows는 같은 작업)을 끝낸다. 출력 관을 물던 자식이 죽어 읽기가 곧 끝난다
    # 한계: Windows에서 작업 객체를 쓰지 못했으면 끝난 주 프로세스의 자식은 taskkill /T로 찾지 못해(끝난 PID는 다시 쓰일 수도 있어 부르지 않는다) 남긴다
    # 한계: setsid로 새 세션을 만든 자식은 그룹 밖이라 못 잡는다(격리가 필요. Windows의 작업에는 이 빈틈이 없다). 그 자식이 관을 물어도 아래 1초 기다림 뒤 결과를 낸다
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
    result = run_command(command, cwd, timeout=timeout, memory_mb=None, processes=None)  # 컴파일러의 메모리와 프로세스 수는 보지 않는다(go build 등이 자식을 많이 띄운다)
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
