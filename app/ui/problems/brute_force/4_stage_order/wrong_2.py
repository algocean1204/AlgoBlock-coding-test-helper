# 틀린 까닭: 남은 개수에서 하나를 꺼내 써 본 뒤 되돌려 놓지 않는다(앞 가지에서 쓴 팀이 다음 가지에서 사라진다)
def solution(genres):
    left = {}
    for genre in genres:
        left[genre] = left.get(genre, 0) + 1

    def place(remaining, last):
        if remaining == 0:
            return 1
        ways = 0
        for genre in left:
            if left[genre] == 0 or genre == last:
                continue
            left[genre] -= 1
            ways += place(remaining - 1, genre)
        return ways

    return place(len(genres), None)
