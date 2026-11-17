# 언어 함정: python.missing_key
def solution(genres):
    left = {}
    for genre in genres:
        left[genre] += 1

    def place(remaining, last):
        if remaining == 0:
            return 1
        ways = 0
        for genre in left:
            if left[genre] == 0 or genre == last:
                continue
            left[genre] -= 1
            ways += place(remaining - 1, genre)
            left[genre] += 1
        return ways

    return place(len(genres), None)
