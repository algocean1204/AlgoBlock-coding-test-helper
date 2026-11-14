def views_of(beads):
    """돌리고 뒤집어 읽을 수 있는 모든 문자열."""
    found = set()
    for text in (beads, beads[::-1]):
        for start in range(len(text)):
            found.add(text[start:] + text[:start])
    return found


def solution(bracelets):
    # 팔찌마다 디자인이 같은 팔찌(자기 자신 포함)를 모두 맞대어 세고, 가장 큰 수를 고른다
    best = 0
    for one in bracelets:
        mine = views_of(one)
        same = sum(1 for other in bracelets if other in mine)
        best = max(best, same)
    return best
