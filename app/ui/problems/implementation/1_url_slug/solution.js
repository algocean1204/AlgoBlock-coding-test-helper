function solution(title, taken) {
    const skip = ["a", "an", "the", "of", "and"];

    // 1~2. 빈칸으로 나누고, 낱말마다 소문자로 바꿔 영문 소문자·숫자만 남긴다. 다 지워진 낱말은 뺀다
    let words = [];
    for (const word of title.split(" ")) {
        let kept = "";
        for (const ch of word.toLowerCase()) {
            if ((ch >= "a" && ch <= "z") || (ch >= "0" && ch <= "9")) {
                kept += ch;
            }
        }
        if (kept !== "") {
            words.push(kept);
        }
    }

    // 3. 규칙 3의 낱말 빼기. 다 빠져 목록이 비면 빼지 않는다
    const left = words.filter((word) => !skip.includes(word));
    if (left.length > 0) {
        words = left;
    }

    // 4. 낱말 단위로 이어 붙이다가 길이가 24를 넘게 되면 멈춘다
    let slug = words[0].slice(0, 24);
    for (let i = 1; i < words.length; i++) {
        if (slug.length + 1 + words[i].length > 24) {
            break;
        }
        slug = slug + "-" + words[i];
    }

    // 5. taken에 있으면 -2, -3, … 을 붙여 본다
    const used = new Set(taken);
    if (!used.has(slug)) {
        return slug;
    }
    let number = 2;
    while (used.has(slug + "-" + number)) {
        number++;
    }
    return slug + "-" + number;
}
