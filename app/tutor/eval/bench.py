"""테마(모델·추론 정도)를 정하는 측정. 정답이 정해진 작은 세트를 실제 노드 프롬프트로 돌린다.

python3 -m tutor.eval.bench judge  [--cli]   판정 노드(chair.judge) 정확도: 사용자 말 → Y·N·D
python3 -m tutor.eval.bench plan   [--cli]   계획 + 해설: 해설 끝 전체 코드가 채점기를 통과하는가, 걸린 시간
python3 -m tutor.eval.bench locate [--cli]   디버그 진단: 틀린 줄을 맞게 짚는가, 고친 줄을 넣으면 통과하는가
테마는 환경 변수로 바꿔 가며 잰다: ALGOBLOCK_THEME_JUDGE=claude/claude-sonnet-5-5:low 등(llm/themes.py).
"""

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import copy_context

from ..chair.prompts import judge_messages
from ..common.verdict import BASIS_RULE, ask_verdict
from ..llm import use_llm
from ..llm.themes import pick
from ..state import Block, TurnContext, TutorContext, TutorRequest
from .drive import Session, check_judge
from .scenarios import all_scenarios, by_id

B = {
    "hash": ("hash_library", Block("b1", "var_during", "이름별 개수 세기", "빌려 간 학생 이름마다 몇 번 나왔는지 센다", "",
                                   ["이름마다 빌린 횟수를 센다", "같은 이름이 여러 명일 수 있음을 다룬다"]),
             "돌려주지 않은 한 명을 찾으려면 이름마다 무엇을 기록해 둬야 할까요?"),
    "stack": ("stack_brackets", Block("b2", "var_during", "여는 괄호 쌓기", "여는 괄호를 만나면 나중에 짝을 맞추려고 차례대로 쌓아 둔다", "",
                                      ["여는 괄호를 순서대로 보관한다", "가장 최근에 연 괄호부터 짝을 맞춘다"]),
              "올바른 순서로 닫혔는지 보려면 여는 괄호를 만났을 때 무엇을 해 둬야 할까요?"),
    "pairs": ("brute_pairs", Block("b3", "loop", "두 번째 카드 고르기", "첫 번째 카드 뒤에 있는 카드만 두 번째 카드로 골라 같은 쌍을 두 번 세지 않는다", "",
                                   ["두 번째 카드는 첫 번째 카드 다음 위치부터 본다", "같은 카드를 두 번 쓰지 않는다"]),
              "같은 두 장을 두 번 세지 않으려면 두 번째 카드는 어디서부터 보면 될까요?"),
}

# (블록, 사용자 말, 정답). 1단계 수준 사용자의 말투: 자신 없는 말, 질문 꼴, 문법 섞인 말, 틀린 방법.
JUDGE_ITEMS = [
    ("hash", "이름마다 몇 번 빌렸는지 세 두면 될 것 같아요", "Y"),
    ("hash", "이름별로 개수를 세면 되나요? 맞는지는 잘 모르겠어요", "Y"),
    ("hash", "dict에 이름 넣고 나올 때마다 +1", "Y"),
    ("hash", "borrowed에서 이름별 개수를 세고 returned에서도 이름별 개수를 세서, 개수가 다른 이름을 찾으면 돼요", "Y"),
    ("hash", "returned에 이름이 있는지 확인하면 돼요", "N"),
    ("hash", "모르겠어요", "N"),
    ("hash", "빌린 사람이 모두 몇 명인지 세요", "N"),
    ("hash", "이름을 set에 넣어 두면 되지 않을까요", "N"),
    ("hash", "borrowed랑 returned를 둘 다 정렬해서 앞에서부터 하나씩 비교하다가 다른 데가 나오면 그 이름이 답 아닌가요?", "D"),
    ("stack", "여는 괄호가 나오면 리스트에 순서대로 넣어 둬요", "Y"),
    ("stack", "나온 순서대로 기억해 뒀다가 닫는 괄호가 오면 제일 마지막 거랑 비교하면 되나요?", "Y"),
    ("stack", "여는 괄호 개수랑 닫는 괄호 개수를 세서 같으면 true요", "N"),
    ("stack", "잘 모르겠는데 그냥 문자열을 뒤집어서 원래랑 비교하면 안 되나요?", "N"),
    ("pairs", "i 다음 칸부터 보면 돼요", "Y"),
    ("pairs", "j를 i+1부터 돌리면 되나요?", "Y"),
    ("pairs", "j도 0부터 끝까지 돌리면 돼요", "N"),
    ("pairs", "카드를 정렬하면 될 것 같아요", "N"),
    ("pairs", "j를 0부터 다 돌리는데 i랑 j가 같을 때는 건너뛰고, 다 센 다음에 마지막에 2로 나누면 안 되나요?", "D"),
]


