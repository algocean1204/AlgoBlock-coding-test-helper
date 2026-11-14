function solution(records) {
    // 첫 번째 훑기: 메시지마다 마지막 상태(보낸이, 마지막 내용, 고친 적 있는가, 지워졌는가)를 모은다
    const order = [];
    const sender = new Map();
    const text = new Map();
    const edited = new Set();
    const deleted = new Set();
    for (const record of records) {
        const words = record.split(" ");
        const number = words[1];
        if (words[0] === "SEND") {
            order.push(number);
            sender.set(number, words[2]);
            text.set(number, words[3]);
        } else if (words[0] === "EDIT") {
            text.set(number, words[2]);
            edited.add(number);
        } else {
            deleted.add(number);
        }
    }

    // 두 번째 훑기: 남은 메시지를 보낸 순서대로 보며, 바로 앞 줄과 보낸이가 같으면 그 줄에 붙인다
    const lines = [];
    let lineSender = "";
    for (const number of order) {
        if (deleted.has(number)) {
            continue;
        }
        const shown = text.get(number) + (edited.has(number) ? "*" : "");
        if (lines.length > 0 && lineSender === sender.get(number)) {
            lines[lines.length - 1] += " " + shown;
        } else {
            lines.push(sender.get(number) + ": " + shown);
            lineSender = sender.get(number);
        }
    }
    return lines;
}
