# 틀린 까닭: 다 센 뒤에 k번 이상 빌려진 책을 처음 나온 순서대로 담는다(꽂힌 순서는 k번째로 빌려진 때의 순서다)
def solution(loans, k):
    count = {}
    for title in loans:
        count[title] = count.get(title, 0) + 1
    shelf = []
    for title in count:  # 딕셔너리는 처음 넣은 순서대로 돈다
        if count[title] >= k:
            shelf.append(title)
    return shelf
