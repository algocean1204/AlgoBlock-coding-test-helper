# 느린 까닭: 정렬은 했지만 경계를 앞에서부터 한 칸씩 걸어가며 찾는다(검색마다 배열의 상당 부분을 걷는다)
def solution(prices, ranges):
    prices = sorted(prices)
    answer = []
    for low, high in ranges:
        i = 0
        while i < len(prices) and prices[i] < low:
            i += 1
        count = 0
        while i < len(prices) and prices[i] <= high:
            count += 1
            i += 1
        answer.append(count)
    return answer
