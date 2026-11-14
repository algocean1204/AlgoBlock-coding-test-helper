function solution(genres) {
    // 같은 장르를 개수로 묶는다: left[장르] = 아직 안 놓은 팀 수
    const left = new Map();
    for (const genre of genres) {
        left.set(genre, (left.get(genre) || 0) + 1);
    }

    // remaining: 더 놓아야 할 자리 수, last: 바로 앞에 놓은 장르(처음에는 null)
    function place(remaining, last) {
        if (remaining === 0) {
            return 1;
        }
        let ways = 0;
        for (const genre of left.keys()) {
            if (left.get(genre) === 0 || genre === last) { // 놓는 도중에 가지를 끊는다
                continue;
            }
            left.set(genre, left.get(genre) - 1);
            ways += place(remaining - 1, genre);
            left.set(genre, left.get(genre) + 1);
        }
        return ways;
    }

    return place(genres.length, null);
}
