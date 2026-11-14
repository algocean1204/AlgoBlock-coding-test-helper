import java.util.ArrayList;
import java.util.List;

class Solution {
    static List<Integer> left; // 장르마다 아직 안 놓은 팀 수
    
    // remaining: 더 놓아야 할 자리 수, last: 바로 앞에 놓은 장르 번호(처음에는 -1)
    static long place(int remaining, int last) {
        if (remaining == 0) {
            return 1;
        }
        long ways = 0; // 경우의 수가 int를 넘을 수 있어 long으로 센다
        for (int genre = 0; genre < left.size(); genre++) {
            if (left.get(genre) == 0 || genre == last) { // 놓는 도중에 가지를 끊는다
                continue;
            }
            left.set(genre, left.get(genre) - 1);
            ways += place(remaining - 1, genre);
            left.set(genre, left.get(genre) + 1);
        }
        return ways;
    }

    public int solution(String[] genres) {
        // 같은 장르를 개수로 묶는다
        List<String> names = new ArrayList<>();
        left = new ArrayList<>();
        for (String genre : genres) {
            int at = names.indexOf(genre);
            if (at < 0) {
                names.add(genre);
                left.add(1);
            } else {
                left.set(at, left.get(at) + 1);
            }
        }
        return (int) place(genres.length, -1);
    }
}
