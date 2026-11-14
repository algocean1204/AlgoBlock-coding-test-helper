# 틀린 까닭: 처음에 한 번만 정렬하고 앞에서부터 차례로 합친다(합쳐 만든 눈덩이가 다음에 가장 가볍다고 본다)
def solution(snowballs):
    balls = sorted(snowballs)
    total = 0
    current = balls[0]
    for weight in balls[1:]:
        current += weight
        total += current
    return total
