# methods on int, float, bool and str
class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()
        s = "  Hello, World  "
        Main.check("upper lower", "abC".upper() == "ABC" and "abC".lower() == "abc" and "abc".capitalize() == "Abc")
        Main.check("trim", s.trim() == "Hello, World" and "".trim() == "" and "   ".trim() == "")
        Main.check("length", "abc".length() == 3 and "".isEmpty() and not "a".isEmpty())
        Main.check("search", "banana".indexOf("nan") == 2 and "banana".indexOf("x") == -1 and "banana".contains("ana"))
        Main.check("starts ends", "hello".startsWith("he") and "hello".endsWith("llo") and not "hello".startsWith("lo"))
        Main.check("count", "banana".count("an") == 2 and "aaaa".count("aa") == 2)
        Main.check("substring", "hello".substring(1, 3) == "el" and "hello".substring(0, 0) == "")
        Main.check("charAt", "hello".charAt(1) == "e" and "A".byteAt(0) == 65)
        Main.check("replace", "a-b-c".replace("-", "+") == "a+b+c" and "aaa".replace("aa", "b") == "ba" and "x".replace("x", "") == "")
        parts = "a,b,,c".split(",")
        Main.check("split", parts.size() == 4 and parts.get(0) == "a" and parts.get(2) == "" and parts.get(3) == "c")
        chars = "abc".split("")
        Main.check("split chars", chars.size() == 3 and chars.get(2) == "c")
        Main.check("join", ", ".join(parts) == "a, b, , c")
        Main.check("repeat reverse", "ab".repeat(3) == "ababab" and "abc".reverse() == "cba" and "x".repeat(0) == "")
        Main.check("pad", "7".padLeft(3, "0") == "007" and "ab".padRight(4, ".") == "ab..")
        Main.check("toInt", "42".toInt() == 42 and "-7".toInt() == -7 and " +5 ".toInt() == 5)
        Main.check("toFloat", "2.5".toFloat() == 2.5 and "-0.5".toFloat() == -0.5 and "1e3".toFloat() == 1000.0 and "3".toFloat() == 3.0)
        Main.check("lines", "a\nb".lines().size() == 2)

        n = 42
        Main.check("int toString", n.toString() == "42" and (0 - 5).toString() == "-5")
        Main.check("int math", (0 - 3).abs() == 3 and n.sign() == 1 and n.min(7) == 7 and n.max(100) == 100 and n.clamp(0, 10) == 10)
        Main.check("int even odd", n.isEven() and 7.isOdd() and not 7.isEven())
        Main.check("pow", 2.pow(10) == 1024 and 3.pow(0) == 1)
        Main.check("hex binary", 255.toHex() == "ff" and 5.toBinary() == "101" and 0.toHex() == "0" and (0 - 1).toHex() == "ffffffffffffffff")
        Main.check("toFloat int", 3.toFloat() == 3.0)

        x = 2.7
        Main.check("float toString", 1.5.toString() == "1.5")
        Main.check("float round", x.floor() == 2 and x.ceil() == 3 and x.round() == 3 and (0.0 - x).floor() == -3 and (0.0 - x).ceil() == -2 and (0.0 - 2.5).round() == -3 and 2.5.round() == 3)
        Main.check("float misc", x.toInt() == 2 and (0.0 - x).abs() == 2.7 and x.sign() == 1 and x.min(1.0) == 1.0 and x.clamp(0.0, 1.0) == 1.0)
        Main.check("nan", (0.0 / 0.0).isNaN() and not x.isNaN())
        Main.check("bool", true.toString() == "true" and false.toString() == "false")
        Main.check("chain", " Ab ".trim().lower().repeat(2) == "abab")

        caught = ""
        try:
            "abc".toInt()
        catch Error as e:
            caught = e.message
        Main.check("bad number", caught == "toInt: \"abc\" is not a number")
        caught = ""
        try:
            "abc".substring(2, 9)
        catch Error as e:
            caught = e.message
        Main.check("bad range", caught.contains("outside"))
        caught = ""
        t: str = null
        try:
            t.upper()
        catch Error as e:
            caught = e.message
        Main.check("null string", caught.contains("null"))

        parts = null
        chars = null
        caught = ""
        s = ""
        if heap_live() != base:
            print("LEAK", heap_live() - base)
