def keeps(people, close, gap):
    """people이 모두 올 때, 0부터 close까지 아무도 없는 시간이 이어지는 구간마다 길이가 gap 이하인가."""
    covered = 0  # 0부터 여기까지는 확인했다
    for arrive, leave in sorted(people):
        if arrive - covered > gap:
            return False
        covered = max(covered, leave)
    return close - covered <= gap


def solution(helpers, close, gap):
    # 약속이 0인 사람을 부르는 모든 경우를 보고, 조건을 지키는 것 가운데 가장 적게 부른 수
    promised = [(a, l) for a, l, p in helpers if p == 1]
    others = [(a, l) for a, l, p in helpers if p == 0]
    best = -1
    for mask in range(1 << len(others)):
        chosen = [others[k] for k in range(len(others)) if mask >> k & 1]
        if keeps(promised + chosen, close, gap) and (best == -1 or len(chosen) < best):
            best = len(chosen)
    return best
