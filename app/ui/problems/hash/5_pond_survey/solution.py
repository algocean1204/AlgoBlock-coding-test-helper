def solution(log):
    count = {}  # 구역 → {종 → 마릿수}. 1마리 이상인 종만 둔다
    zones_of = {}  # 종 → 그 종이 1마리 이상 있는 구역 수
    answers = []
    for line in log:
        words = line.split()
        if words[0] == "see":
            zone, kind, n = words[1], words[2], int(words[3])
            if zone not in count:
                count[zone] = {}
            before = count[zone].get(kind, 0)  # 덮어쓰기 전에 지금 값을 본다
            # 종의 구역 수는 없음 → 있음, 있음 → 없음으로 바뀔 때만 달라진다
            if before == 0 and n > 0:
                zones_of[kind] = zones_of.get(kind, 0) + 1
            if before > 0 and n == 0:
                zones_of[kind] -= 1
            if n > 0:
                count[zone][kind] = n  # 더하지 않고 바꾼다
            elif kind in count[zone]:
                del count[zone][kind]  # 0마리는 지운다: 구역의 종 수 = 안쪽 표의 크기
        elif words[0] == "zone":
            answers.append(len(count.get(words[1], {})))
        else:  # "kind 종"
            answers.append(zones_of.get(words[1], 0))
    return answers
