def solution(loans, k):
    # 제목마다 k번째로 나온 위치를 찾고, 그 위치가 이른 차례로 늘어놓는다
    found = []  # (k번째로 나온 위치, 제목)
    titles = sorted(set(loans))
    for title in titles:
        seen = 0
        for i in range(len(loans)):
            if loans[i] == title:
                seen += 1
                if seen == k:
                    found.append((i, title))
                    break
    found.sort()
    return [title for _, title in found]
