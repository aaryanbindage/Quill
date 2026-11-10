# list and map literals: [a, b] and {k -> v}
class Animal:
    name: str
    def init(self, name: str):
        self.name = name

class Dog < Animal:
    def init(self, name: str):
        super.init(name)

class Kennel:
    dogs: List[Animal]
    def init(self):
        self.dogs = [new Dog("a"), new Dog("b")]
    def reset(self):
        self.dogs = []

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

    static def total(xs: List[int]) -> int:
        t: int = 0
        for x in xs:
            t += x
        return t

    static def pick() -> Map[str, int]:
        return {"x" -> 1, "y" -> 2}

    static def empty() -> List[str]:
        return []

    static def main():
        base: int = heap_live()

        a = [1, 2, 3]
        Main.check("int list", len(a) == 3 and a[0] == 1 and a[2] == 3)
        Main.check("sum", Main.total(a) == 6 and Main.total([4, 5]) == 9)

        f: List[float] = [1, 2.5]
        Main.check("widens to float", f[0] == 1.0 and f[1] == 2.5)
        g = [1, 2.5]
        Main.check("mixed numbers", g[0] == 1.0)

        s = ["x", "y"]
        Main.check("str list", s[1] == "y")
        e: List[str] = []
        e.add("hi")
        Main.check("empty with type", len(e) == 1 and e[0] == "hi")
        Main.check("empty return", len(Main.empty()) == 0)

        zoo: List[Animal] = [new Dog("rex"), new Animal("generic")]
        Main.check("subclass elements", zoo[0].name == "rex" and zoo[1].name == "generic")
        mixed = [new Dog("d"), new Animal("a")]
        Main.check("common supertype", mixed[1].name == "a")
        withnull = ["a", null, "c"]
        Main.check("null element", withnull[1] == null and withnull[2] == "c")

        grid = [[1, 2], [3, 4]]
        Main.check("nested", grid[1][0] == 3)

        m = {"one" -> 1, "two" -> 2}
        Main.check("map", m.get("two") == 2 and m.size() == 2)
        em: Map[str, int] = {}
        em.put("k", 5)
        Main.check("empty map", em.get("k") == 5)
        Main.check("map return", Main.pick().get("y") == 2)
        dup = {"a" -> 1, "a" -> 2}
        Main.check("duplicate key", dup.get("a") == 2 and dup.size() == 1)
        lists = {
            "evens" -> [2, 4],
            "odds" -> [1, 3, 5],
        }
        Main.check("map of lists", lists.get("odds")[2] == 5 and len(lists.get("evens")) == 2)
        byint = {1 -> "one", 2 -> "two"}
        Main.check("int keys", byint.get(2) == "two")

        k = new Kennel()
        Main.check("field initialiser", len(k.dogs) == 2)
        k.reset()
        Main.check("field assign", len(k.dogs) == 0)

        Main.check("temporary", len([1, 2, 3]) == 3)

        a = null
        f = null
        g = null
        s = null
        e = null
        zoo = null
        mixed = null
        withnull = null
        grid = null
        m = null
        em = null
        dup = null
        lists = null
        byint = null
        k = null
        Main.leak("literals", heap_live() - base)
