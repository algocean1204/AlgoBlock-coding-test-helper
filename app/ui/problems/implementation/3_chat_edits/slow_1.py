# 느린 까닭: 기록을 하나 읽을 때마다 지금까지의 메시지로 보이는 줄 전체를 처음부터 다시 만든다(기록이 6만 개면 6만 × 메시지 수)
def solution(records):
    messages = []  # [번호, 보낸이, 내용, 고쳤는가]
    lines = []
    for record in records:
        words = record.split(" ")
        if words[0] == "SEND":
            messages.append([words[1], words[2], words[3], False])
        elif words[0] == "EDIT":
            for message in messages:
                if message[0] == words[1]:
                    message[2] = words[2]
                    message[3] = True
        else:
            messages = [message for message in messages if message[0] != words[1]]
        lines = []
        last = ""
        for number, who, content, edited in messages:
            shown = content + ("*" if edited else "")
            if lines and last == who:
                lines[-1] += " " + shown
            else:
                lines.append(who + ": " + shown)
                last = who
    return lines
