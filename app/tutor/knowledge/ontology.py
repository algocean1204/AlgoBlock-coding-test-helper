"""온톨로지(정적 그래프). 문제 글의 단서 → 기법 → 자주 틀리는 것을 잇는다. 사람이 다듬은 지식이고 모델이 만들지 않는다.

노드: Technique(기법), Pattern(문제 글의 단서와 기법을 잇는 다리), Pitfall(함정), Skill(구현 기술: 알고리즘이 아니라 코드를 옮길 때 필요한 것),
SizeRule(입력 크기 경험칙). 유형(Theme)은 common/scope.py의 15종이다.
엣지: Technique -IN-> Theme, Pattern -SUGGESTS-> Technique, Technique -PRONE_TO-> Pitfall, Theme -PREREQUISITE_OF-> Theme, 문항 -NEEDS-> Skill.
대상은 회사 코딩테스트 1–2단계 수준이다. 대회용 기법은 넣지 않는다. 사람이 고정한 목록이라 모델이 새 노드를 만들지 못한다.
사용자 쪽 엣지(문항 -HAS_PATTERN-> Pattern, 제출 -TRIGGERED-> Pitfall)는 SQLite에 있다(store).
범위는 코딩테스트 1–2단계다. 넣는 기준: 기출에 실제로 나오고, 초보자가 문제 글에서 알아챌 수 있는 단서.
"""

import re

# 기법: id → (유형, 이름, 사용자가 말하기 전에는 의자가 말하지 않는 낱말들)
TECHNIQUES = {
    "count_map": ("hash", "개수 세기(딕셔너리)", ["딕셔너리", "dict", "해시", "Counter"]),
    "seen_set": ("hash", "본 것 기억하기(집합)", ["집합", "set"]),
    "lookup_map": ("hash", "짝 찾아보기(딕셔너리)", ["딕셔너리", "dict", "해시"]),
    "stack": ("stack_queue", "스택", ["스택", "stack", "append", "pop"]),
    "queue": ("stack_queue", "큐", ["큐", "queue", "deque", "덱"]),
    "last_compare": ("stack_queue", "마지막 것과 비교", ["스택", "stack"]),
    "heap": ("heap", "우선순위 큐", ["힙", "heap", "heapq", "우선순위 큐"]),
    "sort_scan": ("sort", "정렬 뒤 한 번 훑기", ["정렬", "sort", "sorted"]),
    "sort_key": ("sort", "비교 기준 정해 정렬", ["정렬", "sort", "sorted", "lambda"]),
    "single_scan": ("brute_force", "한 번 훑으며 최대·최소·합 갱신", []),
    "double_loop": ("brute_force", "이중 반복으로 모든 쌍 보기", ["이중 반복", "이중 for", "중첩"]),
    "all_cases": ("brute_force", "모든 경우 만들어 보기", ["순열", "조합", "permutations", "combinations", "재귀", "백트래킹"]),
    "pattern_cycle": ("brute_force", "되풀이되는 규칙을 나머지로 맞추기", []),
    "greedy_sorted": ("greedy", "정렬하고 앞에서부터 고르기", ["정렬", "sort", "탐욕", "그리디"]),
    "two_pointer": ("greedy", "양 끝에서 좁혀 오기", ["투 포인터", "투포인터", "포인터"]),
    "dp_table": ("dp", "작은 답을 표에 쌓기", ["dp", "DP", "점화식"]),
    "bfs": ("bfs", "가까운 곳부터 넓혀 가기", ["BFS", "bfs", "큐", "너비"]),
    "dfs": ("dfs", "끝까지 들어갔다 돌아오기", ["DFS", "dfs", "재귀", "깊이"]),
    "binary_search": ("binary_search", "절반씩 줄여 찾기", ["이분", "이진", "binary"]),
    "param_search": ("binary_search", "답을 정해 놓고 되는지 확인", ["이분", "이진", "파라메트릭"]),
    "adjacency": ("dfs", "이웃 목록 만들기", ["인접", "그래프"]),
    "dijkstra": ("dijkstra", "가장 가까운 곳부터 확정하기", ["다익스트라", "dijkstra", "힙", "heapq"]),
    "monotonic_stack": ("stack_queue", "아직 답을 못 찾은 것만 쌓아 두기", ["스택", "stack", "단조"]),
    "union_find": ("graph", "같은 묶음인지 대표로 확인하기", ["유니온", "union", "크루스칼"]),
    "sliding_window": ("two_pointer", "정해진 길이의 구간을 한 칸씩 밀기", ["슬라이딩", "윈도우"]),
    "prefix_sum": ("two_pointer", "앞에서부터 더한 값을 미리 구해 두기", ["누적 합", "누적합", "prefix"]),
    "string_build": ("implementation", "글자를 하나씩 보며 새 문자열 만들기", []),
    "digit_math": ("implementation", "자릿수·약수·나머지 계산", []),
    "grid_move": ("simulation", "격자에서 규칙대로 움직이기", []),
    "rule_follow": ("implementation", "조건을 순서대로 그대로 옮기기", []),
}

