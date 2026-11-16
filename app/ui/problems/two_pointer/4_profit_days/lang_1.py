# 언어 함정: python.missing_key
def solution(profits, target):
    # seen[s]: 지금까지 나온 누적 합 가운데 값이 s인 것의 개수
    # 아무 날도 더하지 않은 누적 합 0을 한 번 넣어 두어야 첫째 날부터 시작하는 기간도 센다
    seen = {0: 1}
    total = 0
    count = 0
    for profit in profits:
        total += profit
        # 앞쪽 누적 합이 total - target이었다면, 그다음 날부터 오늘까지의 합이 target이다
        count += seen.get(total - target, 0)
        seen[total] += 1
    return count
