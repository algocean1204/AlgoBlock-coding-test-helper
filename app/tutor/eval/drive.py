"""시나리오 하나를 실제 그래프(Tutor)로 끝까지 돈다. 사용자 쪽은 초보자 시뮬레이터(모델)가 말한다.

흐름(화면에서 초보자가 하는 순서): 의자나 가이드 시작 → 블록마다 대화 → 막히면 꼬리질문(3번째) → 그래도 막히면 이 블록 채우기(5번째)
→ 마지막 블록까지 열리면 전체 코드 작성 → 채점기 제출 → 피드백 → 해설.
기록 한 줄 = 요청 하나. 평가기(checks, judge)가 읽을 숨은 정보(hidden: 블록 목표·신호·참고 코드)를 같이 남긴다.
"""

import importlib.util
import os
import logging
import re
import threading
import tempfile
import time
from pathlib import Path

from ..debug import rules as debug_rules
from ..llm import llm
from ..main import Tutor
from .scenarios import Scenario

FALLBACK_WHY: dict[str, list] = {}  # 스레드 이름 → 이번 요청에서 대체 질문이 나간 이유


class _WhyHandler(logging.Handler):
    def emit(self, record):
        FALLBACK_WHY.setdefault(threading.current_thread().name, []).append(getattr(record, "problems", []))


_talk_log = logging.getLogger("graph.talk")
_talk_log.addHandler(_WhyHandler())
_talk_log.setLevel(logging.INFO)
_talk_log.propagate = False

FOLLOWUP_AT = 3  # 한 블록에서 넘어가지 못한 말이 이만큼이면 꼬리질문
FILL_AT = 5  # 이만큼이면 이 블록 채우기
MAX_USER_TURNS = 24
# 채점기 위치. 설치 파일로 묶였을 때는 ALGOBLOCK_JUDGE_DIR로 받는다
JUDGE_PATH = Path(os.environ.get("ALGOBLOCK_JUDGE_DIR") or Path(__file__).resolve().parents[2] / "judge") / "judge.py"

NOVICE_SYSTEM = (
    "너는 코딩테스트 공부를 막 시작한 학생을 연기한다. 튜터는 답을 바로 알려 주지 않고 질문으로 이끈다.\n"
    "아는 것: {knows}\n처음 품은 생각(튜터가 짚기 전까지 믿는다): {misconception}\n습관: {habits}\n"
    "학생의 말만 쓴다. 따옴표, 머리말, 설명 없이 한국어 1~2문장. 정답 코드를 줄줄 쓰지 않는다."
)


_JUDGE_LOCK = threading.Lock()
_JUDGE = []


