# 틀린 까닭: 돌린 모습만 보고 뒤집은 모습을 빠뜨린다
def solution(bracelets):
    count = {}
    for beads in bracelets:
        key = min(beads[start:] + beads[:start] for start in range(len(beads)))
        count[key] = count.get(key, 0) + 1
    return max(count.values())
