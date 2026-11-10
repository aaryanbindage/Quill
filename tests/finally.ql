# finally blocks: normal exit, caught and uncaught exceptions, return/break/continue
class Log:
    text: str
    def init(self):
        self.text = ""
    def add(self, s: str):
        self.text = self.text + s

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def leak(name: str, live: int):
        if live == 0:
            print("ok  ", name)
        else:
            print("LEAK", name, live)

    static def normal(l: Log):
        try:
            l.add("a")
        finally:
            l.add("F")
        l.add("z")

    static def caught(l: Log):
        try:
            l.add("a")
            throw new Error("x")
        catch Error as e:
            l.add("c")
        finally:
            l.add("F")
        l.add("z")

    static def passes_through(l: Log):
        try:
            l.add("a")
            throw new Error("boom")
        finally:
            l.add("F")
        l.add("never")

    static def returns(l: Log) -> int:
        try:
            l.add("a")
            return 7
        finally:
            l.add("F")
        return 0

    static def nested(l: Log):
        try:
            try:
                l.add("a")
                throw new Error("x")
            finally:
                l.add("1")
        finally:
            l.add("2")

    static def from_catch(l: Log):
        try:
            try:
                throw new Error("first")
            catch Error as e:
                l.add("c")
                throw new Error("second")
            finally:
                l.add("F")
        catch Error as e:
            l.add(e.message)

    static def override(l: Log) -> int:
        try:
            return 1
        finally:
            l.add("F")
            return 2

    static def main():
        # finally blocks and thrown objects release everything they own
        base: int = heap_live()
        for i in range(3):
            try:
                try:
                    throw new Error("x")
                finally:
                    s: str = "a" + "b"
            catch Error as e:
                pass
        for i in range(3):
            try:
                if i == 1:
                    continue
                s2: str = "c" + "d"
            finally:
                s3: str = "e" + "f"
        Main.leak("finally", heap_live() - base)
        l: Log = new Log()
        Main.normal(l)
        Main.check("normal", l.text == "aFz")

        l = new Log()
        Main.caught(l)
        Main.check("caught", l.text == "acFz")

        l = new Log()
        try:
            Main.passes_through(l)
        catch Error as e:
            l.add(e.message)
        Main.check("uncaught runs finally", l.text == "aFboom")

        l = new Log()
        r: int = Main.returns(l)
        Main.check("return", r == 7 and l.text == "aF")

        l = new Log()
        try:
            Main.nested(l)
        catch Error as e:
            l.add("!")
        Main.check("nested order", l.text == "a12!")

        l = new Log()
        Main.from_catch(l)
        Main.check("throw in catch", l.text == "cFsecond")

        l = new Log()
        Main.check("finally return wins", Main.override(l) == 2)

        # break and continue run the finally block of every try they leave
        l = new Log()
        for i in range(5):
            try:
                if i == 1:
                    continue
                if i == 3:
                    break
                l.add("b")
            finally:
                l.add("F")
        Main.check("loop exits", l.text == "bFFbFF")

        # panics go through finally too
        l = new Log()
        xs: Array[int] = new Array[int](1)
        try:
            try:
                print(xs[1])
            finally:
                l.add("F")
        catch Error as e:
            l.add("!")
        Main.check("panic", l.text == "F!")

        # the handler stack is clean afterwards
        l = new Log()
        try:
            throw new Error("later")
        catch Error as e:
            l.add("ok")
        Main.check("stack", l.text == "ok")

