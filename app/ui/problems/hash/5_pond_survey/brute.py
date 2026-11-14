def solution(log):
    # 글의 정의를 그대로: 질문마다 그때까지의 장부를 처음부터 다시 읽는다
    answers = []
    for i, line in enumerate(log):
        words = line.split()
        if words[0] == "see":
            continue
        latest = {}  # (구역, 종) → 마지막으로 적힌 마릿수
        for before in log[:i]:
            w = before.split()
            if w[0] == "see":
                latest[(w[1], w[2])] = int(w[3])
        if words[0] == "zone":
            answers.append(sum(1 for (zone, kind), n in latest.items() if zone == words[1] and n >= 1))
        else:
            answers.append(sum(1 for (zone, kind), n in latest.items() if kind == words[1] and n >= 1))
    return answers
