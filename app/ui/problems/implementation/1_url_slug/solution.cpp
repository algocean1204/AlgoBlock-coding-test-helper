#include <string>
#include <vector>
#include <set>

using namespace std;

string solution(string title, vector<string> taken) {
    vector<string> skip = {"a", "an", "the", "of", "and"};

    // 1~2. 빈칸으로 나누고, 낱말마다 소문자로 바꿔 영문 소문자·숫자만 남긴다. 다 지워진 낱말은 뺀다
    vector<string> words;
    string kept = "";
    for (size_t i = 0; i <= title.size(); i++) {
        if (i == title.size() || title[i] == ' ') {
            if (!kept.empty()) {
                words.push_back(kept);
            }
            kept = "";
            continue;
        }
        char ch = title[i];
        if (ch >= 'A' && ch <= 'Z') {
            ch = ch - 'A' + 'a';
        }
        if ((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9')) {
            kept += ch;
        }
    }

    // 3. 규칙 3의 낱말 빼기. 다 빠져 목록이 비면 빼지 않는다
    vector<string> left;
    for (const string& word : words) {
        bool skipped = false;
        for (const string& s : skip) {
            if (word == s) {
                skipped = true;
            }
        }
        if (!skipped) {
            left.push_back(word);
        }
    }
    if (!left.empty()) {
        words = left;
    }

    // 4. 낱말 단위로 이어 붙이다가 길이가 24를 넘게 되면 멈춘다
    string slug = words[0].substr(0, 24);
    for (size_t i = 1; i < words.size(); i++) {
        if (slug.size() + 1 + words[i].size() > 24) {
            break;
        }
        slug = slug + "-" + words[i];
    }

    // 5. taken에 있으면 -2, -3, … 을 붙여 본다
    set<string> used(taken.begin(), taken.end());
    if (used.count(slug) == 0) {
        return slug;
    }
    int number = 2;
    while (used.count(slug + "-" + to_string(number)) > 0) {
        number++;
    }
    return slug + "-" + to_string(number);
}
