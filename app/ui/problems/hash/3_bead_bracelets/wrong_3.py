# 틀린 까닭: 구슬 색을 정렬한 문자열을 키로 써서, 색의 개수만 같은 팔찌를 같은 디자인으로 묶는다
def solution(bracelets):
    count = {}
    for beads in bracelets:
        key = "".join(sorted(beads))
        count[key] = count.get(key, 0) + 1
    return max(count.values())
