# Every scenario must end with heap_live() back at its starting value (0).

class Node:
    value: int
    next: Node
    label: str

    def init(self, v: int):
        self.value = v
        self.label = "n" + "ode"

    def getLabel(self) -> str:
        return self.label

class Box:
    item: Node

    def set(self, n: Node):
        self.item = n

    static def make(v: int) -> Node:
        return new Node(v)

    static def early(flag: bool) -> str:
        s = "a" + "b"
        t: Node = new Node(1)
        if flag:
            return s + "!"          # return from inside a branch
        return "no"

class Main:
    static def check(name: str, live: int):
        if live == 0:
            print("ok  ", name)
        else:
            print("LEAK", name, live)

    static def main():
        # 1. plain locals
        a = new Node(1)
        a = new Node(2)             # reassign frees the old one
        a = null
        Main.check("locals", heap_live())

        # 2. strings built in a loop
        s = ""
        for i in range(1000):
            s = s + "x"
        print("len", len(s))
        s = ""
        Main.check("string loop", heap_live())

        # 3. a long linked list, then drop the head
        head: Node = null
        for i in range(1000):
            n = new Node(i)
            n.next = head
            head = n
        head = null
        Main.check("linked list", heap_live())

        # 4. temporaries, field-of-temporary, args, static factories
        total = 0
        for i in range(10000):
            total += Box.make(i).value
            t = Box.make(i).getLabel() + "!"
            b = new Box()
            b.set(new Node(i))
            b.set(b.item)           # self-assignment must not free
        print("total", total)
        Main.check("temporaries", heap_live())

        # 5. early return, break, continue
        for i in range(100):
            m = new Node(i)
            if i % 2 == 0:
                continue
            k = "k" + "k"
            if i > 90:
                break
            s2 = Box.early(i % 3 == 0)
        Main.check("break/continue/return", heap_live())

        # 6. copies of the same object share one allocation
        x = new Node(7)
        y = x
        z: Node = x
        print("same:", y == z, "live:", heap_live())
        x = null
        y = null
        z = null
        Main.check("aliases", heap_live())

        # 7. a million allocations should not grow memory
        for i in range(1000000):
            q = new Node(i)
            r = "temp" + "string"
        Main.check("stress", heap_live())
