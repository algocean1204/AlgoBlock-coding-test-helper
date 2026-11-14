function solution(members, roles, auditions, rivals) {
    const n = members;  // 단원 수
    // scores[단원][배역] = 오디션 점수. 0은 오디션을 보지 않아 맡을 수 없다는 뜻
    const scores = Array.from({ length: n }, () => new Array(roles).fill(0));
    for (const [member, role, score] of auditions) {
        scores[member][role] = score;
    }
    const rivalMask = new Array(n).fill(0);  // 함께 무대에 설 수 없는 단원들(비트, 양쪽에 모두 적는다)
    for (const [a, b] of rivals) {
        rivalMask[a] |= 1 << b;
        rivalMask[b] |= 1 << a;
    }
    const memo = new Map();  // "몇 번 배역부터,누구를 썼는가(비트)" → 거기서 더 얻을 수 있는 가장 큰 점수

    // index번 배역부터 끝까지 정해서 더 얻을 수 있는 가장 큰 점수. 끝까지 정할 수 없으면 -1
    function best(index, used) {
        if (index === roles) {
            return 0;
        }
        const state = index + "," + used;
        if (memo.has(state)) {  // 같은 상태에 다시 왔다: 기억한 값을 쓴다
            return memo.get(state);
        }
        let result = -1;
        for (let person = 0; person < n; person++) {
            if ((used >> person & 1) === 1 || scores[person][index] === 0) {
                continue;
            }
            if ((used & rivalMask[person]) !== 0) {  // 이미 정한 단원과 부딪치면 이 가지는 버린다
                continue;
            }
            const rest = best(index + 1, used | 1 << person);
            if (rest !== -1) {  // 뒤의 배역을 끝까지 정할 수 있을 때만 후보가 된다
                result = Math.max(result, scores[person][index] + rest);
            }
        }
        memo.set(state, result);
        return result;
    }

    return best(0, 0);
}
