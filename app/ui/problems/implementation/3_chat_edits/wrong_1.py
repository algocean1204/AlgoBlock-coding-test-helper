# 틀린 까닭: 고친 내용이 처음 내용과 다를 때만 *를 붙인다(EDIT 기록이 한 번이라도 있었으면 붙여야 한다)
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
    first = {}
    for record in records:
        words = record.split(" ")
        if words[0] == "SEND":
            first[words[1]] = words[3]
    order, sender, text, edited, deleted = final_state(records)
    lines, last = [], ""
    for number in order:
        if number in deleted:
            continue
        shown = text[number] + ("*" if text[number] != first[number] else "")
        if lines and last == sender[number]:
            lines[-1] += " " + shown
        else:
            lines.append(sender[number] + ": " + shown)
            last = sender[number]
    return lines
