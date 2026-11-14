import java.io.BufferedReader;
import java.io.InputStreamReader;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        int count = Integer.parseInt(reader.readLine());
        int total = 0;
        for (int index = 0; index < count; index += 1) {
            total += Integer.parseInt(reader.readLine());
        }
        System.out.println(total);
    }
}
