"""평가기 보정 세트. 정답 표가 구성으로 정해지는 사례만 둔다(일부러 참고 코드를 넣은 말 = 유출, 예시 값을 바꾼 말 = 사실 오류).

평가기가 기준마다 이 표를 얼마나 맞히는지(정확도, 카파, 불확실 비율)로 그 기준을 믿을지 정한다.
사람이 본 판정을 더하려면 HUMAN에 같은 모양으로 넣는다.
"""

from .scenarios import by_id

_S = by_id("hash_library")
BLOCK = {
    "name": "이름 세기",
    "goal": "빌려 간 학생 이름마다 몇 번 나왔는지 센다",
    "checks": ["이름마다 빌린 횟수를 센다", "같은 이름이 여러 명일 수 있음을 다룬다"],
    "reference": "for name in borrowed:\n    count[name] = count.get(name, 0) + 1",
}
OPEN_Q = "이 블록에서는 무엇을 정해야 다음으로 갈 수 있을까요?"


def case(cid, reply, labels, *, user=None, decision=None, mode="chair", context=None):
    return {
        "id": cid,
        "item": {"problem": _S.text, "mode": mode, "block": BLOCK, "context": context or [], "user": user,
                 "decision": decision, "reply": reply},
        "labels": labels,
    }


GOLDEN = [
    # leak
    case("L1", "count[name] = count.get(name, 0) + 1 처럼 세면 될까요?", {"leak": "fail"}),
    case("L2", "이름마다 빌린 횟수를 딕셔너리로 세 두면 어떨까요?", {"leak": "fail"}),
    case("L3", "빌려 간 학생 이름마다 몇 번 나왔는지 세어 보세요. 그다음에는 무엇을 하면 될까요?", {"leak": "fail"}),
    case("L4", "'같은 이름의 학생이 여러 명 있을 수 있습니다'를 보면, 이름이 있다·없다만 적어 둬도 충분할까요?",
         {"leak": "pass", "novice_fit": "pass", "grounded": "pass"}),
    case("L5", "borrowed가 [\"tom\", \"ann\", \"tom\"]이고 returned가 [\"ann\", \"tom\"]이면, 누가 남는지 어떻게 알아낼 수 있을까요?",
         {"leak": "pass", "grounded": "pass"}),
    case("L6", "이름을 키로, 횟수를 값으로 두는 딕셔너리를 쓴다면 빈칸에는 무엇을 적어야 할까요?", {"leak": "pass"}, mode="guide"),
    case("L7", "빈칸에는 count[name] = count.get(name, 0) + 1을 쓰면 되는데, 왜 get을 쓸까요?", {"leak": "fail"}, mode="guide"),
    case("L8", "방금 말한 '이름마다 개수'를 세면, 같은 이름이 두 번 나올 때는 숫자가 어떻게 되나요?", {"leak": "pass"},
         user="이름마다 개수를 세면 될 것 같아요", decision="못 찾음"),
    case("L9", "returned에 있는지 확인하는 대신, 각 이름이 몇 번 나오는지를 기록해 두면 되지 않을까요?", {"leak": "fail"},
         user="returned에 있는지 확인하면 돼요", decision="못 찾음"),
    case("L10", OPEN_Q, {"leak": "pass", "responsive": "na"}),
    # responsive
    case("R1", "'같은 이름의 학생이 여러 명 있을 수 있습니다'인데, tom이 두 번 빌렸다면 returned에 tom이 있다는 것만으로 충분할까요?",
         {"responsive": "pass", "leak": "pass"}, user="returned에 이름이 있는지만 보면 돼요", decision="못 찾음"),
    case("R2", OPEN_Q, {"responsive": "fail"}, user="모르겠어요", decision="못 찾음", context=[f"튜터: {OPEN_Q}"]),
    case("R3", "작은 예로 해 볼까요? borrowed가 [\"mina\", \"joon\"]이고 returned가 [\"mina\"]면 누가 남았나요?",
         {"responsive": "pass", "novice_fit": "pass"}, user="모르겠어요", decision="못 찾음", context=[f"튜터: {OPEN_Q}"]),
    case("R4", "입력 크기가 커질 때 시간복잡도는 어떻게 될까요?", {"responsive": "fail", "novice_fit": "fail"},
         user="그냥 답 알려 주시면 안 돼요?", decision="못 찾음"),
    case("R5", "'책을 돌려주지 않은 학생은 정확히 한 명입니다'라는 조건은 어떤 뜻일까요?", {"responsive": "fail"},
         user="for문 두 개로 borrowed랑 returned를 하나씩 다 비교하면 될 것 같아요", decision="못 찾음"),
    case("R6", "이 블록에서 무엇을 기록해 둬야 돌려주지 않은 사람을 찾을 수 있을까요?", {"responsive": "na", "verdict": "na"}),
    # novice_fit
    case("N1", "해시맵의 평균 조회 비용이 O(1)이라는 점을 생각하면 어떤 구조가 맞을까요?", {"novice_fit": "fail"}),
    case("N2", "returned는 어떻게 쓰일까요? 그리고 borrowed는 몇 번 돌아야 할까요?", {"novice_fit": "fail"}),
    case("N3", "같은 이름이 두 번 나오면 한 번으로 볼까요, 두 번으로 볼까요?", {"novice_fit": "pass", "leak": "pass"}),
    case("N4", "그 부분을 다르게 생각해 보면 어떨까요?", {"novice_fit": "fail"}, user="잘 모르겠어요", decision="못 찾음"),
    # grounded
    case("G1", "returned의 길이는 borrowed와 같으니까, 둘을 짝지어 보면 어떨까요?", {"grounded": "fail"}),
    case("G2", "입출력 예에서 borrowed가 [\"mina\", \"joon\", \"sara\"]일 때 답이 \"sara\"인데, 왜 그럴까요?", {"grounded": "fail"}),
    case("G3", "입출력 예 두 번째에서 tom은 두 번 빌렸는데 한 번만 돌려줬어요. 그러면 무엇이 남나요?", {"grounded": "pass"}),
    case("G4", "만약 같은 이름이 하나도 없다면, 있다·없다만 확인해도 될까요?", {"grounded": "pass"}),
    # verdict
    case("V1", "그렇게 세 두면 returned를 볼 때는 무엇을 하면 될까요?", {"verdict": "pass"},
         user="이름마다 몇 번 빌렸는지 세 두면 될 것 같아요. 같은 이름이 여러 번이어도요.", decision="찾음"),
    case("V2", "같은 이름이 여러 번 나오면 어떻게 될까요?", {"verdict": "fail"},
         user="이름마다 몇 번 빌렸는지 세 두면 될 것 같아요. 같은 이름이 여러 번이어도요.", decision="못 찾음"),
    case("V3", "tom이 두 번 빌렸는데 한 번만 돌려줬다면, returned에 tom이 있다는 것만으로 알 수 있을까요?", {"verdict": "pass"},
         user="returned에 이름이 있는지만 보면 돼요", decision="못 찾음"),
    case("V4", "그다음에는 무엇을 하면 될까요?", {"verdict": "fail"}, user="returned에 이름이 있는지만 보면 돼요", decision="찾음"),
    case("V5", "작은 예로 따라가 볼까요? borrowed가 [\"a\", \"b\"]이고 returned가 [\"a\"]면 누가 남나요?", {"verdict": "pass"},
         user="모르겠어요", decision="못 찾음"),
    case("V6", "그렇게 센 값을 returned와 어떻게 맞춰 볼까요?", {"verdict": "pass"}, user="dict에 이름별 개수", decision="찾음"),
    case("V7", "왜 그렇게 생각했나요?", {"verdict": "fail"}, user="dict에 이름별 개수", decision="못 찾음"),
    case("V8", "그다음에는 무엇을 하면 될까요?", {"verdict": "fail"}, user="빌린 사람이 모두 몇 명인지 세요", decision="찾음"),
]

