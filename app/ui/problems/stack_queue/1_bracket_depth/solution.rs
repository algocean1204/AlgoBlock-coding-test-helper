fn solution(expr: String) -> i32 {
    let mut stack: Vec<char> = Vec::new();
    let mut deepest: i32 = 0;
    for ch in expr.chars() {
        if ch == '(' || ch == '[' || ch == '{' {
            stack.push(ch);
            deepest = deepest.max(stack.len() as i32);
        } else if ch == ')' || ch == ']' || ch == '}' {
            let open = if ch == ')' { '(' } else if ch == ']' { '[' } else { '{' };
            if stack.last() != Some(&open) {
                return -1;
            }
            stack.pop();
        }
    }
    if !stack.is_empty() {
        return -1;
    }
    deepest
}
