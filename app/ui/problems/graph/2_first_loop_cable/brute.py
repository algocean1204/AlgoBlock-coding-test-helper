def solution(cables):
    groups = []  # 신호가 오가는 장비끼리 모은 집합들
    for order, (x, y) in enumerate(cables, 1):
        group_x = None
        group_y = None
        for group in groups:
            if x in group:
                group_x = group
            if y in group:
                group_y = group
        if group_x is not None and group_x is group_y:
            return order
        merged = {x, y}
        for group in (group_x, group_y):
            if group is not None:
                merged |= group
                groups.remove(group)
        groups.append(merged)
    return -1
