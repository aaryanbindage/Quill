# std.console input: run_all.sh feeds this "hello world", "second" and then nothing
bring std.console

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()
        line = Console.readLine()
        Main.check("read first", line == "hello world")
        line = Console.ask("")
        Main.check("read second", line == "second")
        line = Console.readLine()
        Main.check("read end", line == null)
        line = null
        if heap_live() != base:
            print("LEAK", heap_live() - base)
