"""풀이 범위 15종, 허용 기법, 설계 원칙, 시스템 프롬프트 조각.

기본 문제의 주제 15개(ui/problems/README.md)와 같다: DFS, BFS, 다익스트라를 저마다 독립 유형으로 두고,
그래프는 그 셋이 아닌 도구(유니온 파인드, 위상 정렬, 최소 신장 트리, 플로이드)만, 시뮬레이션에서 순수 구현(문자열·규칙·계산)을 떼어 냈다.
예전 계획에 남은 dfs_bfs는 계속 읽힌다(LEGACY). 새 계획은 그 키를 쓰지 않는다(SOLVE_SCOPE에 없다).
대회용 기법(세그먼트 트리, 네트워크 플로우 등)은 넣지 않는다.
"""

SCOPE = (
    ("hash", "해시", "딕셔너리, 집합, 개수 세기, 묶어서 세기, 경우의 수 곱"),
    ("stack_queue", "스택/큐", "스택, 큐, 덱, 짝 맞추기, 단조 스택"),
    ("heap", "힙(Heap)", "우선순위 큐, 가장 작은 것 꺼내기, 두 힙, 작업 순서 정하기"),
    ("sort", "정렬", "내장 정렬, 비교 기준 정하기, 여러 기준, 정렬 뒤 한 번 훑기"),
    ("brute_force", "완전탐색", "전수 반복, 순열·조합, 부분집합, 재귀 백트래킹"),
    ("greedy", "탐욕법(Greedy)", "정렬 뒤 고르기, 구간 고르기, 양 끝에서 좁혀 오기"),
    ("dp", "동적계획법(Dynamic Programming)", "1·2차원 표, 점화식 세우기, 구간 DP, 배낭"),
    ("dfs", "깊이 우선 탐색(DFS)", "재귀·스택 DFS, 연결 요소, 경로 만들기, 가지치기"),
    ("bfs", "너비 우선 탐색(BFS)", "큐 BFS, 최소 단계, 격자 최단 거리, 상태를 늘린 BFS"),
    ("dijkstra", "다익스트라", "가중치 최단 경로, 우선순위 큐, 여러 출발점, 상태를 늘린 최단 경로"),
    ("binary_search", "이분탐색", "값 찾기, 하한·상한, 답을 정해 놓고 되는지 확인하기"),
    ("graph", "그래프", "유니온 파인드, 위상 정렬, 최소 신장 트리, 플로이드"),
    ("two_pointer", "투 포인터·누적 합", "투 포인터, 슬라이딩 윈도우, 1·2차원 누적 합"),
    ("simulation", "시뮬레이션", "격자 이동·회전, 시간 흐름대로 상태 바꾸기, 규칙대로 반복"),
    ("implementation", "구현", "문자열 쪼개기·바꾸기, 규칙 여럿을 순서대로 적용, 날짜·시간·진수 계산, 자료 변환"),
)
LEGACY = (("dfs_bfs", "깊이/너비 우선 탐색(DFS/BFS)", "재귀·스택 DFS, 큐 BFS, 격자 탐색, 최소 단계"),)  # 예전에 만든 계획에 남은 유형
ALGORITHMS = tuple(key for key, _, _ in SCOPE)
KNOWN = ALGORITHMS + tuple(key for key, _, _ in LEGACY)  # 저장된 계획에서 받아 주는 유형
BY_KEY = {key: (name, tools) for key, name, tools in (*SCOPE, *LEGACY)}
SOLVE_SCOPE = "\n".join(f"- {name}({key}): {tools}" for key, name, tools in SCOPE)
QUALITY_THRESHOLD = 50

OUTSIDE_PROBLEMS = "다른 사이트·책·대회의 문제 이름이나 번호를 먼저 꺼내지 않는다. 사용자가 먼저 말한 것은 받아 말해도 된다. 비슷한 문제는 이 앱에 있는 문제의 제목으로만 가리킨다."  # 공통 원칙을 쓰지 않는 프롬프트(디버깅, 힌트 규칙, 풀이 가이드, 피드백의 비슷한 문제)도 같은 말을 쓴다
PRINCIPLES = "\n".join(
    [
        "- 답을 대신 적지 않는다. 사용자가 사고 순서를 세우고 코드를 직접 옮기게 돕는다.",
        "- 실전 코딩테스트에서 바로 쓰는 직관적인 코드다. 기교 없이, 모듈식으로, 사고 흐름 순서대로.",
        "- 어려운 알고리즘보다 기초 알고리즘과 자료구조. 기출에 나오는 수준까지만.",
        "- 코딩테스트를 막 시작한 사람에게 말하듯 쉬운 말로 쓴다. 시간복잡도, O(N), 상수 시간 같은 용어는 '입력이 100만 개여도 한 번만 훑으면 된다'처럼 풀어서 말한다.",
        f"- {OUTSIDE_PROBLEMS}",
    ]
)


def algorithm_name(key: str) -> str:
    return BY_KEY[key][0] if key in BY_KEY else ""


def algorithm_line(key: str) -> str | None:
    """계획의 유형 한 줄. 옛 계획처럼 유형이 없으면 None."""
    if key not in BY_KEY:
        return None
    name, tools = BY_KEY[key]
    return f"풀이 유형:{name} — 허용 기법: {tools}"


def system_prompt(role: str, *rules: str) -> str:
    return "\n".join([role, "원칙:", PRINCIPLES, *rules])
