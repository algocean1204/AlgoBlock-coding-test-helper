"""평가 시나리오. 문제 글은 이 프로젝트에서 새로 쓴 것이다(기출 원문을 옮기지 않는다).

시나리오 하나 = 문제 + 채점 케이스(함수 모드) + 초보자 성격. 정답 코드는 채점기 확인용이고 튜터에게 주지 않는다.
"""

from dataclasses import dataclass, field, replace


@dataclass
class Persona:
    """초보자 시뮬레이터가 연기할 사람."""

    knows: str  # 아는 것
    misconception: str  # 처음에 품고 있는 틀린 생각 하나
    habits: list[str] = field(default_factory=list)


@dataclass
class Scenario:
    id: str
    algorithm: str
    text: str
    solution: str  # 채점기 자체 확인용 정답
    cases: list[dict]  # {"id", "input"(인자 배열 JSON), "expected"(JSON)}
    persona: Persona
    language: str = "python"


BEGINNER = "파이썬 for, if, 리스트, 함수는 써 봤다. 딕셔너리·스택·이중 반복을 문제에 골라 쓰는 건 서툴다."
HABITS = [
    "대답은 짧게 1~2문장으로 한다",
    "모르면 솔직히 '모르겠어요'라고 한다",
    "가끔 답을 그냥 알려 달라고 조른다",
    "튜터의 질문이 어려우면 질문 뜻을 되묻는다",
]

SCENARIOS = [
    Scenario(
        id="hash_library",
        algorithm="hash",
        text=(
            "도서관에서 책을 빌려 간 학생 이름 목록 borrowed와 책을 돌려준 학생 이름 목록 returned가 주어집니다.\n"
            "책을 돌려주지 않은 학생은 정확히 한 명입니다. 그 학생의 이름을 return 하도록 solution 함수를 완성하세요.\n\n"
            "제한사항\n"
            "- borrowed의 길이는 1 이상 70,000 이하입니다.\n"
            "- returned의 길이는 borrowed의 길이보다 1 작습니다.\n"
            "- 이름은 알파벳 소문자 1~16글자입니다.\n"
            "- 같은 이름의 학생이 여러 명 있을 수 있습니다.\n\n"
            "입출력 예\n"
            '| borrowed | returned | result |\n'
            '| ["mina", "joon", "sara"] | ["sara", "mina"] | "joon" |\n'
            '| ["tom", "ann", "tom"] | ["ann", "tom"] | "tom" |\n'
        ),
        solution=(
            "def solution(borrowed, returned):\n"
            "    count = {}\n"
            "    for name in borrowed:\n"
            "        count[name] = count.get(name, 0) + 1\n"
            "    for name in returned:\n"
            "        count[name] -= 1\n"
            "    for name, left in count.items():\n"
            "        if left > 0:\n"
            "            return name\n"
        ),
        cases=[
            {"id": "1", "input": '[["mina", "joon", "sara"], ["sara", "mina"]]', "expected": '"joon"'},
            {"id": "2", "input": '[["tom", "ann", "tom"], ["ann", "tom"]]', "expected": '"tom"'},
            {"id": "3", "input": '[["a"], []]', "expected": '"a"'},
            {"id": "4", "input": '[["b", "a", "b", "b"], ["b", "a", "b"]]', "expected": '"b"'},
        ],
        persona=Persona(BEGINNER, "이름이 returned에 있는지만 확인하면 된다고 생각한다(같은 이름 여러 명을 놓침)", HABITS),
    ),
    Scenario(
        id="stack_brackets",
        algorithm="stack_queue",
        text=(
            "'(', ')', '[', ']' 네 가지 문자로만 이루어진 문자열 s가 주어집니다.\n"
            "모든 여는 괄호가 같은 종류의 닫는 괄호로 올바른 순서대로 닫히면 true, 아니면 false를 return 하도록 solution 함수를 완성하세요.\n"
            "예를 들어 \"([])\"는 올바르고, \"([)]\"는 올바르지 않습니다.\n\n"
            "제한사항\n"
            "- s의 길이는 1 이상 80,000 이하입니다.\n\n"
            "입출력 예\n"
            "| s | result |\n"
            '| "([])" | true |\n'
            '| "([)]" | false |\n'
            '| "((" | false |\n'
        ),
        solution=(
            "def solution(s):\n"
            "    pair = {')': '(', ']': '['}\n"
            "    stack = []\n"
            "    for ch in s:\n"
            "        if ch in '([':\n"
            "            stack.append(ch)\n"
            "        elif not stack or stack.pop() != pair[ch]:\n"
            "            return False\n"
            "    return not stack\n"
        ),
        cases=[
            {"id": "1", "input": '["([])"]', "expected": "true"},
            {"id": "2", "input": '["([)]"]', "expected": "false"},
            {"id": "3", "input": '["(("]', "expected": "false"},
            {"id": "4", "input": '["])"]', "expected": "false"},
            {"id": "5", "input": '["()[]"]', "expected": "true"},
        ],
        persona=Persona(BEGINNER, "여는 괄호 개수와 닫는 괄호 개수만 같으면 올바르다고 생각한다(순서를 놓침)", HABITS),
    ),
    Scenario(
        id="brute_pairs",
        algorithm="brute_force",
        text=(
            "숫자가 적힌 카드 목록 cards와 목표 수 target이 주어집니다.\n"
            "서로 다른 카드 두 장을 골라 적힌 수의 합이 target이 되는 방법의 수를 return 하도록 solution 함수를 완성하세요.\n"
            "같은 두 장을 고르는 순서만 다른 것은 한 가지로 셉니다.\n\n"
            "제한사항\n"
            "- cards의 길이는 2 이상 1,000 이하입니다.\n"
            "- 카드에 적힌 수는 1 이상 1,000 이하이고, 같은 수가 적힌 카드가 여러 장 있을 수 있습니다.\n\n"
            "입출력 예\n"
            "| cards | target | result |\n"
            "| [1, 2, 3, 4] | 5 | 2 |\n"
            "| [2, 2, 2] | 4 | 3 |\n"
        ),
        solution=(
            "def solution(cards, target):\n"
            "    answer = 0\n"
            "    for i in range(len(cards)):\n"
            "        for j in range(i + 1, len(cards)):\n"
            "            if cards[i] + cards[j] == target:\n"
            "                answer += 1\n"
            "    return answer\n"
        ),
        cases=[
            {"id": "1", "input": "[[1, 2, 3, 4], 5]", "expected": "2"},
            {"id": "2", "input": "[[2, 2, 2], 4]", "expected": "3"},
            {"id": "3", "input": "[[1, 1], 3]", "expected": "0"},
            {"id": "4", "input": "[[5, 1, 4, 1, 4], 5]", "expected": "4"},
        ],
        persona=Persona(BEGINNER, "j도 0부터 돌려서 (i, j)와 (j, i)를 둘 다 세거나 같은 카드를 두 번 써도 된다고 생각한다", HABITS),
    ),
]


