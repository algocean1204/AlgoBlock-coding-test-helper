# 틀린 까닭: 위와 왼쪽 칸만 보고 새 웅덩이인지 정한다(ㄷ자처럼 아래쪽에서 이어지는 모양을 여러 개로 센다)
def solution(floor):
    count = 0
    for r in range(len(floor)):
        for c in range(len(floor[0])):
            if floor[r][c] != '#':
                continue
            up = r > 0 and floor[r - 1][c] == '#'
            left = c > 0 and floor[r][c - 1] == '#'
            if not up and not left:
                count += 1
    return count
