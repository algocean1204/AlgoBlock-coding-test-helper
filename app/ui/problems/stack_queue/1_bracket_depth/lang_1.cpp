// 언어 함정: cpp.out_of_range
#include <map>
#include <string>
#include <vector>

using namespace std;

int solution(string expr) {
    map<char, char> partner = {{')', '('}, {']', '['}, {'}', '{'}};
    vector<char> stack;
    int deepest = 0;
    for (char ch : expr) {
        if (ch == '(' || ch == '[' || ch == '{') {
            stack.push_back(ch);
            deepest = max(deepest, (int)stack.size());
        } else if (partner.count(ch)) {
            if (stack.back() != partner[ch]) {
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
