# 틀린 까닭: *를 메시지마다가 아니라, 고친 메시지가 든 줄의 끝에 한 번만 붙인다
def final_state(records):
    order, sender, text, edited, deleted = [], {}, {}, {}, set()
    for record in records:
        words = record.split(" ")
        number = words[1]
        if words[0] == "SEND":
            order.append(number)
            sender[number], text[number], edited[number] = words[2], words[3], False
        elif words[0] == "EDIT":
            text[number], edited[number] = words[2], True
        else:
            deleted.add(number)
    return order, sender, text, edited, deleted


def solution(records):
    order, sender, text, edited, deleted = final_state(records)
    lines, marks, last = [], [], ""
    for number in order:
        if number in deleted:
            continue
        if lines and last == sender[number]:
            lines[-1] += " " + text[number]
            marks[-1] = marks[-1] or edited[number]
        else:
            lines.append(sender[number] + ": " + text[number])
            marks.append(edited[number])
            last = sender[number]
    return [line + ("*" if mark else "") for line, mark in zip(lines, marks)]
