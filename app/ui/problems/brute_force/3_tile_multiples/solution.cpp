#include <functional>
#include <string>
#include <unordered_set>
#include <vector>

using namespace std;

int solution(string tiles, int m) {
    unordered_set<int> numbers;
    // 순열 도구가 없어서 직접 만든다: rest에서 length장을 골라 늘어놓는 모든 줄
    function<vector<string>(const string&, int)> permutations = [&](const string& rest, int length) {
        if (length == 0) return vector<string>{""};
        vector<string> out;
        for (int i = 0; i < (int)rest.size(); i++) {
            for (const string& tail : permutations(rest.substr(0, i) + rest.substr(i + 1), length - 1)) {
                out.push_back(rest[i] + tail);
            }
        }
        return out;
    };
    for (int length = 2; length <= (int)tiles.size(); length++) { // 두 장 이상
        for (const string& order : permutations(tiles, length)) {
            if (order[0] == '0') continue; // 맨 앞에 0 타일은 놓을 수 없다
            numbers.insert(stoi(order)); // 같은 수는 집합이 한 번만 남긴다(최대 8자리라 int로 충분하다)
        }
    }
    int count = 0;
    for (int x : numbers) {
        if (x % m == 0) count++;
    }
    return count;
}
