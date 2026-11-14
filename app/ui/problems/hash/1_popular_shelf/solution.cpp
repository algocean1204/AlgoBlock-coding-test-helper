#include <string>
#include <vector>
#include <unordered_map>

using namespace std;

vector<string> solution(vector<string> loans, int k) {
    unordered_map<string, int> count;  // 제목마다 지금까지 빌려진 횟수 (없는 키는 0에서 시작한다)
    vector<string> shelf;  // 추천 서가에 꽂힌 차례대로
    for (const string& title : loans) {
        count[title] += 1;
        if (count[title] == k) {  // 바로 지금 k번째로 빌려졌다
            shelf.push_back(title);
        }
    }
    return shelf;
}
