def solution(gaps, k):
    stations = len(gaps) + 1
    count = 0
    for a in range(stations):
        for b in range(a + 1, stations):
            if sum(gaps[a:b]) == k:
                count += 1
    return count
