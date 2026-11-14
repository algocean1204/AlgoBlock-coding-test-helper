def solution(profits, target):
    count = 0
    for start in range(len(profits)):
        for end in range(start, len(profits)):
            if sum(profits[start:end + 1]) == target:
                count += 1
    return count
