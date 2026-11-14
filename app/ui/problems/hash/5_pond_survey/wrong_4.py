# 틀린 까닭: 없던 종이 0마리로 적혀도 그 종의 구역 수를 줄인다(있음 → 없음일 때만 줄여야 한다)
def solution(log):
    count, zones_of, answers = {}, {}, []
    for line in log:
        words = line.split()
        if words[0] == "see":
            zone, kind, n = words[1], words[2], int(words[3])
            count.setdefault(zone, {})
            before = count[zone].get(kind, 0)
            if before == 0 and n > 0:
                zones_of[kind] = zones_of.get(kind, 0) + 1
            if n == 0:
                zones_of[kind] = zones_of.get(kind, 0) - 1
                count[zone].pop(kind, None)
            else:
                count[zone][kind] = n
        elif words[0] == "zone":
            answers.append(len(count.get(words[1], {})))
        else:
            answers.append(zones_of.get(words[1], 0))
    return answers
