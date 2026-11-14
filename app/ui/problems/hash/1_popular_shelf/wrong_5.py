# 틀린 까닭: 처음 보는 제목도 딕셔너리에 있는 것처럼 바로 1을 더해(count[title] += 1) 없는 키에서 KeyError가 난다
def solution(loans, k):
    count = {}
    shelf = []
    for title in loans:
        count[title] += 1
        if count[title] == k:
            shelf.append(title)
    return shelf