# 패턴: id → (단서, 기법, 왜 그 기법인가, 의자가 쓸 질문 씨앗). 질문 씨앗에는 기법 이름을 넣지 않는다.
PATTERNS = {
    "dup_names": ("같은 값(이름)이 여러 번 나올 수 있다 + 누가/무엇이 남는지 찾는다", "count_map",
                  "있다·없다만으로는 여러 번 나온 것을 가릴 수 없어 횟수가 필요하다", "같은 것이 두 번 나오면 한 번 나온 것과 어떻게 달라야 할까요?"),
    "kinds_count": ("서로 다른 종류가 몇 가지인지가 답을 가른다", "seen_set",
                    "개수가 아니라 종류 수만 필요하면 중복을 버리는 그릇이면 된다", "같은 것을 여러 번 봐도 한 번으로 치려면 무엇을 기억해 둬야 할까요?"),
    "pair_lookup": ("어떤 값에 대해 짝이 되는 값이 있는지 빨리 찾아야 한다(N이 크다)", "lookup_map",
                    "매번 처음부터 찾으면 N×N이라 큰 입력에서 시간 초과다", "짝이 있는지 매번 처음부터 찾지 않으려면 무엇을 미리 적어 둘까요?"),
    "recent_first": ("가장 최근에 넣은 것부터 짝을 맞추거나 되돌린다(괄호, 되돌리기)", "stack",
                     "나중에 들어온 것이 먼저 나가야 순서가 맞는다", "닫는 것이 나왔을 때 지금까지 연 것 중 어느 것과 맞아야 할까요?"),
    "adjacent_same": ("바로 앞의 것과 같은지에 따라 넣거나 뺀다(연속 중복 제거, 붙어 있는 같은 값 쌍 지우기)", "last_compare",
                      "전체가 아니라 마지막으로 남긴 것 하나만 보면 된다", "지금 것을 넣을지 정하려면 앞에서 무엇 하나만 보면 될까요?"),
    "arrival_order": ("먼저 온 것이 먼저 처리된다(대기열, 작업 순서, 줄 서기)", "queue",
                      "앞에서 꺼내고 뒤에 넣는 순서가 문제의 처리 순서와 같다", "먼저 들어온 것과 나중에 들어온 것 중 무엇이 먼저 처리되나요?"),
    "repeat_min": ("가장 작은(큰) 것을 꺼내 처리하고 다시 넣기를 되풀이한다", "heap",
                   "매번 정렬하면 느리고, 가장 작은 것만 빨리 꺼내면 된다", "매번 필요한 것은 전체 순서일까요, 가장 작은 것 하나일까요?"),
    "kth_after_sort": ("순서대로 놓았을 때 몇 번째, 가장 큰/작은 몇 개", "sort_scan",
                       "순서가 정해지면 자리가 곧 답이다", "값들을 어떤 순서로 놓으면 답이 자리로 보일까요?"),
    "custom_order": ("크기가 아닌 다른 기준(길이, 이어 붙인 결과, 여러 조건)으로 순서를 정한다", "sort_key",
                     "비교 기준만 바꾸면 내장 정렬을 그대로 쓸 수 있다", "두 값 중 무엇이 앞에 와야 하는지 정하는 기준은 무엇일까요?"),
    "max_min_scan": ("모든 것을 한 번씩 보며 가장 큰/작은 값이나 합을 구한다", "single_scan",
                     "지금까지의 최댓값(합) 하나만 기억하고 갱신하면 된다", "하나씩 볼 때 지금까지 본 것 중 무엇만 기억하면 될까요?"),
    "normalize_then_max": ("각 항목을 뒤집거나 돌려 놓을 수 있고, 모두를 담는 최소 크기를 구한다", "single_scan",
                           "항목마다 큰 쪽·작은 쪽으로 맞춰 놓으면 각각의 최댓값만 보면 된다", "뒤집어도 된다면 각 항목의 두 값을 어떻게 맞춰 놓고 비교할까요?"),
    "choose_two_small_n": ("N이 작다(1,000 이하) + 두 개(세 개)를 골라 조건을 확인한다", "double_loop",
                           "모든 쌍이 N×N/2개라 다 봐도 시간 안에 든다", "두 개를 고르는 경우를 빠짐없이, 겹치지 않게 보려면 둘째는 어디서부터 볼까요?"),
    "tiny_n_all": ("N이 아주 작다(10 안팎) + 순서나 고르는 방법 전부 중 가장 좋은 것", "all_cases",
                   "경우의 수가 적어 전부 만들어 보는 것이 가장 확실하다", "가능한 경우가 모두 몇 가지쯤 되나요? 전부 해 볼 만한가요?"),
    "fixed_cycle": ("정해진 규칙이 되풀이된다(되풀이되는 답 패턴, 요일, 원형 자리)", "pattern_cycle",
                    "되풀이 길이로 나눈 나머지가 규칙 안의 자리다", "규칙이 몇 개마다 되풀이되나요? 100번째는 규칙의 몇 번째와 같을까요?"),
    "pick_smallest_first": ("한정된 자원으로 가능한 한 많이 처리한다(가진 돈 한도, 무게 제한)", "greedy_sorted",
                            "작은 것부터 고르면 같은 자원으로 더 많이 고를 수 있다", "최대한 많이 고르려면 어떤 것부터 골라야 할까요?"),
    "pair_light_heavy": ("둘씩 짝지어 제한 안에 담는다(두 명씩 태우기, 짝 맞추기)", "two_pointer",
                         "가장 큰 것과 가장 작은 것을 짝지어 보는 것이 낭비가 가장 적다", "가장 무거운 것은 누구와 짝이 되어야 함께 탈 수 있을까요?"),
    "build_from_smaller": ("n번째 답이 앞의 답들로 정해진다(계단, 타일, 위에서 아래로 합 쌓기)", "dp_table",
                           "같은 작은 문제를 되풀이해 풀지 않게 답을 적어 둔다", "n번째 답을 알려면 그 앞의 어떤 답들을 알면 될까요?"),
    "grid_shortest": ("격자에서 한 칸씩 움직여 가장 적은 횟수로 도착한다", "bfs",
                      "가까운 칸부터 넓혀 가면 처음 닿은 때가 가장 빠른 때다", "한 번 움직여 갈 수 있는 칸을 다 표시하고, 그다음에는 무엇을 해야 할까요?"),
    "connected_groups": ("이어진 것끼리 한 덩어리로 세거나, 갈 수 있는 모든 곳을 본다", "dfs",
                         "한 곳에서 이어진 곳을 끝까지 따라가면 한 덩어리가 된다", "한 곳에서 시작해 이어진 곳을 모두 방문했는지 어떻게 기억할까요?"),
    "sorted_find": ("정렬된 값들에서 어떤 값(또는 경계)을 찾는다 + N이 크다", "binary_search",
                    "가운데와 비교하면 절반을 한 번에 버릴 수 있다", "가운데 값과 비교하면 어느 쪽 절반을 볼 필요가 없어지나요?"),
    "answer_range": ("답이 될 수 있는 값의 범위가 아주 크고, 값을 정하면 되는지 안 되는지 판단할 수 있다(최소 시간, 최대 길이)", "param_search",
                     "답을 하나 정해 되는지 확인하는 것이 직접 구하는 것보다 쉽다", "답이 x라고 치면, 그것이 가능한지는 어떻게 확인할 수 있을까요?"),
    "links_given": ("무엇과 무엇이 이어져 있는지 목록으로 준다(도로, 친구 관계, 간선)", "adjacency",
                    "각자의 이웃을 바로 찾을 수 있게 정리해 둬야 탐색할 수 있다", "어떤 곳의 이웃을 매번 목록 전체에서 찾지 않으려면 어떻게 정리해 둘까요?"),
    "next_bigger": ("각 원소에 대해 뒤에서 처음으로 더 큰(작은) 것이 나오는 때를 구한다(가격이 떨어지지 않은 기간, 뒤에서 처음 나오는 더 큰 값)", "monotonic_stack",
                    "아직 답이 안 정해진 것만 남겨 두면 새 값이 올 때 한꺼번에 답이 정해진다", "지금 값이 오면 앞의 것들 중 누구의 답이 정해지나요?"),
    "connect_min_cost": ("모든 곳을 가장 적은 비용으로 잇는다(다리 놓기, 통신망)", "union_find",
                         "싼 것부터 고르되 이미 이어진 둘은 건너뛰어야 한다", "가장 싼 길을 골랐는데 그 둘이 이미 이어져 있다면 어떻게 해야 할까요?"),
    "fixed_window": ("길이가 정해진 연속 구간의 합·개수·종류를 구한다(연속 k일, 연속 부분 수열)", "sliding_window",
                     "구간을 한 칸 밀면 하나가 빠지고 하나가 들어올 뿐이라 처음부터 다시 셀 필요가 없다", "구간을 한 칸 옮기면 무엇이 빠지고 무엇이 들어오나요?"),
    "range_sum_many": ("여러 구간의 합을 되풀이해 묻는다 + N이 크다", "prefix_sum",
                       "앞에서부터 더한 값을 한 번 구해 두면 구간의 합은 뺄셈 한 번이다", "1번부터 5번까지의 합과 1번부터 2번까지의 합을 알면 3번부터 5번까지의 합은 어떻게 구할까요?"),
    "char_transform": ("문자열의 글자를 규칙에 따라 바꾸거나 고른다(문자 밀기, 대소문자, 숫자만 남기기)", "string_build",
                       "글자마다 같은 규칙을 적용해 새 문자열에 붙이면 된다", "글자 하나를 놓고 보면 그 글자는 어떤 규칙으로 무엇이 되어야 하나요?"),
    "digits_or_divisors": ("수의 자릿수, 약수, 배수, 나머지를 다룬다", "digit_math",
                           "나누기와 나머지로 한 자리씩 떼거나 나누어떨어지는지 확인한다", "수에서 마지막 자리 하나만 떼어 내려면 어떤 계산을 하면 될까요?"),
    "grid_rules": ("격자(지도, 보드)에서 정해진 방향과 규칙대로 움직이거나 바꾼다", "grid_move",
                   "위치를 (행, 열)로 두고 방향마다 더할 값을 정해 두면 규칙을 그대로 옮길 수 있다", "오른쪽으로 한 칸 가면 행과 열 중 무엇이 얼마나 바뀌나요?"),
    "follow_steps": ("문제에 적힌 절차·조건을 순서대로 수행한 결과를 구한다(특별한 기법 없음)", "rule_follow",
                     "빠른 방법을 찾는 문제가 아니라 조건을 빠짐없이 옮기는 문제다", "문제에 적힌 조건을 순서대로 번호를 붙여 적어 보면 몇 가지인가요?"),
    "weighted_shortest": ("길마다 걸리는 시간(비용)이 다르고 가장 적게 드는 길을 구한다", "dijkstra",
                          "칸 수가 아니라 비용 합이 기준이라 가장 싼 곳부터 확정해야 한다", "지금까지 알아낸 곳 중 다음으로 확정해도 되는 곳은 어디일까요?"),
}

