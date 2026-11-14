from functools import cmp_to_key


def solution(fix, line, walk):
    def compare(a, b):
        # a 다음에 b를 고치면, b의 손님은 a를 고치고 걸어오는 동안 더 기다린다: (fix[a] + walk) × line[b]
        # b 다음에 a를 고치면, a의 손님이 그만큼 더 기다린다: (fix[b] + walk) × line[a]
        # 나머지 손님이 기다리는 시간은 어느 쪽이든 같다 → 이 둘만 견주어 작은 쪽 차례를 고른다(음수면 a가 먼저)
        return (fix[a] + walk) * line[b] - (fix[b] + walk) * line[a]

    order = sorted(range(len(fix)), key=cmp_to_key(compare))

    now = 0  # 지금 시각
    total = 0  # 기다림의 합
    for k, ride in enumerate(order):
        if k > 0:
            now += walk  # 다음 놀이기구까지 걸어간다(첫 놀이기구는 걷지 않는다)
        now += fix[ride]  # 이 놀이기구를 다 고친 시각
        total += now * line[ride]  # 이 줄의 손님은 모두 지금까지 기다렸다
    return total
