#include <string>
#include <vector>
#include <sstream>
#include <unordered_map>

using namespace std;

vector<int> solution(vector<string> log) {
    unordered_map<string, unordered_map<string, int>> count;  // 구역 → {종 → 마릿수}. 1마리 이상인 종만 둔다
    unordered_map<string, int> zonesOf;  // 종 → 그 종이 1마리 이상 있는 구역 수
    vector<int> answers;
    for (const string& line : log) {
        istringstream in(line);
        string command;
        in >> command;
        if (command == "see") {
            string zone, kind;
            int n;
            in >> zone >> kind >> n;
            unordered_map<string, int>& inZone = count[zone];
            auto found = inZone.find(kind);
            int before = found == inZone.end() ? 0 : found->second;  // 덮어쓰기 전에 지금 값을 본다
            // 종의 구역 수는 없음 → 있음, 있음 → 없음으로 바뀔 때만 달라진다
            if (before == 0 && n > 0) {
                zonesOf[kind] += 1;
            }
            if (before > 0 && n == 0) {
                zonesOf[kind] -= 1;
            }
            if (n > 0) {
                inZone[kind] = n;  // 더하지 않고 바꾼다
            } else {
                inZone.erase(kind);  // 0마리는 지운다: 구역의 종 수 = 안쪽 표의 크기
            }
        } else if (command == "zone") {
            string zone;
            in >> zone;
            auto found = count.find(zone);
            answers.push_back(found == count.end() ? 0 : (int) found->second.size());
        } else {
            string kind;
            in >> kind;
            auto found = zonesOf.find(kind);
            answers.push_back(found == zonesOf.end() ? 0 : found->second);
        }
    }
    return answers;
}
