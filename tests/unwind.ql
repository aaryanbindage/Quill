# exceptions release everything the skipped frames owned
class Obj:
    tag: str
    def init(self, tag: str):
        self.tag = tag
    def fail(self) -> int:
        throw new Error("fail " + self.tag)
    def me(self) -> Obj:
        return self

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

    static def boom() -> int:
        throw new Error("boom")

    # object parameters and locals in every skipped frame
    static def deep(o: Obj, n: int) -> int:
        local: Obj = new Obj("local")
        if n == 0:
            throw new Error("bottom")
        return Main.deep(o, n - 1) + 1

    static def two(a: Obj, b: int) -> int:
        return b

    static def with_list() -> int:
        xs: List[int] = new List[int]()
        xs.add(1)
        return xs.get(5)

    static def loop_throw(xs: List[Obj]) -> int:
        for x in xs:
            if x.tag == "bad":
                throw new Error("bad element")
        return 0

    static def guarded(o: Obj) -> int:
        try:
            return o.fail()
        finally:
            local: Obj = new Obj("in finally")

    static def main():
        base: int = heap_live()

        o: Obj = new Obj("param")
        try:
            Main.deep(o, 5)
        catch Error as e:
            pass
        o = null
        Main.leak("frames with params and locals", heap_live() - base)

        try:
            Main.with_list()
        catch Error as e:
            Main.check("message", e.message == "list index out of range")
        Main.leak("panic inside List.get", heap_live() - base)

        # temporaries that were being passed when the callee threw
        try:
            Main.two(new Obj("temp"), Main.boom())
        catch Error as e:
            pass
        Main.leak("argument temporaries", heap_live() - base)

        # a temporary receiver
        try:
            new Obj("recv").fail()
        catch Error as e:
            Main.check("receiver message", e.message == "fail recv")
        Main.leak("receiver temporary", heap_live() - base)

        # a for-each loop whose hidden iterator is skipped
        items: List[Obj] = [new Obj("a"), new Obj("bad"), new Obj("c")]
        try:
            Main.loop_throw(items)
        catch Error as e:
            pass
        items = null
        Main.leak("for-each", heap_live() - base)

        # finally with objects, exception in flight
        o = new Obj("g")
        try:
            Main.guarded(o)
        catch Error as e:
            pass
        o = null
        Main.leak("finally", heap_live() - base)

        # catch in the middle of the stack, then keep going
        count: int = 0
        for i in range(50):
            try:
                try:
                    Main.deep(new Obj("x"), 3)
                catch Error as e:
                    count += 1
                    throw new Error("again")
            catch Error as e:
                count += 1
        Main.check("repeated", count == 100)
        Main.leak("repeated", heap_live() - base)
