# 틀린 까닭: 보낸이가 같은 메시지를 이어지지 않아도 모두 한 줄로 묶는다(보낸이가 처음 보인 순서대로)
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
    line_of = {}
    for number in order:
        if number in deleted:
            continue
        shown = text[number] + ("*" if edited[number] else "")
        if sender[number] in line_of:
            line_of[sender[number]] += " " + shown
        else:
            line_of[sender[number]] = sender[number] + ": " + shown
    return list(line_of.values())
