// 언어 함정: cpp.int_overflow @ "reading은 1 이상 100,000,000,000,000(10^14) 이하"
#include <string>
#include <vector>
#include <algorithm>

using namespace std;

vector<long long> solution(int base, long long reading) {
    const string DIGITS = "0123456789ABCDEF";

    // 나머지를 끝 자리부터 모은 뒤 뒤집는다
    string text = "";
    while (reading > 0) {
        text += DIGITS[reading % base];
        reading /= base;
    }
    reverse(text.begin(), text.end());

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

    // 조각마다 앞자리부터 값 = 값 × base + 자리값으로 읽어 가장 큰 값을 고른다
    int largest = 0;
    for (const string& piece : pieces) {
        int value = 0;
        for (char ch : piece) {
            value = value * base + (long long) DIGITS.find(ch);
        }
        largest = max(largest, value);
    }
    return {(long long) pieces.size(), largest};
}
