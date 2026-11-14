# 틀린 까닭: 여러 번 고친 메시지에 마지막이 아니라 처음 고친 내용을 쓴다
def solution(records):
    order, sender, text, edited, deleted = [], {}, {}, {}, set()
    for record in records:
        words = record.split(" ")
        number = words[1]
        if words[0] == "SEND":
            order.append(number)
            sender[number], text[number], edited[number] = words[2], words[3], False
        elif words[0] == "EDIT":
            if not edited[number]:
                text[number] = words[2]
            edited[number] = True
        else:
            deleted.add(number)
    lines, last = [], ""
    for number in order:
        if number in deleted:
            continue
        shown = text[number] + ("*" if edited[number] else "")
        if lines and last == sender[number]:
            lines[-1] += " " + shown
        else:
            lines.append(sender[number] + ": " + shown)
            last = sender[number]
    return lines
