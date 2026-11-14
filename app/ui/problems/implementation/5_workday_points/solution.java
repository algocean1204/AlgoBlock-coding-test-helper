import java.util.*;

class Solution {
    static final int[] MONTH_DAYS = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    static long[] yearStart = new long[10000];

    static boolean isLeap(int year) {
        if (year % 400 == 0) return true;
        if (year % 100 == 0) return false;
        return year % 4 == 0;
    }

    static long dayNumber(String date) {
        // "YYYY-MM-DD" → 1년 1월 1일이 0, 그다음 날이 1, …
        int year = Integer.parseInt(date.substring(0, 4));
        int month = Integer.parseInt(date.substring(5, 7));
        int day = Integer.parseInt(date.substring(8, 10));
        long number = yearStart[year];
        for (int m = 1; m < month; m++) {  // 그해에 지나간 달의 날 수
            number += MONTH_DAYS[m - 1];
            if (m == 2 && isLeap(year)) {
                number += 1;
            }
        }
        return number + day - 1;
    }

    static long weekdays(long first, long last) {
        // first일째부터 last일째까지(둘 다 셈) 평일 수. 0일째가 월요일이므로 (일 번호 % 7) < 5이면 평일
        long total = last - first + 1;
        long weeks = total / 7;
        long count = weeks * 5;  // 7일 묶음마다 평일 5일. 점수 합이 약 1,300억이라 long
        for (long number = first + weeks * 7; number <= last; number++) {  // 남은 6일 이하는 하나씩 본다
            if (number % 7 < 5) {
                count++;
            }
        }
        return count;
    }

    public long[] solution(String[][] staff, String today) {
        // 해마다 '1년 1월 1일부터 그해 1월 1일까지 며칠인가'를 한 번만 구해 둔다
        long days = 0;
        for (int year = 1; year < 10000; year++) {
            yearStart[year] = days;
            days += isLeap(year) ? 366 : 365;
        }

        long todayNumber = dayNumber(today);
        TreeMap<String, Long> points = new TreeMap<>();  // TreeMap은 부서 이름을 사전 순으로 꺼낸다
        for (String[] row : staff) {
            long last = row[2].equals("-") ? todayNumber : dayNumber(row[2]);
            points.merge(row[0], weekdays(dayNumber(row[1]), last), Long::sum);
        }

        long[] answer = new long[points.size()];
        int index = 0;
        for (long value : points.values()) {
            answer[index++] = value;
        }
        return answer;
    }
}
