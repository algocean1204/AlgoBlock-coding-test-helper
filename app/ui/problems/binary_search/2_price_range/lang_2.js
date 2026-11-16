// 언어 함정: javascript.sort_default @ "prices의 원소는 1 이상 1,000,000,000 이하"
// values에서 x 이상인 값이 처음 나오는 자리(없으면 길이)
function firstAtLeast(values, x) {
    let left = 0;
    let right = values.length;
    while (left < right) {
        const mid = Math.floor((left + right) / 2);
        if (values[mid] >= x) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}

function solution(prices, ranges) {
    // sort()는 글자 순이라 수는 비교 함수를 준다
    const sorted = [...prices].sort();
    let answer = [];
    for (const [low, high] of ranges) {
        const start = firstAtLeast(sorted, low);
        // 가격이 정수라서 'high보다 큰 값이 처음 나오는 자리' = 'high + 1 이상이 처음 나오는 자리'
        const end = firstAtLeast(sorted, high + 1);
        answer.push(end - start);
    }
    return answer;
}
