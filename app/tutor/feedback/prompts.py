from collections import Counter

from ..common.progress_view import active_plan
from ..common.solution import same_code, solution_lines
from ..common.scope import OUTSIDE_PROBLEMS, algorithm_line, algorithm_name, system_prompt
from ..common.talk_prompts import weak_pitfalls
from ..common.talk_rules import ANSWER_LEAD, BACK_LEAD, BANNED, CHECKED, RETRY_LEAD, SKIPPED, kind_word
from ..knowledge.ontology import PITFALLS, PREREQUISITE
from ..state import MainState

ADVICE = {
    "keep_flow": "순서 유지: 그 순서를 지킨 채 고칠 곳",
    "canonical": "정석으로: 정석 블록 순서로 바꾸라는 문장과 바꿀 첫 블록",
    "fresh": "새로 짜기: 흐름을 먼저 떠올리라는 문장",
}
SOLO_ADVICE = {**ADVICE, "canonical": "정석으로: 정석 풀이 순서로 바꾸라는 문장과 먼저 바꿀 곳"}
# 통과한 제출: 풀이 가이드와 다른 곳을 고칠 곳으로 고르지 않는다(통과한 코드에 가이드의 읽기·출력 방식을 권했다)
# 차례를 못 박는다: 통과해도 틀릴 입력이 먼저, 가이드와의 차이는 그 밖의 것만 '다른 방식'으로
PASSED_RULE = ("제출이 통과했다. 통과했어도 틀릴 입력(빈 입력·경계·큰 값·시간)이 코드에서 보이면 그것을 먼저 짚는다. "
               "그 밖에는 지금 코드보다 더 짧게 쓸 길이 있을 때만 그곳을 짚는다. 그 밖의 풀이 가이드와의 차이는 고칠 곳이 아니라 '다른 방식'으로만 말한다.")
PASSED_ADVICE = ("통과: 통과했어도 틀릴 입력(빈 입력·경계·큰 값·시간)이 보이면 그것 하나를 먼저, 없으면 더 짧게 쓸 곳 하나, 그것도 없으면 다음 비슷한 문제에서 먼저 떠올릴 흐름 하나. "
                 "그 밖의 풀이 가이드와의 차이는 '다른 방식'으로만 말하고 바꾸라고 하지 않는다")

BLOCK_WORD = "풀이 순서의 한 조각은 '블록 n'(예: 블록 3)으로 부른다. '단계', 'n단계', '가이드 블록'이라 하지 않는다('단계'는 문제 난이도를 뜻한다)."
SOLO_WORD = "이 사용자는 블록 방식을 쓰지 않고 혼자 풀었다. '블록'이라는 말과 블록 번호를 쓰지 않는다. 풀이 흐름은 '먼저', '그다음'처럼 말한다."


def system(blocks: bool) -> str:
    return system_prompt(
        "너는 코딩테스트 튜터의 피드백 담당이다. 사용자가 다음 문제에서 흐름을 먼저 떠올리게 돕는다.",
        "분석 원칙:",
        "1. analysis의 첫 문장은 칭찬이나 판정이 아니라, 제출 코드가 기대는 가정이나 놓친 경우를 짚는 질문이다.",
        "2. analysis의 주장 문장마다 맨 앞에 확신 표시를 붙인다. 제출 결과나 코드 줄에서 바로 보이면 [확실], 코드 흐름에서 강하게 추론하면 [가능성 높음], 실행 없이 짐작하면 [추측]. "
        "이번 풀이의 기록에 있는 사실(센 수, 짚은 줄)을 말하는 문장은 [확실]이다. 질문 문장에는 붙이지 않는다.",
        "4. 막힌 지점은 '이번 풀이의 기록'에 있는 것만 적는다. 기록에 없으면 막힌 지점이 없었다고 적는다.",
        "5. 수를 말할 때는 문제 글의 제한에서 계산한 값만 말하고, 계산하지 않았으면 수를 말하지 않는다.",
        f"3. 생각을 닫는 말({', '.join(BANNED)})을 쓰지 않는다.",
        "힌트와 조언에 코드와 코드 블록을 쓰지 않는다. 사용자 코드를 고쳐 쓰지 않는다.",
        BLOCK_WORD if blocks else SOLO_WORD,
    )


def used_blocks(ctx) -> bool:
    """블록 방식(튜터의 질문으로·튜터와 차례로)으로 풀었는가. 혼자 푼 사람에게는 블록 자료를 넘기지 않는다."""
    return bool(ctx.chair or ctx.guide or ctx.block_states)