def check_judge():
    """채점기 모듈. 여러 스레드가 처음에 같이 불러도 한 번만 올린다(올리는 중인 모듈을 다른 스레드가 보면 깨진다)."""
    with _JUDGE_LOCK:
        if not _JUDGE:
            spec = importlib.util.spec_from_file_location("algoblock_check_judge", JUDGE_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _JUDGE.append(module)
        return _JUDGE[0]


def debug_report(scenario: Scenario, source: str) -> dict:
    """채점기 결과를 디버그 요청 모양으로: {status, cases[{id, input, expected, got, error, status}], compile}."""
    raw = check_judge().judge(scenario.language, source, scenario.cases, problem=scenario.text)
    inputs = {case["id"]: case["input"] for case in scenario.cases}
    cases = [{"id": c["id"], "input": inputs.get(c["id"], ""), "expected": c["expected"], "got": (c.get("stdout") or "").strip(),
              "error": c.get("stderr") or "", "status": c["status"]} for c in raw.get("cases", [])]
    return {"status": raw["status"], "cases": cases, "compile": (raw.get("compile") or {}).get("stderr", "")}


def novice_say(scenario: Scenario, visible: list[str], instruction: str) -> str:
    persona = scenario.persona
    system = NOVICE_SYSTEM.format(knows=persona.knows, misconception=persona.misconception, habits=", ".join(persona.habits))
    lines = [f"문제:\n{scenario.text}", "지금까지 화면의 대화:", *(visible[-8:] or ["없음"]), instruction]
    text = llm().use([{"role": "system", "content": system}, {"role": "user", "content": "\n".join(lines)}], None, task="eval.novice")
    return (text or "").strip().strip('"“”') or "모르겠어요"


def novice_code(scenario: Scenario, visible: list[str], filled: dict[str, str]) -> str:
    system = NOVICE_SYSTEM.format(
        knows=scenario.persona.knows, misconception=scenario.persona.misconception, habits=", ".join(scenario.persona.habits)
    ).replace("한국어 1~2문장. 정답 코드를 줄줄 쓰지 않는다.", "이번에는 코드만 쓴다.")
    lines = [
        f"문제:\n{scenario.text}",
        "튜터와 나눈 대화:",
        *(visible[-30:] or ["없음"]),
        "채우기로 받은 블록 코드:",
        *(filled.values() or ["없음"]),
        "대화에서 정한 흐름대로, 초보자인 네 실력으로 solution 함수 전체를 python으로 쓴다. 코드만, 코드 블록 하나로.",
    ]
    text = llm().use([{"role": "system", "content": system}, {"role": "user", "content": "\n".join(lines)}], None, task="eval.novice")
    found = re.search(r"```(?:python)?\n(.*?)```", text or "", re.S)
    return (found.group(1) if found else text or "").strip()


def novice_fix(scenario: Scenario, visible: list[str], code: str) -> str:
    """디버깅 대화 뒤 초보자가 자기 코드를 고친다. 튜터가 짚어 준 만큼만."""
    system = NOVICE_SYSTEM.format(
        knows=scenario.persona.knows, misconception=scenario.persona.misconception, habits=", ".join(scenario.persona.habits)
    ).replace("한국어 1~2문장. 정답 코드를 줄줄 쓰지 않는다.", "이번에는 코드만 쓴다.")
    lines = [
        f"문제:\n{scenario.text}",
        f"네가 쓴 코드(틀렸다고 나왔다):\n{code}",
        "튜터와 나눈 디버깅 대화:",
        *(visible[-8:] or ["없음"]),
        "너는 혼자서는 틀린 곳을 못 찾는다. 위 대화로 틀린 곳과 이유를 알게 됐을 때만 그 부분을 고친다. 아직 모르겠으면 코드를 한 글자도 바꾸지 않고 그대로 다시 쓴다.",
        "solution 함수 전체를 코드 블록 하나로.",
    ]
    text = llm().use([{"role": "system", "content": system}, {"role": "user", "content": "\n".join(lines)}], None, task="eval.novice")
    found = re.search(r"```(?:python)?\n(.*?)```", text or "", re.S)
    return (found.group(1) if found else text or "").strip()


class Session:
    """튜터 하나와 기록. 같은 스레드에서만 쓴다(SQLite 연결)."""

    def __init__(self, scenario: Scenario, mode: str, db: str | None = None):
        self.scenario, self.mode = scenario, mode
        self.dir = tempfile.mkdtemp(prefix="algoblock-eval-")
        # 풀이 가이드의 정답 코드는 이 시나리오의 케이스로 채점한다(화면 서버와 같다)
        self.tutor = Tutor(db or str(Path(self.dir) / "tutor.db"), check=lambda _pid, code, quick=False: debug_report(scenario, code))
        self.tutor.store.put_problem(scenario.id, scenario.language, scenario.text)
        self.rows: list[dict] = []
        self.visible: list[str] = []  # 초보자 화면에 보이는 대화
        self.filled: dict[str, str] = {}

    def close(self) -> None:
        """기록은 rows에 남았으니 임시 DB 폴더는 지운다."""
        import shutil

        self.tutor.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def ctx(self):
        return self.tutor.store.load(self.scenario.id)

    def chat(self, ctx):
        return ctx.chair if self.mode == "chair" else ctx.guide

    def hidden(self, ctx, index: int | None) -> dict:
        plan = ctx.plan
        if plan is None or index is None or not 0 <= index < len(plan.blocks):
            return {}
        b = plan.blocks[index]
        return {"name": b.name, "goal": b.goal, "checks": b.checks, "reference": b.reference,
                "later_names": [x.name for x in plan.blocks[index + 1 :]], "index": index}

    def call(self, kind: str, fn, **row) -> tuple[object, dict]:
        before = self.ctx()
        FALLBACK_WHY.pop(threading.current_thread().name, None)
        began = time.monotonic()
        out = fn()
        seconds = round(time.monotonic() - began, 2)
        after = self.ctx()
        row.update(kind=kind, mode=self.mode, status=out.status, seconds=seconds, problem=self.scenario.text,
                   open_count=after.open_count, blocks_total=len(after.plan.blocks) if after.plan else None,
                   advance=after.open_count > before.open_count)
        if out.status != 200:
            row["error_code"] = (out.body.get("detail") or {}).get("code")
        why = FALLBACK_WHY.pop(threading.current_thread().name, None)
        if why:
            row["fallback_why"] = why
        self.rows.append(row)
        return out, row

    def _reply_row(self, row: dict) -> None:
        """방금 나간 튜터 말과 그 숨은 블록 정보를 기록에 붙인다."""
        if row["status"] != 200:
            return
        ctx = self.ctx()
        said = [m for m in self.chat(ctx) if m.role == "service"]
        if not said:
            return
        last = said[-1]
        row.update(reply=last.text, move=last.move, hidden=self.hidden(ctx, last.block_index), context=self.visible[-4:])
        self.visible.append(f"튜터: {last.text}")

    def start(self) -> None:
        _, row = self.call("turn", lambda: self.tutor.turn(self.scenario.id, self.mode, "start"), event="start")
        self._reply_row(row)

    def say(self, text: str) -> dict:
        before = self.ctx()
        judged = self.hidden(before, before.open_count - 1)  # 판정은 말하기 전 지금 블록에 대한 것
        self.visible.append(f"나: {text}")
        _, row = self.call("turn", lambda: self.tutor.turn(self.scenario.id, self.mode, "message", text=text), event="message", user=text)
        self._reply_row(row)
        if row["status"] == 200:
            yes = row["advance"] or row.get("move") in ("basis", "recap", "run", "write", "verify")
            # 다시 짜기(replan)와 마침 말(close)은 찾음·못 찾음 판정이 아니다
            row["decision"] = None if row.get("move") in ("replan", "close") else ("찾음" if yes else "못 찾음")
            row["judged"] = judged
        return row

    def followup(self, text: str) -> dict:
        ctx = self.ctx()
        quote = [m for m in self.chat(ctx) if m.role == "service"][-1]
        out, row = self.call("followup", lambda: self.tutor.followup(self.scenario.id, self.mode, quote.id, text), user=text)
        if out.status == 200:
            answer = out.body["messages"][-1]["text"] if out.body.get("messages") else ""
            row.update(reply=answer, move="followup", hidden=self.hidden(ctx, ctx.open_count - 1),
                       context=[f"인용: {quote.text}"], quote=quote.text)
            self.visible.append(f"(꼬리질문) 나: {text} / 튜터: {answer}")
        return row

    def fill(self) -> dict:
        ctx = self.ctx()
        block = ctx.plan.blocks[ctx.open_count - 1]
        rows = [{"id": k, "code": v} for k, v in self.filled.items()]
        out, row = self.call("fill", lambda: self.tutor.fill(self.scenario.id, block.id, filled=rows), block_id=block.id)
        if out.status == 200:
            self.filled[block.id] = out.body.get("code", "")
            row.update(code=self.filled[block.id], hidden=self.hidden(ctx, ctx.open_count - 1))
            self.visible.append(f"(채우기 {block.name}) {self.filled[block.id]}")
        return row

    def next(self) -> dict:
        """채우기로 열린 블록의 첫 질문."""
        _, row = self.call("turn", lambda: self.tutor.turn(self.scenario.id, self.mode, "next"), event="next")
        self._reply_row(row)
        return row

    def debug(self, code: str, report: dict, text: str | None = None) -> dict:
        """틀린 코드로 디버깅 대화 한 번. 숨은 정보(진단)는 평가기용으로만 남긴다."""
        before = self.ctx().debug_state
        same = before is not None and before.code_hash == debug_rules.code_hash(code)
        if text:
            self.visible.append(f"나: {text}")
        out, row = self.call("debug", lambda: self.tutor.debug(self.scenario.id, code, report, text=text), user=text, code=code)
        row["mode"] = "debug"
        if out.status == 200:
            state = self.ctx().debug_state
            reply = out.body["messages"][-1]["text"]
            row.update(reply=reply, move=out.body["step"], line=out.body["line"], context=self.visible[-9:-1],
                       hidden={"name": "디버깅", "goal": f"{state.line}번째 줄: {state.cause}", "checks": [], "reference": state.fixed_line,
                               "later_names": [], "pitfall": state.pitfall, "symptom": debug_rules.symptom(report)})
            if text and same:
                row["decision"] = "찾음" if out.body["step"] == "fix" else "못 찾음"
                row["judged"] = {"name": "틀린 곳 찾기", "goal": row["hidden"]["goal"], "checks": ["틀린 줄(또는 그 줄이 하는 일)과 왜 틀렸는지를 짚는다"]}
            self.visible.append(f"튜터: {reply}")
        return row

    def submit(self, source: str) -> dict:
        report = check_judge().judge(self.scenario.language, source, self.scenario.cases, problem=self.scenario.text)
        ok = report["status"] == "passed"
        self.tutor.store.add_submission(self.scenario.id, source, ok)
        row = {"kind": "submit", "status": 200, "ok": ok, "judge_status": report["status"], "source": source,
               "cases": [c.get("status") for c in report.get("cases", [])], "seconds": 0}
        self.rows.append(row)
        return row

    def feedback(self) -> dict:
        out, row = self.call("feedback", lambda: self.tutor.feedback(self.scenario.id))
        if out.status == 200:
            row["body"] = out.body
        return row

    def explain(self) -> dict:
        out, row = self.call("explain", lambda: self.tutor.explain(self.scenario.id))
        if out.status == 200:
            row["body"] = out.body
        return row


LAST_MOVES = ("recap", "run")  # 마지막 블록을 찾은 뒤의 정리 질문


def play(scenario: Scenario, mode: str = "chair") -> Session:
    """초보자 한 명이 문제 하나를 끝까지 푼다."""
    s = Session(scenario, mode)
    s.start()
    if s.rows[-1]["status"] != 200:
        return s
    stuck, asked, turns, closing = 0, False, 0, False
    while turns < MAX_USER_TURNS:
        total = len(s.ctx().plan.blocks)
        if stuck >= FILL_AT:
            row = s.fill()
            stuck, asked = 0, False
            if row["status"] != 200 or (row["hidden"].get("index", -1) >= total - 1):
                break  # 마지막 블록을 채웠으면 코드 쓰기로
            s.next()
            continue
        if stuck == FOLLOWUP_AT and not asked:
            asked = True
            s.followup(novice_say(scenario, s.visible, "방금 튜터 말에서 이해가 안 되는 부분을 꼬리질문으로 한 문장 묻는다."))
            continue
        turns += 1
        row = s.say(novice_say(scenario, s.visible, "튜터의 마지막 질문에 학생으로서 답한다."))
        if row["status"] != 200 or closing:
            break  # 정리 질문에 한 번 답했으면 끝
        closing = row.get("move") in LAST_MOVES
        stuck = 0 if row.get("decision") == "찾음" else stuck + 1
        if row.get("decision") == "찾음":
            asked = False
    source = novice_code(scenario, s.visible, s.filled)
    if not s.submit(source)["ok"]:
        debug_loop(s, source)
    s.feedback()
    s.explain()
    return s


MAX_DEBUG = 8  # 디버깅 대화 최대 횟수(코드를 고쳐 다시 내는 것 포함)


def debug_loop(s: Session, code: str) -> str:
    """제출이 틀렸을 때: 튜터가 묻고 → 초보자가 답하고 → 알게 된 만큼 고쳐 다시 낸다. 통과하거나 횟수가 차면 끝."""
    scenario = s.scenario
    report = debug_report(scenario, code)
    row = s.debug(code, report)
    for _ in range(MAX_DEBUG):
        if row["status"] != 200:
            break
        # 초보자는 자기 코드를 보면서 답한다(코드를 안 주면 모델이 없는 변수 이름을 지어내 대화가 어긋난다)
        say = novice_say(scenario, s.visible, f"네가 쓴 코드(줄 번호 붙임):\n{debug_rules.numbered(code)}\n튜터의 디버깅 질문에 학생으로서 답한다. 위 코드를 실제로 보고 생각한 것을 말한다.")
        fixed = novice_fix(scenario, s.visible + [f"나: {say}"], code)
        if fixed.strip() and fixed.strip() != code.strip():
            code = fixed
            if s.submit(code)["ok"]:
                break
            report = debug_report(scenario, code)
        row = s.debug(code, report, text=say)
    return code


def play_debug(scenario: Scenario, code: str) -> Session:
    """틀린 코드를 들고 온 초보자(대화 없이 혼자 쓴 코드)의 디버깅만 돈다."""
    s = Session(scenario, "chair")
    if not s.submit(code)["ok"]:
        debug_loop(s, code)
    return s
