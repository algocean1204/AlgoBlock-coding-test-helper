# 느린 까닭: 0마리도 표에 남겨 두고, 구역을 물을 때마다 그 구역의 모든 종을 훑어 1마리 이상인 것을 센다
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
            if before > 0 and n == 0:
                zones_of[kind] -= 1
            count[zone][kind] = n
        elif words[0] == "zone":
            answers.append(sum(1 for n in count.get(words[1], {}).values() if n > 0))
        else:
            answers.append(zones_of.get(words[1], 0))
    return answers
