# std.console: the parts that do not need a terminal
bring std.console

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()
        Console.init()
        Console.write("no newline, ")
        Console.writeln("then one")
        Console.flush()
        Main.check("esc", len(Console.esc()) == 1)
        Main.check("reset", len(Console.reset()) == 4)
        Main.check("paint", len(Console.paint("hi", 1)) == len(Console.fg(1)) + 2 + 4)
        Main.check("no colour", Console.fg(-1) == "" and Console.paint("x", -1) == "x" + Console.reset())
        Main.check("rgb red", Console.rgb(255, 0, 0) == 196)
        Main.check("rgb grey", Console.rgb(128, 128, 128) == 243 and Console.rgb(0, 0, 0) == 16 and Console.rgb(255, 255, 255) == 231)
        Main.check("rgb clamp", Console.rgb(999, -5, 0) == 196)
        Main.check("named", Console.red() == 1 and Console.white() == 7)
        Main.check("read at end", Console.readLine() == null)
        if heap_live() != base:
            print("LEAK", heap_live() - base)
