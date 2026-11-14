def solution(pickup, minutes, booked):
    n = len(pickup)
    must = 0
    for i in booked:
        must |= 1 << i
    # can[mask]: mask에 든 주문만 받아 어떤 순서로 만들면 모두 지킬 수 있는가.
    # 그 순서에서 마지막으로 만드는 주문을 하나씩 다 골라 본다(나머지는 그보다 먼저 만든다).
    can = [False] * (1 << n)
    can[0] = True
    best = None  # (받는 주문 수, 모두 다 만드는 시각)
    for mask in range(1 << n):
        finish = sum(minutes[i] for i in range(n) if mask >> i & 1)  # 쉬지 않고 만들면 마지막 꽃다발이 끝나는 시각
        if mask:
            for last in range(n):
                if mask >> last & 1 and can[mask ^ (1 << last)] and finish <= pickup[last]:
                    can[mask] = True
                    break
        if can[mask] and mask & must == must:
            size = bin(mask).count("1")
            if best is None or size > best[0] or (size == best[0] and finish < best[1]):
                best = (size, finish)
    if best is None:
        return [-1, -1]
    return [best[0], best[1]]
