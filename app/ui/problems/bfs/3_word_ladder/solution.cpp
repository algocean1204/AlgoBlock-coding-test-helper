#include <queue>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

int solution(string start, string goal, vector<string> dictionary) {
    unordered_set<string> words(dictionary.begin(), dictionary.end());
    if (!words.count(goal)) return -1;

    // steps: start에서 낱말을 만들기까지 바꾼 횟수. 들어 있으면 이미 큐에 넣은 낱말이다
    unordered_map<string, int> steps;
    steps[start] = 0;
    queue<string> q;
    q.push(start);
    while (!q.empty()) {
        string word = q.front();
        q.pop();
        if (word == goal) return steps[word];
        for (size_t i = 0; i < word.size(); i++) {
            string candidate = word;
            for (char ch = 'a'; ch <= 'z'; ch++) {
                if (ch == word[i]) continue;
                candidate[i] = ch; // 한 자리만 바꾼 이웃 후보를 직접 만든다
                if (words.count(candidate) && !steps.count(candidate)) {
                    steps[candidate] = steps[word] + 1;
                    q.push(candidate);
                }
            }
        }
    }
    return -1;
}
