def solution(rows, apples, k):
    # 글의 정의를 그대로: 줄마다 남은 무게 가운데 가장 무거운 것을 하나씩 골라 적는다(정렬 함수를 쓰지 않는다)
    answer = []
    for row in range(1, rows + 1):
        left = [weight for r, weight in apples if r == row]
        written = []
        while left:
            heaviest = max(left)
            written.append(heaviest)
            left = [weight for weight in left if weight != heaviest]  # 같은 무게는 한 번만 적는다
        answer.append(written[k - 1] if len(written) >= k else -1)
    return answer
