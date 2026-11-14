# 틀린 까닭: 양수 돌은 모두 밟고 음수 돌은 모두 건너뛴다(음수 돌이 jump개 넘게 이어지면 건너뛸 수 없다)
def solution(scores, jump):
    if len(scores) == 1:
        return scores[0]
    total = scores[0] + scores[-1]
    for score in scores[1:-1]:
        if score > 0:
            total += score
    return total
