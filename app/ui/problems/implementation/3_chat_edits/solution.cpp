#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <sstream>

using namespace std;

vector<string> solution(vector<string> records) {
    // 첫 번째 훑기: 메시지마다 마지막 상태(보낸이, 마지막 내용, 고친 적 있는가, 지워졌는가)를 모은다
    vector<string> order;
    unordered_map<string, string> sender, text;
    unordered_set<string> edited, deleted;
    for (const string& record : records) {
        istringstream in(record);
        string kind, number, a, b;
        in >> kind >> number;
        if (kind == "SEND") {
            in >> a >> b;
            order.push_back(number);
            sender[number] = a;
            text[number] = b;
        } else if (kind == "EDIT") {
            in >> a;
            text[number] = a;
            edited.insert(number);
        } else {
            deleted.insert(number);
        }
    }

    // 두 번째 훑기: 남은 메시지를 보낸 순서대로 보며, 바로 앞 줄과 보낸이가 같으면 그 줄에 붙인다
    vector<string> lines;
    string lineSender = "";
    for (const string& number : order) {
        if (deleted.count(number)) {
            continue;
        }
        string shown = text[number] + (edited.count(number) ? "*" : "");
        if (!lines.empty() && lineSender == sender[number]) {
            lines.back() += " " + shown;
        } else {
            lines.push_back(sender[number] + ": " + shown);
            lineSender = sender[number];
        }
    }
    return lines;
}
