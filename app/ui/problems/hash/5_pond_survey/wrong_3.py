# 틀린 까닭: 이미 있던 종을 다시 셀 때마다 그 종의 구역 수를 늘린다(없음 → 있음일 때만 늘려야 한다)
def solution(log):
    count, zones_of, answers = {}, {}, []
    for line in log:
        words = line.split()
        if words[0] == "see":
            zone, kind, n = words[1], words[2], int(words[3])
            count.setdefault(zone, {})
            before = count[zone].get(kind, 0)
            if n > 0:
                zones_of[kind] = zones_of.get(kind, 0) + 1
                count[zone][kind] = n
            elif before > 0:
                zones_of[kind] -= 1
                del count[zone][kind]
        elif words[0] == "zone":
            answers.append(len(count.get(words[1], {})))
        else:
            answers.append(zones_of.get(words[1], 0))
    return answers
