# uses the wrapper `quill wrap` generated from counter.hpp (see tests/run_all.sh)
bring geo

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()

        c = Counter.create2(10)
        c.add(5)
        Main.check("constructor and method", c.value() == 15)
        Main.check("default constructor", Counter.create().value() == 0)
        Main.check("double arguments", c.ratio(9.0, 3.0) == 3.0)
        Main.check("std::string in and out", c.label("n=") == "n=15")
        Main.check("static method", Counter.answer() == 42)
        Main.check("namespace function", Geo.greet("Quill") == "hello, Quill")
        Main.check("int function", Geo.clamp(50, 0, 10) == 10 and Geo.clamp(-5, 0, 10) == 0)

        msg = ""
        try:
            c.ratio(1.0, 0.0)
        catch Error as e:
            msg = e.message
        Main.check("C++ exception becomes Error", msg == "division by zero")
        msg = ""
        try:
            c.fail("boom")
        catch Error as e:
            msg = e.message
        Main.check("exception text carried over", msg == "boom")
        Main.check("error is cleared afterwards", c.value() == 15)

        same = c.self_()
        Main.check("borrowed pointer", same.value() == 15)
        same.add(1)
        Main.check("shared object", c.value() == 16)
        same = null

        c.close()
        c.close()
        Main.check("close twice is safe", true)
        msg = ""
        c = null
        msg = null
        if heap_live() - base == 0:
            print("ok   no leaks")
        else:
            print("LEAK", heap_live() - base)