# 함정: id → (종류, 이름, 증상, 디버깅 질문 씨앗). 종류: syntax, runtime, logic, timeout
PITFALLS = {
    "missing_colon": ("syntax", "콜론(:) 빠짐", "if/for/def/while 줄 끝에 콜론이 없다", "이 줄처럼 아래에 묶음이 딸리는 줄은 끝이 무엇으로 끝나야 할까요?"),
    "indent": ("syntax", "들여쓰기 어긋남", "같은 묶음의 줄들이 칸 수가 다르거나 묶음 밖으로 나갔다", "이 줄은 어느 줄의 묶음 안에 있어야 하나요? 칸 수가 그 묶음의 다른 줄과 같나요?"),
    "assign_vs_equal": ("syntax", "= 와 == 혼동", "조건에서 같은지 물을 때 =를 썼다", "값을 넣는 것과 같은지 묻는 것은 기호가 어떻게 다를까요?"),
    "paren_mismatch": ("syntax", "괄호·따옴표 짝 안 맞음", "여는 괄호나 따옴표가 닫히지 않았다", "이 줄에서 연 괄호와 닫은 괄호의 수를 세어 보면 어떤가요?"),
    "undefined_name": ("runtime", "만들지 않은 이름 사용", "변수를 만들기 전에 쓰거나 이름 철자가 다르다", "이 이름은 어느 줄에서 처음 만들어졌나요? 철자가 똑같은가요?"),
    "key_missing": ("runtime", "없는 키 읽기", "딕셔너리에 아직 없는 키를 읽거나 더했다", "이 키를 처음 만났을 때 그릇 안에는 그 키가 있을까요?"),
    "index_range": ("runtime", "범위 밖 자리 읽기", "리스트 길이를 넘는 자리나 빈 리스트의 마지막을 읽었다", "반복의 마지막 차례에서 이 자리 번호는 얼마인가요? 그 자리가 있나요?"),
    "empty_pop": ("runtime", "빈 것에서 꺼내기", "비어 있는데 꺼내거나 마지막 것을 봤다", "꺼내려는 순간 안에 아무것도 없을 수 있는 입력은 무엇일까요?"),
    "type_mix": ("runtime", "글자와 숫자 섞기", "문자열과 숫자를 더하거나 비교했다", "이 값은 글자인가요 숫자인가요? 어디서 어떤 모양으로 만들어졌나요?"),
    "no_return": ("logic", "돌려주지 않음(None)", "return이 없거나 print만 했다, 또는 조건 안에서만 return 한다", "함수가 끝까지 갔을 때 무엇을 돌려주나요? 모든 경우에 돌려주는 값이 있나요?"),
    "early_return": ("logic", "반복 안에서 너무 일찍 return", "첫 번째만 보고 끝난다", "반복의 첫 차례에서 함수가 끝나 버리는 경우가 있나요?"),
    "wrong_init": ("logic", "시작 값 잘못", "합·개수·최댓값의 시작 값이 틀렸거나 반복 안에서 다시 0이 된다", "이 변수는 반복이 돌기 전 얼마에서 시작하나요? 반복할 때마다 다시 처음 값이 되지는 않나요?"),
    "off_by_one": ("logic", "한 칸 어긋남", "범위의 끝을 하나 덜 가거나 더 간다, 또는 경계 값을 넣을지 뺄지(이하 <=와 미만 <)를 바꿔 썼다", "반복이 마지막으로 보는 자리는 어디인가요? 끝자리까지 보나요?"),
    "pair_twice": ("logic", "같은 쌍을 두 번 셈 / 자기 자신과 짝", "둘째 반복이 처음부터 돌아 (i, j)와 (j, i), (i, i)를 모두 센다", "첫째가 0번일 때 둘째가 도는 자리들을 적어 보면, 겹치거나 자기 자신인 쌍이 있나요?"),
    "exists_not_count": ("logic", "있는지만 보고 횟수를 안 봄", "같은 값이 여러 번일 때 구별하지 못한다", "같은 값이 두 번 들어온 입력에서는 이 조건이 어떻게 되나요?"),
    "dedupe_all": ("logic", "떨어져 있는 같은 값까지 지움", "연속한 것만 지워야 하는데 전체 중복을 없앴다", "같은 값이 떨어져서 다시 나오는 입력에서는 무엇이 남아야 하나요?"),
    "count_not_order": ("logic", "개수만 보고 순서를 안 봄", "개수는 맞지만 순서가 틀린 입력을 통과시킨다", "개수는 같은데 순서가 틀린 입력을 하나 만들어 넣어 보면 어떻게 되나요?"),
    "leftover_unchecked": ("logic", "끝난 뒤 남은 것 확인 안 함", "반복이 끝난 뒤 남아 있는 것이 있는지 보지 않는다", "반복이 다 끝났을 때 그릇에 무엇이 남아 있을 수 있나요? 그때 답은 무엇이어야 하나요?"),
    "wrong_compare": ("logic", "비교 방향·대상이 틀림", "크다/작다가 뒤집혔거나 엉뚱한 값끼리 비교한다(경계 값만 넣고 빼는 차이는 한 칸 어긋남)", "이 조건이 참이 되는 값 하나와 거짓이 되는 값 하나를 넣어 보면 뜻대로 갈리나요?"),
    "update_in_wrong_branch": ("logic", "갱신 위치가 틀림", "값을 바꾸는 줄이 조건 밖이나 엉뚱한 갈래에 있다", "이 줄은 어떤 경우에만 실행되어야 하나요? 지금은 어떤 경우에 실행되나요?"),
    "missed_case": ("logic", "빠진 경우", "특정 경우(같은 값, 빈 입력, 하나뿐인 입력)를 다루지 않는다", "가장 작은 입력이나 값이 모두 같은 입력에서는 어떻게 되나요?"),
    "no_normalize": ("logic", "맞춰 놓지 않고 비교", "뒤집을 수 있는데 원래 놓인 대로만 비교했다", "항목을 돌려 놓아도 된다면 지금 비교는 어떤 경우를 놓치나요?"),
    "mutate_while_loop": ("logic", "도는 중에 지움", "반복 중인 리스트에서 지워 자리가 밀린다", "하나를 지우면 그 뒤 것들의 자리 번호는 어떻게 바뀌나요?"),
    "sort_as_text": ("logic", "숫자를 글자로 정렬", "문자열 그대로 정렬해 '10'이 '9'보다 앞에 온다", "'10'과 '9'를 글자로 비교하면 무엇이 앞에 오나요?"),
    "visit_on_pop": ("timeout", "꺼낼 때 방문 표시", "큐에 넣을 때가 아니라 꺼낼 때 방문 표시를 해 같은 곳이 여러 번 들어간다", "같은 칸이 큐에 두 번 들어가는 경우가 있나요? 방문 표시는 언제 하나요?"),
    "str_immutable": ("runtime", "문자열의 글자를 직접 바꾸려 함", "문자열은 한 글자만 바꿀 수 없다(s[i] = ...)", "문자열의 한 글자를 바꾼 결과를 얻으려면 어디에 새로 만들어 담아야 할까요?"),
    "int_division": ("logic", "나눗셈 종류 혼동", "/ 는 소수가 나오고 // 는 몫만 나온다", "7을 2로 나눈 결과가 3.5가 필요한가요, 3이 필요한가요?"),
    "grid_out": ("runtime", "격자 밖으로 나감", "움직인 뒤 위치가 범위 안인지 확인하지 않았다", "가장자리 칸에서 바깥쪽으로 움직이려 하면 어떤 위치가 되나요?"),
    "condition_order": ("logic", "조건 순서가 틀림", "먼저 걸러야 할 조건이 뒤에 있어 앞 조건에서 먼저 걸린다", "두 조건에 모두 해당하는 값은 어느 갈래로 가야 하나요? 지금은 어디로 가나요?"),
    "slow_search_in_loop": ("timeout", "반복 안에서 처음부터 찾기", "반복마다 리스트 전체를 찾거나(in, count, index) 지운다", "입력이 100,000개라면 이 줄은 모두 몇 번쯤 실행될까요?"),
    "pop_front": ("timeout", "리스트 앞에서 꺼내기", "pop(0)이나 insert(0)은 뒤의 것을 모두 민다", "맨 앞 하나를 꺼내면 나머지 것들에는 무슨 일이 생기나요?"),
    "revisit": ("timeout", "방문 표시 없음", "갔던 곳을 다시 가서 끝나지 않거나 너무 오래 걸린다", "이미 갔던 곳에 다시 가지 않는다는 것을 코드의 어디서 확인하나요?"),
}

