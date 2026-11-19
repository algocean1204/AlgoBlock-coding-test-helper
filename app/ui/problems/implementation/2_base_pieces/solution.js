const DIGITS = "0123456789ABCDEF";

function toBase(reading, base) {
    // 나머지를 끝 자리부터 모은 뒤 뒤집는다
    let reversed = "";
    while (reading > 0) {
        reversed += DIGITS[reading % base];
        reading = Math.floor(reading / base);
    }
    return reversed.split("").reverse().join("");
}

function readBase(text, base) {
    // 앞자리부터 값 = 값 × base + 자리값
    let value = 0;
    for (const ch of text) {
        value = value * base + DIGITS.indexOf(ch);
    }
    return value;
}

function solution(base, reading) {
    const text = toBase(reading, base);

    // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
    const pieces = [text[0]];
    for (let i = 1; i < text.length; i++) {
        if (DIGITS.indexOf(text[i]) < DIGITS.indexOf(text[i - 1])) {
            pieces.push(text[i]);
        } else {
            pieces[pieces.length - 1] += text[i];
        }
    }
    let largest = 0;
    for (const piece of pieces) {
        const value = readBase(piece, base);
        if (value > largest) largest = value;
    }
    return [pieces.length, largest];
}
