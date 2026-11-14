def solution(sticks):
    count = 0
    n = len(sticks)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                short, middle, longest = sorted([sticks[i], sticks[j], sticks[k]])
                if longest < short + middle:
                    count += 1
    return count
