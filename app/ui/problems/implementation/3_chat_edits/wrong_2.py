# 틀린 까닭: 지워진 메시지를 빼기 전에 보낸이가 이어지는지 판단해, 지워진 메시지 양쪽의 같은 보낸이를 따로 둔다
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
    lines, last = [], ""
    for number in order:
        shown = text[number] + ("*" if edited[number] else "")
        if lines and last == sender[number]:
            if number not in deleted:
                lines[-1].append(shown)
        else:
            lines.append([sender[number] + ":"] + ([shown] if number not in deleted else []))
            last = sender[number]
    return [" ".join(line) for line in lines if len(line) > 1]
