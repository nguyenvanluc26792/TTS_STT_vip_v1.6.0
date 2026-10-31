import java.util.regex.*;

public class TestRegex {
    public static void main(String[] args) {
        String regex = "(?<!\\d),\\s*(?!——)";
        String[] samples = {
            "nói thế, nhưng cô ấy",
            "mẹ, con về rồi",
            "quá, không thể tin được",
            "1,5 tỷ đồng",
            "ngươi, chính ngươi, phải chết!",
            "nói xong, —— hắn bước đi"
        };
        for (String s : samples) {
            String res = s.replaceAll(regex, ", —— ");
            System.out.println("Orig: " + s.length() + " -> Res: " + res.length() + " | Changed: " + (!s.equals(res)));
        }
    }
}
