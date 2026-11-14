# 틀린 까닭: 점화식은 맞지만 메모하는 재귀(lru_cache)로 써서, 축제가 10만 일이면 재귀 깊이 오류가 난다
from functools import lru_cache


def solution(pay):
    @lru_cache(maxsize=None)
    def best(i):  # 0 ~ i번째 날만 보고 골랐을 때의 최댓값
        if i < 0:
            return 0
        return max(best(i - 1), best(i - 2) + pay[i])

    return best(len(pay) - 1)
