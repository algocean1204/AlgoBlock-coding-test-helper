import java.util.*;

class Solution {
    static final String DIGITS = "0123456789ABCDEF";

    public long[] solution(int base, long reading) {
        // 나머지를 끝 자리부터 모은 뒤 뒤집는다
        StringBuilder reversed = new StringBuilder();
        while (reading > 0) {
            reversed.append(DIGITS.charAt((int) (reading % base)));
            reading /= base;
        }
        String text = reversed.reverse().toString();

        // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
        List<String> pieces = new ArrayList<>();
        StringBuilder piece = new StringBuilder();
        piece.append(text.charAt(0));
        for (int i = 1; i < text.length(); i++) {
            if (DIGITS.indexOf(text.charAt(i)) < DIGITS.indexOf(text.charAt(i - 1))) {
                pieces.add(piece.toString());
                piece = new StringBuilder();
            }
            piece.append(text.charAt(i));
        }
        pieces.add(piece.toString());

        // 조각마다 앞자리부터 값 = 값 × base + 자리값으로 읽어 가장 큰 값을 고른다
        long largest = 0;
        for (String p : pieces) {
            long value = 0;
            for (char ch : p.toCharArray()) {
                value = value * base + DIGITS.indexOf(ch);
            }
            largest = Math.max(largest, value);
        }
        return new long[]{pieces.size(), largest};
    }
}
