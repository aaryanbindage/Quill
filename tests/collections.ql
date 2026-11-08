class Node:
    id: int
    def init(self, id: int):
        self.id = id

# user-defined generic classes
class Box[T]:
    value: T
    def init(self, v: T):
        self.value = v
    def get(self) -> T:
        return self.value

class Pair[A, B]:
    first: A
    second: B
    def init(self, a: A, b: B):
        self.first = a
        self.second = b

class Main:
    static def check(name: str, live: int):
        if live == 0:
            print("ok  ", name)
        else:
            print("LEAK", name, live)

    static def main():
        # 1. List[int]: growth past the initial capacity, index, set, iterate
        xs = new List[int]()
        for i in range(100):
            xs.add(i)
        xs[50] = -1
        total = 0
        for x in xs:
            total += x
        print("list int:", xs.size(), xs[99], xs[50], total, len(xs))
        xs = null
        Main.check("list int", heap_live())

        # 2. List[str] with refcounted elements, built from temporaries
        names = new List[str]()
        for i in range(50):
            names.add("n" + "x")
        names[0] = "first" + "!"
        print("list str:", names.get(0), names.size(), names.contains("nx"), names.indexOf("nope"))
        names = null
        Main.check("list str", heap_live())

        # 3. List of objects; removing releases them
        nodes = new List[Node]()
        for i in range(10):
            nodes.add(new Node(i))
        gone = nodes.removeAt(3)
        print("removed:", gone.id, "size:", nodes.size(), "next:", nodes[3].id)
        gone = null
        last = nodes.pop()
        print("popped:", last.id)
        last = null
        nodes.insert(0, new Node(99))
        print("inserted:", nodes[0].id, nodes[1].id)
        nodes.clear()
        print("cleared:", nodes.size(), nodes.isEmpty())
        nodes = null
        Main.check("list nodes", heap_live())

        # 4. nested generics: List[List[int]] and Map[str, List[int]]
        grid = new List[List[int]]()
        for r in range(5):
            row = new List[int]()
            for c in range(5):
                row.add(r * c)
            grid.add(row)
        print("grid:", grid[4][4], grid[3].get(2), grid.size())
        grid = null
        Main.check("nested list", heap_live())

        # 5. Map[str,int]: put, update, get, has, remove, keys/values, resize
        m = new Map[str, int]()
        for i in range(2000):
            m.put("key" + "!", i)             # same key every time: one entry
        print("map same key:", m.size(), m["key!"])
        m.clear()
        keys = new List[str]()
        for i in range(500):
            k = "k" + "j"
            keys.add(k)
        m["a"] = 1
        m["b"] = 2
        m["c"] = 3
        m["b"] = 20
        print("map:", m.size(), m["a"], m["b"], m.getOr("zzz", -7), m.has("c"), m.has("q"))
        print("removed c:", m.remove("c"), "again:", m.remove("c"), "size:", m.size())
        ks = m.keys()
        vs = m.values()
        sum = 0
        for v in vs:
            sum += v
        print("keys:", ks.size(), "value sum:", sum)
        ks = null
        vs = null
        keys = null
        m = null
        Main.check("map str int", heap_live())

        # 6. Map[int, str] with many entries (forces several resizes) and removal
        big = new Map[int, str]()
        for i in range(5000):
            big[i] = "v" + "x"
        print("big map:", big.size(), big[0], big[4999], big.has(5000))
        for i in range(2500):
            big.remove(i * 2)
        print("after removes:", big.size(), big.has(0), big.has(1))
        big = null
        Main.check("big map", heap_live())

        # 7. Map with object keys (identity) and object values
        owners = new Map[Node, List[str]]()
        a = new Node(1)
        b = new Node(2)
        la = new List[str]()
        la.add("x" + "y")
        owners[a] = la
        owners[b] = new List[str]()
        print("owners:", owners.size(), owners[a].size(), owners[b].size(), owners.has(new Node(1)))
        a = null
        b = null
        la = null
        owners = null
        Main.check("map objects", heap_live())

        # 8. iterating keys with break/continue
        m2 = new Map[int, int]()
        for i in range(20):
            m2[i] = i * i
        seen = 0
        for k in m2.keys():
            if k % 2 == 0:
                continue
            if seen >= 5:
                break
            seen += 1
        print("iterated:", seen)
        m2 = null
        Main.check("break/continue", heap_live())

        # 9. user-defined generics, mixing element types
        bi = new Box[int](5)
        bs = new Box[str]("hi" + "!")
        bl = new Box[List[int]](new List[int]())
        bl.get().add(7)
        p = new Pair[str, Box[int]]("k", bi)
        print("generics:", bi.get(), bs.get(), bl.get()[0], p.first, p.second.get())
        bi = null
        bs = null
        bl = null
        p = null
        Main.check("user generics", heap_live())

        # 10. raw arrays: float and bool elements, length
        fa = new Array[float](4)
        fa[2] = 2.5
        ba = new Array[bool](3)
        ba[1] = true
        print("arrays:", fa.length, fa[2], fa[0], ba[1], ba[0])
        fa = null
        ba = null
        Main.check("arrays", heap_live())

        # 11. stress: a million list operations leave nothing behind
        for r in range(1000):
            t = new List[str]()
            for i in range(1000):
                t.add("s" + "t")
        Main.check("stress", heap_live())
