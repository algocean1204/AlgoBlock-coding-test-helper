# 느린 까닭: 질문마다 열린 역만으로 다익스트라를 새로 돌린다(질문 5만 개 × 선로 10,000개)
import heapq


def solution(n, tracks, queries):
    linked = [[] for _ in range(n + 1)]
    for a, b, minutes in tracks:
        linked[a].append((b, minutes))
        linked[b].append((a, minutes))
    answer = []
    for k, a, b in queries:
        INF = float("inf")
        dist = [INF] * (k + 1)
        dist[a] = 0
        heap = [(0, a)]
        while heap:
            spent, station = heapq.heappop(heap)
            if spent > dist[station]:
                continue
            if station == b:
                break
            for other, minutes in linked[station]:
                if other <= k and spent + minutes < dist[other]:
                    dist[other] = spent + minutes
                    heapq.heappush(heap, (spent + minutes, other))
        answer.append(dist[b] if dist[b] != INF else -1)
    return answer
