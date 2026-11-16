# 언어 함정: python.missing_key @ "제목이 같으면 같은 책입니다"
def solution(loans, k):
    count = {}  # 제목마다 지금까지 빌려진 횟수
    shelf = []  # 추천 서가에 꽂힌 차례대로
    for title in loans:
        count[title] += 1
        if count[title] == k:  # 바로 지금 k번째로 빌려졌다(k보다 커진 뒤에는 다시 같아지지 않는다)
            shelf.append(title)
    return shelf