def _threads(fn, items, workers=6):
    contexts = [copy_context() for _ in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda pair: pair[0].run(fn, pair[1]), zip(contexts, items)))


def judge_one(item) -> dict:
    key, text, want = item
    sid, block, question = B[key]
    scenario = by_id(sid)
    state = {
        "ctx": TutorContext(problem_id=sid, problem_text=scenario.text, language="python"),
        "request": TutorRequest(kind="turn", problem_id=sid, mode="chair", event="message", text=text),
        "turn": TurnContext(index=0, block=block, last_question=question, recent=[], moves_used=["open"], event="message", text=text),
    }
    began = time.monotonic()
    got = ask_verdict(judge_messages(state), BASIS_RULE, "chair.judge")
    label = "?" if got is None else "D" if got.other else "Y" if got.ok else "N"
    return {"key": key, "text": text, "want": want, "got": label, "seconds": round(time.monotonic() - began, 1)}


def cmd_judge(repeat: int) -> None:
    rows = _threads(judge_one, JUDGE_ITEMS * repeat)
    right = sum(r["want"] == r["got"] for r in rows)
    print(f"테마 judge={pick('chair.judge')}  정확도 {right}/{len(rows)} = {right / len(rows):.3f}  평균 {sum(r['seconds'] for r in rows) / len(rows):.1f}초")
    for want in "YND":
        mine = [r for r in rows if r["want"] == want]
        print(f"  정답 {want}: {sum(r['got'] == want for r in mine)}/{len(mine)}")
    for r in rows:
        if r["want"] != r["got"]:
            print(f"  틀림 [{r['key']}] 정답 {r['want']} 판정 {r['got']}: {r['text']}")


def code_of(text: str) -> str:
    found = re.findall(r"```(?:python)?\n(.*?)```", text or "", re.S)
    return found[-1].strip() if found else ""


def plan_one(scenario) -> dict:
    session = Session(scenario, "chair")
    began = time.monotonic()
    out = session.tutor.explain(scenario.id)
    seconds = round(time.monotonic() - began, 1)
    row = {"id": scenario.id, "status": out.status, "seconds": seconds, "ok": False, "blocks": 0, "hints": 0, "algorithm": ""}
    if out.status == 200:
        plan = session.ctx().plan
        code = code_of(out.body["explain"]["sections"][-1]["body"])
        report = check_judge().judge(scenario.language, code, scenario.cases, problem=scenario.text) if code else {"status": "no_code"}
        row.update(ok=report["status"] == "passed", judge=report["status"], blocks=len(plan.blocks),
                   hints=sum(bool(b.hints) for b in plan.blocks), algorithm=plan.algorithm, want=scenario.algorithm)
    else:
        row["judge"] = (out.body.get("detail") or {}).get("code")
    session.close()
    return row


def cmd_plan(repeat: int) -> None:
    rows = _threads(plan_one, all_scenarios() * repeat)
    done = [r for r in rows if r["status"] == 200]
    print(f"테마 ingest={pick('plan.draft_blocks')}  해설 코드 통과 {sum(r['ok'] for r in rows)}/{len(rows)}  오류 {len(rows) - len(done)}"
          f"  평균 {sum(r['seconds'] for r in rows) / len(rows):.1f}초  최대 {max(r['seconds'] for r in rows)}초")
    if done:
        print(f"  평균 블록 {sum(r['blocks'] for r in done) / len(done):.1f}개  질문 남은 블록 {sum(r['hints'] for r in done)}/{sum(r['blocks'] for r in done)}"
              f"  유형 일치 {sum(r['algorithm'] == r['want'] for r in done)}/{len(done)}")
    for r in rows:
        if not r["ok"]:
            print(f"  실패 {r['id']}: {r.get('judge')} ({r['seconds']}초, {r['algorithm']})")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["judge", "plan", "locate"])
    parser.add_argument("--cli", action="store_true")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args(argv)
    client = None
    if args.cli:
        from .cli_client import ClaudeCli

        client = ClaudeCli()
    with use_llm(client) if client else nullcontext():
        if args.command == "judge":
            cmd_judge(args.repeat)
        elif args.command == "plan":
            cmd_plan(args.repeat)
        else:
            from .debug_bench import cmd_locate

            cmd_locate(args.repeat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
