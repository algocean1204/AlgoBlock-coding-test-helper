// 언어 함정: java.int_overflow @ "가장 큰 조각의 값"
import java.util.*;

class Solution {
    static final String DIGITS = "0123456789ABCDEF";

    static String toBase(long reading, int base) {
        // 나머지를 끝 자리부터 모은 뒤 뒤집는다
        StringBuilder reversed = new StringBuilder();
        while (reading > 0) {
            reversed.append(DIGITS.charAt((int) (reading % base)));
            reading /= base;
        }
        return reversed.reverse().toString();
    }

    static long readBase(String text, int base) {
        // 앞자리부터 값 = 값 × base + 자리값
        int value = 0;
        for (char ch : text.toCharArray()) {
            value = value * base + DIGITS.indexOf(ch);
        }
        return value;
    }

    public long[] solution(int base, long reading) {
        String text = toBase(reading, base);

        // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
        List<String> pieces = new ArrayList<>();
        pieces.add(text.substring(0, 1));
        for (int i = 1; i < text.length(); i++) {
            if (DIGITS.indexOf(text.charAt(i)) < DIGITS.indexOf(text.charAt(i - 1))) {
                pieces.add(text.substring(i, i + 1));
            } else {
                pieces.set(pieces.size() - 1, pieces.get(pieces.size() - 1) + text.charAt(i));
            }
        }
        long largest = 0;
        for (String piece : pieces) {
            long found = readBase(piece, base);
            if (found > largest) largest = found;
        }
        return new long[]{pieces.size(), largest};
    }
}