HUMAN: list[dict] = []  # 사람이 본 실제 대화 판정. 모양은 GOLDEN과 같다.

# 보류 세트: 평가기 프롬프트를 고칠 때 보지 않는다(과적합 확인용). 다른 문제(괄호)로 만든다.
_B = by_id("stack_brackets")
BLOCK_B = {
    "name": "여는 괄호 쌓기",
    "goal": "여는 괄호를 만나면 나중에 짝을 맞추려고 차례대로 쌓아 둔다",
    "checks": ["여는 괄호를 순서대로 보관한다", "가장 최근에 연 괄호부터 짝을 맞춘다"],
    "reference": "if ch in '([':\n    stack.append(ch)",
}


def held(cid, reply, labels, *, user=None, decision=None, mode="chair", context=None):
    made = case(cid, reply, labels, user=user, decision=decision, mode=mode, context=context)
    made["item"].update(problem=_B.text, block=BLOCK_B)
    return made


COUNT_CLAIM = "괄호 개수만 같으면 되는 거 아니에요?"
STACK_CLAIM = "여는 괄호가 나오면 일단 순서대로 모아 두고, 닫는 괄호가 나오면 제일 마지막에 모은 거랑 비교해요"
HOLDOUT = [
    held("H1", "여는 괄호를 스택에 넣어 두면 어떨까요?", {"leak": "fail"}),
    held("H2", "'([)]'에서는 어떤 괄호가 먼저 닫혀야 했을까요?", {"leak": "pass", "novice_fit": "pass"}),
    held("H3", "빈칸에 stack.append(ch)를 쓰면 될까요?", {"leak": "fail"}, mode="guide"),
    held("H4", "스택을 쓴다면, 여는 괄호를 만났을 때 빈칸에서 무엇을 해야 할까요?", {"leak": "pass"}, mode="guide"),
    held("H5", "s의 길이는 최대 얼마일까요?", {"responsive": "fail"}, user=COUNT_CLAIM, decision="못 찾음"),
    held("H6", "'([)]'는 여는 괄호와 닫는 괄호 개수가 같은데도 올바르지 않아요. 개수 말고 무엇을 더 봐야 할까요?",
         {"responsive": "pass", "grounded": "pass"}, user=COUNT_CLAIM, decision="못 찾음"),
    held("H7", "LIFO 구조의 특성을 활용하면 어떻게 될까요?", {"novice_fit": "fail"}),
    held("H8", "'(('는 왜 올바르지 않을까요?", {"novice_fit": "pass", "grounded": "pass"}),
    held("H9", "입출력 예에서 '(('의 결과는 true였는데, 왜 그럴까요?", {"grounded": "fail"}),
    held("H10", "그렇게 모아 둔 괄호는 닫는 괄호를 만났을 때 어떻게 쓰일까요?", {"verdict": "pass", "responsive": "pass"},
         user=STACK_CLAIM, decision="찾음"),
    held("H11", "그다음에는 무엇을 하면 될까요?", {"verdict": "fail"}, user="괄호 개수를 세서 같으면 true예요", decision="찾음"),
    held("H12", "왜 마지막에 모은 것과 비교하나요?", {"verdict": "fail"}, user=STACK_CLAIM, decision="못 찾음"),
    held("H13", "이 블록에서 무엇을 기억해 둬야 짝을 맞출 수 있을까요?", {"responsive": "na", "verdict": "na"}),
]


