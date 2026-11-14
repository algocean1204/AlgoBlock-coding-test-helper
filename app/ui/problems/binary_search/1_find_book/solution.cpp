#include <string>
#include <vector>

using namespace std;

vector<int> solution(vector<int> books, vector<int> queries) {
    vector<int> answer;
    for (int target : queries) {
        int left = 0;
        int right = (int)books.size() - 1;
        int position = -1;
        while (left <= right) {
            int mid = (left + right) / 2;
            if (books[mid] == target) {
                position = mid;
                break;
            } else if (books[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        answer.push_back(position);
    }
    return answer;
}