# 뜻이 겹쳐 같은 실수가 둘로 갈리는 함정 → 셀 때 합칠 대표 id(저장되는 id는 그대로). 같은 '<=를 <로' 실수가 두 id로 갈렸다
PITFALL_GROUPS = {"wrong_compare": "off_by_one", "grid_out": "index_range"}

# 기법 → 그 기법에서 자주 나오는 함정
PRONE_TO = {
    "count_map": ["key_missing", "exists_not_count", "leftover_unchecked", "slow_search_in_loop"],
    "seen_set": ["dedupe_all", "missed_case"],
    "lookup_map": ["key_missing", "pair_twice"],
    "stack": ["empty_pop", "count_not_order", "leftover_unchecked", "wrong_compare"],
    "queue": ["pop_front", "empty_pop"],
    "last_compare": ["empty_pop", "dedupe_all", "index_range"],
    "heap": ["empty_pop", "early_return"],
    "sort_scan": ["sort_as_text", "off_by_one", "index_range"],
    "sort_key": ["sort_as_text", "wrong_compare"],
    "single_scan": ["wrong_init", "wrong_compare", "no_normalize", "update_in_wrong_branch"],
    "double_loop": ["pair_twice", "off_by_one", "wrong_init", "early_return"],
    "all_cases": ["missed_case", "wrong_init"],
    "pattern_cycle": ["off_by_one", "index_range"],
    "greedy_sorted": ["wrong_compare", "early_return", "off_by_one"],
    "two_pointer": ["off_by_one", "wrong_compare"],
    "dp_table": ["wrong_init", "index_range", "off_by_one"],
    "bfs": ["revisit", "visit_on_pop", "pop_front", "grid_out"],
    "dfs": ["revisit", "no_return"],
    "binary_search": ["off_by_one", "wrong_compare"],
    "param_search": ["off_by_one", "wrong_compare"],
    "adjacency": ["key_missing", "missed_case"],
    "dijkstra": ["revisit", "wrong_init"],
    "monotonic_stack": ["empty_pop", "leftover_unchecked", "wrong_compare"],
    "union_find": ["wrong_init", "missed_case"],
    "sliding_window": ["off_by_one", "wrong_init", "index_range"],
    "prefix_sum": ["off_by_one", "index_range"],
    "string_build": ["str_immutable", "type_mix", "condition_order", "missed_case"],
    "digit_math": ["int_division", "wrong_init", "off_by_one"],
    "grid_move": ["grid_out", "index_range", "wrong_compare"],
    "rule_follow": ["condition_order", "missed_case", "off_by_one"],
}
GENERAL = ["missing_colon", "indent", "assign_vs_equal", "paren_mismatch", "undefined_name", "type_mix", "no_return", "early_return", "wrong_init"]  # 어느 문제에서나 나오는 것

