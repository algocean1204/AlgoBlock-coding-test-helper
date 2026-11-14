# 느린 까닭: 팔찌마다 이미 본 디자인의 대표를 하나씩 맞대어 본다(팔찌 수 × 디자인 수)
def solution(bracelets):
    groups = []  # [대표 팔찌, 그 디자인의 팔찌 수]
    for beads in bracelets:
        flipped = beads[::-1]
        mine = set()
        for start in range(len(beads)):
            mine.add(beads[start:] + beads[:start])
            mine.add(flipped[start:] + flipped[:start])
        for group in groups:
            if group[0] in mine:
                group[1] += 1
                break
        else:
            groups.append([beads, 1])
    return max(group[1] for group in groups)
