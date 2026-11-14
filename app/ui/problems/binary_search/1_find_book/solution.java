class Solution {
    public int[] solution(int[] books, int[] queries) {
        int[] answer = new int[queries.length];
        for (int i = 0; i < queries.length; i++) {
            int target = queries[i];
            int left = 0;
            int right = books.length - 1;
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
            answer[i] = position;
        }
        return answer;
    }
}
