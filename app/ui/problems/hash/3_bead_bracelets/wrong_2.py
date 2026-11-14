# 틀린 까닭: 뒤집은 문자열 하나만 더 보고, 뒤집은 것을 돌린 모습은 보지 않는다
def solution(bracelets):
    count = {}
    for beads in bracelets:
        views = [beads[start:] + beads[:start] for start in range(len(beads))]
        views.append(beads[::-1])
        key = min(views)
        count[key] = count.get(key, 0) + 1
    return max(count.values())
