"""AlgoBlock 화면 서버. 표준 라이브러리 HTTP 서버가 튜터(tutor.Tutor)와 채점기(app/judge)를 감싼다.

실행: cd app && uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/server.py
주소: http://127.0.0.1:8791 (ALGOBLOCK_UI_PORT로 바꾼다). 이 기기 안에서만 열린다.
모델: 기본은 연결한 공급자(API 키·ChatGPT 로그인). 키는 화면의 '연결'에서 넣거나 .env에 둔다.
     개발할 때만 ALGOBLOCK_UI_CLIENT=cli 로 이 PC의 Claude Code(claude -p)를 쓴다.
설치 파일로 묶였을 때는 app/packaging/launcher.py가 데이터 폴더·화면 파일·채점기 위치를 환경 변수로 넘긴다.
"""

import ast
import atexit
import base64
import json
import os
import re
import shutil
import signal
import sqlite3
import sys
import threading
import time
import traceback
import uuid
from collections import Counter, defaultdict
from contextlib import contextmanager, nullcontext
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # 저장소 루트(.env). app/ 아래에 ui·tutor·llm·judge·packaging이 있다
APP = HERE.parent
DATA = Path(os.environ.get("ALGOBLOCK_UI_DATA") or HERE / "data")  # 저장소·등록한 문항·블록 코드·로그인 토큰·키가 모두 이 폴더에 있다
DATA.mkdir(parents=True, exist_ok=True)
STATIC_DIR = Path(os.environ.get("ALGOBLOCK_UI_STATIC") or HERE)  # index.html, app.css, app.js
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(APP))
sys.path.insert(0, str(ROOT))  # app.llm(모델 연결)
os.environ.setdefault("ALGOBLOCK_LLM_AUTH_DIR", str(DATA / "auth"))
os.environ.setdefault("ALGOBLOCK_LLM_USAGE_LOG", str(DATA / "usage.jsonl"))  # 모델 호출마다 토큰 한 줄(글·키 없음). tutor/eval/cost.py가 묶어 본다
if os.environ.get("ALGOBLOCK_LLM_PROMPT_DIR") and Path(os.environ["ALGOBLOCK_LLM_PROMPT_DIR"]).resolve().is_relative_to(DATA.resolve()):
    os.environ.pop("ALGOBLOCK_LLM_PROMPT_DIR")  # 측정용 프롬프트 사본은 자료 폴더 밖에만 둔다(자료 폴더는 사용자 것이다)

from tutor import Tutor  # noqa: E402
from tutor.eval.cli_client import ClaudeCli  # noqa: E402
from tutor.eval.drive import check_judge  # noqa: E402
from tutor.common.scope import ALGORITHMS, algorithm_name  # noqa: E402
from tutor.common.solution import composed_parts  # noqa: E402
from tutor.common.talk_rules import MANY_ANSWERS  # noqa: E402
from tutor.save.respond import blocks_body, shown_count  # noqa: E402
from tutor.ingest import IngestError, ocr_doubts, read_pages, reread  # noqa: E402
from tutor.ingest.files import split_files  # noqa: E402
from tutor.eval.scenarios import all_scenarios  # noqa: E402
from tutor.knowledge.ontology import PITFALLS, TECHNIQUES, techniques_of  # noqa: E402
from tutor.llm import LlmNotConfigured, themes, use_llm  # noqa: E402
from tutor.store.sqlite import now  # noqa: E402

import casegen  # noqa: E402  (효율성 케이스의 큰 입력을 다시 만든다)
import casemake  # noqa: E402  (등록한 문제의 풀이를 단순 풀이·생성기와 채점기로 대조해 숨은 케이스를 만든다)
from problemkit import fits  # noqa: E402  (값이 형에 맞는가. 기본 문제를 검사할 때 쓰는 것)
from stubs import program_stub, stub  # noqa: E402  (형에서 언어별 시작 코드, 표준 입출력 뼈대)
import updater  # noqa: E402  (새 버전 확인과 업데이트)
from app.llm import keycheck  # noqa: E402  (키를 저장하기 전에 공급자에 확인)

updater.DIR = DATA / "updates"  # 받은 설치 파일과 업데이트 설정

DB = DATA / "tutor.db"
PROBLEMS_FILE = DATA / "problems.json"  # 등록한 문항(제목·글·케이스). 엔진 SQLite에는 케이스 표가 아직 없다
BLOCKS_FILE = DATA / "blocks.json"  # 블록 칸에 적은 코드 {문항: {블록: {code, by}}}
OWN_FILE = DATA / "own_way.json"  # '끝까지 내 방식으로 쓰기'를 켠 문항 {문항: true}. 블록 진행과 함께 지운다(초기화·계획 지우기·문항 지우기)
CODES_FILE = DATA / "codes.json"  # 언어마다 쓰던 코드 {문항: {언어: 코드}}. 언어를 바꿨다 돌아와도 남아 있게
ATTEND_FILE = DATA / "attendance.json"  # 출석한 날 ["YYYY-MM-DD", …](기기 현지 날짜)
CHECKPOINTS_FILE = DATA / "checkpoints.json"  # 언어마다 마지막 체크포인트 {문항: {언어: {code: 직접 풀기 글, blocks: 블록 칸, at: ISO 시각}}}
TOUCHED_FILE = DATA / "touched.json"  # 문제를 마지막으로 손댄 시각 {문항: ISO 시각}(코드 저장·실행·제출·힌트). '이어서 풀기'가 가장 최근에 쓰던 문제를 고른다
KINDS = ("example", "accuracy", "efficiency")  # 케이스 종류: 공개 예시, 숨긴 정확성, 숨긴 효율성(큰 입력)
STATIC = {"/": ("index.html", "text/html"), "/index.html": ("index.html", "text/html"),
          "/app.css": ("app.css", "text/css"), "/app.js": ("app.js", "text/javascript"),
          "/icon.svg": ("icon.svg", "image/svg+xml"), "/favicon.svg": ("favicon.svg", "image/svg+xml"),  # 앱 아이콘과 탭 아이콘(같은 그림, 여백만 다르다)
          "/tour-demos.js": ("tour-demos.js", "text/javascript"), "/tour-demos.css": ("tour-demos.css", "text/css"),  # 처음 안내의 움직이는 데모(stageshow/에서 미리 빌드, 안내를 열 때만 불러온다)
          "/PretendardVariable.woff2": ("PretendardVariable.woff2", "font/woff2")}  # 맥 밖에서 쓰는 글꼴(OFL)
KEYS = {"claude": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}  # 지원하는 공급자는 Claude·OpenAI 둘이다(그 밖의 키는 저장돼 있어도 읽지 않는다)
KEY_FORM = {"claude": ("Claude", "sk-ant-"), "openai": ("OpenAI", "sk-")}  # 공급자 키의 꼴: 접두사로 시작하고 영문·숫자·-·_만(빈칸·한글이 든 글은 키가 아니다)
SAMPLE_TITLES = {"hash_library": "책을 돌려주지 않은 학생", "stack_brackets": "괄호 짝 맞추기", "brute_pairs": "카드 두 장의 합"}
MAX_BODY = 1_000_000
FILE_PATHS = ("/api/problems/read", "/api/problems/new", "/api/problems/edit")  # 파일을 실어 오는 요청만 본문 상한이 크다
MAX_FILE_BODY = 60_000_000
MAX_FILE = 8 * 1024 * 1024  # 올린 파일 하나(디코드 뒤)
LARGE = DATA / "large"  # 등록한 문제의 효율성 케이스 <문제 id>/<번호>.json {input, expected}(큰 글이라 problems.json에 넣지 않는다)
ASSETS = DATA / "assets"  # 등록할 때 올린 원본 <문제 id>/<순번 두 자리>.<확장자>, 원래 이름은 index.json
ASSET_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "gif": "image/gif",
               "pdf": "application/pdf", "md": "text/plain", "txt": "text/plain"}  # md·txt는 HTML로 읽히지 않게 글로 준다
OWN_ID = re.compile(r"u[0-9a-f]{8}")  # 사용자가 등록한 문항 id
PREPARE = os.environ.get("ALGOBLOCK_UI_PREPARE", "1") != "0"  # 0이면 문항을 열 때 뼈대를 미리 뽑지 않는다(개발 중 모델 호출 아끼기)

KEY_FILE = DATA / "keys.json"  # 화면에서 넣은 API 키. 이 기기에만, 소유자만 읽게(0600) 둔다
PREFS_FILE = DATA / "prefs.json"  # 화면 설정: 처음 안내를 봤는지(tour_seen), 과정별 급과 추론 정도(stages. 예전에는 테마별 모델 themes), 마지막으로 고른 풀이 언어(language), 화면 색(scheme: light·dark. 없으면 운영체제 설정을 따른다)
MODELS_FILE = DATA / "models.json"  # 공급자 목록에서 고른 시리즈마다 최신 이름 {연결: {"at": ISO 시각, "names": {시리즈: 이름}}}. 하루에 한 번까지만 다시 받는다
KEPT_FILE = DATA / "kept.json"  # 언어를 바꿀 때 보관한 준비 결과 {문항: {언어: {"solution": 줄, "session": 줄}}}. 그 언어로 돌아오면 되살린다(모델 0회)


def load_keys() -> None:
    """키를 환경에 올린다. 이미 환경 변수에 있으면 그대로 둔다. 순서: 환경 변수 → 프로젝트·데이터 폴더의 .env → 화면에서 넣은 키."""
    for env_file in (ROOT / ".env", DATA / ".env"):
        try:
            lines = env_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            name, sep, value = line.strip().partition("=")
            if sep and name in KEYS.values() and value.strip():
                os.environ.setdefault(name, value.strip().strip('"\''))
    for name, value in read_json(KEY_FILE, {}).items():
        if name in KEYS.values() and isinstance(value, str) and value:  # 손으로 고쳐 형이 다른 값은 건너뛴다(서버는 뜬다)
            os.environ.setdefault(name, value)


def save_key(env_name: str, value: str) -> None:
    write_keys({**read_json(KEY_FILE, {}), env_name: value})


def drop_key(env_name: str) -> None:
    """화면에서 넣은 키 가운데 그 공급자의 것만 파일에서 지운다(다른 공급자의 키와 .env는 건드리지 않는다)."""
    write_keys({name: value for name, value in read_json(KEY_FILE, {}).items() if name != env_name})


def write_keys(saved: dict) -> None:
    write_json(KEY_FILE, saved)
    try:
        KEY_FILE.chmod(0o600)
    except OSError:  # Windows는 이 권한 비트를 쓰지 않는다(사용자 폴더 권한이 지킨다)
        pass


CLI = ClaudeCli()


def dev_client() -> bool:
    """개발용 연결(이 PC의 Claude Code)을 쓸 수 있게 띄웠는가. 화면은 그때만 그 선택지를 보이고, 요청도 그때만 받는다."""
    return os.environ.get("ALGOBLOCK_UI_CLIENT") == "cli"


STATE = {"client": "cli" if dev_client() else "provider"}
INDEX = []  # 비슷한 문항 찾기 색인(프로세스에 하나. 로컬 Qdrant는 폴더를 한 번만 연다)
INDEX_LOCK = threading.Lock()


def index():
    """qdrant-client가 없거나 못 열면 None(온톨로지와 SQLite만으로 돈다)."""
    with INDEX_LOCK:  # 첫 요청 여럿이 함께 와도 한 번만 연다(로컬 색인은 폴더를 한 번만 열 수 있어, 둘째가 실패하면 검색이 꺼진 채로 남았다)
        if not INDEX:
            try:
                from tutor.knowledge import embed
                from tutor.knowledge.index import open_index

                # 임베딩 모델 폴더: 정해 준 곳 → 데이터 폴더 → 설치 파일을 만들며 받아 둔 곳. 어디에도 없으면 벡터 검색을 끈다(내려받지 않는다)
                spots = [os.environ.get("ALGOBLOCK_EMBED_DIR") or "", str(DATA / "models"), str(APP / "packaging" / "models")]
                INDEX.append(open_index(str(DATA / "vectors"), next((spot for spot in spots if spot and embed.present(spot)), None)))
            except Exception:  # noqa: BLE001 - 색인은 덤이다
                INDEX.append(None)
        return INDEX[0]


REPORTS: dict[str, tuple[str, dict]] = {}  # 문항 → (채점한 코드, 채점 결과). 디버깅이 다시 쓴다
LANG: dict[str, str] = {}  # 문항 → 지금 고른 언어(요청마다 저장소에서 읽어 적어 둔다. 가이드 채점 verify가 쓴다)
LOCKS: dict[str, threading.Lock] = defaultdict(threading.Lock)  # 문항마다 모델 요청은 한 번에 하나(미리 뽑기와 첫 질문이 겹치지 않게)
PREPARED: set[str] = set()
PREPARING: set[str] = set()  # 지금 뒤에서 미리 만들기가 도는 문항(화면이 '준비 중'을 보여 준다)
PREP_FAILED: set[str] = set()  # 마지막 미리 만들기가 실패한 문항(화면이 '준비하지 못했어요'와 '다시 준비'를 보여 준다)
RECHECKED: set[str] = set()  # 이 프로세스에서 대조를 시작한 문항(대조 없이 준비해 둔 등록 문제를 열 때 한 번)
TOOLS: dict[str, bool] = {}  # 언어 → 이 기기에 실행 도구가 있는가. 한 번 세어 두고, 화면이 '다시 확인'하면 다시 센다
FILE_LOCK = threading.Lock()


class Refuse(Exception):
    """화면에 그대로 보여 줄 거절."""

    def __init__(self, message: str, status: int = 400, code: str = "validation", field: str = ""):
        super().__init__(message)
        self.status, self.code, self.field = status, code, field


def read_json(path: Path, default):
    """없으면 기본값. 깨졌거나 형이 다르면 <이름>.broken-<때>로 옮겨 두고(사용자가 되살릴 수 있게) 기본값."""
    try:
        raw = path.read_bytes()
    except OSError:
        return default
    try:
        value = json.loads(raw.decode("utf-8"))
        if default is None or type(value) is type(default):
            return value
    except (ValueError, RecursionError):  # JSON 오류, UTF-8 오류, 너무 깊은 중첩
        pass
    stamp = time.strftime("%Y%m%d-%H%M%S")
    broken, n = path.with_name(f"{path.name}.broken-{stamp}"), 1
    while broken.exists():  # 덮어쓰지 않는다
        broken, n = path.with_name(f"{path.name}.broken-{stamp}-{n}"), n + 1
    try:
        path.rename(broken)
        print(f"{path}을(를) 읽지 못해 {broken.name}(으)로 옮겨 두고 기본값으로 시작합니다.", file=sys.stderr)
    except OSError as exc:  # 다른 요청이 먼저 옮겼거나 읽기 전용 폴더다
        print(f"{path}을(를) 읽지 못해 기본값으로 시작합니다(옮기지 못함: {exc}).", file=sys.stderr)
    return default


def write_json(path: Path, data) -> None:
    with FILE_LOCK:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)


def extra_titles() -> dict:
    """ALGOBLOCK_EVAL_EXTRA 폴더 문제의 제목(시나리오는 제목을 싣지 않는다)."""
    root = os.environ.get("ALGOBLOCK_EVAL_EXTRA", "")
    rows = [read_json(path, {}) for path in sorted(Path(root).glob("*.json"))] if root else []
    return {raw.get("scenario_id"): raw.get("title") for raw in rows if raw.get("title")}


def first_line(text: str) -> str:
    line = next((row.strip() for row in text.splitlines() if row.strip()), "제목 없는 문제")
    return line if len(line) <= 28 else line[:27] + "…"


# 기본 문제(make_builtin.py가 ui/problems에서 묶는다): 글, 케이스(공개 예시·숨긴 정확성·숨긴 효율성), 실전 신호, 언어별 정답 풀이·시작 코드,
# 그리고 미리 만들어 둔 뼈대·풀이 가이드·블록 계획(ready. 없을 수 있다). 단계가 없는 예전 형식은 읽지 않는다
BUILTIN = {row["id"]: row for row in read_json(Path(os.environ.get("ALGOBLOCK_UI_BUILTIN") or STATIC_DIR / "builtin.json"), []) if "level" in row}
THEME_ORDER = {key: n for n, key in enumerate(ALGORITHMS)}


def theme_name(key: str) -> str:
    return algorithm_name(key).split("(")[0]


def load_problems() -> dict:
    """등록한 문항(최근 등록이 위) 다음에 기본 문제(주제 순서, 단계 순서).
    평가용 예시 문제는 개발할 때만 보인다(ALGOBLOCK_EVAL_EXTRA를 주거나 ALGOBLOCK_UI_SCENARIOS=1). 글이 같은 것은 하나만 둔다."""
    out, seen = {}, set()
    for raw in reversed(read_json(PROBLEMS_FILE, [])):
        if not isinstance(raw, dict) or not {"id", "title", "language", "text", "cases"} <= raw.keys():  # 꼭 필요한 키가 없는 행은 건너뛴다
            continue
        theme = raw.get("theme") if raw.get("theme") in ALGORITHMS else ""  # 사용자가 붙인 주제(없으면 빈 글)
        mode = "program" if raw.get("mode") == "program" else "function"  # 푸는 방식. 없는 예전 문항은 함수 방식
        made = [case for case in raw.get("made") or [] if isinstance(case, dict)]  # 대조로 만든 숨은·효율성 케이스(made: true). 사용자가 넣은 케이스(cases)와 따로 둔다
        level = raw.get("level") if raw.get("level") in range(1, 6) else 0  # 사용자가 고친 단계(없으면 분석이 붙인 것을 목록이 쓴다)
        out[raw["id"]] = SimpleNamespace(**{**raw, "theme": theme, "mode": mode, "cases": [*raw["cases"], *made], "level": level},
                                         sample=False, builtin=False, theme_name=theme_name(theme) if theme else "")
    for row in sorted(BUILTIN.values(), key=lambda row: (THEME_ORDER.get(row["theme"], 99), row["level"])):
        seen.add(row["text"])
        out[row["id"]] = SimpleNamespace(id=row["id"], title=row["title"], language="python", text=row["text"], cases=row["cases"],
                                         sample=True, builtin=True, theme=row["theme"], theme_name=theme_name(row["theme"]), level=row["level"], mode="function")
    if os.environ.get("ALGOBLOCK_EVAL_EXTRA") or os.environ.get("ALGOBLOCK_UI_SCENARIOS") == "1":
        titles = SAMPLE_TITLES | extra_titles()
        for s in all_scenarios():
            if s.text in seen or s.id in out:
                continue
            seen.add(s.text)
            out[s.id] = SimpleNamespace(id=s.id, title=titles.get(s.id) or first_line(s.text), language=s.language, text=s.text, cases=s.cases,
                                        sample=True, builtin=False, theme=s.algorithm, theme_name=theme_name(s.algorithm), level=0, mode="function")
    return out


PROBLEMS = load_problems()
themes.choose(read_json(PREFS_FILE, {}).get("stages") or themes.from_old(read_json(PREFS_FILE, {}).get("themes")))  # 저장해 둔 과정별 급을 올린다(예전 테마별 모델은 급으로 옮긴다)
for _here, _row in read_json(MODELS_FILE, {}).items():  # 지난번에 받아 둔 최신 이름(꼴을 다시 본다. 손으로 고친 값은 버린다)
    if _here in themes.SERIES and isinstance(_row, dict) and isinstance(_row.get("names"), dict):
        themes.NEWEST[_here] = themes.newest(_row["names"].values())


@lru_cache(maxsize=12)  # 큰 입력 글은 하나에 1~2MB다. 최근에 채점한 것만 들고 있는다
def large_case(pid: str, index: int) -> dict:
    """효율성 케이스의 큰 입력 {input(인자 배열의 JSON 글)[, expected]}. 기본 문제는 저장해 두지 않고 실린 gen.py 소스와 고정 씨앗으로 다시 만든다(언제 만들어도 같다).
    등록한 문제는 대조할 때 만들어 둔 파일(LARGE)에서 읽는다(기대 결과도 거기 있다)."""
    if pid in BUILTIN:
        return {"input": json.dumps(casegen.large_args(pid, BUILTIN[pid]["large"], index), ensure_ascii=False)}
    return read_json(LARGE / pid / f"{index}.json", {"input": "[]", "expected": "null"})


def materialize(p, language: str) -> list[dict]:
    """채점기에 넣을 케이스 [{id, kind, input, expected[, timeout]}]. 종류가 없는 케이스(사용자가 등록한 공개 예시, 예전 문항)는 공개 예시다."""
    # 기본 문제는 정답 풀이가 걸린 시간에서 정한 문제·언어별 제한(limits.json), 등록한 문제는 대조할 때 정답 풀이가 걸린 시간에서 정한 그 언어의 제한
    rows, limits = [], (BUILTIN.get(p.id) or {}).get("limits") or getattr(p, "limits", None) or {}
    for case in p.cases:
        kind = case.get("kind", "example")
        big = large_case(p.id, case["gen"]) if "input" not in case else {}
        rows.append({"id": case["id"], "kind": kind, "input": case["input"] if "input" in case else big["input"], "expected": case["expected"] if "expected" in case else big["expected"],
                     **({"timeout": limits.get(language) or casegen.LIMIT.get(language, 10)} if kind == "efficiency" else {})})  # 효율성 케이스는 언어마다 제한 시간이 다르다
    return rows


