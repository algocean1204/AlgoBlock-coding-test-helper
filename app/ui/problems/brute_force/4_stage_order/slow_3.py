# 느린 까닭: 같은 장르를 개수로 묶어 서로 다른 순서표를 한 번씩 만들지만, 이웃 조건은 다 놓은 뒤에야 확인한다(8, 8, 7팀이면 약 31억 가지를 끝까지 만든다)
def solution(genres):
    left = {}
    for genre in genres:
        left[genre] = left.get(genre, 0) + 1
    order = []

    def place():
        if len(order) == len(genres):
            for i in range(len(order) - 1):
                if order[i] == order[i + 1]:
                    return 0
            return 1
        ways = 0
        for genre in left:
            if left[genre] == 0:
                continue
            left[genre] -= 1
            order.append(genre)
            ways += place()
            order.pop()
            left[genre] += 1
        return ways

    return place()
