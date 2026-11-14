function solution(start, goal, dictionary) {
    const words = new Set(dictionary);
    if (!words.has(goal)) return -1;
    const letters = 'abcdefghijklmnopqrstuvwxyz';

    // steps: start에서 낱말을 만들기까지 바꾼 횟수. 들어 있으면 이미 큐에 넣은 낱말이다
    const steps = new Map([[start, 0]]);
    const queue = [start];
    let head = 0; // shift()는 느릴 수 있어 읽는 위치로 큐를 흉내 낸다
    while (head < queue.length) {
        const word = queue[head++];
        if (word === goal) return steps.get(word);
        for (let i = 0; i < word.length; i++) {
            for (const ch of letters) {
                if (ch === word[i]) continue;
                const candidate = word.slice(0, i) + ch + word.slice(i + 1); // 한 자리만 바꾼 이웃 후보를 직접 만든다
                if (words.has(candidate) && !steps.has(candidate)) {
                    steps.set(candidate, steps.get(word) + 1);
                    queue.push(candidate);
                }
            }
        }
    }
    return -1;
}
