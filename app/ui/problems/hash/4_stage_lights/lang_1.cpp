// 언어 함정: cpp.int_overflow @ "presses의 길이는 1 이상 200,000 이하"
#include <string>
#include <vector>
#include <unordered_map>

using namespace std;

long long solution(vector<int> presses, int m) {
    // 조명 상태를 정수 하나로 담는다: k번 조명이 켜져 있으면 (k - 1)번째 비트가 1
    unordered_map<int, int> seen;  // 상태 → 지금까지 그 상태가 나온 횟수
    seen[0] = 1;  // 아무것도 누르지 않은 처음(모두 꺼짐)도 한 번
    int state = 0;
    int total = 0;
    for (int button : presses) {
        if (button == 0) {
            state = 0;  // 모두 끈다
        } else {
            state ^= 1 << (button - 1);  // 그 조명만 뒤집는다
        }
        // 앞서 지금과 같은 상태였던 때마다, 그 다음 버튼부터 지금 버튼까지가 제자리 토막이다
        total += seen[state];
        seen[state]++;
    }
    return total;
}
