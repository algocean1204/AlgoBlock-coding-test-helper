// 언어 함정: cpp.out_of_range
#include <string>
#include <vector>

using namespace std;

int solution(string expr) {
    vector<char> stack;
    int deepest = 0;
    for (char ch : expr) {
        if (ch == '(' || ch == '[' || ch == '{') {
            stack.push_back(ch);
            deepest = max(deepest, (int)stack.size());
        } else if (ch == ')' || ch == ']' || ch == '}') {
            char open = ch == ')' ? '(' : (ch == ']' ? '[' : '{');
            if (stack.back() != open) {
                return -1;
            }
            stack.pop_back();
        }
    }
    if (!stack.empty()) {
        return -1;
    }
    return deepest;
}