# 유형 → 먼저 익히면 좋은 유형(선수 지식)
PREREQUISITE = {
    "simulation": ["implementation"], "brute_force": ["implementation"], "two_pointer": ["brute_force"],
    "stack_queue": ["brute_force"], "hash": ["brute_force"], "sort": ["brute_force"], "heap": ["sort", "stack_queue"],
    "greedy": ["sort"], "binary_search": ["sort"], "dfs": ["stack_queue"], "bfs": ["stack_queue"], "dp": ["brute_force"],
    "dijkstra": ["bfs", "heap"], "graph": ["dfs"],
}


# 구현 기술: id → (이름, 언제 필요한가, 이 문제와 상관없는 변수로 쓴 문법 예 한 줄). 알고리즘은 아는데 손이 안 움직일 때 쓰는 것이다.
# 문법 예는 사람이 써서 확인한 것이라 꼬리질문·디버그의 '같은 문법의 다른 예'에 그대로 쓴다(파이썬).
SKILLS = {
    "dict_count": ("딕셔너리로 개수 세기", "값마다 몇 번 나왔는지 셀 때", "fruit[name] = fruit.get(name, 0) + 1"),
    "dict_loop": ("딕셔너리 훑기", "키와 값을 함께 볼 때", "for name, count in fruit.items():"),
    "list_last": ("리스트의 마지막 것 보기·꺼내기", "방금 넣은 것과 비교하거나 되돌릴 때", "last = basket[-1]  # 꺼내려면 basket.pop()"),
    "list_empty": ("리스트가 비었는지 확인", "꺼내기 전에", "if len(basket) == 0:"),
    "range_pairs": ("겹치지 않게 두 개 고르는 이중 반복", "모든 쌍을 한 번씩 볼 때", "for i in range(len(scores)):\n    for j in range(i + 1, len(scores)):"),
    "swap": ("두 값 맞바꾸기", "큰 쪽·작은 쪽을 맞춰 놓을 때", "apple, pear = pear, apple"),
    "sort_key": ("기준을 정해 정렬", "길이·둘째 값 등으로 줄 세울 때", "words.sort(key=lambda word: len(word))"),
    "str_split_join": ("문자열 쪼개기와 합치기", "띄어쓰기·기호로 나뉜 글을 다룰 때", "parts = line.split(' ')  # 합치려면 '-'.join(parts)"),
    "str_build": ("글자를 하나씩 붙여 새 문자열 만들기", "글자마다 바꿔야 할 때", "result = ''\nfor ch in word:\n    result += ch.upper()"),
    "char_code": ("글자와 번호 바꾸기", "알파벳을 몇 칸 밀 때", "ord('a')  # 97, chr(98)은 'b'"),
    "digits": ("수를 자릿수로 나누기", "각 자리 숫자를 볼 때", "for d in str(number):\n    total += int(d)"),
    "div_mod": ("몫과 나머지", "나누어떨어지는지, 자리를 떼어 낼 때", "quotient = 17 // 5  # 3, 나머지는 17 % 5"),
    "time_convert": ("시간 글을 분으로 바꾸기", "'12:30' 같은 시간을 비교·계산할 때", "hour, minute = clock.split(':')\ntotal = int(hour) * 60 + int(minute)"),
    "grid_dirs": ("격자 방향 표", "상하좌우로 움직일 때", "for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:\n    nr, nc = r + dr, c + dc"),
    "grid_bounds": ("격자 범위 확인", "움직인 위치가 안쪽인지 볼 때", "if 0 <= nr < rows and 0 <= nc < cols:"),
    "set_use": ("집합으로 중복 없애기·있는지 보기", "종류 수를 세거나 본 적 있는지 볼 때", "seen = set(colors)  # 넣기는 seen.add('red'), 확인은 'red' in seen"),
    "deque_use": ("앞에서 빨리 꺼내기", "대기열처럼 앞에서 빼고 뒤에 넣을 때", "from collections import deque\nline = deque([1, 2, 3])\nfirst = line.popleft()"),
    "max_min_update": ("가장 큰 값 갱신", "하나씩 보며 최댓값을 구할 때", "if height > tallest:\n    tallest = height"),
    "early_stop": ("찾으면 바로 끝내기", "조건에 맞는 첫 번째를 찾을 때", "for name in guests:\n    if name == 'kim':\n        return name"),
    "two_d_list": ("2차원 리스트 다루기", "행과 열이 있는 값을 볼 때", "for row in table:\n    for value in row:"),
}

