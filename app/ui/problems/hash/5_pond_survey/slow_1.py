# 느린 까닭: 종을 물을 때마다 모든 구역을 훑어 그 종이 있는지 본다(구역이 수만 곳이면 질문 수 × 구역 수)
def solution(log):
    count, answers = {}, []
    for line in log:
        words = line.split()
        if words[0] == "see":
            zone, kind, n = words[1], words[2], int(words[3])
            count.setdefault(zone, {})
            if n > 0:
                count[zone][kind] = n
            else:
                count[zone].pop(kind, None)
        elif words[0] == "zone":
            answers.append(len(count.get(words[1], {})))
        else:
            answers.append(sum(1 for zone in count if words[1] in count[zone]))
    return answers
