# 느린 까닭: 시작하는 날마다 끝나는 날을 하나씩 늘리며 더해 본다(음수가 있어 중간에 멈출 수도 없다. 약 50억 번)
def solution(profits, target):
    count = 0
    for start in range(len(profits)):
        total = 0
        for end in range(start, len(profits)):
            total += profits[end]
            if total == target:
                count += 1
    return count
