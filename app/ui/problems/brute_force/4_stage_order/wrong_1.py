# 틀린 까닭: 팀을 서로 다르게 보고 순서를 세어 같은 순서표를 여러 번 센다
def solution(genres):
    used = [False] * len(genres)

    def place(count, last):
        if count == len(genres):
            return 1
        ways = 0
        for i in range(len(genres)):
            if used[i] or genres[i] == last:
                continue
            used[i] = True
            ways += place(count + 1, genres[i])
            used[i] = False
        return ways

    return place(0, None)
