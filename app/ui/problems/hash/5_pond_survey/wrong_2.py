# 틀린 까닭: 0마리가 된 종을 표에서 지우지 않아, 구역의 종 수에 사라진 종까지 센다
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
            answers.append(len(count.get(words[1], {})))
        else:
            answers.append(zones_of.get(words[1], 0))
    return answers