# 입력 크기 경험칙: (N이 이 값 이하이면, 쓸 수 있는 방법). 대략 1초에 1억 번 연산이 기준이다. 정밀한 계산이 아니라 방법을 좁히는 어림이다.
SIZE_RULES = (
    (10, "순서를 전부 만들어 보기(순열)도 된다"),
    (20, "고르는 방법을 전부 만들어 보기(부분집합 2^N)도 된다"),
    (500, "삼중 반복(N×N×N)도 된다"),
    (5_000, "이중 반복(N×N)이 된다"),
    (200_000, "이중 반복은 안 된다. 정렬·이분 탐색(N log N)이나 한 번 훑기(N)여야 한다"),
    (10**18, "한 번 훑기(N)여야 한다. 값의 범위 자체가 아주 크면 답을 정해 놓고 되는지 확인하는 방법을 떠올린다"),
)


def size_rule(size: int) -> str:
    """입력 크기에 맞는 경험칙 한 줄. 크기를 모르면(0) 빈 글."""
    if not size or size < 1:
        return ""
    return next(f"N이 {size:,} 정도면 {text}." for limit, text in SIZE_RULES if size <= limit)


def size_table() -> str:
    return "\n".join(f"- N ≤ {limit:,}: {text}" if limit < 10**18 else f"- 그보다 크면: {text}" for limit, text in SIZE_RULES)


