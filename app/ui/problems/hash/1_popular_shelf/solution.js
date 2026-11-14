function solution(loans, k) {
    const count = new Map();  // 제목마다 지금까지 빌려진 횟수
    const shelf = [];  // 추천 서가에 꽂힌 차례대로
    for (const title of loans) {
        const now = (count.get(title) || 0) + 1;
        count.set(title, now);
        if (now === k) {  // 바로 지금 k번째로 빌려졌다
            shelf.push(title);
        }
    }
    return shelf;
}
