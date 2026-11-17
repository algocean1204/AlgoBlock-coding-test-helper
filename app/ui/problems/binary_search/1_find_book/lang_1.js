// 언어 함정: javascript.float_division
function solution(books, queries) {
    let answer = [];
    for (const target of queries) {
        let left = 0;
        let right = books.length - 1;
        let position = -1;
        while (left <= right) {
            const mid = (left + right) / 2;
            if (books[mid] === target) {
                position = mid;
                break;
            } else if (books[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        answer.push(position);
    }
    return answer;
}
