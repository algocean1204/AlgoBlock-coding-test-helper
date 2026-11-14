# 틀린 까닭: 다시 센 마릿수를 덮어쓰지 않고 지금 값에 더한다
def solution(log):
    count, zones_of, answers = {}, {}, []
    for line in log:
        words = line.split()
        if words[0] == "see":
            zone, kind, n = words[1], words[2], int(words[3])
            count.setdefault(zone, {})
            before = count[zone].get(kind, 0)
            after = before + n
            if before == 0 and after > 0:
                zones_of[kind] = zones_of.get(kind, 0) + 1
            if after > 0:
                count[zone][kind] = after
        elif words[0] == "zone":
            answers.append(len(count.get(words[1], {})))
        else:
            answers.append(zones_of.get(words[1], 0))
    return answers