STILL = ("basis", "recap", "run", "close", "done")  # 같은 블록에 남았어도 막힌 것이 아닌 말(근거 질문, 마지막 정리)
# 제출 결과 종류를 화면(통계)이 쓰는 말로('runtime_error 1번, failed 1번'을 모델이 그대로 옮겼다)
FAIL_WORD = {"failed": "오답", "wrong_answer": "오답", "runtime_error": "실행 오류", "timeout": "시간 초과", "compile_error": "컴파일·형식 오류",
             "memory_limit": "메모리 초과", "output_limit": "출력 초과"}


def record_lines(ctx, plan) -> list[str]:
    """이번 풀이의 기록. 저장소에 남은 것만: 블록마다 넘어가지 못한 차례와 틀린 블록 코드, 디버그에서 짚은 줄과 함정, 통과하지 못한 제출, 본 힌트 수.
    '이 블록 채우기'는 남는 기록이 없어 넣지 못한다."""
    blocks = plan.blocks if plan else []
    name = lambda i: f"블록 {i + 1}({blocks[i].name})" if i is not None and 0 <= i < len(blocks) else "블록"
    lines = []
    for label, said in (("튜터의 질문으로", ctx.chair), ("튜터와 차례로", ctx.guide)):  # '가이드 블록 1'로 옮겨 썼다. 화면의 방식 이름으로
        # 답 조르기·딴소리는 막힌 것이 아니다. 블록 코드 확인(판정 표시 CHECKED가 붙은 글)은 아래 블록 상태로만 센다('확인 전'은 막힘이 아니다).
        # 표시가 없는 옛 기록은 거부 말(RETRY_LEAD)로 가른다
        stuck = Counter(user.block_index for user, reply in zip(said, said[1:])
                        if user.role == "user" and not (user.move or "").startswith(CHECKED)
                        and reply.role == "service" and reply.block_index == user.block_index and reply.move not in (*STILL, "found")
                        and not reply.text.startswith((ANSWER_LEAD, BACK_LEAD, RETRY_LEAD)))
        lines += [f"- {name(i)}: {label} 풀 때 이 블록에서 다음 블록으로 넘어가지 못한 답이 {n}번" for i, n in sorted(stuck.items(), key=lambda kv: kv[0] or 0)]
    for i, block in enumerate(blocks):
        state = ctx.block_states.get(block.id)
        wrong = 0 if state is None else state.tries - (state.verdict in ("Y", "?"))  # '?': 통과했다가 앞 블록이 바뀌어 확인 전으로 돌아갔다
        if state is not None and state.verdict == "Y":
            # 모델 판정이 틀렸다가 같은 코드(이름만 다른 것 포함)가 뒤에 통과했으면 튜터의 오판이라 세지 않는다.
            # 거부 말(RETRY_LEAD)을 받은 것만 뺀다: 통과한 코드를 다시 확인한 것은 tries에 들지 않는다
            same = sum(user.role == "user" and user.block_index == i and reply.role == "service" and reply.text.startswith(RETRY_LEAD)
                       and same_code(user.text, state.code, ctx.language) for chat in (ctx.chair, ctx.guide) for user, reply in zip(chat, chat[1:]))
            wrong = max(0, wrong - same)
        if wrong > 0:
            lines.append(f"- {name(i)} 블록 코드 확인에서 튜터의 코드와 이어지지 않은 횟수 {wrong}번(틀렸다는 뜻이 아니다)" + (f". 아직 통과하지 못한 코드:\n{state.code}" if state.verdict == "N" else ""))
    if any(m.role == "service" and m.text.startswith(SKIPPED) for m in ctx.guide):  # '이대로 넘어가기'로 넘어간 블록은 맞았다고도 틀렸다고도 말하지 않는다
        # 확인을 눌러 이어지지 않은 뒤에 넘긴 블록은 '확인 없이'가 아니다. 그 뒤의 제출이 통과했으면 그 코드는 제출로 확인되었다(실행해 보지 않았다고 말했다)
        passed = bool(ctx.latest_submission and ctx.latest_submission.ok)
        tried = {m.block_index for m in ctx.guide if m.role == "user" and m.move in (CHECKED + "N", CHECKED + "?")}  # 확인을 눌러 통과하지 못한 블록
        lines += [f"- {name(i)}: {'블록 코드 확인에서 통과하지 못한 뒤' if i in tried else '확인하지 않고'} '이대로 넘어가기'로 넘어감"
                  + ("(그 뒤 이 풀이의 제출이 모든 테스트를 통과했다. 이 블록을 실행해 보지 않았다거나 다시 확인해 보라고 하지 않는다)" if passed
                     else "(확인 전. 맞았다고도 틀렸다고도 하지 않는다)")
                  for i, block in enumerate(blocks) if getattr(ctx.block_states.get(block.id), "verdict", None) == "?"]
    debug = ctx.debug_state
    if debug is not None:
        found = any(m.role == "service" and m.move == "fix" for m in ctx.debug)
        pitfall = f" 함정: {PITFALLS[debug.pitfall][1]}." if debug.pitfall in PITFALLS else ""
        lines.append(f"- 디버그: 틀린 곳은 {debug.line}번째 줄. {debug.cause}{pitfall} 사용자가 원인을 {'짚었다' if found else '아직 짚지 못했다'}.")
    if ctx.failed_submissions:
        lines.append("- 통과하지 못한 제출: " + ", ".join(f"{FAIL_WORD.get(kind, kind)} {n}번" for kind, n in Counter(ctx.failed_submissions).items()))
    if ctx.hints_seen:
        lines.append(f"- 본 힌트: {ctx.hints_seen}개")
    return lines


