# try / catch / throw, including runtime panics and control flow out of try blocks
class AppError < Error:
    code: int
    def init(self, msg: str, code: int):
        super.init(msg)
        self.code = code

class NotFound < AppError:
    def init(self, what: str):
        super.init(what + " not found", 404)

class Odd:
    n: int

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

    static def fail(n: int) -> int:
        if n < 0:
            throw new NotFound("item")
        if n == 0:
            throw new AppError("zero", 1)
        return n

    static def deep(n: int) -> int:
        if n == 0:
            throw new Error("bottom")
        return Main.deep(n - 1) + 1

    static def early(n: int) -> int:
        try:
            if n > 0:
                return 100
            throw new Error("no")
        catch Error as e:
            return -1
        return 0

    static def main():
        # thrown objects are freed once their catch block ends, also across frames
        base: int = heap_live()
        for i in range(3):
            try:
                throw new Error("x")
            catch Error as e:
                pass
        try:
            Main.deep(4)
        catch Error as e:
            pass
        try:
            throw new NotFound("item")
        catch AppError as e:
            pass
        Main.leak("exceptions", heap_live() - base)

        # basic catch and field access
        r: int = 0
        try:
            r = Main.fail(5)
        catch Error as e:
            r = -1
        Main.check("no throw", r == 5)

        msg: str = ""
        try:
            Main.fail(-1)
        catch NotFound as e:
            msg = e.message
            r = e.code
        Main.check("subclass catch", msg == "item not found" and r == 404)

        # first matching clause wins; unmatched types fall through to the next
        which: int = 0
        try:
            Main.fail(0)
        catch NotFound as e:
            which = 1
        catch AppError as e:
            which = 2
        catch Error as e:
            which = 3
        Main.check("clause order", which == 2)

        # exceptions cross several frames
        try:
            Main.deep(5)
        catch Error as e:
            msg = e.message
        Main.check("unwinds frames", msg == "bottom")

        # nested try, rethrow when the inner clause does not match
        out: str = ""
        try:
            try:
                Main.fail(-1)
            catch Odd as o:
                out = "wrong"
            out = out + "after inner"
        catch AppError as e:
            out = out + "outer " + str(e.code)
        Main.check("propagates", out == "outer 404")

        # throwing from a catch block reaches the outer handler
        out = ""
        try:
            try:
                Main.fail(0)
            catch AppError as e:
                throw new Error("again")
        catch Error as e:
            out = e.message
        Main.check("throw in catch", out == "again")

        # runtime panics are catchable as Error
        xs: List[int] = new List[int]()
        try:
            print(xs[2])
        catch Error as e:
            msg = e.message
        Main.check("index panic", msg == "list index out of range")

        arr: Array[int] = new Array[int](2)
        try:
            arr[5] = 1
        catch Error as e:
            msg = e.message
        Main.check("array panic", msg == "index 5 out of range (length 2)")

        nul: Odd = null
        try:
            print(nul.n)
        catch Error as e:
            msg = e.message
        Main.check("null panic", msg == "null pointer dereference")

        m: Map[str, int] = new Map[str, int]()
        try:
            print(m.get("x"))
        catch Error as e:
            msg = e.message
        Main.check("map panic", msg == "key not found in map")

        # a catch-all clause takes anything, including non-Error objects
        hit: bool = false
        try:
            throw new Odd()
        catch:
            hit = true
        Main.check("catch all", hit)

        which = 0
        try:
            throw new Odd()
        catch Error as e:
            which = 1
        catch Odd as o:
            which = 2
        Main.check("non-Error object", which == 2)

        # return, break and continue out of a try block unlink the handler
        Main.check("return in try", Main.early(1) == 100)
        Main.check("return in catch", Main.early(0) == -1)
        total: int = 0
        for i in range(10):
            try:
                if i == 3:
                    continue
                if i == 6:
                    break
                total += i
            catch Error as e:
                total = -1000
        Main.check("break/continue in try", total == 0 + 1 + 2 + 4 + 5)
        # a throw after leaving the loop must not find a stale handler
        try:
            Main.fail(0)
        catch Error as e:
            total = 7
        Main.check("handler stack intact", total == 7)

        # exceptions thrown in a loop, locals modified inside try survive
        count: int = 0
        for i in range(5):
            try:
                count += 1
                Main.fail(i - 2)
                count += 10
            catch Error as e:
                count += 100
        Main.check("loop of try", count == 5 + 20 + 300)