# 디버그 모드: 고친 줄을 말하면 유출, 증상·줄 번호·오류 뜻·다른 예는 허용
BUGGY = "def solution(borrowed, returned):\n    count = {}\n    for name in borrowed:\n        count[name] += 1\n    for name in returned:\n        count[name] -= 1\n    for name in count:\n        if count[name] > 0:\n            return name"
DEBUG_BLOCK = {"name": "디버깅", "goal": "4번째 줄: 처음 보는 이름은 그릇에 없어서 += 1을 할 수 없다", "checks": [],
               "reference": "        count[name] = count.get(name, 0) + 1"}


def bug(cid, reply, labels, *, user=None, decision=None, context=None, base=None):
    made = case(cid, reply, labels, user=user, decision=decision, mode="debug", context=context)
    made["item"].update({"block": DEBUG_BLOCK, "code": BUGGY, **(base or {})})
    return made


STUCK = ["튜터: 4번째 줄에서 오류가 났어요. 그 줄에서 무엇이 어긋났을까요?", "나: 모르겠어요", "튜터: tom을 처음 만났을 때 count 안에는 무엇이 있나요?", "나: 잘 모르겠어요"]
GOLDEN += [
    bug("D1", "4번째 줄을 count[name] = count.get(name, 0) + 1 로 바꾸면 돼요. 왜 그럴까요?", {"leak": "fail"}),
    bug("D2", "solution([\"tom\", \"ann\", \"tom\"], [\"ann\", \"tom\"])에서 오류가 났어요. 이 입력을 코드 첫 줄부터 손으로 따라가 보면, 어느 줄에서 멈출까요?", {"leak": "pass", "grounded": "pass"}),
    bug("D3", "KeyError는 그릇에 없는 이름을 꺼내려 했다는 뜻이고, 4번째 줄에서 났어요. tom을 처음 만났을 때 count 안에 tom이 있을까요?", {"leak": "pass", "novice_fit": "pass"}),
    bug("D4", "4번째 줄에서 += 대신 count.get(name, 0)에 1을 더한 값을 넣어야 해요. 고쳐 볼까요?", {"leak": "fail"}),
    bug("D5", "과일 개수를 셀 때는 fruit[x] = fruit.get(x, 0) + 1 처럼 처음 보는 과일도 0에서 시작하게 써요. 4번째 줄과 무엇이 다른가요?", {"leak": "pass"}, user="모르겠어요", decision="못 찾음", context=STUCK[:2]),
    bug("D6", "처음 보는 이름은 그릇에 아직 없어서 거기에 1을 더할 수가 없어요. 그러면 처음 보는 이름일 때는 어떻게 시작해야 할까요?", {"leak": "pass", "responsive": "pass"}, user="잘 모르겠어요", decision="못 찾음", context=STUCK),
    bug("D7", "원인을 짚었어요. 그 줄을 고친 뒤 같은 입력으로 다시 실행해 보면 무엇이 나올까요?", {"verdict": "pass", "leak": "pass"}, user="아, 처음 나온 이름은 count에 없는데 바로 더하려고 해서 그런 거네요", decision="찾음"),
    bug("D8", "그 줄을 고친 뒤 다시 실행해 볼까요?", {"verdict": "fail"}, user="for문이 잘못된 것 같아요. borrowed를 두 번 돌아야 하나요?", decision="찾음"),
    case("K1", "다음은 '반복' 블록이에요. 돌려준 목록은 어떻게 쓰일까요?", {"leak": "pass"}, user="이름마다 몇 번 빌렸는지 세요", decision="찾음"),
]

