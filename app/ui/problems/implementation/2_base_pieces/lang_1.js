// 언어 함정: javascript.float_division @ "그 몫을 다시 base로 나눈"
function solution(base, reading) {
    const DIGITS = "0123456789ABCDEF";

    // 나머지를 끝 자리부터 모은 뒤 뒤집는다
    let reversed = "";
    while (reading > 0) {
        reversed += DIGITS[reading % base];
        reading = reading / base;
    }
    const text = reversed.split("").reverse().join("");

    // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
    const pieces = [text[0]];
    for (let i = 1; i < text.length; i++) {
        if (DIGITS.indexOf(text[i]) < DIGITS.indexOf(text[i - 1])) {
            pieces.push(text[i]);
        } else {
            pieces[pieces.length - 1] += text[i];
        }
    }

    // 조각마다 앞자리부터 값 = 값 × base + 자리값으로 읽어 가장 큰 값을 고른다
    let largest = 0;
    for (const piece of pieces) {
        let value = 0;
        for (const ch of piece) {
            value = value * base + DIGITS.indexOf(ch);
        }
        largest = Math.max(largest, value);
    }
    return [pieces.length, largest];
}