# 사용자 방향 따르기 확인용: 같은 문제를, 계획(개수 세기)과 다른 풀리는 방법(정렬해 비교)으로 풀고 싶어 하는 사용자
SCENARIOS.append(replace(
    SCENARIOS[0], id="hash_library_sortway",
    persona=Persona(BEGINNER, "개수를 세는 방법은 떠올리지 못한다. 대신 두 목록을 정렬해서 앞에서부터 하나씩 비교하다가 처음 다른 자리의 이름이 답이라고 생각하고(맞는 방법이다), "
                    "첫 대답부터 그 방법을 말하고 그 방법으로 풀고 싶어 한다", HABITS),
))


def load_extra(folder: str | None = None) -> list[Scenario]:
    """저장소 밖의 폴더(ALGOBLOCK_EVAL_EXTRA)에 둔 문제(JSON)를 시나리오로 읽는다. 저장소에는 넣지 않는다.

    JSON: {scenario_id, algorithm, text, solution, cases, persona{knows, misconception, habits}}
    """
    import json
    import os
    from pathlib import Path

    root = folder or os.environ.get("ALGOBLOCK_EVAL_EXTRA", "")
    if not root:
        return []
    out = []
    for path in sorted(Path(root).glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        out.append(Scenario(id=raw["scenario_id"], algorithm=raw["algorithm"], text=raw["text"], solution=raw["solution"],
                            cases=raw["cases"], persona=Persona(**raw["persona"])))
    return out


def all_scenarios() -> list[Scenario]:
    return SCENARIOS + load_extra()


def by_id(scenario_id: str) -> Scenario:
    return next(s for s in all_scenarios() if s.id == scenario_id)