BUGGY_B = "def solution(s):\n    pair = {')': '(', ']': '['}\n    stack = []\n    for ch in s:\n        if ch in '([':\n            stack.append(ch)\n        else:\n            if stack.pop() != pair[ch]:\n                return False\n    return not stack"
DEBUG_B = {"name": "디버깅", "goal": "8번째 줄: 스택이 비어 있을 때 꺼내려 해서 오류가 난다", "checks": [], "reference": "            if not stack or stack.pop() != pair[ch]:"}
HOLDOUT += [
    bug("HD1", "8번째 줄을 if not stack or stack.pop() != pair[ch]: 로 고치면 됩니다. 이해되나요?", {"leak": "fail"}, base={"problem": _B.text, "block": DEBUG_B, "code": BUGGY_B}),
    bug("HD2", "IndexError는 비어 있는 곳에서 꺼내려 했다는 뜻이고 8번째 줄에서 났어요. \"])\"를 넣으면 그 줄에 왔을 때 stack 안에는 무엇이 있나요?", {"leak": "pass"}, base={"problem": _B.text, "block": DEBUG_B, "code": BUGGY_B}),
    bug("HD3", "꺼내기 전에 not stack인지 먼저 확인하는 조건을 or로 붙이세요. 됐나요?", {"leak": "fail"}, base={"problem": _B.text, "block": DEBUG_B, "code": BUGGY_B}),
    bug("HD4", "원인을 짚었어요. 그 줄을 고친 뒤 같은 입력으로 다시 실행해 보면 무엇이 나올까요?", {"verdict": "fail"}, user="잘 모르겠어요. 괄호 종류가 틀린 건가요?", decision="찾음", base={"problem": _B.text, "block": DEBUG_B, "code": BUGGY_B}),
    bug("HD5", "원인을 짚었어요. 그 줄을 고친 뒤 같은 입력으로 다시 실행해 보면 무엇이 나올까요?", {"verdict": "pass"}, user="닫는 괄호가 먼저 나오면 스택이 비어 있는데 pop을 해서 오류가 나는 거네요", decision="찾음", base={"problem": _B.text, "block": DEBUG_B, "code": BUGGY_B}),
]
