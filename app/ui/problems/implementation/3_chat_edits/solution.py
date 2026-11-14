def solution(records):
    # 첫 번째 훑기: 메시지마다 마지막 상태(보낸이, 마지막 내용, 고친 적 있는가, 지워졌는가)를 모은다
    order = []  # SEND 기록의 순서대로 메시지 번호
    sender = {}
    text = {}
    edited = {}
    deleted = {}
    for record in records:
        words = record.split(" ")
        number = words[1]
        if words[0] == "SEND":
            order.append(number)
            sender[number] = words[2]
            text[number] = words[3]
            edited[number] = False
            deleted[number] = False
        elif words[0] == "EDIT":
            text[number] = words[2]
            edited[number] = True
        else:
            deleted[number] = True

    # 두 번째 훑기: 남은 메시지를 보낸 순서대로 보며, 바로 앞 줄과 보낸이가 같으면 그 줄에 붙인다
    lines = []
    line_sender = ""
    for number in order:
        if deleted[number]:
            continue
        shown = text[number]
        if edited[number]:
            shown += "*"
        if len(lines) > 0 and line_sender == sender[number]:
            lines[-1] += " " + shown
        else:
            lines.append(sender[number] + ": " + shown)
            line_sender = sender[number]
    return lines