def skill_list() -> str:
    return "\n".join(f"- {sid}: {name} ({when})" for sid, (name, when, _) in SKILLS.items())


def known_skills(ids) -> list[str]:
    return [sid for sid in ids or [] if sid in SKILLS]


def skill_examples(ids, limit: int = 3) -> list[str]:
    """구현 기술의 문법 예(이 문제와 상관없는 변수로 쓴 것). 꼬리질문과 디버그가 문법을 보여 줄 때 참고한다."""
    return [f"- {SKILLS[sid][0]}: {SKILLS[sid][2]}" for sid in known_skills(ids)[:limit]]


def pattern_list() -> str:
    """계획 프롬프트에 넣는 패턴 목록(작아서 전부 넣는다. 검색이 필요 없다)."""
    return "\n".join(f"- {pid}: {cue}" for pid, (cue, _, _, _) in PATTERNS.items())


def technique_list() -> str:
    """분석 프롬프트에 넣는 기법 목록(문제의 태그는 이 낱말만 쓴다. 모델이 새 낱말을 짓지 못한다)."""
    return "\n".join(f"- {tid}: {name}" for tid, (_, name, _) in TECHNIQUES.items())


def known_techniques(ids) -> list[str]:
    return list(dict.fromkeys(tid for tid in ids or [] if tid in TECHNIQUES))


