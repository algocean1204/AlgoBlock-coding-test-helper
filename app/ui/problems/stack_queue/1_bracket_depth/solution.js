function solution(expr) {
    const partner = { ')': '(', ']': '[', '}': '{' };
    const stack = [];
    let deepest = 0;
    for (const ch of expr) {
        if (ch === '(' || ch === '[' || ch === '{') {
            stack.push(ch);
            deepest = Math.max(deepest, stack.length);
        } else if (ch in partner) {
            if (stack.length === 0 || stack[stack.length - 1] !== partner[ch]) {
                return -1;
            }
            stack.pop();
        }
    }
    if (stack.length > 0) {
        return -1;
    }
    return deepest;
}
