# 틀린 까닭: 가장 큰 묶음의 크기가 아니라 서로 다른 디자인의 수를 센다
def solution(bracelets):
    count = {}
    for beads in bracelets:
        flipped = beads[::-1]
        views = []
        for start in range(len(beads)):
            views.append(beads[start:] + beads[:start])
            views.append(flipped[start:] + flipped[:start])
        key = min(views)
        count[key] = count.get(key, 0) + 1
    return len(count)