def grade(p, language: str, code: str, kinds: tuple = KINDS, stop_after: int | None = None, timeout: float | None = None) -> dict:
    """채점기를 돌린다(제출로 남기지 않는다). {status, reason, compile, compile_line, language, cases[{id, kind, input, expected, got, error, status, ms, line, near, limit}]}.
    status는 케이스 상태(passed, failed, runtime_error, timeout, skipped, output_limit, memory_limit)이거나
    채점하지 못한 까닭(compile_error, toolchain_missing, entry_missing, unsupported_signature, undecided, no_cases, bad_case)이다.
    line(오류가 난 내 코드의 줄), near(제한 시간에 가깝게 통과), compile_line은 채점기가 줄 때만 있다.
    stop_after: 연속 시간 초과가 이만큼이면 남은 케이스를 돌리지 않는다(없으면 채점기의 기본값).
    timeout: 케이스마다의 제한 시간이 없는 케이스에 줄 제한(초. 없으면 채점기의 기본값)."""
    cases = [case if "timeout" in case or not timeout else {**case, "timeout": timeout} for case in materialize(p, language) if case["kind"] in kinds]
    raw = check_judge().judge(language, code, [{key: case[key] for key in ("id", "input", "expected", "timeout") if key in case} for case in cases], problem=p.text, mode=p.mode,
                              decimal=p.mode == "program" and getattr(p, "float_output", False) is True, **({"stop_after": stop_after} if stop_after else {}))
    by, many = {case["id"]: case for case in cases}, getattr(p, "many_answers", False) is True
    rows = [{"id": c["id"], "kind": by[c["id"]]["kind"], "input": by[c["id"]]["input"], "expected": c["expected"],
             "got": (c.get("stdout") or "") if p.mode == "program" else (c.get("stdout") or "").strip(),  # 프로그램 방식은 출력 전체(앞 공백도 답이다)
             "error": c.get("stderr") or "", "status": c["status"], "ms": c.get("time_ms", 0), "line": c.get("line"), "near": c.get("near") is True,
             "limit": by[c["id"]].get("timeout"), **({"note": MANY_ANSWERS} if many and c["status"] == "failed" else {})} for c in raw.get("cases", [])]
    return {"status": raw["status"], "reason": raw.get("reason") or "", "cases": rows, "compile": (raw.get("compile") or {}).get("stderr", ""),
            "compile_line": raw.get("compile_line"), "language": language, "notice": notice_of(raw)}


# 채점기가 Windows에서 실행 제한(작업 객체)을 걸지 못했을 때(결과의 warning) 화면에 한 줄로 알린다. 무엇이 빠졌는지와 무엇을 뜻하는지
# 작업 없이 돌렸으면(no_job) 시간 제한과 0.25초마다 재는 메모리 상한은 그대로 걸린다. 시작하지 못했으면(not_started) 그 실행은 실행 오류로 끝났다
NO_LIMITS = ("이 PC에서는 채점 실행 제한(CPU 시간 상한, 커밋 메모리 상한, 끝난 뒤 남은 프로그램 정리)을 걸지 못하고 돌렸어요. "
             "채점 결과는 그대로지만, 코드가 띄운 다른 프로그램이 남아 있을 수 있어요.")
NOT_STARTED = "이 PC에서 제출 코드를 시작하지 못해 실행 오류로 끝난 테스트가 있어요. 다시 해 보고, 계속되면 GitHub 이슈로 알려 주세요."


def notice_of(raw: dict) -> str:
    """채점기 결과(컴파일 포함)의 warning을 화면의 한 줄로: 시작하지 못한 실행이 있으면 NOT_STARTED, 작업 없이 돈 실행이 있으면 NO_LIMITS, 없으면 빈 글."""
    kinds = {part.get("warning_kind") for part in [raw.get("compile") or {}, *raw.get("cases", [])] if part.get("warning")}
    return NOT_STARTED if "not_started" in kinds else NO_LIMITS if kinds else ""


# 앱의 다른 말처럼 '~어요'
LIMIT_WORDS = {"output_limit": "출력이 너무 많아 멈췄어요(끝나지 않는 반복일 수 있어요)", "memory_limit": "메모리를 너무 많이 써서 멈췄어요"}


def tutor_view(report: dict) -> dict:
    """채점 결과를 튜터 엔진이 읽는 모양으로: 큰 입력(효율성 케이스)은 글을 싣지 않고, 엔진이 모르는 상태는 실행 오류로 바꾼다."""
    cases = []
    for case in report["cases"]:
        limit = LIMIT_WORDS.get(case["status"])
        status = "runtime_error" if limit else "timeout" if case["status"] == "skipped" else case["status"]  # 돌리지 않은 케이스는 앞선 시간 초과 탓이다
        cases.append({"id": case["id"], "kind": case["kind"], "input": "(아주 큰 입력)" if case["kind"] == "efficiency" else case["input"], "expected": case["expected"],
                      "got": "" if case["kind"] == "efficiency" else case["got"], "error": limit or case["error"], "status": status, "line": case.get("line")})
    status = report["status"] if not cases else next((case["status"] for case in cases if case["status"] != "passed"), "passed")
    return {"status": status, "cases": cases, "compile": report["compile"], "compile_line": report.get("compile_line")}  # 줄은 채점기가 알려 준 오류의 줄(이어 붙인 프로그램의 줄)


def verify(pid: str, code: str, quick: bool = False) -> dict | None:
    """풀이 가이드의 정답 코드를 이 문항의 테스트 케이스로 채점한다(제출로 남기지 않는다). 케이스가 없으면 None.
    quick: 효율성 케이스를 빼고 돌고, 시간 초과가 한 번 나오면 남은 케이스를 돌리지 않는다(블록 코드 확인. 한 번에 여러 번 돌 수 있다. 끝나지 않는 반복에 30초)."""
    found = PROBLEMS.get(pid)
    if found is None or not found.cases:
        return None
    language, kinds = LANG.get(pid, found.language), tuple(kind for kind in KINDS if kind != "efficiency") if quick else KINDS
    # 끝나지 않는 반복이 채점기 기본 제한(10초)까지 기다렸다. 기본 문제는 그 언어의 효율성 제한(최소 2초)으로 줄인다
    limit = ((BUILTIN.get(pid) or {}).get("limits") or {}).get(language)
    return tutor_view(grade(found, language, code, kinds, stop_after=1 if quick else None, timeout=max(2.0, limit) if quick and limit else None))


def given(pid: str, language: str) -> dict | None:
    """기본 문제는 풀이 가이드를 새로 풀지 않는다: 실린 그 언어의 정답 풀이가 가이드 코드다. 단서·방향·단계는 미리 만든 것(언어와 상관없다)을 그대로 쓴다."""
    row = BUILTIN.get(pid)
    if row is None or language not in row["solutions"]:
        return None
    guide = (row.get("ready") or {}).get("solution") or {}
    return {"code": row["solutions"][language], "clues": guide.get("clues"), "approach": guide.get("approach"), "steps": guide.get("steps")}


def problem_shape(pid: str, language: str) -> dict:
    """엔진에 넘기는 문항의 방식과 이 언어의 시작 코드(블록 코드 확인이 방식을 짐작하지 않고, 풀이 가이드가 시작 코드의 머리를 따른다)."""
    p = PROBLEMS.get(pid)
    return {} if p is None else {"mode": p.mode, "starter": starter_of(p, language), "many_answers": getattr(p, "many_answers", False) is True}


def cross_mode(pid: str) -> str | None:
    """대조할 문제(등록한 문제)의 푸는 방식. 기본 문제·예시 문제는 None(대조하지 않는다: 기본 문제는 problemkit으로 검수해 실었다).
    답이 여럿일 수 있는 문제도 None이다: 정답 풀이의 답 하나를 기대 출력으로 삼는 숨은 테스트는 다른 맞는 답을 틀렸다고 한다."""
    p = PROBLEMS.get(pid)
    return p.mode if p is not None and OWN_ID.fullmatch(pid) and getattr(p, "many_answers", False) is not True else None


def cross_run(pid: str, code: str, brute: str, maker: str, bounds: list) -> dict:
    """정답 풀이와 단순 풀이를 생성기의 입력에서 채점기로 대조한다(casemake). 맞으면 숨은·효율성 케이스를 문제에 붙인다(사용자가 넣은 케이스와 따로, made)."""
    p = PROBLEMS[pid]
    language = LANG.get(pid, p.language)
    examples = [case for case in p.cases if not case.get("made")]
    arity = len(json.loads(examples[0]["input"])) if p.mode == "function" and examples else None
    found = casemake.make(language, p.mode, code, brute, maker, bounds, arity, decimal=p.mode == "program" and getattr(p, "float_output", False) is True)
    if found["status"] == "same":
        folder = LARGE / pid
        shutil.rmtree(folder, ignore_errors=True)
        made = [{"id": f"m{n}", "kind": "accuracy", "input": given, "expected": expected, "made": True} for n, (given, expected) in enumerate(found["hidden"], 1)]
        for n, (given, expected) in enumerate(found["large"]):
            folder.mkdir(parents=True, exist_ok=True)
            write_json(folder / f"{n}.json", {"input": given, "expected": expected})
            made.append({"id": f"e{n + 1}", "kind": "efficiency", "gen": n, "made": True})
        large_case.cache_clear()
        with FILE_LOCK_ROWS:
            rows = read_json(PROBLEMS_FILE, [])
            for row in rows:
                if isinstance(row, dict) and row.get("id") == pid:
                    row["made"] = made
                    row.pop("limits", None)
                    if found["limit"]:
                        row["limits"] = {language: found["limit"]}
            write_json(PROBLEMS_FILE, rows)
        reload_problems()
    return {"status": found["status"], "why": found.get("why") or "", "input": found.get("input"), "got": found.get("got"), "want": found.get("want"), "slow": bool(found.get("slow")),
            "hidden": len(found.get("hidden") or []), "efficiency": len(found.get("large") or []), "dropped": found.get("dropped", 0)}


def cross_done(pid: str, verdict: dict) -> None:
    """대조 결과(검증, 쓴 호출 수와 급, 확인이 필요한 곳, 까닭)를 문제에 남긴다. 다음에 열 때 다시 대조하지 않는다."""
    with FILE_LOCK_ROWS:
        rows = read_json(PROBLEMS_FILE, [])
        for row in rows:
            if isinstance(row, dict) and row.get("id") == pid:
                row["check"] = {**verdict, "at": now()}
        write_json(PROBLEMS_FILE, rows)
    reload_problems()


CROSS = SimpleNamespace(mode=cross_mode, run=cross_run, done=cross_done)
UNVERIFIED = {"verified": "none", "calls": 0, "tiers": [], "doubts": [], "hidden": 0, "efficiency": 0,
              "why": "AI의 풀이를 얻지 못해 검증하지 못했어요. 응답 오류였거나 예시가 문제 글과 맞지 않을 수 있어요."}

FILE_LOCK_ROWS = threading.RLock()  # problems.json을 읽고 고쳐 쓰는 동안(뒤에서 도는 대조와 등록·수정이 서로 덮어쓰지 않게)
VERIFIED_WORDS = {"all": "예시와 자동 테스트 모두 통과", "examples": "예시만 통과", "none": "검증하지 못함"}


@contextmanager
def tutor():
    """요청마다 연결 하나(SQLite 연결은 만든 스레드에서만 쓴다)."""
    one = Tutor(str(DB), index=index(), check=verify, given=given, cross=CROSS, shape=problem_shape)
    try:
        yield one
    finally:
        one.close()


def model():
    return use_llm(CLI) if STATE["client"] == "cli" else nullcontext()


def problem(body: dict):
    found = PROBLEMS.get(str(body.get("id") or ""))
    if found is None:
        raise Refuse("문제를 찾지 못했어요.", 404, "not_found")
    return found


def prepare_later(pid: str) -> None:
    """뼈대(명세·패턴)와 블록 계획을 뒤에서 미리 만든다. 화면은 기다리지 않는다. 실패해도 첫 질문 때 다시 만든다."""
    if not PREPARE or pid in PREPARED or not connected():  # 모델이 연결되지 않았으면 만들 수 없다(AI 없이 풀 때)
        return
    PREPARED.add(pid)
    PREPARING.add(pid)
    PREP_FAILED.discard(pid)

    def run():
        try:
            with LOCKS[pid], model(), tutor() as t:
                out = t.prepare(pid)
                if out.status >= 400:  # 모델의 답이 어긋났거나 공급자 오류(엔진은 예외 대신 실패 결과를 돌려준다)
                    raise RuntimeError(f"{out.status} {out.body}")
                if CROSS.mode(pid) and t.store.load(pid).canonical is None and not getattr(PROBLEMS.get(pid), "check", None):
                    cross_done(pid, UNVERIFIED)  # 준비는 끝났는데 풀이 가이드를 얻지 못했다: 대조 결과가 없는 채로 두면 화면에서 '검증' 줄이 사라진다
        except Exception as exc:  # noqa: BLE001 - 덤이다
            PREPARED.discard(pid)
            PREP_FAILED.add(pid)
            print(f"prepare {pid}: {type(exc).__name__}: {exc}"[:500], file=sys.stderr)
        finally:
            PREPARING.discard(pid)

    threading.Thread(target=run, daemon=True, name=f"prepare-{pid}").start()


def recheck_later(pid: str) -> None:
    """대조 없이 준비해 둔 등록 문제를 뒤에서 한 번 대조한다(Tutor.recheck). 다시 푼 풀이가 대조를 통과해 가이드가 바뀌면,
    옛 코드로 짠 블록 계획을 지우고 새 가이드로 다시 짠다(사용자의 코드·제출 기록은 남는다)."""
    if not PREPARE or pid in RECHECKED or pid in PREPARING or not connected():
        return
    RECHECKED.add(pid)
    PREPARING.add(pid)

    def run():
        try:
            with LOCKS[pid], model(), tutor() as t:
                new = t.recheck(pid)
                if new is not None:
                    drop_plan(t, pid)
                    ctx = t.store.load(pid)
                    t.store.save_success(ctx, None, 0, None, [], None, solution=new)
                    out = t.prepare(pid)
                    if out.status >= 400:
                        raise RuntimeError(f"{out.status} {out.body}")
        except Exception as exc:  # noqa: BLE001 - 덤이다(다시 열면 지금 계획 그대로 푼다)
            print(f"recheck {pid}: {type(exc).__name__}: {exc}"[:500], file=sys.stderr)
        finally:
            PREPARING.discard(pid)

    threading.Thread(target=run, daemon=True, name=f"recheck-{pid}").start()


def chatgpt_status() -> dict:
    """ChatGPT 요금제 로그인 상태 {"connected", "error"(연결되지 않은 까닭, 사람 말)}."""
    try:
        from app.llm.openai.oauth import token

        return token.login_status()
    except Exception:  # noqa: BLE001 - 모델 연결 코드(app/llm)가 없어도 화면은 뜬다
        return {"connected": False, "error": None}


def chatgpt_connected() -> bool:
    return bool(chatgpt_status().get("connected"))


def connected() -> bool:
    """모델을 부를 수 있는가(키, ChatGPT 로그인, 개발용 CLI)."""
    return STATE["client"] == "cli" or any(os.environ.get(env) for env in KEYS.values()) or chatgpt_connected()


def accounts() -> dict:
    chatgpt = chatgpt_status()
    refresh_models()
    rows = []
    for key, (label, _, _) in themes.THEMES.items():
        (tier, effort), (tier_default, effort_default) = themes.chosen(key), themes.default(key)
        model = themes.model_of(tier)
        rows.append({"key": key, "label": label, "tier": tier, "effort": effort, "default_tier": tier_default, "default_effort": effort_default,
                     "model": model, "model_label": themes.label(model)})
    return {"client": STATE["client"], "dev": dev_client(), "model": os.environ.get("ALGOBLOCK_LLM_MODEL", ""), "chatgpt": bool(chatgpt.get("connected")), "chatgpt_note": chatgpt.get("error") or "", "connected": connected(),
            "keys": {name: bool(os.environ.get(env)) for name, env in KEYS.items()},
            "keys_saved": {name: env in read_json(KEY_FILE, {}) for name, env in KEYS.items()},  # 화면에서 넣은 키(keys.json에 있는 것. 지울 수 있는 것)
            "tour_seen": bool(read_json(PREFS_FILE, {}).get("tour_seen")), "language": last_language(), "scheme": scheme_pref(),
            "themes": rows, "tiers": [{"key": tier, "label": themes.label(themes.model_of(tier))} for tier in themes.TIERS],
            "topics": [{"key": key, "name": theme_name(key)} for key in ALGORITHMS]}  # 등록 화면의 주제 고르기


MODEL_TRIED: set[str] = set()  # 이 프로세스에서 모델 목록을 받으려 한 연결(실패해도 다시 켤 때까지 표의 이름을 쓴다)


def refresh_models() -> None:
    """지금 연결의 모델 목록을 뒤에서 받아 시리즈마다 최신 이름을 고른다(하루에 한 번까지만. 목록 요청은 돈이 들지 않는다).
    키나 ChatGPT 요금제로 연결했을 때만 받는다. 화면과 첫 호출은 기다리지 않는다. 미리 만들기를 끈 개발·시험에서는 받지 않는다."""
    here = themes.provider()
    ready = chatgpt_connected() if here == "chatgpt" else here in KEYS and os.environ.get(KEYS[here])
    if not PREPARE or STATE["client"] == "cli" or not ready or here in MODEL_TRIED:
        return
    at = (read_json(MODELS_FILE, {}).get(here) or {}).get("at")
    try:
        if at and datetime.now().astimezone() - datetime.fromisoformat(at) < timedelta(days=1):
            return
    except (TypeError, ValueError):  # 손으로 고친 시각이면 다시 받는다
        pass
    MODEL_TRIED.add(here)

    def run():
        try:
            from app.llm.claude.api_key import messages
            from app.llm.openai.api_key import chat
            from app.llm.openai.oauth import chat as plan

            names = themes.newest({"claude": messages.models, "openai": chat.models, "chatgpt": plan.models}[here]())
        except Exception as exc:  # noqa: BLE001 - 오프라인·권한 없음: 표의 이름을 쓴다
            print(f"models {here}: {type(exc).__name__}: {exc}"[:300], file=sys.stderr)
            return
        themes.NEWEST[here] = names
        write_json(MODELS_FILE, {**read_json(MODELS_FILE, {}), here: {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "names": names}})

    threading.Thread(target=run, daemon=True, name=f"models-{here}").start()


def scheme_pref() -> str:
    """고른 화면 색: light, dark, 없거나 모르는 값이면 system(운영체제 설정을 따른다)."""
    scheme = read_json(PREFS_FILE, {}).get("scheme")
    return scheme if scheme in ("light", "dark") else "system"


def last_language() -> str:
    """마지막으로 고른 풀이 언어(코드 화면에서 언어를 바꿀 때 적는다). 없거나 모르는 값이면 python."""
    language = read_json(PREFS_FILE, {}).get("language")
    return language if language in check_judge().LANGUAGES else "python"


def first_language(p) -> str:
    """처음 여는 문제의 언어: 기본 문제는 마지막으로 고른 언어(그 문제가 지원할 때), 아니면 문제의 언어."""
    language = last_language()
    return language if p.builtin and language in BUILTIN[p.id]["languages"] else p.language


def counts(t) -> dict:
    """문항 → (통과 수, 제출 수). 언어 도구가 없어 채점하지 못한 예전 기록은 세지 않는다."""
    try:
        rows = t.store.conn.execute("SELECT problem_id, COALESCE(SUM(ok), 0) AS passed, COUNT(*) AS total FROM submission "
                                    "WHERE status != 'toolchain_missing' GROUP BY problem_id").fetchall()
    except sqlite3.Error:
        return {}
    return {row["problem_id"]: (int(row["passed"]), int(row["total"])) for row in rows}


def starter_of(p, language: str) -> str:
    return BUILTIN[p.id]["starters"].get(language, "") if p.builtin else "" if p.sample else own_starter(p, language)


def touched(t) -> set:
    """저장된 코드가 시작 코드와 다른(손댄) 문항."""
    out = set()
    for row in t.store.conn.execute("SELECT id, language, direct_code FROM problem WHERE direct_code != ''").fetchall():
        p = PROBLEMS.get(row["id"])
        if p is not None and row["direct_code"].strip() != starter_of(p, row["language"]).strip():
            out.add(p.id)
    return out


def planned_themes(t) -> dict:
    """등록한 문항 → 튜터가 준비한 계획의 알고리즘(주제 15개 가운데 하나일 때만). 주제를 붙이지 않은 문항에 보여 주기만 한다(저장하지 않는다)."""
    out = {}
    for row in t.store.conn.execute("SELECT problem_id, plan_json FROM tutor_session WHERE plan_json IS NOT NULL").fetchall():
        if OWN_ID.fullmatch(row["problem_id"]):
            algorithm = (json.loads(row["plan_json"]) or {}).get("algorithm")
            out[row["problem_id"]] = algorithm if algorithm in ALGORITHMS else ""  # 15개 밖(예전 유형)이면 '기타'로 보인다
    return out


def report_themes(t) -> tuple[dict, dict]:
    """학습 보고서가 쓰는 문제의 주제(문제 → 주제): 붙인 주제가 먼저, 없으면 풀이 계획의 유형(대조 검증이 all인 등록 문제만).
    그리고 고른 주제가 계획의 유형과 다른 등록 문제 → 계획의 유형(보고서가 둘을 나란히 보인다)."""
    planned, theme_of, differ = planned_themes(t), {}, {}
    for pid, p in PROBLEMS.items():
        plan = planned.get(pid, "")
        if p.theme:
            theme_of[pid] = p.theme
            if plan and plan != p.theme:
                differ[pid] = plan
        elif plan and (getattr(p, "check", None) or {}).get("verified") == "all":
            theme_of[pid] = plan
    return theme_of, differ


def labels_of(t, p, marks: dict | None = None) -> dict:
    """문제의 라벨: 단계(사용자가 고친 것 > 분석이 붙인 것), 태그(쓰는 방법. 온톨로지 기법 이름), 검증(verified: all·examples·none, 아직 대조 전이면 빈 글)과 그 말.
    등록한 문제는 대조 결과(check)의 숨은·효율성 케이스 수와 확인이 필요한 곳(doubts), 까닭(why)도. marks: 미리 읽은 store.labels()(목록은 한 번만 읽는다)."""
    if p.builtin:
        tags = techniques_of(((BUILTIN[p.id].get("ready") or {}).get("fact") or {}).get("patterns") or [])
        return {"level": p.level, "tags": [TECHNIQUES[tid][1] for tid in tags], "verified": "all", "verified_name": VERIFIED_WORDS["all"]}
    if p.sample:
        return {"tags": [], "verified": "", "verified_name": ""}
    fact = (marks if marks is not None else t.store.labels()).get(p.id) or {}
    check = getattr(p, "check", None) or {}
    verified = check.get("verified") or ""
    return {"level": p.level or fact.get("level") or 0, "level_by": "user" if p.level else "analysis" if fact.get("level") else "",
            "tags": [TECHNIQUES[tid][1] for tid in fact.get("tags") or [] if tid in TECHNIQUES], "verified": verified, "verified_name": VERIFIED_WORDS.get(verified, ""),
            "check": {key: check[key] for key in ("hidden", "efficiency", "tiers", "calls", "why", "doubts") if key in check}}


