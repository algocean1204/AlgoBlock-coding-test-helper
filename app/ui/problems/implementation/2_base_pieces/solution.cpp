#include <string>
#include <vector>
#include <algorithm>

using namespace std;

const string DIGITS = "0123456789ABCDEF";

string toBase(long long reading, int base) {
    // 나머지를 끝 자리부터 모은 뒤 뒤집는다
    string text = "";
    while (reading > 0) {
        text += DIGITS[reading % base];
        reading /= base;
    }
    reverse(text.begin(), text.end());
    return text;
}

long long readBase(const string& text, int base) {
    // 앞자리부터 값 = 값 × base + 자리값
    long long value = 0;
    for (char ch : text) {
        value = value * base + (long long) DIGITS.find(ch);
    }
    return value;
}

vector<long long> solution(int base, long long reading) {
    string text = toBase(reading, base);

    // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
    vector<string> pieces;
    pieces.push_back(string(1, text[0]));
    for (size_t i = 1; i < text.size(); i++) {
        if (DIGITS.find(text[i]) < DIGITS.find(text[i - 1])) {
            pieces.push_back(string(1, text[i]));
        } else {
            pieces.back() += text[i];
        }
    }
    long long largest = 0;
    for (const string& piece : pieces) {
        long long found = readBase(piece, base);
        if (found > largest) largest = found;
    }
    return {(long long) pieces.size(), largest};
}
