def solution(bracelets):
    count = {}  # 대표 키 → 그 디자인의 팔찌 수
    for beads in bracelets:
        flipped = beads[::-1]  # 반대 방향으로 읽은 것
        views = []  # 이 팔찌가 적힐 수 있는 모든 모습
        for start in range(len(beads)):
            views.append(beads[start:] + beads[:start])  # start번째 구슬부터 같은 방향으로
            views.append(flipped[start:] + flipped[:start])  # 뒤집어서 start번째 구슬부터
        key = min(views)  # 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
        count[key] = count.get(key, 0) + 1
    return max(count.values())