def problem_rows(t) -> list[dict]:
    done, mine, guessed, marks = counts(t), touched(t), planned_themes(t), t.store.labels()
    chosen = {row["id"]: row["language"] for row in t.store.conn.execute("SELECT id, language FROM problem").fetchall()}  # 사용자가 고른 언어
    rows = []
    for p in PROBLEMS.values():
        passed, total = done.get(p.id, (0, 0))
        # 붙인 주제가 이긴다. 계획의 알고리즘이 15개 밖이면 주제 칩을 빼낸다
        shown = p.theme_name or (theme_name(guessed[p.id]) if not p.sample and guessed.get(p.id) else "")
        # 등급: 통과 2회마다 한 등급, 8회 이상 5등급
        rows.append({"id": p.id, "title": p.title, "language": chosen.get(p.id, p.language), "sample": p.sample, "builtin": p.builtin,
                     "theme": p.theme, "theme_name": shown, "level": p.level, "passed": passed, "submitted": total, "solved": passed > 0,
                     "touched": p.id in mine, "grade": min(5, 1 + min(passed, 10) // 2), **labels_of(t, p, marks)})
    return rows


def next_up(mine: list[dict], solved: set):
    """한 주제(단계 순서)에서 다음에 풀 문제: 위에 못 푼 단계가 남은 통과 단계 가운데 가장 높은 것 바로 위의 못 푼 단계(3·5단계를 통과했으면 4단계).
    통과한 단계 위에 못 푼 것이 없으면 가장 낮은 못 푼 단계. 다 풀었으면 None."""
    todo = [row for row in mine if row["id"] not in solved]
    for top in sorted({row["level"] for row in mine if row["id"] in solved}, reverse=True):
        above = [row for row in todo if row["level"] > top]
        if above:
            return above[0]
    return todo[0] if todo else None


def theme_rows(rows: list[dict]) -> list[dict]:
    """주제마다 몇 문제를 풀었고 다음에 풀 문제(next_up)가 무엇인가."""
    out = []
    for key in ALGORITHMS:
        mine = [row for row in rows if row["builtin"] and row["theme"] == key]
        if mine:
            todo = next_up(mine, {row["id"] for row in mine if row["solved"]})
            out.append({"key": key, "name": theme_name(key), "total": len(mine), "solved": sum(row["solved"] for row in mine),
                        "next": {"id": todo["id"], "title": todo["title"]} if todo else None})
    return out


def tools(refresh: bool = False) -> dict:
    """언어 → 이 기기에 실행 도구가 있는가. 채점기가 채점 전에 도구를 찾는 방법(judge.judge의 첫 검사)을 그대로 쓴다."""
    if refresh or not TOOLS:
        judge = check_judge()
        for language in judge.LANGUAGES:
            lang = judge.load_language(language)
            TOOLS[language] = not (lang.toolchain() if hasattr(lang, "toolchain") else judge.common.missing(*lang.TOOLS))
    return dict(TOOLS)


def no_constant(name: str):
    raise ValueError(name)


JSON_WHY = {"quote": "문자열은 큰따옴표로 감싸요. 예: [\"mina\", \"joon\"]", "comma": "끝에 남은 쉼표를 지워 주세요."}  # 읽지 못한 까닭 → 고칠 말


def json_value(text: str):
    """JSON 값 하나. NaN·Infinity는 언어마다 달라 받지 않는다. 못 읽으면 ValueError(까닭: quote 작은따옴표, comma 끝에 남은 쉼표, json 그 밖)."""
    try:
        return json.loads(text, parse_constant=no_constant)
    except (ValueError, RecursionError):
        raise ValueError("quote" if "'" in text else "comma" if re.search(r",\s*[\]}]", text) else "json") from None


def case_args(given: str) -> list:
    """케이스의 넣을 값: solution에 넘길 값을 순서대로 담은 JSON 목록. 아니면 ValueError(까닭은 json_value, 목록이 아니면 list)."""
    args = json_value(given)
    if not isinstance(args, list):
        raise ValueError("list")
    return args


RESULT_HEADS = {"result", "return", "answer", "결과", "반환", "출력"}  # 입출력 예 표 머리의 마지막 칸


def table_cells(line: str) -> tuple[bool, list[str]]:
    """표 한 줄의 (마크다운인가, 칸들). 마크다운은 | a | b |, 아니면 탭이나 둘 이상의 공백으로 가른다(화면에서 복사한 표 꼴)."""
    row = line.strip()
    if row.startswith("|"):
        return True, [cell.strip() for cell in row.strip("|").split("|")]
    return False, [cell for cell in re.split(r"\t|\s{2,}", row) if cell.strip()]


def plain(value):
    """literal_eval이 읽은 값 가운데 JSON에 있는 것만. 튜플·집합 등은 받지 않는다('1,000'을 (1, 0)으로 읽지 않게)."""
    if isinstance(value, list):
        return [plain(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: plain(item) for key, item in value.items()}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise ValueError(type(value).__name__)


def cell_value(cell: str):
    """표 칸의 값: JSON, 아니면 파이썬식(True·False·None, 작은따옴표 문자열, 끝 쉼표)으로 읽는다. 못 읽으면 ValueError.
    따옴표 없는 낱말은 문자열로 짐작하지 않는다(literal_eval은 이름을 읽지 않는다)."""
    try:
        value = json_value(cell)
    except ValueError:
        try:
            value = plain(ast.literal_eval(cell))
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            raise ValueError(cell) from None
    json_value(json.dumps(value))  # 넘치는 수(1e999 → Infinity)는 받지 않는다
    return value


def table_cases(text: str) -> dict:
    """문제 글의 입출력 예 표를 케이스로(규칙만, 모델 0회). 머리의 마지막 칸이 결과(RESULT_HEADS)인 첫 표를 고른다.
    {names: 머리의 나머지 칸(인자 이름), cases: [{input: 인자들을 목록으로 감싼 JSON 글, expected: 결과의 JSON 글}], skipped: 읽지 못한 줄 수}.
    표가 없으면 cases가 빈 목록."""
    lines = text.splitlines()
    for at, line in enumerate(lines):
        md, head = table_cells(line)
        if len(head) < 2 or head[-1].strip("`* ").lower() not in RESULT_HEADS:
            continue
        cases, skipped, missed = [], 0, []
        for k, row in enumerate(lines[at + 1:], at + 1):
            if not row.strip():
                if cases or skipped:
                    missed = missed_after(lines, k)
                    break
                continue
            row_md, cells = table_cells(row)
            if row_md != md:
                missed = missed_after(lines, k)
                break
            if md and all(re.fullmatch(r":?-+:?", cell) for cell in cells):  # 마크다운 구분 줄
                continue
            if len(cells) != len(head):
                if not md:  # 탭 표는 칸 수가 다른 줄(설명 글)에서 끝난다
                    missed = missed_after(lines, k)
                    break
                skipped += 1
                continue
            try:
                values = [cell_value(cell) for cell in cells]
            except ValueError:
                skipped += 1
                continue
            cases.append({"input": json.dumps(values[:-1], ensure_ascii=False), "expected": json.dumps(values[-1], ensure_ascii=False)})
        if cases or skipped:
            return {"names": [cell.strip("`* ") for cell in head[:-1]], "cases": cases, "skipped": skipped, **({"missed": missed} if missed else {})}
    return flat_table(lines)


def missed_after(lines: list[str], at: int) -> list[str]:
    """표가 끝난 줄부터 바로 이어지는 '예시처럼 생긴 줄'(대괄호·숫자·쉼표가 대부분): 표로 읽지 못하고 버린 예시일 수 있다.
    글자 읽기가 깨뜨린 예시 한 줄('0, 2, 2, 3, 4,5, 1]   4')이 표의 끝으로 읽혀 조용히 빠졌다."""
    out = []
    while at < len(lines) and not lines[at].strip():  # 표와 그 줄 사이에 빈 줄이 끼기도 한다(글자 읽기)
        at += 1
    for row in lines[at:]:
        t = row.strip()
        if len(t) < 3 or not re.search(r"\d", t) or not re.search(r"[\[\],]", t) or len(re.findall(r"[\[\]\d,.\-\s\"']", t)) < 0.7 * len(t):
            break
        out.append(t)
    return out


def row_values(row: str) -> list | None:
    """칸 구분이 공백 하나로 접힌 표 한 줄(PDF에서 읽은 글: '[1, 2, 3] 5 2')의 값들. 앞에서부터 JSON 값을 하나씩 읽고(raw_decode),
    JSON이 아니면 공백에서 끊기는 가장 짧은 파이썬식 값(cell_value)을 읽는다. 하나라도 못 읽으면 None."""
    values, at, row = [], 0, row.strip()
    while at < len(row):
        try:
            end = JSON_READER.raw_decode(row, at)[1]
            values.append(cell_value(row[at:end]))  # 넘치는 수(1e999)는 cell_value가 거른다
        except ValueError:
            ends = [m.start() for m in re.finditer(r"\s", row[at:])] + [len(row) - at]
            end = next((at + n for n in ends if readable(row[at:at + n])), None)
            if end is None:
                return None
            values.append(cell_value(row[at:end]))
        if end < len(row) and not row[end].isspace():  # 값 다음은 공백이어야 한다('1,000'은 1과 ',000'이 아니다)
            return None
        at = end
        while at < len(row) and row[at].isspace():
            at += 1
    return values


JSON_READER = json.JSONDecoder(parse_constant=no_constant)


def readable(cell: str) -> bool:
    try:
        cell_value(cell)
        return True
    except ValueError:
        return False


def flat_table(lines: list[str]) -> dict:
    """마크다운 표·탭 표가 없을 때: 머리 줄을 공백으로 나눈 낱말의 마지막이 결과 낱말(RESULT_HEADS)이고, 뒤따르는 줄에서 값을 차례로 읽어(row_values)
    값의 수가 머리 낱말 수와 같은 줄을 케이스로 본다(PDF에서 읽은 표). 한 줄이라도 맞으면 표다. 맞지 않는 줄에서 표가 끝난다."""
    for at, line in enumerate(lines):
        head = line.split()
        if len(head) < 2 or head[-1].strip("`* ").lower() not in RESULT_HEADS:
            continue
        cases, missed = [], []
        for k, row in enumerate(lines[at + 1:], at + 1):
            if not row.strip():
                if cases:
                    missed = missed_after(lines, k)
                    break
                continue
            values = row_values(row)
            if values is None or len(values) != len(head):
                missed = missed_after(lines, k) if cases else []
                break
            cases.append({"input": json.dumps(values[:-1], ensure_ascii=False), "expected": json.dumps(values[-1], ensure_ascii=False)})
        if cases:
            return {"names": [cell.strip("`* ") for cell in head[:-1]], "cases": cases, "skipped": 0, **({"missed": missed} if missed else {})}
    return {"names": [], "cases": [], "skipped": 0}


SAMPLE_HEAD = re.compile(r"\s*(?:#+\s*)?(예제\s*입력|입력\s*예|sample\s+input|예제\s*출력|출력\s*예|sample\s+output)\s*(\d+)\s*(?:복사)?\s*:?\s*", re.IGNORECASE)


def stdin_text(text) -> str:
    """표준 입력에 넣을 글: 줄 끝은 \\n, 비었으면(공백뿐이어도) 빈 글, 아니면 줄바꿈으로 끝나게 한다(마지막 줄을 줄 단위로 읽는 프로그램이 있다)."""
    text = str(text).replace("\r\n", "\n")
    return "" if not text.strip() else text if text.endswith("\n") else text + "\n"


SPILL = "예시 {n}의 기대 출력에 빈 줄 뒤로 글이 더 있어요. 출력이 아닌 글이 섞였는지 확인해 주세요."  # 예제 출력 뒤의 힌트·출처 글을 삼켰을 수 있다


def sample_cases(text: str) -> dict:
    """문제 글의 예제 구역('예제 입력 N' 꼴)을 케이스로(규칙만, 모델 0회). '예제 입력 N'·'예제 출력 N'(또는 '입력 예 N'·'출력 예 N', 'Sample Input N'·'Sample Output N') 머리 다음부터
    다음 머리나 빈 줄 둘 전까지의 글을 번호가 같은 것끼리 짝짓는다(입력 머리가 없으면 입력 없는 문제). 코드 울타리 줄(```)은 뺀다.
    table_cases와 같은 모양 {names: [], cases: [{input, expected}], skipped: 출력이 없거나 빈 번호 수}. 기대 출력 안에 빈 줄이 있으면 spill에 알림 글."""
    found, at, blank = {}, None, 0  # (입력인가, 번호) → 줄들
    for line in text.splitlines():
        head = SAMPLE_HEAD.fullmatch(line)
        if head:
            at, blank = ("입력" in head[1] or "input" in head[1].lower(), int(head[2])), 0
            found[at] = []
            continue
        blank = blank + 1 if not line.strip() else 0
        if blank >= 2:
            at = None
        if at is not None and not line.strip().startswith("```"):
            found[at].append(line)
    def block(key) -> str:  # 앞뒤의 빈 줄(공백뿐인 줄 포함)만 뗀다. 줄 앞 공백은 답이다
        return re.sub(r"\A\s*\n|\n\s*\Z", "", "\n".join(found.get(key, [])))

    cases, skipped, spill = [], 0, []
    for n in sorted({n for _, n in found}):
        expected = block((False, n))
        if not expected.strip():
            skipped += 1
            continue
        cases.append({"input": stdin_text(block((True, n))), "expected": expected + "\n"})
        if re.search(r"\n[ \t]*\n", expected):  # 끊는 규칙은 그대로 두고 알리기만 한다(빈 줄이 든 출력도 있다. 낱말 목록으로 끊으면 새 짐작이다)
            spill.append(SPILL.format(n=n))
    return {"names": [], "cases": cases, "skipped": skipped, **({"spill": spill} if spill else {})}


ARG_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# 일곱 언어의 흔한 예약어와, 시작 코드·채점기가 쓰는 이름(answer, solution). 인자 이름이 이것과 같으면 뒤에 _를 붙인다
RESERVED = set("""
and as assert async await auto bool boolean break byte case catch chan char class const continue crate debugger def default defer del delete do double dyn
elif else enum eval except explicit export extends extern false False fallthrough final finally float fn for friend fun func function go goto if impl
implements import in inline instanceof int interface is lambda len let long loop map match mod move mut namespace new nil None nonlocal not null object
operator or package pass private protected pub public raise range ref register return select self Self short signed sizeof static string String struct
super switch template this throw throws trait true True try type typedef typename typeof union unsafe unsigned use using val var vector virtual void
volatile when where while with yield answer solution Solution
""".split())


def arg_names(body: dict, cases: list[dict]) -> list[str] | None:
    """등록 요청의 names(입출력 예 표 머리의 인자 이름): 식별자 모양이고 서로 다르고 인자 수와 같을 때만. 아니면 None(버린다)."""
    names = body.get("names")
    if not isinstance(names, list) or not names or not all(isinstance(name, str) and ARG_NAME.fullmatch(name) for name in names):
        return None
    return names if len(set(names)) == len(names) == len(json.loads(cases[0]["input"])) else None


def reload_problems() -> None:
    global PROBLEMS
    PROBLEMS = load_problems()  # 통째로 바꿔 끼운다: 뒤에서 도는 대조가 다시 올리는 동안 다른 요청이 빈 목록을 보지 않게


def own(body: dict):
    """사용자가 등록한 문항만(기본 문제와 예시 문제는 고치거나 지울 수 없다)."""
    found = problem(body)
    if found.sample:
        raise Refuse("기본 문제는 고치거나 지울 수 없어요.")
    return found


def shape(value):
    """케이스끼리 견줄 값의 모양: int, float, str, bool, null, obj, 목록은 ("list", 원소 모양). 빈 목록의 원소는 None(무엇과도 어울린다).
    한 목록 안에 어울리지 않는 원소가 섞였으면 원소 모양은 mixed."""
    if isinstance(value, list):
        elem = None
        for item in value:
            try:
                elem = joined(elem, shape(item))
            except ValueError:
                return ("list", "mixed")
        return ("list", elem)
    return next(name for kind, name in ((bool, "bool"), (int, "int"), (float, "float"), (str, "str"), (type(None), "null"), (dict, "obj")) if isinstance(value, kind))


def joined(a, b):
    """두 모양을 합친다(정수와 실수는 실수, 빈 목록은 다른 쪽). 어울리지 않으면 ValueError."""
    if a is None or b is None:
        return b if a is None else a
    if isinstance(a, tuple) and isinstance(b, tuple):
        return ("list", joined(a[1], b[1]))
    if a == b:
        return a
    if {a, b} == {"int", "float"}:
        return "float"
    raise ValueError


def mixed(value) -> bool:
    """목록(안의 목록까지) 하나에 서로 어울리지 않는 종류의 값이 섞였는가(null은 무엇과도 섞여도 된다. 정수와 실수는 어울린다)."""
    if not isinstance(value, list):
        return False
    if any(mixed(item) for item in value):
        return True
    try:
        merged = None
        for item in value:
            if item is not None:
                merged = joined(merged, shape(item))
    except ValueError:
        return True
    return False


SHAPE_WORDS = {"int": "정수", "float": "실수", "str": "문자열", "bool": "참·거짓", "null": "빈 값", "obj": "묶음", "mixed": "여러 형이 섞인", None: ""}


def shape_name(s) -> str:
    depth = 0
    while isinstance(s, tuple):
        s, depth = s[1], depth + 1
    word = SHAPE_WORDS[s]
    return word if not depth else (word + " " if word else "") + ("배열" if depth == 1 else f"{depth}차원 배열")


def yo(word: str) -> str:
    """'…예요/이에요': 받침이 있는 한글로 끝나면 이에요."""
    last = word[-1]
    return word + ("이에요" if not "가" <= last <= "힣" or (ord(last) - 0xAC00) % 28 else "예요")


def same_shapes(rows: list[tuple[int, object]], word: str, field: str) -> None:
    """케이스들의 같은 자리 값이 서로 어울리는지(rows: [(케이스 번호, 값)]). 어울리지 않으면 앞 케이스 가운데 처음 어긋난 것을 짚어 거절한다."""
    seen = []
    merged = None
    for n, value in rows:
        mine = shape(value)
        try:
            merged = joined(merged, mine)
        except ValueError:
            m, other = next(((m, s) for m, s in seen if not fits_shape(s, mine)), seen[0])
            raise Refuse(f"{n}번 케이스의 {word} {shape_name(mine)}인데 {m}번 케이스는 {yo(shape_name(other))}.", field=f"{field}-{n}") from None
        seen.append((n, mine))


def fits_shape(a, b) -> bool:
    try:
        joined(a, b)
        return True
    except ValueError:
        return False


def checked(body: dict, mode: str = "function") -> tuple[str, str, list[dict]]:
    """등록·수정 글의 검사: (제목, 문제 글, 케이스). 빈 줄의 케이스는 뺀다. 케이스끼리 인자 수와 자리마다의 형(기대 결과 포함)이 어울려야 한다.
    hidden이 true인 케이스는 숨긴 정확성 테스트(kind: accuracy), 아니면 공개 예시(kind를 적지 않는다. 예전 문항과 같은 모양). 공개 예시가 하나는 있어야 한다.
    프로그램 방식(표준 입출력)은 입력·기대 출력이 글 그대로다: 입력은 비어도 되고(입력 없는 문제), 기대 출력은 있어야 하고, 저마다 MAX_INPUT자까지. 모양 검사는 없다."""
    title, text = str(body.get("title") or "").strip(), str(body.get("text") or "").strip()
    if not title:
        raise Refuse("제목을 적어 주세요.", field="title")
    if len(title) > 80:  # 말없이 자르지 않는다
        raise Refuse("제목은 80자까지 적을 수 있어요.", field="title")
    if not text:
        raise Refuse("문제 글을 적어 주세요.", field="text")
    rows = body.get("cases") or []
    if not isinstance(rows, list) or not all(isinstance(raw, dict) for raw in rows):
        raise Refuse("테스트 케이스 모양이 맞지 않아요.", field="case-input-1")
    cases, read = [], []  # read: [(줄 번호, 인자들, 기대 결과)]
    for n, raw in enumerate(rows, 1):
        if mode == "program":
            given, expected = stdin_text(raw.get("input") or ""), str(raw.get("expected") or "").replace("\r\n", "\n")
            if not given and not expected.strip():
                continue
            for field, value, word in (("input", given, "입력"), ("expected", expected, "기대 출력")):
                if len(value) > MAX_INPUT:
                    raise Refuse(f"{n}번 케이스의 {word}은 {MAX_INPUT:,}자까지 적을 수 있어요.", field=f"case-{field}-{n}")
            if not expected.strip():
                raise Refuse(f"{n}번 케이스의 기대 출력을 적어 주세요.", field=f"case-expected-{n}")
            read.append((n, None, None))
            cases.append({"id": str(len(cases) + 1), "input": given, "expected": expected, **({"kind": "accuracy"} if raw.get("hidden") is True else {})})
            continue
        given, expected = str(raw.get("input") or "").strip(), str(raw.get("expected") or "").strip()
        if not given and not expected:
            continue
        try:
            args = case_args(given)
        except ValueError as exc:
            why = JSON_WHY.get(str(exc))
            raise Refuse(f"{n}번 케이스의 넣을 값을 읽지 못했어요. {why}" if why else f"{n}번 케이스의 넣을 값은 대괄호로 감싼 목록이어야 해요. 예: [[1, 2, 3], 5]",
                         field=f"case-input-{n}") from None
        if not expected:
            raise Refuse(f"{n}번 케이스의 기대 결과를 적어 주세요.", field=f"case-expected-{n}")
        try:
            value = json_value(expected)
        except ValueError as exc:
            why = JSON_WHY.get(str(exc)) or "글자는 큰따옴표로 감싸요. 예: \"joon\", 3, true"
            raise Refuse(f"{n}번 케이스의 기대 결과를 읽지 못했어요. {why}", field=f"case-expected-{n}") from None
        if read and len(args) != len(read[0][1]):
            first = read[0][0]
            raise Refuse(f"{n}번 케이스는 넣을 값이 {len(args)}개인데 {first}번 케이스는 {len(read[0][1])}개예요. 배열 하나를 넘기려면 [[1, 2, 3]]처럼 한 번 더 감싸요.",
                         field=f"case-input-{n}")
        for field, item in [*(("input", arg) for arg in args), ("expected", value)]:
            if mixed(item):  # 한 목록 안에 종류가 다른 값([1, "a"])은 어느 언어의 형으로도 받지 못한다(null은 섞여도 된다)
                raise Refuse(f"{n}번 케이스의 목록에 서로 다른 종류의 값이 섞여 있어요.", field=f"case-{field}-{n}")
        read.append((n, args, value))
        cases.append({"id": str(len(cases) + 1), "input": given, "expected": expected, **({"kind": "accuracy"} if raw.get("hidden") is True else {})})
    if not cases:
        raise Refuse("테스트 케이스를 하나 이상 적어 주세요.", field="case-input-1")
    if all(case.get("kind") == "accuracy" for case in cases):
        raise Refuse("공개 예시가 하나는 있어야 해요.", field=f"case-hidden-{read[0][0]}")
    if mode == "program":
        return title, text, cases
    try:
        for k in range(len(read[0][1])):
            same_shapes([(n, args[k]) for n, args, _ in read], f"{k + 1}번째 값은", "case-input")
        same_shapes([(n, value) for n, _, value in read], "기대 결과는", "case-expected")
    except RecursionError:  # 아주 깊은 중첩
        raise Refuse("케이스의 값이 너무 깊게 겹쳐 있어요.", field="case-input-1") from None
    return title, text, cases


def kind_of(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def files_of(body: dict) -> list[tuple[str, bytes]]:
    """요청의 files [{name, data(base64, 데이터 URL 머리가 붙어도 된다)}] → [(이름, 바이트)]. 받는 형식, 크기, PDF 수(하나)만 본다(장 수는 엔진이 본다)."""
    rows = body.get("files") or []
    if not isinstance(rows, list) or not all(isinstance(raw, dict) and isinstance(raw.get("name"), str) and isinstance(raw.get("data"), str) for raw in rows):
        raise Refuse("올린 파일 모양이 맞지 않아요.")
    out = []
    for raw in rows:
        name, data = raw["name"].strip()[:200], raw["data"]
        if kind_of(name) not in ASSET_TYPES:
            raise Refuse(f"올릴 수 없는 파일이에요({name}). 이미지(png·jpg·webp·gif), md·txt, PDF만 받아요.")
        if data.startswith("data:"):
            data = data.partition(",")[2]
        try:
            got = base64.b64decode(data, validate=True)
        except ValueError:  # binascii.Error
            raise Refuse(f"{name} 파일을 읽지 못했어요.") from None
        if len(got) > MAX_FILE:
            raise Refuse(f"파일 하나는 8MB까지 올릴 수 있어요: {name}")
        out.append((name, got))
    if sum(kind_of(name) == "pdf" for name, _ in out) > 1:
        raise Refuse("PDF는 하나만 올릴 수 있어요.")
    return out


def kept_files(body: dict) -> list[tuple[str, bytes]] | None:
    """등록·수정 때 보관할 원본. files가 없으면 None(수정이면 그대로 둔다)."""
    if body.get("files") is None:
        return None
    files = files_of(body)
    try:
        split_files(files)  # 이미지 장 수
    except IngestError as exc:
        raise Refuse(str(exc)) from None
    return files


def save_assets(pid: str, files: list[tuple[str, bytes]]) -> None:
    """원본을 통째로 바꾼다. 파일 시스템 경로에는 사용자가 붙인 이름을 쓰지 않는다."""
    folder = ASSETS / pid
    shutil.rmtree(folder, ignore_errors=True)
    if not files:
        return
    folder.mkdir(parents=True)
    rows = []
    for n, (name, data) in enumerate(files, 1):
        (folder / f"{n:02d}.{kind_of(name)}").write_bytes(data)
        rows.append({"n": n, "name": name, "type": kind_of(name)})
    write_json(folder / "index.json", rows)


def assets(pid: str) -> list[dict]:
    return read_json(ASSETS / pid / "index.json", []) if OWN_ID.fullmatch(pid) else []


RANGE = re.compile(r"\d[^\n]{0,40}?(?:≤|<=|<|≥|>=|이상|이하|미만|초과)|(?:≤|<=|<|≥|>=|이상|이하|미만|초과)[^\n]{0,40}?\d")  # 제한사항의 수 범위 한 자리


def read_doubts(text: str, mode: str) -> list[dict]:
    """읽은 글을 규칙으로 대조한다(모델 0회): 입출력 예가 읽혔는가(줄마다 칸 수가 머리와 같고 값을 읽을 수 있는가), 제한사항의 수 범위가 읽혔는가."""
    found = (sample_cases if mode == "program" else table_cases)(text)
    out = []
    if not found["cases"] and not found["skipped"]:
        out.append({"where": "입출력 예", "note": "입출력 예를 찾지 못했어요"})
    elif found["skipped"]:
        out.append({"where": "입출력 예", "note": f"읽지 못한 줄이 {found['skipped']}개 있어요(표의 제목 줄과 칸 수가 다르거나 값을 읽지 못했어요)"})
    out += [{"where": "입출력 예", "note": f"예시 한 줄을 읽지 못했어요: `{' '.join(line.split())}`"} for line in found.get("missed") or []]
    out += [{"where": "입출력 예", "note": note} for note in found.get("spill") or []]
    if not RANGE.search(text):
        out.append({"where": "제한사항", "note": "수 범위를 찾지 못했어요"})
    return out


def doubt_page(doubts: list[dict], done: dict) -> int | None:
    """다시 읽을 장 하나: 숫자가 어긋난 장, 아니면 어긋난 곳의 낱말(입출력 예·제한)이 든 장, 아니면 입출력 예는 마지막 장·제한사항은 첫 장. AI가 읽은 장만."""
    ai = [n for n in range(len(done.get("parts") or [])) if n not in (done.get("ocr_pages") or [])]
    if not ai:
        return None
    page = next((d["page"] for d in doubts if d.get("page") in ai), None)
    if page is not None:
        return page
    where = doubts[0]["where"]
    words = ("입출력", "예제", "result", "return") if where == "입출력 예" else ("제한", "제약")
    hits = [n for n in ai if any(word in done["parts"][n] for word in words)]
    return (hits[-1] if hits else ai[-1]) if where == "입출력 예" else (hits[0] if hits else ai[0])


def read_files(body: dict) -> dict:
    """올린 파일에서 문제 글을 읽는다(저장하지 않는다). 이미지는 AI가 연결돼 있으면 모델, 아니면(또는 모델이 실패한 장은) tesseract.
    ocr: 본문에 tesseract로 읽은 장이 있다(틀린 글자가 많을 수 있어 화면이 원본과 견주라고 알린다).
    doubts: 읽은 글을 규칙과 글자 읽기로 대조해 어긋난 곳 [{where, note | ai, ocr}]. 어긋나면 그 장만 한 번 다시 읽고(모델 1회), 그래도 남은 것을 준다."""
    text = body.get("text") or ""
    if not isinstance(text, str):
        raise Refuse("문제 글은 글이어야 해요.", field="text")
    mode = "program" if body.get("mode") == "program" else "function"
    files = files_of(body)
    try:
        done = read_pages(text, files)
        doubts = read_doubts(done["body"], mode) + ocr_doubts(done)
        page = doubt_page(doubts, done) if doubts and done["used_ocr"] is not True else None  # AI가 연결되지 않았으면 다시 읽을 수 없다
        if page is not None:
            try:
                reread(done, page)  # 글자 읽기 결과(ocr_text)는 같은 이미지라 그대로 다시 견준다
            except (IngestError, LlmNotConfigured):  # 다시 읽기에 실패하면 처음 읽은 글 그대로(어긋난 곳은 그대로 알린다)
                pass
            doubts = read_doubts(done["body"], mode) + ocr_doubts(done)
        return {"text": done["body"], "ocr": done["used_ocr"], "doubts": [{key: value for key, value in d.items() if key != "page"} for d in doubts]}
    except IngestError as exc:
        raise Refuse(str(exc)) from None
    except LlmNotConfigured:
        raise Refuse("이미지에서 글을 읽으려면 AI를 연결해야 해요. 연결하거나, 글을 직접 붙여 넣어 주세요.", 503, "llm_not_configured") from None


def chosen_theme(body: dict) -> str:
    """등록·수정 요청의 주제(theme): 빈 글(정하지 않음)이거나 주제 15개 가운데 하나."""
    theme = body.get("theme") or ""
    if theme and theme not in ALGORITHMS:
        raise Refuse("고를 수 없는 주제예요.", field="theme")
    return theme


def chosen_level(body: dict) -> int:
    """등록·수정 요청의 단계(level): 0(정하지 않음. 분석이 붙인 것을 쓴다)이거나 1~5."""
    level = body.get("level") or 0
    if level not in range(0, 6) or isinstance(level, bool):
        raise Refuse("고를 수 없는 단계예요.", field="level")
    return level


ANSWER_FLAGS = ("float_output", "many_answers")  # 표준 입출력 문제의 답 비교 표시(등록 둘째 걸음의 칸 둘)


def answer_flags(body: dict, mode: str) -> dict:
    """켠 답 비교 표시만 {이름: True}. float_output: 실수 답(기대 출력의 소수 낱말을 0.000001 차이까지 같게 본다), many_answers: 답이 여럿일 수 있다
    (값이 다르면 맞는지 가릴 수 없다고 말하고, 숨은 테스트를 만들지 않는다). 표준 입출력 문제에만 둔다(함수 방식의 실수 비교는 늘 켜져 있다).
    문제 글의 낱말로 짐작하지 않는다: 사용자가 켤 때만."""
    return {key: True for key in ANSWER_FLAGS if mode == "program" and body.get(key) is True}


def register(body: dict, once: bool = False) -> dict:
    """문제를 넣는다. once(화면의 요청): 같은 글을 이미 넣었으면 준비(모델 호출)를 또 하기 전에 알리고, 그대로 한 번 더 보내면(again) 넣는다."""
    mode = body.get("mode") or "function"
    if mode not in ("function", "program"):
        raise Refuse("고를 수 없는 푸는 방식이에요.", field="mode")
    title, text, cases = checked(body, mode)
    language = body.get("language")
    if language in (None, ""):
        language = "python"
    elif not isinstance(language, str) or language not in check_judge().LANGUAGES:
        raise Refuse("고를 수 없는 언어예요.", field="language")
    theme, level = chosen_theme(body), chosen_level(body)
    files = kept_files(body)
    if once and not body.get("again"):
        same = next((raw for raw in read_json(PROBLEMS_FILE, []) if isinstance(raw, dict) and str(raw.get("text", "")).split() == text.split()), None)
        if same is not None:
            raise Refuse(f"같은 글의 문제를 이미 넣었어요(‘{same.get('title') or '제목 없음'}’). 그래도 하나 더 넣으려면 ‘등록’을 한 번 더 눌러 주세요.", 400, "duplicate")
    pid = "u" + uuid.uuid4().hex[:8]
    names = arg_names(body, cases) if mode == "function" else None
    row = {"id": pid, "title": title, "language": language, "mode": mode, "text": text, "cases": cases, **({"names": names} if names else {}),
           **({"theme": theme} if theme else {}), **({"level": level} if level else {}), **answer_flags(body, mode)}
    with tutor() as t:
        t.store.put_problem(pid, language, text, title=title)
    with FILE_LOCK_ROWS:
        write_json(PROBLEMS_FILE, [*read_json(PROBLEMS_FILE, []), row])
    save_assets(pid, files or [])
    reload_problems()
    prepare_later(pid)
    return {"id": pid}


def edit(body: dict) -> dict:
    """등록한 문항을 고친다. 바뀐 만큼만 다시 준비한다(모델 호출을 아낀다).
    - 제목·주제만, 또는 글이 공백·줄바꿈만 다름: 준비 결과를 그대로 둔다.
    - 케이스만 바뀜(답 비교 표시 float_output·many_answers가 바뀐 것도): 풀이 가이드의 정답 코드를 새 케이스로 채점한다(모델 0회). 통과하면 그대로 두고, 아니면 가이드·계획만 지우고 뼈대는 남겨 다시 준비한다.
    - 글이 바뀜: 풀이 가이드·계획·대화·블록 진행·디버그 상태·문항 뼈대를 지우고 새 글로 다시 준비한다.
    제출 기록과 내가 쓴 코드는 남긴다. 언어는 여기서 바꾸지 않는다(코드 화면의 언어 바꾸기).
    files가 오면 원본을 통째로 바꾸고, 안 오면 그대로 둔다. 푸는 방식은 바꾸지 않는다(보내도 등록한 방식으로 검사한다. 방식이 바뀌면 케이스와 코드가 모두 달라진다)."""
    found = own(body)
    pid = found.id
    title, text, cases = checked(body, found.mode)
    theme, level = chosen_theme(body), chosen_level(body)
    files = kept_files(body)
    redo = False
    with LOCKS[pid], FILE_LOCK_ROWS:
        rows = read_json(PROBLEMS_FILE, [])
        row = next(raw for raw in rows if isinstance(raw, dict) and raw.get("id") == pid)
        text_changed = text.split() != row["text"].split()  # 공백·줄바꿈만 다르면 같은 글이다
        flags = {key: True for key in ANSWER_FLAGS if row.get(key) is True}
        new_flags = answer_flags(body, found.mode) if set(ANSWER_FLAGS) & body.keys() else flags  # 보낼 때만 바꾼다
        cases_changed = cases != row["cases"] or new_flags != flags  # 비교가 바뀌면 케이스가 바뀐 것과 같다(대조로 만든 케이스·가이드 검증을 다시)
        row.update(title=title, text=text, cases=cases)
        for key in ANSWER_FLAGS:
            row.pop(key, None)
        row.update(new_flags)
        if "theme" in body:  # 주제는 보낼 때만 바꾼다
            row.pop("theme", None)
            if theme:
                row["theme"] = theme
        if "level" in body:  # 단계도 보낼 때만. 0이면 분석이 붙인 단계로 돌린다
            row.pop("level", None)
            if level:
                row["level"] = level
        if text_changed or cases_changed:  # 대조로 만든 케이스와 결과는 옛 글·케이스에서 나왔다. 다음 준비(또는 열 때의 대조)가 다시 만든다
            row.pop("made", None)
            row.pop("check", None)
            row.pop("limits", None)
            shutil.rmtree(LARGE / pid, ignore_errors=True)
            large_case.cache_clear()
            RECHECKED.discard(pid)
        if "names" in body:  # 입출력 예 표에서 다시 채웠다. 없으면 예전 이름 그대로
            names = arg_names(body, cases) if found.mode == "function" else None
            row.pop("names", None)
            if names:
                row["names"] = names
        write_json(PROBLEMS_FILE, rows)
        reload_problems()  # 새 케이스로 채점하려면 먼저 올린다
        with tutor() as t:
            ctx = t.store.load(pid)
            if text_changed or cases_changed:
                forget_kept(pid)  # 다른 언어로 보관한 준비는 옛 글·케이스로 만든 것이다
            if text_changed and ctx is not None:
                drop_plan(t, pid, "problem_fact")
            elif cases_changed and ctx is not None and (ctx.solution is not None or ctx.plan is not None):
                LANG[pid] = ctx.language  # 가이드 코드의 언어로 채점한다(켜고 처음 온 요청일 수 있다)
                passed = ctx.solution is not None and (verify(pid, ctx.solution.code) or {}).get("status") == "passed"
                if not passed:
                    drop_plan(t, pid)
                redo = not passed
            if text_changed and t.index is not None:  # 옛 글의 색인 항목을 남기지 않는다(새 글로 다시 준비할 때 넣는다)
                t.index.delete(pid)
            if text_changed:  # 옛 글에 맞춰 남긴 코드다
                write_json(CHECKPOINTS_FILE, {key: value for key, value in read_json(CHECKPOINTS_FILE, {}).items() if key != pid})
            t.store.put_problem(pid, ctx.language if ctx else row["language"], text, direct_code=ctx.direct_code if ctx else "", title=title)
        if files is not None:
            save_assets(pid, files)
    if text_changed or redo:
        prepare_later(pid)
    return {"id": pid}


def delete(body: dict) -> dict:
    """등록한 문항과 그 기록(엔진 저장소의 모든 표, 블록 코드, 언어별 코드, 체크포인트, 올린 원본)을 지운다. 뒤에서 미리 만들기가 돌고 있으면 끝나기를 기다린다."""
    pid = own(body).id
    with LOCKS[pid], FILE_LOCK_ROWS:
        write_json(PROBLEMS_FILE, [raw for raw in read_json(PROBLEMS_FILE, []) if not (isinstance(raw, dict) and raw.get("id") == pid)])
        reload_problems()  # 먼저 목록에서 빼야 겹친 요청이 엔진 저장소에 다시 넣지 않는다
        with tutor() as t:
            t.store.delete_problem(pid)
            if t.index is not None:  # 비슷한 문항 찾기 색인에서도 뺀다
                t.index.delete(pid)
        for path in (BLOCKS_FILE, OWN_FILE, CODES_FILE, CHECKPOINTS_FILE, TOUCHED_FILE):
            write_json(path, {key: value for key, value in read_json(path, {}).items() if key != pid})
        shutil.rmtree(ASSETS / pid, ignore_errors=True)
        shutil.rmtree(LARGE / pid, ignore_errors=True)
        forget_kept(pid)
        LANG.pop(pid, None)
        REPORTS.pop(pid, None)
        PREPARED.discard(pid)
    return {"ok": True}


def score(report: dict) -> dict:
    """정확성(공개 예시 + 숨긴 정확성)과 효율성의 [통과 수, 전체 수]."""
    def part(kinds):
        mine = [case for case in report["cases"] if case["kind"] in kinds]
        return [sum(case["status"] == "passed" for case in mine), len(mine)]

    return {"accuracy": part(("example", "accuracy")), "efficiency": part(("efficiency",))}


ERROR_WORDS = ("Error", "Exception", "panic", "terminate called", "terminating due to")  # TypeError, Exception in thread "main" …, panic: …(Go), thread 'main' panicked at …(Rust), C++ 예외로 멈춤
TRACE_LINES = ("    at ", "\tat ", "Node.js v")  # JS·Java 호출 자취와 Node 버전 줄


ABNORMAL = "프로그램이 비정상적으로 끝났어요. 배열 범위를 벗어났거나 재귀가 너무 깊을 수 있어요."  # 오류 글 없이 끝났다(C++ 등)
TEMP_DIR = re.compile(r"[^\s'\"(]*algoblock-check-[^/\\\s]+[/\\]")  # 채점기의 임시 폴더 경로(app/judge common.work_directory)
HARNESS = re.compile(r"\b(?:algoblock_main|algoblock_runner|FunctionRunner)\.\w+")  # 채점기가 만든 호출 파일(app/judge의 언어별 runner.py)
# 채점기가 내 코드를 적어 둔 파일: 함수 방식, 프로그램 방식(main. 임시 폴더 경로는 먼저 지우므로 경로 안의 main.rs 같은 남의 파일은 둔다)
USER_FILE = re.compile(r"\b(?:solution\.(?:py|js|go|rs|cpp)|Solution\.(?:java|kt))\b|(?<![/\\])\b(?:main\.(?:py|js|go|rs|cpp)|Main\.(?:java|kt))\b")


def clean(text: str) -> str:
    """오류 글에서 채점기 안쪽 이름을 가린다: 임시 폴더 경로는 지우고, 호출 파일을 가리키는 자취 줄과 Go 모듈 이름 줄(# algoblockcheck)은 빼고,
    호출 파일의 위치 머리(FunctionRunner.java:12:)는 떼고, 내 코드를 적어 둔 파일 이름은 '내 코드'로 바꾼다."""
    rows = []
    for row in TEMP_DIR.sub("", text or "").splitlines():
        if "algoblockcheck" in row or (HARNESS.search(row) and row.strip().startswith(("at ", "-->", "File "))):
            continue
        rows.append(USER_FILE.sub("내 코드", re.sub(HARNESS.pattern + r"(?::\d+)*:?\s?", "", row)))
    return "\n".join(rows)


def error_line(text: str, status: str = "") -> str:
    """오류 글에서 초보자가 읽을 한 줄: 들여쓰기 없이 오류 이름이 든 첫 줄 → 자취가 아닌 마지막 줄 → 마지막 줄."""
    lines = clean(text).strip().splitlines()
    at = next((i for i, row in enumerate(lines) if row and not row[0].isspace() and any(word in row for word in ERROR_WORDS)), None)
    line = lines[at] if at is not None else next((row for row in reversed(lines) if row.strip() and not row.startswith(TRACE_LINES)), lines[-1] if lines else "")
    if at is not None and "panicked at" in line and line.rstrip().endswith(":"):  # Rust: 위치 줄 다음 줄이 이유다(index out of bounds: …)
        line = f"{line.rstrip()} {next((row.strip() for row in lines[at + 1:] if row.strip()), '')}".rstrip()
    if not line.strip() and status == "runtime_error":
        line = ABNORMAL
    return line[:300]


def exception_name(line: str) -> str:
    """오류 한 줄에서 예외 이름만: 첫 ':' 앞의 마지막 낱말, 패키지 경로는 마지막 이름(java.lang.X → X). 숨은 테스트는 이것만 보여 준다
    (메시지의 숫자가 숨은 입력의 크기를 알려 준다). Rust 패닉은 이유의 ':' 앞(index out of bounds), 이유가 없으면 panic. C++ 예외는 std::이름. 이름이 없으면(비정상 종료 안내) 그대로."""
    if line == ABNORMAL:
        return line
    if "panicked" in line:
        reason = re.search(r"panicked at .*?:\d+:\d+:\s+(.+)", line)
        return reason[1].split(": ", 1)[0] if reason else "panic"
    thrown = re.search(r"\bstd::\w+", line) if "terminat" in line else None
    if thrown:
        return thrown[0]
    words = line.split(":", 1)[0].split()
    return words[-1].rsplit(".", 1)[-1].strip("'\"") if words else ""


FAMILY = {"kotlin": "java"}  # 같은 예외 이름을 쓰는 언어
HINTS = {  # 예외 이름 → 한 줄 풀이(무엇이 일어났나, 무엇을 볼까). 숨은 테스트에도 붙으니 입력을 드러내지 않는 일반적인 말이다
    "python": {
        "KeyError": "딕셔너리에 없는 키를 읽었어요. 처음 보는 값일 때를 따져 보세요.",
        "IndexError": "리스트나 문자열의 범위를 벗어난 자리를 읽었어요. 비었거나 마지막 자리 다음일 수 있어요.",
        "TypeError": "값의 형이 맞지 않아요. 숫자와 글자를 섞었거나 인자 수가 다른지 보세요.",
        "NameError": "만들지 않은 이름을 썼어요. 오타이거나 만들기 전에 쓴 곳을 보세요.",
        "ValueError": "형은 맞지만 쓸 수 없는 값이에요. int()로 바꾼 글자 같은 변환을 보세요.",
        "ZeroDivisionError": "0으로 나눴어요. 나누는 값이 0이 되는 경우를 따져 보세요.",
        "RecursionError": "재귀가 너무 깊어요. 끝나는 조건을 확인하거나 반복문으로 바꿔 보세요.",
        "AttributeError": "그 값에 없는 메서드나 속성을 불렀어요. 값의 형과 이름을 확인해 보세요.",
        "SyntaxError": "파이썬 문법에 맞지 않는 줄이 있어요. 콜론, 괄호, 따옴표 짝을 보세요.",
        "IndentationError": "들여쓰기가 어긋났어요. 같은 묶음의 줄이 같은 칸에서 시작하는지 보세요.",
        "UnboundLocalError": "값을 넣기 전에 지역 변수를 읽었어요. 함수 안에서 처음 쓰는 곳을 보세요.",
    },
    "java": {
        "ArrayIndexOutOfBoundsException": "배열의 범위를 벗어난 자리를 읽었어요. 빈 배열이거나 길이와 같은 번호일 수 있어요.",
        "StringIndexOutOfBoundsException": "문자열의 범위를 벗어난 자리를 읽었어요. 빈 문자열이나 마지막 글자 다음을 보세요.",
        "IndexOutOfBoundsException": "리스트의 범위를 벗어난 자리를 읽었어요. 빈 리스트이거나 size()와 같은 번호일 수 있어요.",
        "NullPointerException": "null인 값을 썼어요. 만들지 않은 객체나 맵에 없는 키의 값을 보세요.",
        "ArithmeticException": "0으로 나눴어요. 나누는 값이 0이 되는 경우를 따져 보세요.",
        "StackOverflowError": "재귀가 너무 깊어요. 끝나는 조건을 확인하거나 반복문으로 바꿔 보세요.",
        "NumberFormatException": "숫자로 바꿀 수 없는 글자를 바꿨어요. 바꾸기 전의 글자를 확인해 보세요.",
        "ClassCastException": "값을 맞지 않는 형으로 바꿨어요. 담은 값의 실제 형을 확인해 보세요.",
        "NoSuchElementException": "빈 곳에서 값을 꺼냈어요. 꺼내기 전에 비었는지 확인해 보세요.",
        "ConcurrentModificationException": "도는 중인 목록을 고쳤어요. 고칠 것을 따로 모았다가 나중에 바꿔 보세요.",
        "OutOfMemoryError": "메모리를 너무 많이 썼어요. 아주 큰 배열이나 끝없이 늘어나는 목록을 보세요.",
    },
    "cpp": {
        "std::out_of_range": "범위를 벗어난 자리를 at()으로 읽었어요. 빈 벡터이거나 size()와 같은 번호일 수 있어요.",
        "std::bad_alloc": "메모리를 너무 많이 쓰려 했어요. 아주 큰 벡터나 끝없이 늘어나는 목록을 보세요.",
        "std::invalid_argument": "숫자로 바꿀 수 없는 글자를 바꿨어요. stoi에 넘긴 글자를 확인해 보세요.",
        "std::length_error": "벡터나 문자열을 너무 길게 만들려 했어요. 음수 크기가 들어가지 않았는지 보세요.",
    },
    "javascript": {
        "TypeError": "없는 값(undefined, null)을 쓰거나 함수가 아닌 것을 불렀어요. 그 값이 있는지 보세요.",
        "ReferenceError": "만들지 않은 이름을 썼어요. 오타이거나 선언하기 전에 쓴 곳을 보세요.",
        "RangeError": "재귀가 너무 깊거나 배열 길이가 잘못됐어요. 끝나는 조건을 확인해 보세요.",
        "SyntaxError": "자바스크립트 문법에 맞지 않는 줄이 있어요. 괄호와 따옴표 짝을 보세요.",
    },
}
PHRASE_HINTS = (  # 이름 없이 문구로 알리는 오류(Go 패닉, Rust 패닉): (언어, 오류 글에서 찾을 것, 풀이)
    ("go", re.compile(r"index out of range"), "배열·슬라이스의 범위를 벗어난 자리를 읽었어요. 길이와 같은 번호일 수 있어요."),
    ("go", re.compile(r"nil pointer dereference"), "nil인 값을 썼어요. 만들지 않은 맵이나 포인터를 쓴 곳을 보세요."),
    ("go", re.compile(r"integer divide by zero"), "0으로 나눴어요. 나누는 값이 0이 되는 경우를 따져 보세요."),
    ("rust", re.compile(r"index out of bounds"), "벡터의 범위를 벗어난 자리를 읽었어요. 빈 벡터이거나 len()과 같은 번호일 수 있어요."),
    ("rust", re.compile(r"attempt to .+ with overflow"), "계산한 값이 형의 범위를 넘었어요. i64를 쓰거나 빼기가 음수가 되는지 보세요."),
    ("rust", re.compile(r"called `?Option::unwrap\(\)`? on a `?None`? value"), "None인 값에 unwrap()을 불렀어요. 값이 없을 때를 먼저 따져 보세요."),
)


IMPORTED = {  # 가져와야(import) 쓸 수 있는 표준 모듈과 그 안의 흔한 이름 → 맨 위에 적을 가져오기 문장
    **{name: f"from collections import {name}" for name in ("deque", "Counter", "defaultdict", "OrderedDict")},
    **{name: f"import {name}" for name in ("heapq", "math", "sys", "bisect", "itertools", "functools", "re", "string", "collections")},
    **{name: f"from itertools import {name}" for name in ("permutations", "combinations", "product", "accumulate")},
    **{name: f"from functools import {name}" for name in ("lru_cache", "reduce")},
    **{name: f"from bisect import {name}" for name in ("bisect_left", "bisect_right")},
    **{name: f"from heapq import {name}" for name in ("heappush", "heappop", "heapify")},
}


def error_hint(text: str, language: str) -> str:
    """실행 오류 글에 붙일 한국어 한 줄 풀이. 모르는 오류면 빈 글. 가져오지 않은 표준 모듈 이름의 NameError는 import를 덧붙인다."""
    full, name = clean(text), exception_name(error_line(text, "runtime_error"))
    known = HINTS.get(FAMILY.get(language, language), {}).get(name)
    missing = re.search(r"name '(\w+)' is not defined", full) if language == "python" and name == "NameError" else None
    if known and missing and missing[1] in IMPORTED:
        name = missing[1]
        also = f"(또는 `import heapq` 뒤 `heapq.{name}`)" if IMPORTED[name].startswith("from heapq") else ""
        return f"{known} {name}{'을' if name in ('deque', 'heappop', 'string') else '를'} 쓰려면 맨 위에 `{IMPORTED[name]}`{also}처럼 적어요."  # 화면은 `…`를 코드로 보여 준다
    if known:
        return known
    return next((hint for lang, found, hint in PHRASE_HINTS if lang == language and found.search(full)), "")


def error_fields(case: dict, language: str, hidden: bool) -> dict:
    """실행 오류 케이스의 {error, hint, line}. 숨은 테스트는 예외 이름만(줄 번호와 풀이는 입력을 드러내지 않는다)."""
    line = error_line(case["error"], "runtime_error")
    out = {"error": exception_name(line) if hidden else line, "hint": error_hint(case["error"], language)}
    return {**out, **({"line": case["line"]} if case.get("line") else {})}


def result_body(report: dict) -> dict:
    """채점 결과를 화면 모양으로. 오류 글은 한 줄만(error_line, 초보자가 읽을 한 줄)과 한 줄 풀이(hint), 줄 번호(line, 채점기가 줄 때).
    숨은 테스트는 통과 여부만: 입력·기대값·내 결과는 공개 예시에만 싣고, 숨은 테스트는 실행 오류일 때 예외 이름만 싣는다.
    효율성 케이스가 제한 시간에 가깝게 통과했으면 near와 제한(limit, 초). 같은 코드를 다시 내서 제출로 남기지 않았으면 repeat."""
    language = report.get("language", "")
    cases = []
    for case in report["cases"]:
        row = {"id": case["id"], "kind": case["kind"], "status": case["status"], "ms": case["ms"]}
        hidden = case["kind"] != "example"
        if not hidden:
            row |= {"input": case["input"], "expected": case["expected"], "got": case["got"][:2000], "error": error_line(case["error"], case["status"])}
        if case["status"] == "runtime_error":
            row |= error_fields(case, language, hidden)
        if case.get("note"):  # 답이 여럿일 수 있는 문제에서 값이 달랐다: 틀렸다고 단정하지 않는다(숨은 테스트도 입력·값은 싣지 않는다)
            row["error"] = case["note"]
        if case.get("near") is True and case.get("limit"):
            row |= {"near": True, "limit": case["limit"]}
        cases.append(row)
    missed = [case for case in report["cases"] if case["status"] != "passed"]
    # many: 통과하지 못한 케이스가 모두 '답이 여럿일 수 있는 문제에서 값이 다름'이다(틀렸다고 단정하지 않는다. 화면 머리가 그렇게 말한다)
    return {"ok": report["status"] == "passed", "status": report["status"], "reason": report["reason"], "compile": compile_head(report["compile"]),
            "compile_line": report.get("compile_line"), "score": score(report), "cases": cases, "repeat": report.get("repeat") is True,
            "many": bool(missed) and all(case.get("note") for case in missed), "notice": report.get("notice") or ""}


CALL_FAILED = "채점기가 이 함수를 부르는 코드를 만들지 못했어요. 반환형과 인자 형을 시작 코드 그대로 두었는지 확인해 주세요."


def compile_head(text: str) -> str:
    """컴파일 오류는 앞부분을 준다(Java·C++는 마지막 줄이 '1 error'뿐이고, 어느 줄이 왜 틀렸는지는 앞에 있다)."""
    shown = clean(text).strip()
    if re.search(r"\balgoblock[A-Z_]", shown):  # 채점기가 만든 호출 코드의 이름(algoblockJson …)이 든 오류: 내 코드의 오류가 아니라 호출 코드가 내 함수의 모양을 다루지 못한 것이다
        return CALL_FAILED
    rows = [row for row in shown.splitlines() if not row.startswith("In file included from") and not re.match(r"\s+from \S.*:\d+[:,]$", row)]  # C++ 머리 파일 자취
    return "\n".join(rows[:8])[:800]


MAX_INPUT = 20_000


def own_input(p, raw) -> str:
    """직접 실행에 넣을 값. 등록 케이스와 같은 검사에, 인자 수와 형까지 본다(Java 등은 형이 다르면 알아듣기 어려운 오류가 난다).
    기본 문제는 실린 params, 등록한 문제는 모든 케이스에서 정한 형(own_types. 형을 못 정한 자리는 보지 않는다).
    프로그램 방식은 표준 입력에 넣을 글 그대로(길이만 본다)."""
    if p.mode == "program":
        if not isinstance(raw, str) or len(raw) > MAX_INPUT:
            raise Refuse(f"직접 입력은 {MAX_INPUT:,}자까지 넣을 수 있어요.", field="run-input")
        return stdin_text(raw)
    row = BUILTIN.get(p.id)
    sample = row["examples"][0]["input"] if row else next((case["input"] for case in p.cases if case.get("kind", "example") == "example"), "[1, 2]")  # 숨긴 케이스는 예로 들지 않는다
    if not isinstance(raw, str) or len(raw) > MAX_INPUT:
        raise Refuse(f"직접 입력은 {MAX_INPUT:,}자까지 넣을 수 있어요.", field="run-input")
    given = raw.strip()
    try:
        args = case_args(given)
    except ValueError as exc:
        raise Refuse(JSON_WHY.get(str(exc)) or f"넣을 값은 대괄호로 감싼 목록이어야 해요. 예: {sample}", field="run-input") from None
    types = [param["type"] for param in row["params"]] if row else (own_types(p) or (None, None))[0]
    if types is not None and (len(args) != len(types) or not all(typ is None or fits(value, typ) for value, typ in zip(args, types))):
        raise Refuse(f"넣을 값이 이 문제의 입력 모양과 달라요. 예: {sample}", field="run-input")
    return given


OUT_OF_RANGE = "문제의 제한사항을 벗어난 입력이라 정답 풀이의 결과는 보여 주지 않아요."


def reference(row: dict, given: str, got: str | None) -> dict:
    """기본 문제: 실린 Python 정답 풀이를 같은 입력으로 한 번 돌린 결과(reference)와, 내 코드가 돌려준 값(got)이 그것과 같은지(same).
    정답 풀이가 오류를 내거나 시간을 넘기면 제한사항 밖의 입력일 수 있어 결과 대신 알림(reference_note)."""
    judge = check_judge()
    raw = judge.judge("python", row["solutions"]["python"], [{"id": "1", "input": given, "expected": "null", "timeout": casegen.LIMIT["python"]}], mode="function")
    case = (raw.get("cases") or [{}])[0]
    if case.get("status") not in ("passed", "failed"):
        return {"reference_note": OUT_OF_RANGE}
    lines = (case.get("stdout") or "").strip().splitlines()
    out = {"reference": (lines[-1] if lines else "")[:2000]}
    return out | ({"same": judge.common.same_function_output(got, out["reference"])} if got is not None else {})


def run_once(p, language: str, code: str, given: str) -> dict:
    """직접 넣은 값으로 한 번 돌린다(제출로 남기지 않는다). 기대 결과가 없어 판정하지 않는다: 채점기에는 아무 기대값이나 넣고 판정은 버린다.
    끝까지 돌았으면 status는 ran, got은 돌려준 값(출력의 마지막 줄), stdout은 그 앞에 찍은 것. 실행 오류면 hint(한 줄 풀이)와 line(채점기가 줄 때).
    기본 문제는 정답 풀이의 결과도 함께(reference). 프로그램 방식은 got이 표준 출력 전체(2000자까지. 오류로 멈췄어도 그때까지 쓴 것)이고 stdout은 비운다."""
    raw = check_judge().judge(language, code, [{"id": "1", "input": given, "expected": "null"}], problem=p.text, mode=p.mode)
    case = (raw.get("cases") or [{}])[0]
    status = case.get("status") or raw["status"]
    ran = status in ("passed", "failed")
    lines = (case.get("stdout") or "").strip().splitlines()
    got, printed = (lines[-1], lines[:-1]) if ran and lines else ("", lines)
    out = {"status": "ran" if ran else status, "reason": raw.get("reason") or "", "input": given, "got": got[:2000], "stdout": "\n".join(printed)[:2000],
           "error": "" if ran else error_line(case.get("stderr") or "", status), "ms": case.get("time_ms", 0),
           "compile": compile_head((raw.get("compile") or {}).get("stderr", "")), "compile_line": raw.get("compile_line"), "notice": notice_of(raw)}
    if p.mode == "program":
        out |= {"got": (case.get("stdout") or "")[:2000], "stdout": ""}
    if status == "runtime_error":
        out |= error_fields({"error": case.get("stderr") or "", "line": case.get("line")}, language, False)
    row = BUILTIN.get(p.id)
    return out | (reference(row, given, got if ran else None) if row and "python" in row["solutions"] else {})


def judge(t, p, language: str, code: str) -> dict:
    """모든 케이스로 채점하고 제출로 남긴다(언어, 결과 종류, 정확성·효율성 통과 수).
    직전 제출과 언어·코드·결과가 모두 같으면 다시 남기지 않고 repeat를 붙인다(언어나 결과가 달라졌으면 남긴다).
    이 기기에 언어 도구가 없으면(toolchain_missing) 채점하지 못한 것이라 제출로 세지 않는다."""
    report = grade(p, language, code)
    REPORTS[p.id] = (code, report)
    last = t.store.conn.execute("SELECT source, ok, language, status FROM submission WHERE problem_id=? ORDER BY rowid DESC LIMIT 1", (p.id,)).fetchone()
    repeat = last is not None and (last["source"].strip(), last["language"], last["status"] or ("passed" if last["ok"] else "failed")) == (code.strip(), language, report["status"])
    if report["status"] != "toolchain_missing" and not repeat:
        t.store.add_submission(p.id, code, report["status"] == "passed", language=language, status=report["status"],
                               detail={**score(report), "ms": max((case["ms"] for case in report["cases"]), default=0)})
    t.store.update_code(p.id, code)
    return {**report, "repeat": repeat}


def code_of(body: dict) -> str:
    """요청의 code(없으면 빈 글). 글이 아니거나 NUL·짝 없는 서로게이트가 있으면 거절한다."""
    code = body.get("code")
    if code is None:
        return ""
    if not isinstance(code, str):
        raise Refuse("코드는 글이어야 해요.")
    try:
        code.encode("utf-8")  # 짝 없는 서로게이트는 여기서 걸린다
    except UnicodeEncodeError:
        raise Refuse("코드에 쓸 수 없는 글자가 있어요.") from None
    if "\0" in code:
        raise Refuse("코드에 쓸 수 없는 글자가 있어요.")
    return code


def blocks_of(body: dict) -> dict:
    """요청의 blocks: {블록 id: {code, by}} 모양만 받는다."""
    blocks = body.get("blocks") or {}
    if not isinstance(blocks, dict) or not all(isinstance(one, dict) and isinstance(one.get("code"), str) and isinstance(one.get("by"), str) for one in blocks.values()):
        raise Refuse("블록 코드 모양이 맞지 않아요.")
    return blocks


def checkpoint(pid: str, language: str) -> dict | None:
    saved = read_json(CHECKPOINTS_FILE, {}).get(pid, {}).get(language)
    return saved if isinstance(saved, dict) and isinstance(saved.get("code"), str) and isinstance(saved.get("blocks"), dict) else None


def need_code(body: dict) -> str:
    code = code_of(body)
    if not code.strip():
        raise Refuse("코드 칸이 비어 있어요. 직접 풀기 칸에 코드를 먼저 써 주세요.")
    return code


def reset(t, pid: str) -> None:
    """대화·블록 진행·피드백·해설 모드의 글(다른 언어로 보관한 것도)·다른 언어로 쓰던 코드를 지운다. 제출 기록(통과 횟수), 문항 뼈대, 정석 풀이 가이드,
    체크포인트는 남긴다. 엔진에 초기화 기능이 없어 표를 직접 지운다. 학습 기록에 새 풀이의 시작을 적는다(mark_reset)."""
    # 정석 가이드로 짠 계획은 그대로 두고 첫 블록으로만 돌린다(다시 풀어도 같은 블록 순서로 배운다).
    # 사용자 방법으로 다시 짠 계획이었다면 지운다(다음에 정석 가이드로 다시 짠다).
    ctx = t.store.load(pid)
    keep = ctx is not None and ctx.plan is not None and ctx.plan.strategy in ("fresh", "canonical")
    with t.store.conn:
        for table in ("message", "block_state", "debug_state", "feedback", *(() if keep else ("tutor_session",))):
            t.store.conn.execute(f"DELETE FROM {table} WHERE problem_id=?", (pid,))
        t.store.conn.execute("UPDATE tutor_session SET open_count=1, explain_json=NULL WHERE problem_id=?", (pid,))  # 해설 모드의 글도 지운다(다시 열면 도움)
    t.store.update_code(pid, "")
    t.store.mark_reset(pid)  # 새 풀이의 시작(학습 보고서는 이 뒤에 도움 없이 다시 푼 통과도 센다)
    codes = read_json(CODES_FILE, {})
    if pid in codes:  # 다른 언어로 쓰던 코드도 비운다(언어를 바꿔 되살리면 처음부터가 아니다). 체크포인트는 남긴다(되살리면 도움으로 센다)
        write_json(CODES_FILE, {key: value for key, value in codes.items() if key != pid})
    kept = read_json(KEPT_FILE, {})
    for saved in (kept.get(pid) or {}).values():  # 다른 언어로 보관한 해설 모드의 글도 비운다(언어를 바꿔 되살리지 않게)
        if isinstance(saved, dict) and isinstance(saved.get("session"), dict):
            saved["session"]["explain_json"] = None
    if pid in kept:
        write_json(KEPT_FILE, kept)
    REPORTS.pop(pid, None)
    write_json(BLOCKS_FILE, {key: value for key, value in read_json(BLOCKS_FILE, {}).items() if key != pid})
    own_way(pid, False)


def change_language(t, p, language: str, code: str | None) -> None:
    """언어를 바꾼다. 쓰던 코드는 예전 언어 것으로 적어 두고 새 언어에서 쓰던 코드를 꺼낸다.
    풀이 가이드와 블록은 언어마다 코드가 달라 지운다(대화·블록 진행도 함께). 제출 기록, 문항 뼈대, 피드백, 학습 기록은 남긴다.
    지우기 전에 예전 언어의 가이드·계획·해설을 보관하고, 새 언어로 보관한 것이 있으면 되살린다(원래 언어로 돌아와도 모델을 다시 부르지 않는다)."""
    pid, ctx = p.id, t.store.load(p.id)
    codes = read_json(CODES_FILE, {})
    mine = {**codes.get(pid, {}), ctx.language: ctx.direct_code if code is None else code}
    write_json(CODES_FILE, {**codes, pid: mine})
    keep_plan(t, pid, ctx.language)
    drop_plan(t, pid)
    t.store.set_language(pid, language)
    restore_plan(t, pid, language)
    t.store.update_code(pid, mine.get(language, ""))
    LANG[pid] = language


SOLUTION_COLUMNS = ("approach", "steps_json", "code", "verified", "clues_json")
SESSION_COLUMNS = ("plan_json", "explain_json", "solution_json")  # 대화 진행(open_count)은 보관하지 않는다(되살리면 첫 블록부터)


def keep_plan(t, pid: str, language: str) -> None:
    """이 언어의 풀이 가이드·블록 계획·해설을 보관한다(없으면 아무것도 하지 않는다)."""
    kept = {}
    for name, table, columns in (("solution", "solution", SOLUTION_COLUMNS), ("session", "tutor_session", SESSION_COLUMNS)):
        row = t.store.conn.execute(f"SELECT {', '.join(columns)} FROM {table} WHERE problem_id=?", (pid,)).fetchone()
        if row is not None and any(value is not None for value in tuple(row)):
            kept[name] = dict(zip(columns, tuple(row)))
    if kept:
        saved = read_json(KEPT_FILE, {})
        write_json(KEPT_FILE, {**saved, pid: {**(saved.get(pid) or {}), language: kept}})


def restore_plan(t, pid: str, language: str) -> None:
    """보관해 둔 그 언어의 준비 결과를 되살린다. 손으로 고쳐 모양이 다른 것은 건너뛴다(다시 준비한다)."""
    kept = (read_json(KEPT_FILE, {}).get(pid) or {}).get(language)
    if not isinstance(kept, dict):
        return
    with t.store.conn:
        for name, table, columns in (("solution", "solution", SOLUTION_COLUMNS), ("session", "tutor_session", SESSION_COLUMNS)):
            row = kept.get(name)
            if not isinstance(row, dict) or set(row) != set(columns):
                continue
            extra = ("open_count",) if table == "tutor_session" else ()
            if name == "session" and row["plan_json"]:  # 돌아온 계획은 낡았다고 다시 짜지 않는다(그 언어로 쓰던 코드가 있고 대화가 지워졌어도)
                row = {**row, "plan_json": json.dumps({**json.loads(row["plan_json"]), "settled": True}, ensure_ascii=False)}
            t.store.conn.execute(f"INSERT OR REPLACE INTO {table}(problem_id, {', '.join(columns + extra)}) VALUES({', '.join('?' * (len(columns) + len(extra) + 1))})",
                                 (pid, *(row[column] for column in columns), *((1,) if extra else ())))


def forget_kept(pid: str) -> None:
    """보관한 다른 언어의 준비 결과를 버린다(글·케이스가 바뀌었거나 문항을 지웠다)."""
    saved = read_json(KEPT_FILE, {})
    if pid in saved:
        write_json(KEPT_FILE, {key: value for key, value in saved.items() if key != pid})


def drop_plan(t, pid: str, *more: str) -> None:
    """풀이 가이드·블록 계획·대화·블록 진행·디버그 상태를 지운다(more: 함께 지울 표). 다음에 열 때 다시 준비한다."""
    with t.store.conn:
        for table in ("message", "block_state", "debug_state", "tutor_session", "solution", *more):
            t.store.conn.execute(f"DELETE FROM {table} WHERE problem_id=?", (pid,))
    PREPARED.discard(pid)
    REPORTS.pop(pid, None)
    write_json(BLOCKS_FILE, {key: value for key, value in read_json(BLOCKS_FILE, {}).items() if key != pid})
    own_way(pid, False)


def own_way(pid: str, on: bool) -> None:
    """'끝까지 내 방식으로 쓰기'를 켜거나 끈다. 켠 동안 화면은 블록 코드 확인을 숨기고 '모아서 실행'으로 이끈다(엔진의 판정은 그대로다)."""
    rows = {key: value for key, value in read_json(OWN_FILE, {}).items() if key != pid}
    write_json(OWN_FILE, {**rows, pid: True} if on else rows)


def hints_now(study: dict, rows: list) -> int:
    """이번 풀이(처음, 또는 마지막 '처음부터' 뒤)에서 본 힌트 수."""
    return min(max(0, study["hints_seen"] - study["hints_at_reset"]), len(rows))


def hint_rows(t, pid: str) -> list[dict]:
    """미리 만든 힌트를 순서대로: 블록 1의 힌트 1·2·3, 블록 2의 … 기본 문제는 실린 계획에서, 아니면 저장된 계획에서 읽는다(모델 0회)."""
    blocks = (((BUILTIN.get(pid) or {}).get("ready") or {}).get("plan") or {}).get("blocks")
    if blocks is None:
        plan = t.store.load(pid).plan
        blocks = [{"hints": block.hints, "kind": block.kind, "name": block.name} for block in plan.blocks] if plan else []
    return [{"block": n, "step": k, "hint": hint, "kind": block.get("kind", ""), "name": block.get("name", ""), "last": k == len(block["hints"][:3])}
            for n, block in enumerate(blocks, 1) for k, hint in enumerate(block["hints"][:3], 1)]


def hints_shown(rows: list[dict], seen: int) -> list[dict]:
    """본 힌트까지. 블록 이름은 그 블록의 힌트를 모두 본 뒤에만 싣는다(이름이 답의 일부다. 화면에서 가리지 않고 보내지 않는다)."""
    done = {row["block"] for row in rows[:seen] if row["last"]}
    return [{key: value for key, value in row.items() if key != "last" and (key != "name" or row["block"] in done)} for row in rows[:seen]]


QUOTE_PAIRS = {"'": "'", '"': '"', "‘": "’", "“": "”"}


def unquoted(phrase: str) -> str:
    """맨 바깥 따옴표 한 쌍만 벗긴다. 안에 같은 따옴표가 또 있으면(여러 인용을 이은 구절 "'A'와 'B'") 그대로 둔다."""
    text = phrase.strip()
    close = QUOTE_PAIRS.get(text[:1])
    if len(text) >= 2 and text[-1] == close and text[0] not in text[1:-1] and close not in text[1:-1]:
        return text[1:-1].strip()
    return text


def clue_signals(clues: list[str]) -> list[dict]:
    """풀이 가이드의 단서 "'표현' → 뜻"을 실전 신호 {phrase, means}로. 화살표가 없는 줄은 뜻만."""
    rows = []
    for clue in clues:
        phrase, arrow, means = str(clue).partition("→")
        rows.append({"phrase": unquoted(phrase), "means": means.strip()} if arrow else {"phrase": "", "means": phrase.strip()})
    return rows


def value_type(*values) -> str | None:
    """같은 자리 값들(모든 케이스)의 형(stubs.py의 이름: int, long, double, bool, string과 그 1·2차원 배열). 기본 문제 검사의 fits로 작은 형부터 맞춰 본다:
    정수 하나라도 32비트를 넘으면 long, 실수가 하나라도 있으면 double(정수와 섞여도), 빈 목록은 다른 값에서 원소 형을 가져온다.
    끝까지 원소 형이 정해지지 않거나 어느 형에도 맞지 않으면 None."""
    def filled(item, dims):
        return dims == 0 or any(filled(x, dims - 1) for x in item)

    return next((base + "[]" * dims for dims in range(3) for base in ("int", "long", "double", "bool", "string")
                 if all(fits(value, base + "[]" * dims) for value in values) and any(filled(value, dims) for value in values)), None)


def own_types(p) -> tuple[list, str | None] | None:
    """등록한 문제의 모든 케이스를 보고 정한 (인자 형들, 돌려줄 형). 형을 못 정한 자리는 None.
    케이스를 못 읽거나, 케이스마다 인자 수가 다르거나(검사 전에 등록한 문항), 인자가 26개를 넘으면 None."""
    try:
        rows = [(json.loads(case["input"]), json.loads(case["expected"])) for case in p.cases if not case.get("made")]  # 사용자가 넣은 케이스만(만든 케이스는 형을 따른다)
    except (KeyError, TypeError, ValueError, RecursionError):
        return None
    if not rows or not all(isinstance(args, list) and len(args) == len(rows[0][0]) for args, _ in rows) or len(rows[0][0]) > 26:
        return None
    return [value_type(*(args[k] for args, _ in rows)) for k in range(len(rows[0][0]))], value_type(*(expected for _, expected in rows))


def own_starter(p, language: str) -> str:
    """등록한 문제의 시작 코드: 모든 케이스의 넣을 값과 기대 결과에서 형을 정해 함수 머리를 만든다. 정할 수 없으면 빈 글.
    인자 이름은 입출력 예 표 머리에서 가져온 것(names, 예약어면 뒤에 _), 없거나 수가 다르면 a, b, c …
    프로그램 방식은 표준 입력을 읽는 main 뼈대."""
    if p.mode == "program":
        return program_stub(language)
    types, returns = own_types(p) or ([None], None)
    if None in types or returns is None:
        return ""
    names = getattr(p, "names", None)
    names = [name + "_" if name in RESERVED else name for name in names] if isinstance(names, list) and len(names) == len(types) else [chr(ord("a") + n) for n in range(len(types))]
    return stub({"params": [{"name": name, "type": typ} for name, typ in zip(names, types)], "returns": returns}, language)


DEBUG_DONE = "고친 코드가 통과했어요. 기록으로 남기려면 제출해 주세요."


def debug_closed(t, pid: str, text: str) -> list[dict]:
    """틀린 곳 같이 찾기 중에 고친 코드가 통과했다: 사용자의 말(있으면)과 맺음말을 디버그 대화에 더하고(엔진 저장소의 save_success. 엔진의 디버그 저장과 같은 모양)
    디버그 대화 전체를 돌려준다."""
    ctx, at = t.store.load(pid), now()
    rows = ([{"mode": "chair", "thread": "debug", "role": "user", "text": text, "at": at}] if text else []) + [
        {"mode": "chair", "thread": "debug", "role": "service", "text": DEBUG_DONE, "at": at}]
    t.store.save_success(ctx, ctx.plan, ctx.open_count, ctx.explain, rows, None)
    return t.session(pid).body["debug"]


def next_problem(pid: str, solved: set) -> dict | None:
    """같은 주제에서 아직 통과하지 않은 가장 낮은 단계의 문제(이 문제는 뺀다). 다 통과했으면 None(화면이 홈의 추천을 쓴다).
    지금 단계 + 1로 정해 이미 통과한 문제를 가리켰다."""
    row = BUILTIN[pid]
    left = sorted((other for other in BUILTIN.values() if other["theme"] == row["theme"] and other["id"] != pid and other["id"] not in solved), key=lambda other: other["level"])
    return {"id": left[0]["id"], "title": left[0]["title"]} if left else None


def state_body(t, p, body: dict) -> dict:
    pid, ctx, row = p.id, t.store.load(p.id), BUILTIN.get(p.id)
    if body.get("open") is True and ctx.plan is None and not p.builtin:  # 문제를 읽는 동안 뼈대와 블록 계획을 미리 만든다
        prepare_later(pid)  # 기본 문제는 힌트·해설이 실려 있어, 튜터를 시작할 때(/api/turn·/api/explain) 준비한다(튜터를 쓰지 않을 사람이 열기만 해도 모델을 부르지 않게)
    elif body.get("open") is True and not p.sample and ctx.canonical is not None and not getattr(p, "check", None):
        recheck_later(pid)  # 대조 없이 준비해 둔 등록 문제(대조 기능 전에 등록): 한 번 대조한다
    passed, total = counts(t).get(pid, (0, 0))
    study = t.store.study(pid)
    # 주제를 붙이지 않은 등록 문제는 튜터가 준비한 계획의 알고리즘(15개 주제 가운데 하나일 때만)을 보인다(목록과 같다)
    planned = ctx.plan.algorithm if not p.sample and ctx is not None and ctx.plan is not None and ctx.plan.algorithm in ALGORITHMS else ""
    kinds = Counter(case.get("kind", "example") for case in p.cases)
    examples = row["examples"] if row else [{"input": case["input"], "expected": case["expected"], "note": ""} for case in p.cases if case.get("kind", "example") == "example"]
    # 내가 등록한 문제는 수정 화면이 숨긴 케이스까지 값을 보여 준다(내가 넣은 것이다). 문제 화면은 examples만 쓴다
    mine = {} if p.sample else {"own_cases": [{"input": case["input"], "expected": case["expected"], "hidden": case.get("kind", "example") != "example"} for case in p.cases if not case.get("made")],
                                **{key: getattr(p, key, False) is True for key in ANSWER_FLAGS}}
    return {"problem": {"id": pid, "title": p.title, "language": ctx.language, "text": p.text, "sample": p.sample, "builtin": p.builtin, "mode": p.mode,
                        "theme": p.theme, "theme_name": p.theme_name or (theme_name(planned) if planned else ""), "level": p.level, **labels_of(t, p),
                        "languages": row["languages"] if row else list(check_judge().LANGUAGES), "starter": row["starters"].get(ctx.language, "") if row else own_starter(p, ctx.language),
                        "examples": examples, "cases": {kind: kinds.get(kind, 0) for kind in KINDS},
                        "study": {"hints_seen": hints_now(study, hint_rows(t, pid)), "hints_total": len(hint_rows(t, pid)), "solution_seen": bool(study["solution_at"]),
                                  "solution_open": passed > 0 or bool(study["solution_at"]), "has_guide": row is not None or ctx.solution is not None,
                                  "passed_now": passed_since(problem_subs(t, pid), study)},  # 이번 풀이에서 통과했다(아니면 화면이 해설을 저절로 열지 않는다)
                        "code": ctx.direct_code or "", "passed": passed, "submitted": total,
                        "tools": tools(), "preparing": pid in PREPARING, "prepare_failed": pid in PREP_FAILED and ctx.plan is None, "assets": assets(pid), "checkpoint_at": (checkpoint(pid, ctx.language) or {}).get("at"), **mine},
            "session": t.session(pid, body.get("mode")).body, "blocks": read_json(BLOCKS_FILE, {}).get(pid, {}), "own_way": pid in read_json(OWN_FILE, {}),
            "has_feedback": t.store.get_feedback(pid) is not None}


def attend() -> None:
    """오늘 출석을 찍는다(앱을 열면 가장 먼저 부르는 /api/problems가 부른다)."""
    today, days = date.today().isoformat(), read_json(ATTEND_FILE, [])
    if today not in days:
        write_json(ATTEND_FILE, [*days, today])


def attendance() -> dict:
    """출석한 날 수와 최근 14일(오래된 날 → 오늘)의 출석 여부."""
    days, today = {day for day in read_json(ATTEND_FILE, []) if isinstance(day, str)}, date.today()
    return {"days": len(days), "recent": [(today - timedelta(days=n)).isoformat() in days for n in range(13, -1, -1)]}


FAIL_KINDS = {"failed": "오답", "runtime_error": "실행 오류", "timeout": "시간 초과", "compile_error": "컴파일·형식 오류"}  # 함수를 못 찾은 제출도 코드 모양이 틀린 것으로 묶는다
FAIL_OF = {"output_limit": "runtime_error", "memory_limit": "runtime_error",  # 보고서에서는 실행 오류로 묶는다
           "entry_missing": "compile_error", "unsupported_signature": "compile_error",  # 코드 모양이 틀렸다
           "undecided": "failed"}
LANG_NAMES = {"python": "Python", "java": "Java", "javascript": "JavaScript", "cpp": "C++", "go": "Go", "kotlin": "Kotlin", "rust": "Rust"}

# 준비도(이 앱의 기본 문제 기준). 군과 문턱은 여기 한 곳에만 둔다. 심화(dijkstra, graph)는 단계 조건에 넣지 않는다
ESSENTIAL = ("implementation", "simulation", "hash", "sort", "brute_force", "bfs", "dfs")  # 필수
FREQUENT = ("stack_queue", "greedy", "heap", "two_pointer", "binary_search", "dp")  # 자주 나옴
READY_MIN = 5  # 도움 없이 푼 문제가 이보다 적으면 판정 보류(눈높이의 beginner 문턱과 같다)
MASTER_COUNT, BASIC_LEVEL, REAL_LEVEL = 2, 2, 3  # 주제 익힘: 도움 없이 2문제 이상, 그중 가장 높은 단계가 2(기초 익힘)·3(실전 익힘) 이상
UNAIDED_MAX_SUBMITS = 3  # 한 번의 풀이(처음, 또는 '처음부터' 뒤)에서 이 횟수 안에 통과해야 '도움 없이 푼 문제'다
REPEAT_GAP_HOURS = 24  # '처음부터' 뒤의 통과는 그 '처음부터'에서 이만큼 지난 뒤여야 센다(본 해설을 외워 붙이지 않고 시간을 두고 다시 떠올린 것만)
STAGES = {"hold": "판정 보류", "building": "기초 다지는 중", "easy": "쉬운 코딩테스트 도전", "practice": "실전 연습 단계"}
# 학습 지도: 주제 → 먼저 기초를 익힐 주제. 적은 순서가 지도 순서다(먼저 익힐 주제가 늘 앞에 있다)
PREREQS = {"implementation": (), "sort": (), "hash": (), "simulation": ("implementation",), "brute_force": ("implementation",),
           "stack_queue": (), "bfs": ("stack_queue",), "dfs": ("stack_queue", "brute_force"),
           "greedy": ("sort",), "two_pointer": ("sort",), "binary_search": ("sort",), "heap": ("sort",), "dp": ("brute_force",),
           "dijkstra": ("bfs", "heap"), "graph": ("dfs", "bfs")}
MAP_ORDER = {key: n for n, key in enumerate(PREREQS)}
COMPILE_LIKE = ("compile_error", "entry_missing", "unsupported_signature")
EARLIEST = datetime.min.replace(tzinfo=timezone.utc)


def stamp(at: str) -> datetime:
    """ISO 시각 → 시간대가 있는 시각(시간대가 다른 값끼리도 견준다). 읽지 못하면 가장 이른 시각으로 본다(도움을 놓치지 않는 쪽)."""
    try:
        moment = datetime.fromisoformat(at)
    except (TypeError, ValueError):
        return EARLIEST
    return moment if moment.tzinfo else moment.astimezone()


def problem_subs(t, pid: str) -> list[dict]:
    """한 문제의 제출(오래된 것부터). 도구가 없어 채점하지 못한 기록은 뺀다."""
    return [sub for sub in t.store.submissions() if sub["problem_id"] == pid and sub["status"] != "toolchain_missing"]


def passed_since(subs: list[dict], study: dict) -> bool:
    """이번 풀이(처음, 또는 마지막 '처음부터' 뒤)에서 이미 통과했는가."""
    start = study["reset_at"]
    return any(sub["ok"] and (start is None or stamp(sub["at"]) > stamp(start)) for sub in subs)


def unaided_pass(subs: list[dict], study: dict, talked: str | None) -> bool:
    """도움 없이 푼 문제인가. 한 번의 풀이 안에서 도움(튜터 기능·힌트·해설)을 쓰기 전에 UNAIDED_MAX_SUBMITS번 안에 통과했다:
    (가) 처음부터 첫 통과까지, 또는 (나) 마지막 '처음부터' 뒤부터 그 뒤 첫 통과까지(언어 바꾸기는 '처음부터'가 아니다). (나)의 통과는 그 '처음부터'에서
    REPEAT_GAP_HOURS 지난 뒤여야 한다(그 앞의 도움은 모두 '처음부터' 앞이므로, 마지막 도움에서도 그만큼 지났다). 통과 뒤의 도움은 판정을 바꾸지 않는다.
    talked: 남아 있는 튜터 대화의 가장 이른 시각(도움 기록을 놓쳤을 때를 위해 함께 본다. '처음부터'가 대화를 지우므로 지금 풀이의 것이다).
    도움 시각이 비었는데 해설을 먼저 봤거나 본 힌트가 있으면(시각이 없는 옛 기록) 가장 이른 때 도움을 받은 것으로 본다."""
    def clean(start, helped, gap=timedelta(0)) -> bool:
        tries = [sub for sub in subs if start is None or stamp(sub["at"]) > start]
        n = next((n for n, sub in enumerate(tries) if sub["ok"]), None)
        return (n is not None and n < UNAIDED_MAX_SUBMITS and all(stamp(at) > stamp(tries[n]["at"]) for at in helped if at)
                and (start is None or stamp(tries[n]["at"]) - start >= gap))

    first = study["help_first_at"] or (EARLIEST.isoformat() if study["solution_before_pass"] or study["hints_seen"] else None)
    return clean(None, (first, talked)) or (study["reset_at"] is not None
                                            and clean(stamp(study["reset_at"]), (study["help_after_reset_at"], talked), timedelta(hours=REPEAT_GAP_HOURS)))


def fail_kind(sub: dict) -> str | None:
    """기록(결과 종류, 정확성·효율성 통과 수)으로 가를 수 있는 실패 꼴. 세부가 없는 예전 기록과 가를 수 없는 실패는 None."""
    detail = sub["detail"]
    if sub["ok"] or not detail:
        return None
    acc, eff = detail.get("accuracy") or [0, 0], detail.get("efficiency") or [0, 0]
    right = acc[1] > 0 and acc[0] == acc[1]  # 정확성 케이스(공개 예시 포함)를 모두 통과했다
    if sub["status"] == "timeout":
        return ("slow" if eff[0] < eff[1] else None) if right else "accuracy_timeout"
    if sub["status"] in ("runtime_error", "memory_limit", "output_limit") and right:
        return "large_stop"
    return "compile:" + sub["language"] if sub["status"] in COMPILE_LIKE else None


FAIL_SAID = {"slow": "답은 맞았지만 큰 입력에서 시간이 모자랐어요.", "large_stop": "정확성 케이스는 모두 맞았지만 큰 입력에서 실행이 멈췄어요.",
             "accuracy_timeout": "정확성 케이스가 제한 시간 안에 끝나지 않았어요.", "compile": "컴파일·형식 오류가 났어요."}
FAIL_TODO = {"slow": "제한사항의 입력 크기를 먼저 보고 방법을 골라 보세요.", "large_stop": "제한사항의 가장 큰 입력을 넣었다고 생각하며 코드를 따라가 보세요.",
             "accuracy_timeout": "예시 입력을 넣고 반복이 어떻게 도는지 따라가 보세요.", "compile": "제출하기 전에 '예시 실행'으로 먼저 돌려 보세요."}


def fail_patterns(subs: list[dict], theme_of: dict) -> list[dict]:
    """주제를 가로지른 실패 꼴: 서로 다른 문제 3개 이상, 주제 2개 이상에서 나온 것만. 원인은 말하지 않고 센 사실, 고친 수, 할 일만 말한다.
    theme_of: 문제 → 보고서가 쓰는 주제(report_themes). 주제가 없는 문제는 세지 않는다."""
    hits, last_ok = defaultdict(dict), {}  # 꼴 → {문제: 처음 걸린 차례}, 문제 → 마지막 통과 차례
    for n, sub in enumerate(subs):
        pid, kind = sub["problem_id"], fail_kind(sub)
        if not theme_of.get(pid):
            continue
        if sub["ok"]:
            last_ok[pid] = n
        elif kind:
            hits[kind].setdefault(pid, n)
    out = []
    for kind, first in hits.items():
        keys = sorted({theme_of[pid] for pid in first}, key=MAP_ORDER.get)
        if len(first) < 3 or len(keys) < 2:
            continue
        fixed = sum(last_ok.get(pid, -1) > n for pid, n in first.items())
        base, language = kind.split(":")[0], kind.partition(":")[2]
        where = (f"{LANG_NAMES.get(language, language)} 코드로 낸 " if language else "") + f"{len(first)}문제({', '.join(theme_name(key) for key in keys)})에서"
        done = f"그중 {fixed}문제는 고쳐서 통과했어요." if fixed else "아직 고쳐서 통과한 문제는 없어요."
        out.append({"kind": kind, "problems": len(first), "themes": keys, "fixed": fixed, "line": f"{where} {FAIL_SAID[base]} {done} {FAIL_TODO[base]}"})
    return sorted(out, key=lambda row: -row["problems"])


RESTART = f"'이 문제 처음부터'로 다시 시작하고 {REPEAT_GAP_HOURS}시간이 지난 뒤에 도움 없이 풀어 보세요."


def left(key: str, level: int, levels: list, fresh: list, after: list) -> dict:
    """남은 주제 한 줄: 지금 도달한 단계(도움 없이 푼 문제의 가장 높은 단계)와 할 수 있는 남은 일.
    fresh: 아직 통과하지 않은 기본 문제의 단계들. 그것으로 채울 수 없으면 이미 푼 문제를 처음부터 다시 풀라고 말한다."""
    top, more = max(levels, default=0), max(0, MASTER_COUNT - len(levels))
    if len(levels) + len(fresh) < MASTER_COUNT:
        todo = f"이 주제의 남은 문제는 모두 이미 풀었어요. {RESTART}"
    elif max(levels + fresh, default=0) < level:
        todo = f"{level}단계 이상 문제는 모두 이미 풀었어요. {RESTART}"
    elif more:
        todo = f"도움 없이 {more}문제 더" + (f"({level}단계 이상 하나 포함)" if top < level else "")
    else:
        todo = f"{level}단계 이상 문제 하나 더(지금 {top}단계까지)"
    return {"key": key, "name": theme_name(key), "level": level, "solved": len(levels), "top": top, "more": more, "todo": todo, "after": after}


def readiness(unaided: dict, started: set, fresh: dict) -> dict:
    """준비도와 다음 단계까지 남은 주제(학습 지도 순서). unaided: 주제 → 도움 없이 푼 기본 문제의 단계들, fresh: 주제 → 아직 통과하지 않은 기본 문제의 단계들."""
    def mastered(key: str, level: int) -> bool:
        return len(unaided.get(key, [])) >= MASTER_COUNT and max(unaided[key]) >= level

    basic = {key: mastered(key, BASIC_LEVEL) for key in PREREQS}
    solved = sum(len(levels) for levels in unaided.values())
    need = {key: BASIC_LEVEL for key in ESSENTIAL if not basic[key]}
    if need:
        stage = "hold" if solved < READY_MIN else "building"
    else:
        need = {key: REAL_LEVEL for key in ESSENTIAL if not mastered(key, REAL_LEVEL)} | {key: BASIC_LEVEL for key in FREQUENT if not basic[key]}
        stage = "easy" if need else "practice"
    line = {"hold": f"아직 판단하기에 기록이 적어요. 도움 없이 {READY_MIN}문제를 풀면 알려 드릴게요(지금 {solved}문제).",
            "building": f"도움 없이 {solved}문제를 풀었어요. 쉬운 코딩테스트 도전까지 필수 주제 {len(need)}개가 남았어요.",
            "easy": f"필수 주제 {len(ESSENTIAL)}개를 모두 {BASIC_LEVEL}단계 이상까지 도움 없이 풀었어요({solved}문제). 쉬운 코딩테스트에 도전해 볼 만해요. "
                    f"실전 연습 단계까지 주제 {len(need)}개가 남았어요.",
            "practice": f"필수 주제 {len(ESSENTIAL)}개를 {REAL_LEVEL}단계 이상까지, 자주 나오는 주제 {len(FREQUENT)}개를 {BASIC_LEVEL}단계 이상까지 "
                        f"도움 없이 풀었어요({solved}문제). 실전 문제로 연습해 볼 만해요."}[stage]
    # 다음에 배울 주제: 남은 것 가운데 먼저 익힐 주제를 모두 익힌 것(필수 → 자주, 시작한 주제, 지도 순서). 없으면 첫 주제의 못 익힌 선수 주제로 거슬러 간다
    order = sorted(need, key=lambda key: (key not in ESSENTIAL, key not in started, MAP_ORDER[key]))
    focus = next((key for key in order if all(basic[p] for p in PREREQS[key])), order[0] if order else None)
    while focus and any(not basic[p] for p in PREREQS[focus]):
        focus = next(p for p in PREREQS[focus] if not basic[p])
    return {"stage": stage, "label": STAGES[stage], "line": line, "solved": solved, "focus": focus,
            "goal": STAGES["practice" if stage == "easy" else "easy"] if need else None,  # 남은 것이 향하는 단계
            "remaining": [left(key, need[key], unaided.get(key, []), fresh.get(key, []), [theme_name(p) for p in PREREQS[key] if not basic[p]])
                          for key in PREREQS if key in need],
            "basis": "이 앱의 기본 문제 기준이에요.",
            "rules": [f"도움 없이 푼 문제: 튜터 기능(대화, 블록 채우기, 해설 모드, 틀린 곳 같이 찾기, AI 피드백), 힌트, 해설을 쓰기 전에 제출 {UNAIDED_MAX_SUBMITS}번 안에 "
                      f"통과한 기본 문제예요. '이 문제 처음부터'로 다시 시작했다면 {REPEAT_GAP_HOURS}시간이 지난 뒤에 그렇게 통과해도 세요. "
                      "통과한 뒤에 쓴 도움은 판정을 바꾸지 않아요. 등록한 문제는 세지 않아요.",
                      f"기초 익힘: 한 주제에서 도움 없이 {MASTER_COUNT}문제 이상 풀었고, 그중 하나가 {BASIC_LEVEL}단계 이상이에요. 실전 익힘은 {REAL_LEVEL}단계 이상이에요.",
                      f"판정 보류: 도움 없이 푼 문제가 {READY_MIN}문제보다 적어요.",
                      f"쉬운 코딩테스트 도전: 필수 주제({', '.join(theme_name(key) for key in ESSENTIAL)})를 모두 기초 익힘.",
                      f"실전 연습 단계: 필수 주제를 모두 실전 익힘, 자주 나오는 주제({', '.join(theme_name(key) for key in FREQUENT)})를 모두 기초 익힘."]}


def learning_report(t) -> dict:
    """학습 보고서. 저장된 제출·학습 기록에서 규칙으로만 계산한다(모델 0회).

    주제의 상태(기본 문제를 본다. 주제가 있는 등록 문제(report_themes: 붙인 주제, 없으면 검증된 계획의 유형)는 제출·실패 수와 약점 판정에만 더한다.
    단계 칸, 'n문제 중 m문제', 준비도는 기본 문제만)
    - new      아직 제출한 적이 없다.
    - strong   도움 없이(unaided_pass) 3문제 이상 풀었고, 그 가운데 60% 이상을 첫 제출에 통과했고,
               풀기 전에 해설을 연 문제가 없다.
    - weak     아래 가운데 하나: 두 문제 이상에 걸쳐 제출이 3번 이상인데 60% 이상이 통과하지 못했다(한 문제에서 여러 번 틀리고 푼 것은 약점이 아니다) /
               두 문제 이상에서 답은 맞았지만 큰 입력에서 시간이 모자랐다(fail_kind의 slow) /
               풀기 전에 해설을 연 문제가 2개 이상이다 / 3번 넘게 제출하고도 아직 못 푼 문제가 있다.
    - progress 그 밖(풀고 있는 중).
    """
    subs = [sub for sub in t.store.submissions() if sub["status"] != "toolchain_missing"]  # 도구가 없어 채점하지 못한 예전 기록은 제출이 아니다
    by_problem: dict[str, list] = defaultdict(list)
    for sub in subs:
        if sub["problem_id"] in PROBLEMS:
            by_problem[sub["problem_id"]].append(sub)
    solved = {pid for pid, rows in by_problem.items() if any(row["ok"] for row in rows)}
    first = {pid for pid, rows in by_problem.items() if rows[0]["ok"]}
    talked = {row["problem_id"]: row["at"] for row in t.store.conn.execute("SELECT problem_id, MIN(at) AS at FROM message GROUP BY problem_id")}
    unaided, fresh = {}, {}  # 주제 → 도움 없이 푼 기본 문제의 단계들, 아직 통과하지 않은 기본 문제의 단계들
    theme_of, differ = report_themes(t)
    own_by_theme = defaultdict(list)  # 주제가 있는 등록 문제(붙인 주제, 없으면 검증된 계획의 유형)
    for pid, p in PROBLEMS.items():
        if not p.sample and theme_of.get(pid):
            own_by_theme[theme_of[pid]].append(pid)
    theme_rows_, signals, started = [], [], set()  # started: 기본 문제를 제출해 본 주제(다음에 풀 문제의 '이어서 풀기'는 이것만. 등록 문제는 실패 수·약점 판정에만 쓴다)
    for key in ALGORITHMS:
        mine = [row for row in BUILTIN.values() if row["theme"] == key]
        if not mine:
            continue
        mine.sort(key=lambda row: row["level"])
        tried = [row for row in mine if row["id"] in by_problem]
        done = [row for row in mine if row["id"] in solved]
        if tried:
            started.add(key)
        own_tried = [{"id": pid, "title": PROBLEMS[pid].title} for pid in own_by_theme[key] if pid in by_problem]
        mine_subs = [sub for row in tried + own_tried for sub in by_problem[row["id"]]]
        fails = Counter(FAIL_OF.get(sub["status"], sub["status"]) for sub in mine_subs if not sub["ok"])
        fails = {kind: fails.get(kind, 0) for kind in FAIL_KINDS}
        studies = {row["id"]: t.store.study(row["id"]) for row in mine}
        early = sum(study["solution_before_pass"] for study in studies.values())
        first_try = sum(row["id"] in first for row in done)
        alone = [row for row in done if unaided_pass(by_problem[row["id"]], studies[row["id"]], talked.get(row["id"]))]  # 도움 없이 푼 문제
        unaided[key], fresh[key] = [row["level"] for row in alone], [row["level"] for row in mine if row["id"] not in solved]
        alone_first = sum(row["id"] in first for row in alone)
        slow = {sub["problem_id"] for sub in mine_subs if fail_kind(sub) == "slow"}
        stuck = [row for row in tried + own_tried if row["id"] not in solved and len(by_problem[row["id"]]) > 3]
        failed = sum(fails.values())
        todo = next_up(mine, solved)
        # 해설을 먼저 본 문제: 그 뒤의 통과 제출이 한 번 이하면 힌트·해설 없이 다시 풀었는지 가릴 수 없어 다시 권한다
        review = next((row for row in mine if studies[row["id"]]["solution_before_pass"]
                       and sum(sub["ok"] and stamp(sub["at"]) >= stamp(studies[row["id"]]["solution_at"]) for sub in by_problem.get(row["id"], [])) <= 1), None)
        if not tried and not own_tried and not early:
            state, why = "new", "아직 풀어 보지 않았어요."
        elif len(alone) >= 3 and alone_first >= 0.6 * len(alone) and not early:
            state, why = "strong", f"{len(mine)}문제 중 {len(alone)}문제를 도움 없이 풀었고, 그중 {alone_first}문제를 첫 제출에 통과했어요."
        elif len(slow) >= 2:
            fixed = sum(pid in solved for pid in slow)
            state, why = "weak", (f"{len(slow)}문제에서 답은 맞았지만 큰 입력에서 시간이 모자랐어요" + (f"(그중 {fixed}문제는 통과)" if fixed else "")
                                  + ". 제한사항의 입력 크기를 먼저 보고 방법을 골라 보세요.")
        elif len(tried) + len(own_tried) >= 2 and len(mine_subs) >= 3 and failed >= 0.6 * len(mine_subs):
            most = max(fails.values())
            tops = [kind for kind, n in fails.items() if n == most]  # 수가 같으면 나란히
            state, why = "weak", f"제출 {len(mine_subs)}번 중 {failed}번이 통과하지 못했어요(가장 많은 것: {' · '.join(FAIL_KINDS[k] for k in tops)} {most}번{'씩' if len(tops) > 1 else ''})."
        elif early >= 2:
            state, why = "weak", f"풀기 전에 해설을 먼저 연 문제가 {early}개예요. 힌트까지만 보고 한 번 더 버텨 보세요."
        elif stuck:
            state, why = "weak", f"'{stuck[0]['title']}' 문제를 {len(by_problem[stuck[0]['id']])}번 제출했지만 아직 통과하지 못했어요."
        else:
            own_line = f" 등록한 문제 {sum(pid in solved for pid in own_by_theme[key])}개를 풀었어요." if own_by_theme[key] else ""  # 등록 문제의 통과는 따로 말한다(제출 수와 기준을 맞춘다)
            state, why = "progress", f"기본 문제 {len(mine)}문제 중 {len(done)}문제를 풀었어요.{own_line}" + (f" 다음은 {todo['level']}단계예요." if todo else " 모두 풀었어요.")
        theme_rows_.append({"key": key, "name": theme_name(key), "solved": len(done), "total": len(mine), "level_reached": max((row["level"] for row in done), default=0),
                            "submissions": len(mine_subs), "first_try": first_try, "fails": fails, "hints": sum(study["hints_seen"] for study in studies.values()),
                            "solution_before_pass": early, "state": state, "why": why, "next": {"id": todo["id"], "title": todo["title"], "level": todo["level"]} if todo else None,
                            "review": {"id": review["id"], "title": review["title"], "level": review["level"]} if review else None,
                            # 이 주제를 고른 등록 문제 가운데 풀이 계획의 유형이 다른 것(둘을 나란히 보인다)
                            "plan_differs": [{"id": pid, "title": PROBLEMS[pid].title, "planned": theme_name(differ[pid])} for pid in own_by_theme[key] if pid in differ]})
        if done:  # 실전 신호는 푼 문제 것만 보여 준다(풀기 전에 보이면 스스로 알아채는 연습이 사라진다)
            signals.append({"key": key, "name": theme_name(key), "items": [{**signal, "title": row["title"]} for row in done for signal in row["signals"]]})
    strong = sorted((row for row in theme_rows_ if row["state"] == "strong"), key=lambda row: (-row["solved"], -row["first_try"]))[:3]
    weak = sorted((row for row in theme_rows_ if row["state"] == "weak"), key=lambda row: -sum(row["fails"].values()))[:3]
    # 다음에 풀 문제: 쓰던 문제 → 약한 주제(해설을 먼저 본 문제, 다음 단계) → 풀고 있는 주제의 다음 단계 → 아직 안 해 본 주제 → 강한 주제의 다음 단계.
    # 쓰던 문제: 통과하지 못했고 손댄(코드 저장·실행·제출·힌트) 문제 가운데 가장 최근 것. 손댄 시각(touched.json)이 없는 예전 기록은 마지막 제출 시각,
    # 그것도 없으면(코드만 쓴 예전 기록) 가장 뒤에 문제 순서로
    stamps, mine_code = read_json(TOUCHED_FILE, {}), touched(t)
    last = {pid: max(str(stamps.get(pid) or ""), by_problem[pid][-1]["at"] if pid in by_problem else "") for pid in PROBLEMS}
    writing = sorted((pid for pid in PROBLEMS if pid not in solved and (pid in by_problem or pid in mine_code or pid in stamps)), key=lambda pid: last[pid], reverse=True)
    queue = [({"id": pid, "title": PROBLEMS[pid].title, "level": PROBLEMS[pid].level}, PROBLEMS[pid].theme_name or (theme_name(theme_of[pid]) if theme_of.get(pid) else ""),
              "쓰던 문제예요.") for pid in writing[:1]]
    for row in weak:
        queue += [(row["review"], row["name"], "해설을 먼저 본 문제예요. 힌트 없이 다시 풀어 보세요.")] if row["review"] else []
        queue += [(row["next"], row["name"], "약한 주제예요: " + row["why"])]
    # 까닭에는 주제·단계를 다시 적지 않는다(화면이 '해시 3단계 · '를 앞에 붙인다)
    queue += [(row["next"], row["name"], "이어서 풀기") for row in theme_rows_ if row["state"] == "progress" and row["next"] and row["key"] in started]
    queue += [(row["next"], row["name"], "새 주제 시작") for row in sorted(theme_rows_, key=lambda row: MAP_ORDER[row["key"]])  # 학습 지도 순서
              if row["state"] == "new" or (row["state"] == "progress" and row["key"] not in started)]
    queue += [(row["next"], row["name"], "한 단계 더") for row in theme_rows_ if row["state"] == "strong" and row["next"]]
    todo_rows, picked = [], set()
    for target, name, why in queue:
        if target and target["id"] not in picked and len(todo_rows) < 5:
            picked.add(target["id"])
            todo_rows.append({"id": target["id"], "title": target["title"], "theme_name": name, "level": target["level"], "why": why})
    feedbacks = []
    for row in t.store.conn.execute("SELECT f.problem_id, f.body_json, s.at FROM feedback f LEFT JOIN submission s ON s.id=f.submission_id ORDER BY s.at DESC").fetchall():
        if row["problem_id"] in PROBLEMS:
            saved = json.loads(row["body_json"])
            feedbacks.append({"id": row["problem_id"], "title": PROBLEMS[row["problem_id"]].title, "at": row["at"] or "",
                              "summary": str(saved.get("advice") or saved.get("analysis") or "")[:200]})
    builtin_solved = sum(pid in BUILTIN for pid in solved)
    ready = readiness(unaided, started, fresh)
    if ready["focus"]:  # 다음에 배울 주제와 그 주제의 다음 문제
        row = next((row for row in theme_rows_ if row["key"] == ready["focus"]), {})
        ready["focus"] = {"key": ready["focus"], "name": theme_name(ready["focus"]), "next": row.get("next")}
    mine_ids = [pid for pid, p in PROBLEMS.items() if not p.sample]  # 사용자가 등록한 문제
    # 통과하지 못한 제출은 기본 문제와 등록한 문제를 모두 센다(주제별 진행·강점·약점은 기본 문제만)
    fails_all = Counter(FAIL_OF.get(sub["status"], sub["status"]) for rows in by_problem.values() for sub in rows if not sub["ok"])
    return {
        "summary": {"solved": builtin_solved, "total": len(BUILTIN), "submissions": len(subs), "fails": {kind: fails_all.get(kind, 0) for kind in FAIL_KINDS},
                    "own": {"solved": sum(pid in solved for pid in mine_ids), "total": len(mine_ids)},
                    "first_try_rate": round(len(first) / len(by_problem), 2) if by_problem else 0, "languages": dict(Counter(sub["language"] for sub in subs))},
        "themes": theme_rows_,
        "strengths": [{"key": row["key"], "name": row["name"], "why": row["why"]} for row in strong],
        "weaknesses": [{"key": row["key"], "name": row["name"], "why": row["why"], "next": {"id": (row["review"] or row["next"])["id"], "title": (row["review"] or row["next"])["title"]}
                        if row["review"] or row["next"] else None} for row in weak],
        "pitfalls": [{"name": PITFALLS[pid][1] if pid in PITFALLS else pid, "count": count} for pid, count in t.store._frequent_pitfalls(5)],
        "recent": [{"id": sub["problem_id"], "title": PROBLEMS[sub["problem_id"]].title, "ok": sub["ok"], "status": sub["status"], "language": sub["language"], "at": sub["at"]}
                   for sub in reversed(subs) if sub["problem_id"] in PROBLEMS][:10],
        "signals": signals, "feedbacks": feedbacks, "next": todo_rows, "attendance": attendance(),
        "readiness": ready, "patterns": fail_patterns(subs, theme_of),
    }


def handle(path: str, body: dict) -> tuple[int, dict]:
    if path == "/api/problems":
        attend()
        with tutor() as t:
            rows = problem_rows(t)
            return 200, {"problems": rows, "themes": theme_rows(rows)}
    if path == "/api/report":
        with tutor() as t:
            return 200, learning_report(t)
    if path == "/api/problems/new":
        return 200, register(body, once=True)
    if path == "/api/problems/edit":
        return 200, edit(body)
    if path == "/api/problems/delete":
        return 200, delete(body)
    if path == "/api/problems/read":  # 올린 파일에서 글 읽기(등록 전에 사용자가 확인하고 고친다)
        return 200, read_files(body)
    if path == "/api/problems/cases":  # 문제 글의 입출력 예 표(함수 방식)나 예제 입력·출력 구역(mode: program)에서 케이스 찾기(모델 0회)
        if not isinstance(body.get("text"), str):
            raise Refuse("문제 글은 글이어야 해요.", field="text")
        found, other = (sample_cases, table_cases) if body.get("mode") == "program" else (table_cases, sample_cases)
        return 200, {**found(body["text"]), "other": len(other(body["text"])["cases"])}  # other: 다른 방식으로 찾은 케이스 수(방식을 바꾸자고 한다)
    if path == "/api/tools":  # 언어 도구 있음·없음. refresh가 참이면 다시 센다(도구를 설치한 뒤)
        return 200, {"tools": tools(body.get("refresh") is True)}
    if path == "/api/accounts":
        return 200, accounts()
    if path == "/api/tour":  # 처음 안내를 봤다고 적는다(창을 다시 켜도 또 뜨지 않게. 웹뷰는 localStorage를 남기지 않는다)
        write_json(PREFS_FILE, {**read_json(PREFS_FILE, {}), "tour_seen": True})
        return 200, accounts()
    if path == "/api/prefs":  # 화면 설정. 지금은 화면 색(system이면 키를 지워 운영체제 설정을 따른다)
        if body.get("scheme") not in ("system", "light", "dark"):
            raise Refuse("화면 색은 시스템 설정대로, 라이트, 다크 가운데 하나예요.", field="scheme")
        kept = {key: value for key, value in read_json(PREFS_FILE, {}).items() if key != "scheme"}
        write_json(PREFS_FILE, kept if body["scheme"] == "system" else {**kept, "scheme": body["scheme"]})
        return 200, accounts()
    if path == "/api/theme":  # 과정 하나의 급과 추론 정도. 빈 값은 기본값으로 돌린다는 뜻이다
        if not all(isinstance(body.get(key, ""), str) for key in ("theme", "tier", "effort")) or body.get("theme") not in themes.THEMES:
            raise Refuse("알 수 없는 과정이에요.")
        tier, effort = str(body.get("tier") or "").strip(), str(body.get("effort") or "").strip()
        if tier and tier not in themes.TIERS:
            raise Refuse("급은 small, middle, large 가운데 하나예요.")
        if effort and effort not in themes.EFFORTS:
            raise Refuse("추론 정도는 low, medium, high 가운데 하나예요.")
        chosen = {**themes.CHOSEN, body["theme"]: {"tier": tier, "effort": effort}}
        write_json(PREFS_FILE, {**{key: value for key, value in read_json(PREFS_FILE, {}).items() if key != "themes"}, "stages": chosen})  # 예전 테마별 모델은 옮겨 담았으니 지운다
        themes.choose(chosen)
        return 200, accounts()
    if path == "/api/client":
        if body.get("client") not in ("cli", "provider"):
            raise Refuse("알 수 없는 연결 방식이에요.")
        if body["client"] == "cli" and not dev_client():  # 화면에서 숨긴 선택지를 요청으로 고르지 못하게 한다
            raise Refuse("이 연결 방식은 쓸 수 없어요. 연결한 AI를 써 주세요.", 403, "dev_only")
        STATE["client"] = body["client"]
        return 200, accounts()
    if path == "/api/key":
        value = body.get("value")
        if not isinstance(body.get("name"), str) or body["name"] not in KEYS or not isinstance(value, str) or not value.strip():
            raise Refuse("키 종류를 고르고 키를 적어 주세요.")
        value = value.strip()
        if len(value) > 400 or any(ch in value for ch in "\r\n\0"):
            raise Refuse("키가 너무 길거나 쓸 수 없는 글자가 있어요.")
        label, prefix = KEY_FORM[body["name"]]
        if not (value.startswith(prefix) and re.fullmatch(r"[A-Za-z0-9_-]+", value)) or (body["name"] == "openai" and value.startswith("sk-ant-")):  # Claude 키를 OpenAI 칸에 넣어도 거른다
            raise Refuse(f"{label} 키의 꼴이 아니에요. {prefix}로 시작하고 영문·숫자·-·_만 있어야 해요. 빈칸이나 한글이 섞이지 않았는지 확인해 주세요.", field="value")
        found = keycheck.check(body["name"], value)  # 공식 주소에 모델 목록 조회 한 번(요금 없음, 10초). 키 값은 어디에도 남기지 않는다
        if found == keycheck.INVALID:
            raise Refuse(f"{label}가 이 키를 받아 주지 않아요(401). 키를 다시 복사해 붙여 넣어 주세요.", 400, "key_invalid", "value")
        if body.get("force") is not True:  # 아래는 사용자가 '그래도 저장'을 고를 수 있다
            if found == keycheck.DENIED:
                raise Refuse(f"이 키로는 {label}의 모델 목록을 볼 권한이 없어요(403). 키의 권한을 확인하거나, 그래도 저장할 수 있어요.", 409, "key_denied", "value")
            if found == keycheck.SERVER:
                raise Refuse(f"{label} 서버가 답하지 않아 키를 확인하지 못했어요. 잠시 뒤 다시 시도하거나, 확인 없이 저장할 수 있어요.", 409, "key_unverified", "value")
            if found == keycheck.OFFLINE:
                raise Refuse(f"{label}에 연결하지 못해 키를 확인하지 못했어요. 인터넷 연결을 보고 다시 시도하거나, 확인 없이 저장할 수 있어요.", 409, "key_unverified", "value")
        os.environ[KEYS[body["name"]]] = value
        save_key(KEYS[body["name"]], value)  # 다음에 켜도 쓰게 이 기기에만 저장한다
        return 200, {**accounts(), "key_check": found}  # found: ok·limited(키는 맞음), 그 밖은 확인 없이 저장한 것
    if path == "/api/key/delete":  # 화면에서 넣은 그 공급자의 키만 지운다
        if not isinstance(body.get("name"), str) or body["name"] not in KEYS:
            raise Refuse("지울 키 종류를 골라 주세요.")
        env, saved = KEYS[body["name"]], read_json(KEY_FILE, {})
        if env not in saved:
            raise Refuse("이 키는 화면에서 넣은 것이 아니에요. 넣어 둔 곳(.env나 환경 변수)에서 지워 주세요.", 409, "key_outside")
        if os.environ.get(env) == saved[env]:  # 환경 변수의 값이 다른 것이면(밖에서 준 키) 그대로 둔다
            os.environ.pop(env)
        drop_key(env)
        load_keys()  # .env에 같은 공급자의 키가 있으면 다시 올린다(지운 뒤의 연결 상태가 실제와 같게)
        return 200, accounts()
    if path == "/api/update":  # 새 버전: 상태·확인·받기·바꾸기(action)
        try:
            return 200, updater.handle(body, stop_grading)
        except updater.Refused as exc:
            raise Refuse(str(exc), 409, "update") from None
    if path == "/api/chatgpt/login":
        from app.llm.openai.oauth import token

        return 200, {"url": token.begin_login()["url"]}

    p = problem(body)
    pid = p.id
    with tutor() as t:
        if t.store.load(pid) is None:  # 기본 문제는 처음 열 때 엔진 저장소에 넣는다(마지막으로 고른 언어로)
            t.store.put_problem(pid, first_language(p), p.text, title=p.title)
        language = LANG[pid] = t.store.load(pid).language
        row = BUILTIN.get(pid)
        if path in ("/api/code", "/api/blocks") and "language" in body and body["language"] != language:  # 언어를 바꾸는 사이에 온 옛 언어의 코드는 새 언어 칸에 넣지 않는다
            return 200, {"stale": True}
        if path in ("/api/run", "/api/submit") or (path == "/api/hint" and body.get("peek") is not True) or (  # 손댄 시각('이어서 풀기'). 시작 코드 그대로 저장한 것은 아니다
                path == "/api/code" and code_of(body).strip() != starter_of(p, language).strip()):
            write_json(TOUCHED_FILE, {**read_json(TOUCHED_FILE, {}), pid: datetime.now().astimezone().isoformat(timespec="microseconds")})  # 같은 초의 제출 시각보다 뒤로 놓인다
        if path == "/api/language":
            code = code_of(body) if "code" in body else None
            wanted = str(body.get("language") or "")
            if wanted not in (row["languages"] if row else check_judge().LANGUAGES):
                raise Refuse("이 문제에서 고를 수 없는 언어예요.", field="language")
            if wanted != language:
                with LOCKS[pid]:
                    change_language(t, p, wanted, code)
                language = wanted
            write_json(PREFS_FILE, {**read_json(PREFS_FILE, {}), "language": wanted})  # 다음에 처음 여는 문제도 이 언어로
            body = {**body, "open": True}  # 새 언어의 블록 계획을 뒤에서 만들어 둔다(아래 /api/state와 같은 길)
        if row and row.get("ready") and language == "python" and path in ("/api/state", "/api/language", "/api/turn", "/api/explain"):
            t.adopt(pid, row["ready"])  # 기본 문제는 미리 만들어 둔 풀이 가이드와 블록으로 바로 시작한다(계획이 이미 있으면 그대로 둔다)
        if path in ("/api/state", "/api/language"):
            return 200, state_body(t, p, body)
        if path == "/api/run":  # 공개 예시만, 또는 직접 넣은 값(input) 하나로 돌려 본다. 제출로 남기지 않는다
            code = need_code(body)
            if body.get("input") is not None:
                return 200, run_once(p, language, code, own_input(p, body["input"]))
            return 200, result_body(grade(p, language, code, ("example",)))
        if path == "/api/hint":
            rows = hint_rows(t, pid)
            if not rows:
                raise Refuse("이 문제에는 미리 만들어 둔 힌트가 없어요. 튜터를 연결하면 질문으로 도와드려요.", 404, "not_found")
            study = t.store.study(pid)
            seen = hints_now(study, rows)
            if body.get("peek") is True:  # 이번 풀이에서 본 힌트만 다시 보여 준다(문제를 다시 열었을 때). 새 힌트를 열지 않는다
                return 200, {"seen": seen, "total": len(rows), "done": seen == len(rows), "shown": hints_shown(rows, seen)}
            if seen < len(rows):  # 다 본 뒤에는 마지막 힌트를 다시 준다
                seen += 1
                t.store.set_study(pid, hints_seen=study["hints_seen"] + 1)  # 본 힌트 수는 누적이다
                t.store.mark_help(pid)
            shown = hints_shown(rows, seen)
            return 200, {**shown[-1], "seen": seen, "total": len(rows), "done": seen == len(rows), "shown": shown}
        if path == "/api/solution":  # 기본 문제는 실린 해설, 등록한 문제는 엔진이 만들어 둔 그 언어의 풀이 가이드
            own_guide = None if row else t.store.load(pid).solution
            if row is None and own_guide is None:
                raise Refuse("아직 풀이 가이드가 없어요. AI를 연결하고 튜터를 시작하면 만들어져요.", 404, "not_found")
            study, passed = t.store.study(pid), counts(t).get(pid, (0, 0))[0] > 0
            if not (passed or study["solution_at"] or body.get("force") is True):
                return 409, {"error": "locked", "message": "아직 통과하지 않았어요. 그래도 해설을 보려면 한 번 더 눌러 주세요."}
            if not study["solution_at"]:  # 처음 연 때와, 그때 아직 못 풀었는지를 적어 둔다(학습 보고서가 본다)
                t.store.set_study(pid, solution_at=now(), solution_before_pass=not passed)
            if not passed_since(problem_subs(t, pid), study):  # 통과한 뒤에 여는 해설(통과하면 화면이 저절로 연다)은 도움이 아니다
                t.store.mark_help(pid)
            if own_guide is not None:
                return 200, {"signals": clue_signals(own_guide.clues), "pattern": "", "learn": "", "pitfalls": [], "ladder": [], "clues": own_guide.clues,
                             "approach": own_guide.approach, "steps": own_guide.steps, "code": own_guide.code, "language": language, "next": None, "verified": own_guide.verified}
            guide = (row.get("ready") or {}).get("solution") or {}
            shown = language if language in row["solutions"] else "python"
            return 200, {"signals": row["signals"], "pattern": row["pattern"], "learn": row["learn"], "pitfalls": row["pitfalls"], "ladder": row["ladder"],
                         "clues": guide.get("clues") or [], "approach": guide.get("approach") or "", "steps": guide.get("steps") or [],
                         "code": row["solutions"][shown], "language": shown, "next": next_problem(pid, {key for key, (ok, _) in counts(t).items() if ok}), "verified": True}
        if path == "/api/code":
            t.store.update_code(pid, code_of(body))
            return 200, {"ok": True}
        if path == "/api/own_way":  # '튜터 차례로 돌아가기'(on: false). 켜는 것은 넘어가기 요청(/api/turn own_way)이 한다
            own_way(pid, body.get("on") is True and pid in read_json(OWN_FILE, {}))
            return 200, {"own_way": pid in read_json(OWN_FILE, {})}
        if path == "/api/blocks":
            write_json(BLOCKS_FILE, {**read_json(BLOCKS_FILE, {}), pid: blocks_of(body)})
            return 200, {"ok": True}
        if path == "/api/compose":  # 블록 칸의 글을 블록 코드 확인이 잇는 것과 같은 함수(framed)로 모은다. 화면에는 모으기 구현이 없다
            ctx = t.store.load(pid)
            if ctx is None or ctx.plan is None:
                return 200, {"parts": []}
            names = [row["name"] for row in blocks_body(ctx.plan, shown_count(ctx, body.get("mode")), ctx.language)]
            return 200, {"parts": composed_parts(ctx.plan.blocks, blocks_of(body), ctx.language, names, p.mode == "program", starter_of(p, ctx.language),
                                                 trusted=ctx.solution is not None and ctx.solution.verified is not False)}
        if path == "/api/checkpoint":  # 지금 언어의 체크포인트를 덮어쓴다
            saved = {"code": code_of(body), "blocks": blocks_of(body), "at": now()}
            marks = read_json(CHECKPOINTS_FILE, {})
            write_json(CHECKPOINTS_FILE, {**marks, pid: {**marks.get(pid, {}), language: saved}})
            return 200, {"at": saved["at"]}
        if path == "/api/checkpoint/restore":  # 코드 칸만 되돌린다(대화·블록 진행·제출 기록은 그대로)
            saved = checkpoint(pid, language)
            if saved is None:
                raise Refuse("남겨 둔 체크포인트가 없어요.", 404, "not_found")
            t.store.update_code(pid, saved["code"])
            write_json(BLOCKS_FILE, {**read_json(BLOCKS_FILE, {}), pid: saved["blocks"]})
            reset_at = t.store.study(pid)["reset_at"]
            if reset_at and stamp(saved.get("at")) <= stamp(reset_at):  # '처음부터' 앞에 남긴 코드를 되살렸다: 이번 풀이의 도움으로 센다(첫 풀이의 판정은 그대로)
                t.store.mark_help(pid, this_try_only=True)
            return 200, state_body(t, p, body)
        if path == "/api/reset":
            with LOCKS[pid]:
                reset(t, pid)
            return 200, {"ok": True}
        if path == "/api/submit":
            return 200, result_body(judge(t, p, language, need_code(body)))
        if path == "/api/feedback/get":
            saved = t.feedback_get(pid)
            return saved.status, saved.body
        with LOCKS[pid]:
            if path in ("/api/turn", "/api/followup", "/api/fill", "/api/explain", "/api/feedback", "/api/debug"):
                t.store.mark_help(pid)  # 튜터 기능을 쓴 시각(학습 보고서가 도움 없이 푼 문제를 가린다)
            if path == "/api/turn":
                mine = body.get("own_way") is True and body.get("skip") is True  # 끝까지 내 방식으로 쓰기: 넘어가기 + 남은 블록 모두 열기
                out = t.turn(pid, body.get("mode"), body.get("event"), text=body.get("text"), block_id=body.get("block_id"), code=body.get("code"),
                             quiet=body.get("quiet") is True, skip=body.get("skip") is True, own_way=mine)
                if mine and out.status < 400:
                    own_way(pid, True)
            elif path == "/api/followup":
                out = t.followup(pid, body.get("mode"), body.get("quote_id"), body.get("text"))
            elif path == "/api/fill":
                out = t.fill(pid, body.get("block_id"), filled=body.get("filled") or [])
            elif path == "/api/explain":
                out = t.explain(pid)
            elif path == "/api/feedback":
                out = t.feedback(pid)
            elif path == "/api/debug":
                code = need_code(body)
                saved_code, report = REPORTS.get(pid) or ("", None)
                judged = None
                if report is None or saved_code.strip() != code.strip():  # 코드를 고쳤으면 다시 채점한 결과로 본다. 제출로 남기지 않는다(예시 실행 뒤에 열린 디버그가 제출 수를 늘렸다)
                    report = grade(p, language, code)
                    REPORTS[pid] = (code, report)
                    judged = {**result_body(report), "unsaved": True}
                if report["status"] == "passed":  # 엔진을 부르지 않는다: 내 말(있으면)과 맺음말만 디버그 대화에 남긴다
                    return 200, {"passed": True, "judged": judged or result_body(report), "messages": debug_closed(t, pid, str(body.get("text") or "").strip())}
                if report["cases"] and all(case["status"] == "passed" for case in report["cases"] if case["kind"] != "efficiency"):
                    # 답은 맞고 큰 입력에서만 걸렸다: 틀린 줄을 찾을 일이 아니라 방법을 바꿀 일이다(큰 입력은 모델에 넘기지 않는다)
                    return 200, {"passed": False, "efficiency_only": True, "judged": judged or result_body(report),
                                 "message": "답은 맞아요. 다만 입력이 아주 클 때 시간이 모자라요. 제한사항의 입력 크기를 보고, 같은 것을 되풀이해 세거나 찾는 곳이 없는지 살펴보세요."}
                seen = tutor_view(report)
                lines = [{**case, "line": raw.get("line")} for case, raw in zip(seen["cases"], report["cases"]) if raw["kind"] != "efficiency"] or seen["cases"]  # 채점기가 준 오류 줄을 같이 넘긴다
                out = t.debug(pid, code, {**seen, "compile_line": report.get("compile_line"), "cases": lines},
                              text=str(body.get("text") or "").strip() or None)
                return out.status, {**out.body, "judged": judged}
            else:
                raise Refuse("찾지 못했어요.", 404, "not_found")
            return out.status, out.body


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload, kind: str = "application/json", headers: dict | None = None) -> None:
        data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{kind}; charset=utf-8" if kind.startswith("text/") or kind == "application/json" or kind.endswith("+xml") else kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def _local(self) -> bool:
        """다른 사이트가 이 서버를 부르지 못하게: 호스트는 이 기기 이름만(DNS 되묶기 막기)."""
        return (self.headers.get("Host") or "").rsplit(":", 1)[0] in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self._local():
            return self._send(403, {"detail": {"code": "forbidden", "message": "이 기기에서만 열 수 있어요."}})
        path = self.path.split("?", 1)[0]
        if path in STATIC:
            name, kind = STATIC[path]
            page = (STATIC_DIR / name).read_bytes()
            if name == "index.html":  # 고른 화면 색을 첫 HTML에 실어 첫 그림 전에 맞춘다(웹뷰는 localStorage를 남기지 않고, 요청을 기다리면 깜빡인다)
                page = page.replace(b'data-scheme-pref="system"', f'data-scheme-pref="{scheme_pref()}"'.encode(), 1)
            return self._send(200, page, kind)
        found = re.fullmatch(r"/asset/([^/]+)/([^/]+)", path)  # 올린 원본: index.json에 적힌 것만
        if found and OWN_ID.fullmatch(found[1]) and re.fullmatch(r"\d{1,2}", found[2]):
            row = next((raw for raw in assets(found[1]) if isinstance(raw, dict) and raw.get("n") == int(found[2]) and raw.get("type") in ASSET_TYPES), None)
            file = row and ASSETS / found[1] / f"{row['n']:02d}.{row['type']}"
            if file and file.is_file():
                return self._send(200, file.read_bytes(), ASSET_TYPES[row["type"]], {"X-Content-Type-Options": "nosniff", "Content-Disposition": "inline"})
        return self._send(404, {"detail": {"code": "not_found", "message": "찾지 못했어요."}})

    def _refused(self) -> tuple[int, str, str] | None:
        """본문을 읽기 전에 다른 사이트의 요청을 막는다. 브라우저의 단순 요청(text/plain 등)은 사전 확인 없이 오므로
        미디어 타입을 정확히 보고, Origin·Sec-Fetch-Site가 있으면 이 서버 자신이어야 한다."""
        if not self._local():
            return 403, "forbidden", "이 화면에서 보낸 요청만 받아요."
        if (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower() != "application/json":
            return 415, "unsupported_media_type", "이 화면에서 보낸 요청만 받아요."
        origin, port = self.headers.get("Origin"), self.server.server_port
        if origin is not None and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
            return 403, "forbidden", "이 화면에서 보낸 요청만 받아요."
        if self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            return 403, "forbidden", "이 화면에서 보낸 요청만 받아요."
        return None

    def do_POST(self):
        refused = self._refused()
        if refused:
            return self._send(refused[0], {"detail": {"code": refused[1], "message": refused[2]}})
        size = self.headers.get("Content-Length") or "0"
        if not size.isdigit():  # 숫자가 아니거나 음수(-1이면 끝까지 읽으려다 멈춘다)
            return self._send(400, {"detail": {"code": "validation", "message": "요청을 읽지 못했어요."}})
        if int(size) > (MAX_FILE_BODY if self.path in FILE_PATHS else MAX_BODY):
            return self._send(413, {"detail": {"code": "validation", "message": "보낸 내용이 너무 커요. 줄여서 다시 보내 주세요."}})
        began, calls = time.monotonic(), len(CLI.calls)
        try:
            try:
                body = json.loads(self.rfile.read(int(size)) or b"{}")
            except (ValueError, RecursionError):  # 잘못된 JSON, UTF-8이 아닌 바이트, 너무 깊은 중첩
                body = None
            if not isinstance(body, dict):
                raise Refuse("요청을 읽지 못했어요.")
            with model():
                status, payload = handle(self.path, body)
        except Refuse as exc:
            status, payload = exc.status, {"detail": {"code": exc.code, "message": str(exc), "field": exc.field}}
        except FileNotFoundError as exc:  # 개발용 연결의 claude 명령이 없을 때만 연결 문제다. 그 밖의 없는 파일은 그대로 알린다
            print(f"{self.path} 없는 파일: {exc.filename}", file=sys.stderr)
            code = "llm_not_configured" if STATE["client"] == "cli" else "file_missing"
            status, payload = 503, {"detail": {"code": code, "message": "필요한 파일을 찾지 못했어요."}}
        except Exception:  # noqa: BLE001 - 화면이 멈추지 않게 오류를 글로 돌려준다. 예외 이름과 자취는 표준 오류에만
            traceback.print_exc()
            status, payload = 500, {"detail": {"code": "internal", "message": "앱 안에서 문제가 생겼어요. 다시 해 보고, 계속되면 GitHub 이슈로 알려 주세요."}}
        # 모델 호출 수는 개발용 CLI 연결에서만 센다(공급자 연결의 호출은 이 서버가 세지 못해, 늘 0회로 적던 칸을 뺐다)
        print(f"{self.path} {status} {time.monotonic() - began:.1f}초" + (f" 모델 {len(CLI.calls) - calls}회" if STATE["client"] == "cli" else ""), file=sys.stderr)
        self._send(status, payload)

    def _not_allowed(self):
        self._send(405, {"detail": {"code": "method_not_allowed", "message": "이 방식의 요청은 받지 않아요."}})

    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_TRACE = do_CONNECT = _not_allowed

    def log_message(self, *args):
        pass


def stop_grading(*_) -> None:
    """돌고 있는 채점 프로세스를 끝낸다(앱이 끝날 때). 채점기를 아직 불러오지 않았으면 할 일이 없다."""
    common = sys.modules.get("algoblock_check_common")  # judge.sibling이 붙이는 이름
    if common is not None:
        common.kill_running()


atexit.register(stop_grading)


def main() -> None:
    load_keys()
    updater.start()  # 켤 때(마지막 확인에서 24시간이 지났으면)와 24시간마다 새 버전을 뒤에서 본다(실패하면 1시간부터 늘려 다시)
    if threading.current_thread() is threading.main_thread():  # 창(window.py)에서 띄우면 스레드라 신호를 받을 수 없다
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # 끝내기 전에 atexit의 stop_grading이 돈다
    port = int(os.environ.get("ALGOBLOCK_UI_PORT", "8791"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    print(f"AlgoBlock: http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_grading()


if __name__ == "__main__":
    main()
