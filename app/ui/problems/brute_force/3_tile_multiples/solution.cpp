#include <string>
#include <unordered_set>
#include <vector>

using namespace std;

// 순열 도구 대신 재귀로 직접 만든다: 안 쓴 타일을 하나씩 뒤에 붙여 가며 모든 순서를 본다
void build(const string& tiles, vector<bool>& used, int number, int length, unordered_set<int>& numbers) {
    if (length >= 2) {
        numbers.insert(number); // 같은 수는 집합이 한 번만 남긴다
    }
    for (int i = 0; i < (int)tiles.size(); i++) {
        if (used[i]) continue;
        if (length == 0 && tiles[i] == '0') continue; // 맨 앞에 0 타일은 놓을 수 없다
        used[i] = true;
        // 최대 8자리라 int로 충분하다
        build(tiles, used, number * 10 + (tiles[i] - '0'), length + 1, numbers);
        used[i] = false;
    }
}

int solution(string tiles, int m) {
    unordered_set<int> numbers;
    vector<bool> used(tiles.size(), false);
    build(tiles, used, 0, 0, numbers);
    int count = 0;
    for (int x : numbers) {
        if (x % m == 0) count++;
    }
    return count;
}