def known_patterns(ids) -> list[str]:
    return [pid for pid in ids or [] if pid in PATTERNS]


def techniques_of(pattern_ids) -> list[str]:
    seen = []
    for pid in known_patterns(pattern_ids):
        tech = PATTERNS[pid][1]
        if tech not in seen:
            seen.append(tech)
    return seen


def pitfall_candidates(pattern_ids, frequent=(), limit: int = 14) -> list[str]:
    """디버그 진단 후보: 이 사용자가 자주 밟은 것 → 문제의 기법에 딸린 것 → 어느 문제에나 나오는 것."""
    out = []
    for pid in [*frequent, *(p for t in techniques_of(pattern_ids) for p in PRONE_TO.get(t, [])), *GENERAL]:
        if pid in PITFALLS and pid not in out:
            out.append(pid)
    return out[:limit]


def pitfall_lines(ids) -> list[str]:
    return [f"- {pid}: {PITFALLS[pid][1]} — {PITFALLS[pid][2]}" for pid in ids if pid in PITFALLS]


def has_term(term: str, text: str) -> bool:
    """영어 낱말은 낱말 경계로(set이 reset에 걸리지 않게), 한글은 부분 일치로."""
    if re.fullmatch(r"[A-Za-z]+", term):
        return re.search(rf"(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", text or "") is not None
    return term in (text or "")


def hidden_terms(pattern_ids, known: str = "") -> list[str]:
    """의자가 먼저 꺼내면 안 되는 낱말(이 문제의 기법 이름). known(문제 글, 지금까지의 대화)에 이미 나온 낱말은 뺀다.

    지난 평가 기록으로 재 보면 평가기가 잡은 의자 유출 21건 중 4건만 이 규칙에 걸린다(뜻으로 새는 것이 더 많다). 보조 수단이다.
    """
    terms = []
    for tech in techniques_of(pattern_ids):
        for word in TECHNIQUES[tech][2]:
            if word not in terms and not has_term(word, known):
                terms.append(word)
    return terms


def pattern_context(pattern_ids) -> list[str]:
    """계획 초안에 넣을 1-hop 문맥: 단서 → 기법(왜) → 초보자가 자주 틀리는 것."""
    lines = []
    for pid in known_patterns(pattern_ids):
        cue, tech, why, seed = PATTERNS[pid]
        falls = ", ".join(PITFALLS[p][1] for p in PRONE_TO.get(tech, [])[:3])
        lines.append(f"- 단서 '{cue}' → {TECHNIQUES[tech][1]}: {why}. 질문 씨앗: {seed} 자주 틀리는 것: {falls}")
    return lines
