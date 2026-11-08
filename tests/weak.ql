class Parent:
    name: str
    child: Child

    def init(self, name: str):
        self.name = name

    def hello(self) -> str:
        return "hi from " + self.name

class Child:
    parent: weak Parent      # back-pointer: does not keep the parent alive
    tag: str

class Main:
    static def check(name: str, live: int):
        if live == 0:
            print("ok  ", name)
        else:
            print("LEAK", name, live)

    static def main():
        # 1. a parent<->child cycle that would leak with strong refs only
        p = new Parent("dad")
        c = new Child()
        p.child = c
        c.parent = p
        print(c.parent.hello())          # upgrade while alive
        print("same parent:", c.parent == p)
        p = null
        c = null
        Main.check("cycle freed", heap_live())

        # 2. the weak ref reads as null once the target dies
        p2 = new Parent("mom")
        c2 = new Child()
        p2.child = c2
        c2.parent = p2
        p2 = null                         # parent dies, child survives via c2
        print("parent gone:", c2.parent == null)
        c2 = null
        Main.check("dead weak ref", heap_live())

        # 3. weak locals
        a = new Parent("x")
        w: weak Parent = a
        print("weak local alive:", w == a)
        a = null
        print("weak local dead:", w == null)
        w = null
        Main.check("weak local", heap_live())

        # 4. weak survives target (memory stays valid), and re-pointing works
        q = new Parent("q")
        r = new Parent("r")
        cc = new Child()
        cc.parent = q
        cc.parent = r
        q = null
        print("repointed:", cc.parent.name)
        r = null
        cc = null
        Main.check("repoint", heap_live())

        # 5. many cyclic structures
        for i in range(100000):
            pp = new Parent("loop")
            ch = new Child()
            pp.child = ch
            ch.parent = pp
        Main.check("cycle loop", heap_live())
