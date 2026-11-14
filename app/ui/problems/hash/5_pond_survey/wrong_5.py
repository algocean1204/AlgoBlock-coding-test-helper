# 틀린 까닭: 종의 구역 수를 한 번이라도 적힌 구역의 수로 센다(지금 0마리인 구역까지 센다)
def solution(log):
    count, seen_in, answers = {}, {}, []
    for line in log:
        words = line.split()
        if words[0] == "see":
            zone, kind, n = words[1], words[2], int(words[3])
            count.setdefault(zone, {})
            seen_in.setdefault(kind, set()).add(zone)
            if n > 0:
                count[zone][kind] = n
            else:
                count[zone].pop(kind, None)
        elif words[0] == "zone":
            answers.append(len(count.get(words[1], {})))
        else:
            answers.append(len(seen_in.get(words[1], ())))
    return answers
