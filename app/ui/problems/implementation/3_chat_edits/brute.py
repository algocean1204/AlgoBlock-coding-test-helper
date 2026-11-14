from itertools import groupby


def solution(records):
    # 글의 정의를 그대로: SEND 기록마다 그 뒤의 기록을 모두 훑어 그 메시지가 고쳐졌는지·지워졌는지 찾는다
    visible = []  # (보낸이, 보이는 내용)
    for i, record in enumerate(records):
        words = record.split()
        if words[0] != "SEND":
            continue
        number, who, content = words[1], words[2], words[3]
        star, gone = "", False
        for later in records[i + 1:]:
            parts = later.split()
            if parts[1] != number:
                continue
            if parts[0] == "EDIT":
                content, star = parts[2], "*"
            elif parts[0] == "DELETE":
                gone = True
        if not gone:
            visible.append((who, content + star))
    # 보이는 메시지를 보낸이가 바로 이어지는 덩어리로 묶는다
    return [who + ": " + " ".join(shown for _, shown in group) for who, group in groupby(visible, key=lambda pair: pair[0])]