def analyze_messages(state: MainState) -> list[dict]:
    plan = active_plan(state)
    sub = state["ctx"].latest_submission
    strategy = state.get("strategy") or "fresh"
    blocks = used_blocks(state["ctx"])
    key = plan.algorithm if plan else ""
    guide = solution_lines(state, code=True)
    lines = [f"문제:\n{state['ctx'].problem_text}", f"언어:{state['ctx'].language}", *guide]
    algorithm = algorithm_line(key)
    if algorithm:
        lines.append(algorithm)
    if plan and blocks:
        lines.append("블록(정석 흐름 순서):")
        lines += [f"블록 {n}: {b.name} ({kind_word(b.kind)}) — {b.goal}" for n, b in enumerate(plan.blocks, 1)]
    ctx = state["ctx"]
    weak = weak_pitfalls(ctx)
    if weak:
        lines.append("참고 — 이 사용자가 여러 문제에서 되풀이한 실수(이번 제출 코드에 실제로 보일 때만 analysis에서 짚고, advice에 다음에 스스로 확인할 방법 하나를 넣는다): " + ", ".join(weak))
    if plan and plan.link:  # 풀어 본 문항 가운데 같은 구조라고 판정된 하나(계획 때 정한다)
        lines.append(f"참고 — 사용자가 전에 풀어 본 같은 구조의 문제: {plan.link} (similar_hint에서 그 문제와 무엇이 같은지 한마디로 잇는다)")
    before = [f"{algorithm_name(k)} {ctx.solved.get(k, 0)}문제" for k in PREREQUISITE.get(key, [])]
    if before and sub and not sub.ok:
        lines.append("참고 — 이 유형보다 먼저 익히는 유형과 지금까지 통과한 수(0문제면 advice에서 그 유형의 쉬운 문제를 먼저 권해도 된다): " + ", ".join(before))
    lines += ["이번 풀이의 기록(막힌 지점은 여기 있는 것만 적는다):", *(record_lines(ctx, plan) or ["- 남은 기록 없음"])]
    passed = bool(sub and sub.ok)
    lines += [
        f"제출 코드:\n{sub.source if sub else ''}",
        f"제출 결과:{'통과' if passed else '실패'}",
        "",
        f"analysis: 제출 코드가 {'블록 순서' if blocks else '풀이 흐름'} 중 어디까지 맞게 갔고, 이번 풀이에서 어디서 막혔는지(위 기록)."
        + (f" {PASSED_RULE}" if passed else ""),
        f'similar_hint: "{algorithm_name(key) or "유형 이름"}: …"으로 시작하는, 다음 비슷한 문제에 쓸 흐름 한 줄. {OUTSIDE_PROBLEMS}',
        f"advice: {PASSED_ADVICE if passed else (ADVICE if blocks else SOLO_ADVICE)[strategy]}",
        '출력: JSON {"analysis", "similar_hint", "advice"}',
    ]
    # 캐시 표시를 하지 않는다: 제출마다 한 번 부르는 호출이라 앞부분이 다시 읽히지 않고, 표시하면 쓰기 할증(1.25배)만 붙는다
    return [{"role": "system", "content": system(blocks)}, {"role": "user", "content": "\n".join(lines)}]
